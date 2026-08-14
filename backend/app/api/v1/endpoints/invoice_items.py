from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db, reload_after_commit
from app.db.tenant_delete import delete_tenant_entity
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.schemas.invoice_item import InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_INVOICE_ITEMS_CREATE,
    PERMISSION_INVOICE_ITEMS_DELETE,
    PERMISSION_INVOICE_ITEMS_READ,
    PERMISSION_INVOICE_ITEMS_UPDATE
)
from app.services.inventory import (
    InsufficientStockError,
    ensure_stock_for_invoice_item,
    insufficient_stock_http,
    remove_stock_for_invoice_item,
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


async def _load_invoice(db: AsyncSession, invoice_id, tenant_id) -> Invoice | None:
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.tenant_id == tenant_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


@router.post("/", response_model=InvoiceItemResponse)
async def create_invoice_item(
    item: InvoiceItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICE_ITEMS_CREATE)),
):
    """Create a new invoice item within the current user's tenant."""
    logger.info("create_invoice_item_called", invoice_id=item.invoice_id, product_id=item.product_id)

    if str(item.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create an invoice item for a different tenant",
        )

    invoice = await _load_invoice(db, item.invoice_id, current_user.tenant_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    item_obj = InvoiceItem(
        tenant_id=item.tenant_id,
        company_id=item.company_id,
        invoice_id=item.invoice_id,
        product_id=item.product_id,
        quantity=item.quantity,
        unit_price=item.unit_price,
        discount=item.discount or 0,
        tax_amount=item.tax_amount,
        total=item.total,
        description=item.description,
    )
    db.add(item_obj)
    await db.flush()
    try:
        await ensure_stock_for_invoice_item(db, invoice, item_obj, commit=False)
    except InsufficientStockError as exc:
        await db.rollback()
        raise insufficient_stock_http(exc) from exc
    await db.commit()
    item_obj = await reload_after_commit(db, item_obj, current_user.tenant_id)
    return item_obj


@router.get("/", response_model=List[InvoiceItemResponse])
async def list_invoice_items(
    skip: int = 0,
    limit: int = 100,
    invoice_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICE_ITEMS_READ)),
):
    """List invoice items for the current user's tenant."""
    logger.info(
        "list_invoice_items_called",
        skip=skip,
        limit=limit,
        tenant_id=current_user.tenant_id,
        invoice_id=invoice_id,
    )
    stmt = select(InvoiceItem).where(InvoiceItem.tenant_id == current_user.tenant_id)
    if invoice_id:
        stmt = stmt.where(InvoiceItem.invoice_id == invoice_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return items


@router.get("/{item_id}", response_model=InvoiceItemResponse)
async def get_invoice_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICE_ITEMS_READ)),
):
    """Get a specific invoice item by ID for the current tenant."""
    logger.info("get_invoice_item_called", item_id=item_id, tenant_id=current_user.tenant_id)
    stmt = select(InvoiceItem).where(
        InvoiceItem.id == item_id,
        InvoiceItem.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    item_obj = result.scalar_one_or_none()
    if not item_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found",
        )
    return item_obj


@router.put("/{item_id}", response_model=InvoiceItemResponse)
async def update_invoice_item(
    item_id: str,
    item: InvoiceItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICE_ITEMS_UPDATE)),
):
    """Update an invoice item within the current user's tenant."""
    logger.info("update_invoice_item_called", item_id=item_id, tenant_id=current_user.tenant_id)
    stmt = select(InvoiceItem).where(
        InvoiceItem.id == item_id,
        InvoiceItem.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    item_obj = result.scalar_one_or_none()
    if not item_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found",
        )

    if item.quantity is not None:
        item_obj.quantity = item.quantity
    if item.unit_price is not None:
        item_obj.unit_price = item.unit_price
    if item.discount is not None:
        item_obj.discount = item.discount
    if item.tax_amount is not None:
        item_obj.tax_amount = item.tax_amount
    if item.total is not None:
        item_obj.total = item.total
    if item.description is not None:
        item_obj.description = item.description
    if item.invoice_id is not None:
        item_obj.invoice_id = item.invoice_id
    if item.product_id is not None:
        item_obj.product_id = item.product_id

    invoice = await _load_invoice(db, item_obj.invoice_id, current_user.tenant_id)
    if invoice:
        try:
            await ensure_stock_for_invoice_item(db, invoice, item_obj, commit=False)
        except InsufficientStockError as exc:
            await db.rollback()
            raise insufficient_stock_http(exc) from exc

    await db.commit()
    item_obj = await reload_after_commit(db, item_obj, current_user.tenant_id)
    return item_obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICE_ITEMS_DELETE)),
):
    """Delete an invoice item within the current user's tenant."""
    logger.info("delete_invoice_item_called", item_id=item_id, tenant_id=current_user.tenant_id)
    await remove_stock_for_invoice_item(
        db,
        tenant_id=current_user.tenant_id,
        item_id=item_id,
        commit=False,
    )
    await delete_tenant_entity(
        db,
        InvoiceItem,
        item_id,
        current_user.tenant_id,
        not_found_detail="Invoice item not found",
    )
    return None
