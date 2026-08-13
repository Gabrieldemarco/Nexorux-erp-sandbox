from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.fiscal_document import FiscalDocument
from app.models.invoice import Invoice
from app.schemas.fiscal_document import (
    FiscalDocumentCreate,
    FiscalDocumentUpdate,
    FiscalDocumentResponse,
    FiscalDocumentIssueRequest,
    FiscalDocumentSendRequest,
    FiscalDocumentRetryRequest,
    FiscalDocumentSendTaskResponse,
)
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_FISCAL_DOCUMENTS_CREATE,
    PERMISSION_FISCAL_DOCUMENTS_DELETE,
    PERMISSION_FISCAL_DOCUMENTS_ISSUE,
    PERMISSION_FISCAL_DOCUMENTS_QUERY,
    PERMISSION_FISCAL_DOCUMENTS_READ,
    PERMISSION_FISCAL_DOCUMENTS_RETRY,
    PERMISSION_FISCAL_DOCUMENTS_SEND,
    PERMISSION_FISCAL_DOCUMENTS_UPDATE,
)
from app.tasks.fiscal_tasks import send_cfe_async
from celery.result import AsyncResult

from app.models.user import User
from app.services.fiscal.engine import FiscalEngine, FiscalEngineError, FiscalDocumentNotFoundError
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=FiscalDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_fiscal_document(
    fiscal_document: FiscalDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_CREATE)),
):
    """Create a new fiscal document within the current user's tenant."""
    logger.info("create_fiscal_document_called", tenant_id=fiscal_document.tenant_id)

    if str(fiscal_document.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a fiscal document for a different tenant",
        )

    invoice_result = await db.execute(
        select(Invoice).where(
            Invoice.id == fiscal_document.invoice_id,
            Invoice.tenant_id == current_user.tenant_id,
        )
    )
    invoice = invoice_result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    existing = await db.execute(
        select(FiscalDocument.id).where(
            FiscalDocument.tenant_id == current_user.tenant_id,
            FiscalDocument.invoice_id == fiscal_document.invoice_id,
            FiscalDocument.series == fiscal_document.series,
            FiscalDocument.number == fiscal_document.number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un documento fiscal con esa serie/número para esta factura",
        )

    data = fiscal_document.model_dump()
    data["tenant_id"] = current_user.tenant_id
    data["company_id"] = fiscal_document.company_id or invoice.company_id
    fiscal_document_obj = FiscalDocument(**data)
    db.add(fiscal_document_obj)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo crear el documento fiscal (conflicto de datos)",
        )
    await db.refresh(fiscal_document_obj)
    return fiscal_document_obj


@router.get("/", response_model=List[FiscalDocumentResponse])
async def list_fiscal_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_READ)),
):
    """List fiscal documents for the current user's tenant."""
    logger.info("list_fiscal_documents_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(FiscalDocument).where(FiscalDocument.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    fiscal_documents = result.scalars().all()
    return fiscal_documents


@router.get("/{fiscal_document_id}", response_model=FiscalDocumentResponse)
async def get_fiscal_document(
    fiscal_document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_READ)),
):
    """Get a specific fiscal document by ID for the current tenant."""
    logger.info("get_fiscal_document_called", fiscal_document_id=fiscal_document_id, tenant_id=current_user.tenant_id)
    stmt = select(FiscalDocument).where(
        FiscalDocument.id == fiscal_document_id,
        FiscalDocument.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    fiscal_document_obj = result.scalar_one_or_none()
    if not fiscal_document_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal document not found",
        )
    return fiscal_document_obj


@router.put("/{fiscal_document_id}", response_model=FiscalDocumentResponse)
async def update_fiscal_document(
    fiscal_document_id: str,
    fiscal_document: FiscalDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_UPDATE)),
):
    """Update a fiscal document within the current user's tenant."""
    logger.info("update_fiscal_document_called", fiscal_document_id=fiscal_document_id, tenant_id=current_user.tenant_id)
    stmt = select(FiscalDocument).where(
        FiscalDocument.id == fiscal_document_id,
        FiscalDocument.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    fiscal_document_obj = result.scalar_one_or_none()
    if not fiscal_document_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal document not found",
        )

    update_data = fiscal_document.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fiscal_document_obj, field, value)

    await db.commit()
    await db.refresh(fiscal_document_obj)
    return fiscal_document_obj


@router.delete("/{fiscal_document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fiscal_document(
    fiscal_document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_DELETE)),
):
    """Delete a fiscal document within the current user's tenant."""
    logger.info("delete_fiscal_document_called", fiscal_document_id=fiscal_document_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        FiscalDocument,
        fiscal_document_id,
        current_user.tenant_id,
        not_found_detail="Fiscal document not found",
    )


@router.post("/{fiscal_document_id}/issue", response_model=FiscalDocumentResponse)
async def issue_fiscal_document(
    fiscal_document_id: str,
    payload: FiscalDocumentIssueRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_ISSUE)),
):
    """Issue a fiscal document: build CFE XML and sign it."""
    logger.info("issue_fiscal_document_called", fiscal_document_id=fiscal_document_id, certificate_id=payload.certificate_id)

    stmt = select(FiscalDocument).where(
        FiscalDocument.id == fiscal_document_id,
        FiscalDocument.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    fiscal_doc = result.scalar_one_or_none()
    if not fiscal_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal document not found",
        )

    try:
        engine = FiscalEngine(db)
        updated_fiscal_doc = await engine.issue_cfe(
            invoice_id=fiscal_doc.invoice_id,
            certificate_id=payload.certificate_id,
            tenant_id=current_user.tenant_id,
        )
    except FiscalDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except FiscalEngineError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await db.commit()
    await db.refresh(updated_fiscal_doc)
    return updated_fiscal_doc


@router.post("/{fiscal_document_id}/send", response_model=FiscalDocumentSendTaskResponse)
async def send_fiscal_document(
    fiscal_document_id: str,
    payload: FiscalDocumentSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_SEND)),
):
    """Send a fiscal document to DGI asynchronously."""
    logger.info("send_fiscal_document_called", fiscal_document_id=fiscal_document_id, environment=payload.environment)

    stmt = select(FiscalDocument).where(
        FiscalDocument.id == fiscal_document_id,
        FiscalDocument.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    fiscal_document_obj = result.scalar_one_or_none()
    if not fiscal_document_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal document not found",
        )

    task = send_cfe_async.delay(
        fiscal_document_id=str(fiscal_document_id),
        tenant_id=str(current_user.tenant_id),
        environment=payload.environment,
        certificate_id=str(payload.certificate_id) if payload.certificate_id else None,
    )

    logger.info("send_fiscal_document_enqueued", task_id=task.id, fiscal_document_id=fiscal_document_id)

    return FiscalDocumentSendTaskResponse(
        task_id=task.id,
        status="queued",
        fiscal_document_id=fiscal_document_id,
    )


@router.get("/{fiscal_document_id}/query-status", response_model=dict)
async def query_fiscal_document_status(
    fiscal_document_id: str,
    environment: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_QUERY)),
):
    """Query fiscal document status from DGI."""
    logger.info("query_fiscal_document_status_called", fiscal_document_id=fiscal_document_id, environment=environment)

    try:
        engine = FiscalEngine(db)
        response = await engine.query_status(
            fiscal_document_id=UUID(fiscal_document_id),
            tenant_id=current_user.tenant_id,
            environment=environment,
        )
    except FiscalDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except FiscalEngineError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return response


@router.post("/{fiscal_document_id}/retry", response_model=FiscalDocumentResponse)
async def retry_fiscal_document(
    fiscal_document_id: str,
    payload: FiscalDocumentRetryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_RETRY)),
):
    """Retry sending a rejected fiscal document."""
    logger.info("retry_fiscal_document_called", fiscal_document_id=fiscal_document_id)

    try:
        engine = FiscalEngine(db)
        fiscal_doc = await engine.retry_cfe(
            fiscal_document_id=UUID(fiscal_document_id),
            tenant_id=current_user.tenant_id,
        )
    except FiscalDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except FiscalEngineError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await db.commit()
    await db.refresh(fiscal_doc)
    return fiscal_doc


@router.get("/tasks/{task_id}", response_model=dict)
async def get_send_task_status(task_id: str, current_user: User = Depends(require_permissions(PERMISSION_FISCAL_DOCUMENTS_READ))):
    """Get the status of an async CFE send task."""
    from app.core.celery_app import celery_app
    task_result = AsyncResult(task_id, app=celery_app)
    result = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
    }
    return result
