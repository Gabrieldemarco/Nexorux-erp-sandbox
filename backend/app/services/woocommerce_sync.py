"""WooCommerce helpers: stock push and refund → credit note."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.services.inventory import ensure_stock_for_invoice, list_stock_balances

logger = structlog.get_logger(__name__)


def _money(value: float) -> float:
    return round(float(value or 0), 2)


def _next_invoice_number(invoices: List[Invoice], series: str) -> str:
    nums: List[int] = []
    for inv in invoices:
        if inv.series != series:
            continue
        try:
            nums.append(int(str(inv.number)))
        except (TypeError, ValueError):
            continue
    next_n = max(nums) + 1 if nums else 1
    return f"{next_n:08d}"


def credit_note_type(document_type: str) -> Optional[str]:
    if document_type == "101":
        return "102"
    if document_type == "111":
        return "112"
    return None


def woo_api_configured() -> bool:
    return bool(
        settings.WOOCOMMERCE_URL
        and settings.WOOCOMMERCE_CONSUMER_KEY
        and settings.WOOCOMMERCE_CONSUMER_SECRET
    )


async def build_stock_export(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    warehouse_id: Optional[UUID] = None,
    skus: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    stmt = select(Product).where(
        Product.tenant_id == tenant_id,
        Product.is_active.is_(True),
    )
    products = list((await db.execute(stmt)).scalars().all())
    if skus:
        wanted = {s.strip() for s in skus if s and str(s).strip()}
        products = [p for p in products if p.sku in wanted]

    balances = await list_stock_balances(
        db,
        tenant_id=tenant_id,
        warehouse_id=warehouse_id,
    )
    qty_by_product: Dict[UUID, float] = {}
    for row in balances:
        pid = row["product_id"]
        qty_by_product[pid] = qty_by_product.get(pid, 0.0) + float(row["quantity"] or 0)

    items: List[Dict[str, Any]] = []
    for product in products:
        if product.is_service or (product.product_type or "").lower() == "service":
            continue
        if not product.sku:
            continue
        items.append(
            {
                "product_id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "stock_quantity": max(0, int(round(qty_by_product.get(product.id, 0.0)))),
            }
        )
    items.sort(key=lambda x: x["sku"])
    return items


async def push_stock_to_woo(items: List[Dict[str, Any]]) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    """Update Woo product stock by SKU. Returns updated, skipped, failed, details."""
    if not woo_api_configured():
        return 0, len(items), 0, [{"sku": i["sku"], "status": "skipped", "detail": "Woo API not configured"} for i in items]

    base = settings.WOOCOMMERCE_URL.rstrip("/")
    auth = (settings.WOOCOMMERCE_CONSUMER_KEY, settings.WOOCOMMERCE_CONSUMER_SECRET)
    updated = 0
    skipped = 0
    failed = 0
    details: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for item in items:
            sku = item["sku"]
            qty = int(item["stock_quantity"])
            try:
                lookup = await client.get(
                    f"{base}/wp-json/wc/v3/products",
                    params={"sku": sku},
                    auth=auth,
                )
                if lookup.status_code >= 400:
                    failed += 1
                    details.append(
                        {
                            "sku": sku,
                            "status": "failed",
                            "detail": f"lookup HTTP {lookup.status_code}",
                        }
                    )
                    continue
                products = lookup.json()
                if not isinstance(products, list) or not products:
                    skipped += 1
                    details.append({"sku": sku, "status": "skipped", "detail": "SKU not found in Woo"})
                    continue
                woo_id = products[0].get("id")
                put = await client.put(
                    f"{base}/wp-json/wc/v3/products/{woo_id}",
                    json={
                        "manage_stock": True,
                        "stock_quantity": qty,
                        "stock_status": "instock" if qty > 0 else "outofstock",
                    },
                    auth=auth,
                )
                if put.status_code >= 400:
                    failed += 1
                    details.append(
                        {
                            "sku": sku,
                            "status": "failed",
                            "detail": f"update HTTP {put.status_code}: {put.text[:200]}",
                        }
                    )
                    continue
                updated += 1
                details.append(
                    {
                        "sku": sku,
                        "status": "updated",
                        "woo_product_id": woo_id,
                        "stock_quantity": qty,
                    }
                )
            except Exception as exc:  # noqa: BLE001 — collect per-SKU failures
                failed += 1
                details.append({"sku": sku, "status": "failed", "detail": str(exc)})
                logger.warning("woo_stock_push_failed", sku=sku, error=str(exc))

    return updated, skipped, failed, details


async def find_invoice_by_woo_order(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    order_id: Any,
) -> Optional[Invoice]:
    order_id_str = str(order_id)
    stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
    invoices = list((await db.execute(stmt)).scalars().all())
    for inv in invoices:
        meta = inv.metadata_json or {}
        if not isinstance(meta, dict):
            continue
        if str(meta.get("woocommerce_order_id")) == order_id_str:
            # Prefer original sale (not a credit note)
            if str(inv.document_type) in {"102", "112"}:
                continue
            return inv
    return None


async def find_existing_woo_credit_note(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    parent_invoice_id: UUID,
    refund_id: Optional[Any] = None,
) -> Optional[Invoice]:
    stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
    invoices = list((await db.execute(stmt)).scalars().all())
    refund_key = str(refund_id) if refund_id is not None else None
    for inv in invoices:
        meta = inv.metadata_json or {}
        if not isinstance(meta, dict):
            continue
        if str(meta.get("parent_invoice_id")) != str(parent_invoice_id):
            continue
        if meta.get("source") != "woocommerce_refund":
            continue
        if refund_key and str(meta.get("woocommerce_refund_id")) != refund_key:
            continue
        return inv
    return None


async def create_credit_note_from_invoice(
    db: AsyncSession,
    *,
    parent: Invoice,
    refund_id: Optional[Any] = None,
    order_id: Optional[Any] = None,
    notes: Optional[str] = None,
    status: str = "paid",
) -> Tuple[Invoice, bool]:
    """Create NC from parent invoice lines. Returns (invoice, created)."""
    nc_type = credit_note_type(str(parent.document_type or ""))
    if not nc_type:
        raise ValueError(f"Cannot create NC from document_type {parent.document_type}")

    existing = await find_existing_woo_credit_note(
        db,
        tenant_id=parent.tenant_id,
        parent_invoice_id=parent.id,
        refund_id=refund_id or order_id,
    )
    if existing:
        return existing, False

    tenant_invoices = list(
        (
            await db.execute(select(Invoice).where(Invoice.tenant_id == parent.tenant_id))
        ).scalars().all()
    )
    number = _next_invoice_number(tenant_invoices, parent.series)
    now = datetime.now(timezone.utc)
    due = now + timedelta(days=30)

    items = list(
        (
            await db.execute(
                select(InvoiceItem).where(
                    InvoiceItem.invoice_id == parent.id,
                    InvoiceItem.tenant_id == parent.tenant_id,
                )
            )
        ).scalars().all()
    )

    invoice = Invoice(
        tenant_id=parent.tenant_id,
        company_id=parent.company_id,
        customer_id=parent.customer_id,
        branch_id=parent.branch_id,
        warehouse_id=parent.warehouse_id,
        document_type=nc_type,
        series=parent.series,
        number=number,
        status=status,
        issue_date=now,
        due_date=due,
        subtotal=parent.subtotal,
        tax_total=parent.tax_total,
        discount_total=parent.discount_total or 0,
        total=parent.total,
        currency=parent.currency or "UYU",
        exchange_rate=parent.exchange_rate or 1,
        notes=notes or f"NC WooCommerce refund order {order_id or ''}".strip(),
        metadata_json={
            "parent_invoice_id": str(parent.id),
            "source": "woocommerce_refund",
            "woocommerce_order_id": order_id
            if order_id is not None
            else (parent.metadata_json or {}).get("woocommerce_order_id"),
            "woocommerce_refund_id": refund_id or order_id,
            "woocommerce_status": "refunded",
        },
    )
    db.add(invoice)
    await db.flush()

    for item in items:
        db.add(
            InvoiceItem(
                tenant_id=parent.tenant_id,
                company_id=parent.company_id,
                invoice_id=invoice.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount or 0,
                tax_amount=item.tax_amount,
                total=item.total,
                description=item.description,
            )
        )
    await db.flush()
    await ensure_stock_for_invoice(db, invoice, commit=False)
    await db.commit()
    await db.refresh(invoice)
    return invoice, True
