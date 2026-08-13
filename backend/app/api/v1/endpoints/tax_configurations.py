from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.config import settings
from app.db.session import get_db, set_tenant_guc, reload_after_commit
from app.db.tenant_delete import delete_tenant_entity
from app.models.tax_configuration import TaxConfiguration
from app.schemas.tax_configuration import (
    TaxConfigurationCreate,
    TaxConfigurationUpdate,
    TaxConfigurationResponse,
)
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_TAX_CONFIGURATIONS_CREATE,
    PERMISSION_TAX_CONFIGURATIONS_DELETE,
    PERMISSION_TAX_CONFIGURATIONS_READ,
    PERMISSION_TAX_CONFIGURATIONS_UPDATE,
)
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=TaxConfigurationResponse)
async def create_tax_configuration(
    tax_configuration: TaxConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TAX_CONFIGURATIONS_CREATE)),
):
    """Create a new tax configuration within the current user's tenant."""
    logger.info(
        "create_tax_configuration_called",
        tax_code=tax_configuration.tax_code,
        tenant_id=str(current_user.tenant_id),
    )

    if str(tax_configuration.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a tax configuration for a different tenant",
        )

    company_id = tax_configuration.company_id or current_user.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu usuario no tiene company_id; no se puede crear el impuesto.",
        )
    if current_user.company_id and str(company_id) != str(current_user.company_id):
        company_id = current_user.company_id

    effective_from = tax_configuration.effective_from or datetime.now(timezone.utc)

    if settings.RLS_TENANT_CONTEXT_ENABLED:
        await set_tenant_guc(db, current_user.tenant_id)

    tax_configuration_obj = TaxConfiguration(
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        tax_code=tax_configuration.tax_code.strip(),
        description=tax_configuration.description,
        rate=tax_configuration.rate,
        effective_from=effective_from,
        effective_to=tax_configuration.effective_to,
        metadata_json=tax_configuration.metadata or {},
    )
    db.add(tax_configuration_obj)
    try:
        await db.flush()  # assign PK / server defaults before commit
        await db.commit()
        # FORCE RLS can make refresh() fail after COMMIT; reload with GUC re-applied.
        tax_configuration_obj = await reload_after_commit(
            db, tax_configuration_obj, current_user.tenant_id
        )
    except IntegrityError as exc:
        await db.rollback()
        logger.exception("create_tax_configuration_integrity_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo guardar el impuesto (datos inválidos o duplicados).",
        ) from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("create_tax_configuration_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Error de base de datos al crear el impuesto. "
                "Si RLS está activo, verificá RLS_TENANT_CONTEXT_ENABLED=true y reiniciá el API."
            ),
        ) from exc

    return TaxConfigurationResponse.model_validate(tax_configuration_obj)


@router.get("/", response_model=List[TaxConfigurationResponse])
async def list_tax_configurations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TAX_CONFIGURATIONS_READ)),
):
    """List tax configurations for the current user's tenant."""
    logger.info(
        "list_tax_configurations_called",
        skip=skip,
        limit=limit,
        tenant_id=str(current_user.tenant_id),
    )
    stmt = (
        select(TaxConfiguration)
        .where(TaxConfiguration.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [TaxConfigurationResponse.model_validate(row) for row in rows]


@router.get("/{tax_configuration_id}", response_model=TaxConfigurationResponse)
async def get_tax_configuration(
    tax_configuration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TAX_CONFIGURATIONS_READ)),
):
    """Get a specific tax configuration by ID for the current tenant."""
    logger.info(
        "get_tax_configuration_called",
        tax_configuration_id=tax_configuration_id,
        tenant_id=str(current_user.tenant_id),
    )
    stmt = select(TaxConfiguration).where(
        TaxConfiguration.id == tax_configuration_id,
        TaxConfiguration.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    tax_configuration_obj = result.scalar_one_or_none()
    if not tax_configuration_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax configuration not found",
        )
    return TaxConfigurationResponse.model_validate(tax_configuration_obj)


@router.put("/{tax_configuration_id}", response_model=TaxConfigurationResponse)
async def update_tax_configuration(
    tax_configuration_id: str,
    tax_configuration: TaxConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TAX_CONFIGURATIONS_UPDATE)),
):
    """Update a tax configuration by ID for the current tenant."""
    logger.info(
        "update_tax_configuration_called",
        tax_configuration_id=tax_configuration_id,
        tenant_id=str(current_user.tenant_id),
    )
    stmt = select(TaxConfiguration).where(
        TaxConfiguration.id == tax_configuration_id,
        TaxConfiguration.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    tax_configuration_obj = result.scalar_one_or_none()
    if not tax_configuration_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax configuration not found",
        )

    update_data = tax_configuration.model_dump(exclude_unset=True, by_alias=False)
    for field, value in update_data.items():
        if field == "metadata":
            setattr(tax_configuration_obj, "metadata_json", value or {})
        elif value is not None:
            setattr(tax_configuration_obj, field, value)

    try:
        await db.commit()
        tax_configuration_obj = await reload_after_commit(
            db, tax_configuration_obj, current_user.tenant_id
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.exception("update_tax_configuration_db_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de base de datos al actualizar el impuesto.",
        ) from exc

    return TaxConfigurationResponse.model_validate(tax_configuration_obj)


@router.delete("/{tax_configuration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tax_configuration(
    tax_configuration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TAX_CONFIGURATIONS_DELETE)),
):
    """Delete a tax configuration by ID for the current tenant."""
    logger.info(
        "delete_tax_configuration_called",
        tax_configuration_id=tax_configuration_id,
        tenant_id=str(current_user.tenant_id),
    )
    await delete_tenant_entity(
        db,
        TaxConfiguration,
        tax_configuration_id,
        current_user.tenant_id,
        not_found_detail="Tax configuration not found",
    )
