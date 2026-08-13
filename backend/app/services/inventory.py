"""Inventory helpers: stock in from purchases, stock out/in from invoices."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.stock_movement import StockMovement

# Statuses that should affect warehouse stock (draft/cancelled do not).
STOCK_AFFECTING_STATUSES = frozenset({"paid", "issued", "confirmed", "posted"})

# Credit notes return stock to the warehouse.
CREDIT_NOTE_TYPES = frozenset({"102", "112"})

REF_INVOICE_ITEM = "invoice_item"
REF_PURCHASE_RECEIPT_ITEM = "purchase_receipt_item"

OUT_TYPES = frozenset({"out", "outbound"})


class InsufficientStockError(Exception):
    """Raised when a sale would drive stock below zero."""

    def __init__(
        self,
        *,
        product_id: UUID,
        warehouse_id: UUID,
        available: Decimal,
        required: Decimal,
        product_name: Optional[str] = None,
    ):
        self.product_id = product_id
        self.warehouse_id = warehouse_id
        self.available = available
        self.required = required
        self.product_name = product_name
        label = product_name or str(product_id)[:8]
        super().__init__(
            f"Stock insuficiente para '{label}': disponible {available}, requerido {required}"
        )


def _as_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _signed_qty(movement_type: str, quantity) -> Decimal:
    qty = _as_decimal(quantity)
    if (movement_type or "").lower() in OUT_TYPES:
        return -qty
    return qty


def invoice_affects_stock(invoice: Invoice) -> bool:
    status_value = (invoice.status or "").strip().lower()
    return status_value in STOCK_AFFECTING_STATUSES


def movement_type_for_invoice(invoice: Invoice) -> str:
    doc = str(invoice.document_type or "")
    if doc in CREDIT_NOTE_TYPES:
        return "in"
    return "out"


async def _product_tracks_stock(db: AsyncSession, product_id: Optional[UUID]) -> bool:
    if not product_id:
        return False
    stmt = select(Product).where(Product.id == product_id)
    product = (await db.execute(stmt)).scalar_one_or_none()
    if not product:
        return False
    if product.is_service:
        return False
    if (product.product_type or "").lower() == "service":
        return False
    return True


async def _find_movement(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    reference_type: str,
    reference_id: UUID,
) -> Optional[StockMovement]:
    stmt = select(StockMovement).where(
        StockMovement.tenant_id == tenant_id,
        StockMovement.reference_type == reference_type,
        StockMovement.reference_id == reference_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_stock_balances(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    warehouse_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
) -> list[dict]:
    """Aggregate on-hand qty per product/warehouse for a tenant."""
    stmt = select(StockMovement).where(StockMovement.tenant_id == tenant_id)
    if warehouse_id:
        stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    movements = (await db.execute(stmt)).scalars().all()

    totals: dict[tuple[UUID, UUID], Decimal] = {}
    for mov in movements:
        if not mov.product_id or not mov.warehouse_id:
            continue
        key = (mov.product_id, mov.warehouse_id)
        totals[key] = totals.get(key, Decimal("0")) + _signed_qty(mov.movement_type, mov.quantity)

    rows = [
        {
            "product_id": pid,
            "warehouse_id": wid,
            "quantity": float(qty),
        }
        for (pid, wid), qty in totals.items()
    ]
    rows.sort(key=lambda r: (str(r["warehouse_id"]), str(r["product_id"])))
    return rows


async def get_available_qty(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    warehouse_id: UUID,
    product_id: UUID,
    exclude_reference_type: Optional[str] = None,
    exclude_reference_id: Optional[UUID] = None,
) -> Decimal:
    stmt = select(StockMovement).where(
        StockMovement.tenant_id == tenant_id,
        StockMovement.warehouse_id == warehouse_id,
        StockMovement.product_id == product_id,
    )
    movements = (await db.execute(stmt)).scalars().all()
    total = Decimal("0")
    for mov in movements:
        if (
            exclude_reference_id
            and exclude_reference_type
            and mov.reference_type == exclude_reference_type
            and mov.reference_id == exclude_reference_id
        ):
            continue
        total += _signed_qty(mov.movement_type, mov.quantity)
    return total


async def assert_enough_stock_for_out(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    warehouse_id: UUID,
    product_id: UUID,
    required,
    exclude_item_id: Optional[UUID] = None,
) -> None:
    if settings.STOCK_ALLOW_NEGATIVE:
        return
    required_qty = _as_decimal(required)
    if required_qty <= 0:
        return
    available = await get_available_qty(
        db,
        tenant_id=tenant_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        exclude_reference_type=REF_INVOICE_ITEM if exclude_item_id else None,
        exclude_reference_id=exclude_item_id,
    )
    if required_qty > available:
        product = (
            await db.execute(select(Product).where(Product.id == product_id))
        ).scalar_one_or_none()
        raise InsufficientStockError(
            product_id=product_id,
            warehouse_id=warehouse_id,
            available=available,
            required=required_qty,
            product_name=product.name if product else None,
        )


def insufficient_stock_http(exc: InsufficientStockError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    )


async def ensure_stock_for_invoice_item(
    db: AsyncSession,
    invoice: Invoice,
    item: InvoiceItem,
    *,
    commit: bool = False,
) -> Optional[StockMovement]:
    """Create or sync a stock movement for one invoice line (idempotent)."""
    if not invoice_affects_stock(invoice):
        return None
    if not invoice.warehouse_id:
        return None
    if not await _product_tracks_stock(db, item.product_id):
        return None

    qty = _as_decimal(item.quantity)
    if qty <= 0:
        return None

    movement_type = movement_type_for_invoice(invoice)
    existing = await _find_movement(
        db,
        tenant_id=invoice.tenant_id,
        reference_type=REF_INVOICE_ITEM,
        reference_id=item.id,
    )

    if movement_type == "out":
        await assert_enough_stock_for_out(
            db,
            tenant_id=invoice.tenant_id,
            warehouse_id=invoice.warehouse_id,
            product_id=item.product_id,
            required=qty,
            exclude_item_id=item.id if existing else None,
        )

    if existing:
        existing.quantity = qty
        existing.movement_type = movement_type
        existing.warehouse_id = invoice.warehouse_id
        existing.product_id = item.product_id
        if commit:
            await db.commit()
            await db.refresh(existing)
        return existing

    movement = StockMovement(
        tenant_id=invoice.tenant_id,
        company_id=invoice.company_id,
        warehouse_id=invoice.warehouse_id,
        product_id=item.product_id,
        quantity=qty,
        movement_type=movement_type,
        reference_id=item.id,
        reference_type=REF_INVOICE_ITEM,
        movement_date=datetime.now(timezone.utc),
    )
    db.add(movement)
    if commit:
        await db.commit()
        await db.refresh(movement)
    return movement


async def ensure_stock_for_invoice(
    db: AsyncSession,
    invoice: Invoice,
    *,
    commit: bool = False,
) -> int:
    """Ensure stock movements exist for all lines of an invoice. Returns count touched."""
    if not invoice_affects_stock(invoice):
        return 0
    stmt = select(InvoiceItem).where(
        InvoiceItem.invoice_id == invoice.id,
        InvoiceItem.tenant_id == invoice.tenant_id,
    )
    items = (await db.execute(stmt)).scalars().all()
    count = 0
    for item in items:
        moved = await ensure_stock_for_invoice_item(db, invoice, item, commit=False)
        if moved:
            count += 1
    if commit and count:
        await db.commit()
    return count


async def remove_stock_for_invoice_item(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    item_id: UUID | str,
    commit: bool = False,
) -> bool:
    ref_id = item_id if isinstance(item_id, UUID) else UUID(str(item_id))
    existing = await _find_movement(
        db,
        tenant_id=tenant_id,
        reference_type=REF_INVOICE_ITEM,
        reference_id=ref_id,
    )
    if not existing:
        return False
    await db.delete(existing)
    if commit:
        await db.commit()
    return True


async def create_purchase_stock_in(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    company_id: UUID,
    warehouse_id: UUID,
    product_id: UUID,
    quantity,
    reference_id: UUID,
    movement_date: Optional[datetime] = None,
) -> StockMovement:
    """Stock IN for a purchase receipt line (always adds)."""
    qty = _as_decimal(quantity)
    movement = StockMovement(
        tenant_id=tenant_id,
        company_id=company_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        quantity=qty,
        movement_type="in",
        reference_id=reference_id,
        reference_type=REF_PURCHASE_RECEIPT_ITEM,
        movement_date=movement_date or datetime.now(timezone.utc),
    )
    db.add(movement)
    return movement
