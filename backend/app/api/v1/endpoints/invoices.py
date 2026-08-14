from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db, reload_after_commit
from app.db.tenant_delete import delete_tenant_entity
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_INVOICES_CREATE,
    PERMISSION_INVOICES_DELETE,
    PERMISSION_INVOICES_READ,
    PERMISSION_INVOICES_UPDATE
)
from app.services.inventory import InsufficientStockError, ensure_stock_for_invoice, insufficient_stock_http

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICES_CREATE)),
):
    """Create a new invoice within the current user's tenant."""
    logger.info("create_invoice_called", document_type=invoice.document_type, tenant_id=invoice.tenant_id)

    if str(invoice.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create an invoice for a different tenant",
        )

    invoice_obj = Invoice(
        tenant_id=current_user.tenant_id,
        company_id=invoice.company_id,
        customer_id=invoice.customer_id,
        branch_id=invoice.branch_id,
        warehouse_id=invoice.warehouse_id,
        document_type=invoice.document_type,
        series=invoice.series,
        number=invoice.number,
        status=invoice.status or "draft",
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        subtotal=invoice.subtotal,
        tax_total=invoice.tax_total,
        discount_total=invoice.discount_total,
        total=invoice.total,
        currency=invoice.currency,
        exchange_rate=invoice.exchange_rate or 1,
        notes=invoice.notes,
        metadata_json=invoice.metadata,
    )
    db.add(invoice_obj)
    await db.flush()
    await db.commit()
    invoice_obj = await reload_after_commit(db, invoice_obj, current_user.tenant_id)
    return InvoiceResponse.model_validate(invoice_obj)


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICES_READ)),
):
    """List invoices for the current user's tenant."""
    logger.info("list_invoices_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Invoice).where(Invoice.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    invoices = result.scalars().all()
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICES_READ)),
):
    """Get a specific invoice by ID for the current tenant."""
    logger.info("get_invoice_called", invoice_id=invoice_id, tenant_id=current_user.tenant_id)
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    invoice_obj = result.scalar_one_or_none()
    if not invoice_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice_obj


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICES_UPDATE)),
):
    """Update an invoice within the current user's tenant."""
    logger.info("update_invoice_called", invoice_id=invoice_id, tenant_id=current_user.tenant_id)
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    invoice_obj = result.scalar_one_or_none()
    if not invoice_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    if invoice.document_type is not None:
        invoice_obj.document_type = invoice.document_type
    if invoice.series is not None:
        invoice_obj.series = invoice.series
    if invoice.number is not None:
        invoice_obj.number = invoice.number
    if invoice.status is not None:
        invoice_obj.status = invoice.status
    if invoice.issue_date is not None:
        invoice_obj.issue_date = invoice.issue_date
    if invoice.due_date is not None:
        invoice_obj.due_date = invoice.due_date
    if invoice.subtotal is not None:
        invoice_obj.subtotal = invoice.subtotal
    if invoice.tax_total is not None:
        invoice_obj.tax_total = invoice.tax_total
    if invoice.discount_total is not None:
        invoice_obj.discount_total = invoice.discount_total
    if invoice.total is not None:
        invoice_obj.total = invoice.total
    if invoice.currency is not None:
        invoice_obj.currency = invoice.currency
    if invoice.exchange_rate is not None:
        invoice_obj.exchange_rate = invoice.exchange_rate
    if invoice.notes is not None:
        invoice_obj.notes = invoice.notes
    if invoice.metadata is not None:
        invoice_obj.metadata_json = invoice.metadata
    if invoice.company_id is not None:
        invoice_obj.company_id = invoice.company_id
    if invoice.customer_id is not None:
        invoice_obj.customer_id = invoice.customer_id
    if invoice.branch_id is not None:
        invoice_obj.branch_id = invoice.branch_id
    if invoice.warehouse_id is not None:
        invoice_obj.warehouse_id = invoice.warehouse_id

    # Leaving draft → paid/issued applies stock for existing lines (POS already paid).
    try:
        await ensure_stock_for_invoice(db, invoice_obj, commit=False)
        await db.commit()
    except InsufficientStockError as exc:
        await db.rollback()
        raise insufficient_stock_http(exc) from exc
    invoice_obj = await reload_after_commit(db, invoice_obj, current_user.tenant_id)
    return InvoiceResponse.model_validate(invoice_obj)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICES_DELETE)),
):
    """Delete an invoice within the current user's tenant."""
    logger.info("delete_invoice_called", invoice_id=invoice_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        Invoice,
        invoice_id,
        current_user.tenant_id,
        not_found_detail="Invoice not found",
    )
