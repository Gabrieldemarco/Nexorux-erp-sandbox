from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.config import settings
from app.db.session import get_db, set_tenant_guc, reload_after_commit
from app.db.tenant_delete import delete_tenant_entity
from app.models.certificate import Certificate
from app.schemas.certificate import CertificateCreate, CertificateUpdate, CertificateResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_CERTIFICATES_CREATE,
    PERMISSION_CERTIFICATES_DELETE,
    PERMISSION_CERTIFICATES_READ,
    PERMISSION_CERTIFICATES_UPDATE,
)
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=CertificateResponse)
async def create_certificate(
    certificate: CertificateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CERTIFICATES_CREATE)),
):
    """Create a new certificate within the current user's tenant."""
    logger.info("create_certificate_called", name=certificate.name, tenant_id=str(current_user.tenant_id))

    if str(certificate.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a certificate for a different tenant",
        )

    company_id = certificate.company_id or current_user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu usuario no tiene company_id; no se puede crear el certificado.",
        )
    if current_user.company_id and str(company_id) != str(current_user.company_id):
        # Keep certificates scoped to the caller's company for now
        company_id = current_user.company_id

    if settings.RLS_TENANT_CONTEXT_ENABLED:
        await set_tenant_guc(db, current_user.tenant_id)

    certificate_obj = Certificate(
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        name=certificate.name.strip(),
        thumbprint=certificate.thumbprint.strip(),
        issued_at=certificate.issued_at,
        expires_at=certificate.expires_at,
        usage=(certificate.usage or "signing").strip() or "signing",
        is_active=True if certificate.is_active is None else bool(certificate.is_active),
        metadata_json=certificate.metadata or {},
    )
    db.add(certificate_obj)
    try:
        await db.flush()
        await db.commit()
        certificate_obj = await reload_after_commit(db, certificate_obj, current_user.tenant_id)
    except IntegrityError as exc:
        await db.rollback()
        logger.exception("create_certificate_integrity_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo guardar el certificado (datos inválidos o duplicados).",
        ) from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("create_certificate_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Error de base de datos al crear el certificado. "
                "Si RLS está activo, verificá RLS_TENANT_CONTEXT_ENABLED=true y reiniciá el API."
            ),
        ) from exc

    return CertificateResponse.model_validate(certificate_obj)


@router.get("/", response_model=List[CertificateResponse])
async def list_certificates(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CERTIFICATES_READ)),
):
    """List certificates for the current user's tenant."""
    logger.info("list_certificates_called", skip=skip, limit=limit, tenant_id=str(current_user.tenant_id))
    stmt = (
        select(Certificate)
        .where(Certificate.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [CertificateResponse.model_validate(row) for row in result.scalars().all()]


@router.get("/{certificate_id}", response_model=CertificateResponse)
async def get_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CERTIFICATES_READ)),
):
    """Get a specific certificate by ID for the current tenant."""
    logger.info("get_certificate_called", certificate_id=certificate_id, tenant_id=str(current_user.tenant_id))
    stmt = select(Certificate).where(
        Certificate.id == certificate_id,
        Certificate.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    certificate_obj = result.scalar_one_or_none()
    if not certificate_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
    return CertificateResponse.model_validate(certificate_obj)


@router.put("/{certificate_id}", response_model=CertificateResponse)
async def update_certificate(
    certificate_id: str,
    certificate: CertificateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CERTIFICATES_UPDATE)),
):
    """Update a certificate by ID for the current tenant."""
    logger.info("update_certificate_called", certificate_id=certificate_id, tenant_id=str(current_user.tenant_id))
    stmt = select(Certificate).where(
        Certificate.id == certificate_id,
        Certificate.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    certificate_obj = result.scalar_one_or_none()
    if not certificate_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    update_data = certificate.model_dump(exclude_unset=True, by_alias=False)
    for field, value in update_data.items():
        if field == "metadata":
            setattr(certificate_obj, "metadata_json", value or {})
        elif value is not None:
            setattr(certificate_obj, field, value)

    try:
        await db.commit()
        certificate_obj = await reload_after_commit(db, certificate_obj, current_user.tenant_id)
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("update_certificate_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de base de datos al actualizar el certificado.",
        ) from exc

    return CertificateResponse.model_validate(certificate_obj)


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CERTIFICATES_DELETE)),
):
    """Delete a certificate by ID for the current tenant."""
    logger.info("delete_certificate_called", certificate_id=certificate_id, tenant_id=str(current_user.tenant_id))
    await delete_tenant_entity(
        db,
        Certificate,
        certificate_id,
        current_user.tenant_id,
        not_found_detail="Certificate not found",
    )
