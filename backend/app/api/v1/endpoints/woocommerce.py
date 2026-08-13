"""WooCommerce MVP: order webhook, catalog sync, and Woo-linked invoices list."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.permissions import (
    PERMISSION_INVOICES_CREATE,
    PERMISSION_INVOICES_READ,
    PERMISSION_PRODUCTS_READ,
    PERMISSION_PRODUCTS_UPDATE,
    PERMISSION_STOCK_MOVEMENTS_READ,
)
from app.core.rbac import (
    get_current_user_with_permissions,
    _has_permission,
    require_permissions,
)
from app.db.session import get_db
from app.models.branch import Branch
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.woocommerce_sync import (
    build_stock_export,
    create_credit_note_from_invoice,
    find_invoice_by_woo_order,
    push_stock_to_woo,
    woo_api_configured,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


class WooWebhookResponse(BaseModel):
    invoice_id: Optional[UUID] = None
    created: bool = False
    ignored: bool = False
    detail: Optional[str] = None


class AuthContext(BaseModel):
    tenant_id: UUID
    company_id: UUID


class WooProductIn(BaseModel):
    sku: str
    name: Optional[str] = None
    regular_price: Optional[float] = None
    price: Optional[float] = None
    barcode: Optional[str] = None


class WooProductSyncRequest(BaseModel):
    dry_run: bool = False
    products: List[WooProductIn] = Field(default_factory=list)


class WooProductSyncResponse(BaseModel):
    dry_run: bool = False
    created: int = 0
    updated: int = 0
    skipped: int = 0
    total: int = 0
    detail: Optional[str] = None


class WooOrderListItem(BaseModel):
    id: UUID
    series: str
    number: str
    total: float
    status: str
    woocommerce_order_id: Optional[Any] = None
    woocommerce_status: Optional[str] = None
    woocommerce_order_number: Optional[str] = None


class WooStockSyncRequest(BaseModel):
    dry_run: bool = False
    push: bool = True
    warehouse_id: Optional[UUID] = None
    skus: Optional[List[str]] = None


class WooStockSyncItem(BaseModel):
    product_id: str
    sku: str
    name: str
    stock_quantity: int


class WooStockSyncResponse(BaseModel):
    dry_run: bool = False
    pushed: bool = False
    configured: bool = False
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    total: int = 0
    items: List[WooStockSyncItem] = Field(default_factory=list)
    details: List[Dict[str, Any]] = Field(default_factory=list)
    detail: Optional[str] = None



def _extract_rut(payload: Dict[str, Any]) -> Optional[str]:
    billing = payload.get("billing") or {}
    rut = billing.get("rut")
    if rut:
        return str(rut).strip()
    for meta in payload.get("meta_data") or []:
        if not isinstance(meta, dict):
            continue
        key = str(meta.get("key") or "").lower().strip()
        if key in {"rut", "_billing_rut", "billing_rut", "ci", "billing_ci"}:
            value = meta.get("value")
            if value is not None and str(value).strip():
                return str(value).strip()
    return None


def _customer_legal_name(billing: Dict[str, Any]) -> str:
    company = (billing.get("company") or "").strip()
    if company:
        return company
    parts = [billing.get("first_name") or "", billing.get("last_name") or ""]
    name = " ".join(p.strip() for p in parts if p and str(p).strip()).strip()
    return name or (billing.get("email") or "Cliente WooCommerce")


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


async def _resolve_auth(
    db: AsyncSession,
    token: Optional[str],
    webhook_secret: Optional[str],
    tenant_header: Optional[str],
    company_header: Optional[str],
    allowed_permissions: Optional[Sequence[str]] = None,
) -> AuthContext:
    perms = list(allowed_permissions or [PERMISSION_INVOICES_CREATE])
    secret_ok = bool(
        settings.WOOCOMMERCE_WEBHOOK_SECRET
        and webhook_secret
        and webhook_secret == settings.WOOCOMMERCE_WEBHOOK_SECRET
    )

    user: Optional[User] = None
    if token:
        try:
            raw_user = await get_current_user(token=token, db=db)
            user = await get_current_user_with_permissions(current_user=raw_user, db=db)
        except HTTPException:
            user = None

    if user is not None and any(_has_permission(user, p) for p in perms):
        return AuthContext(tenant_id=user.tenant_id, company_id=user.company_id)

    if secret_ok:
        if user is not None:
            return AuthContext(tenant_id=user.tenant_id, company_id=user.company_id)
        if not tenant_header or not company_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Webhook secret auth requires X-Nexorux-Tenant-Id and "
                    "X-Nexorux-Company-Id headers (or a JWT with "
                    f"{' or '.join(perms)})"
                ),
            )
        try:
            return AuthContext(
                tenant_id=UUID(str(tenant_header)),
                company_id=UUID(str(company_header)),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant/company UUID headers",
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            f"Missing {' or '.join(perms)} permission or valid X-Nexorux-Webhook-Secret"
        ),
    )


def _parse_product_price(raw: Dict[str, Any]) -> Optional[float]:
    for key in ("regular_price", "price", "sales_price"):
        val = raw.get(key)
        if val is None or val == "":
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return None


def _normalize_woo_products(body: Any) -> tuple[List[Dict[str, Any]], bool]:
    """Accept either a product array or `{ dry_run?, products? }`."""
    dry_run = False
    products: List[Any] = []
    if isinstance(body, list):
        products = body
    elif isinstance(body, dict):
        dry_run = bool(body.get("dry_run") or False)
        if "products" in body:
            products = body.get("products") or []
        elif body.get("sku"):
            products = [body]
        else:
            products = []
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected JSON array of products or { dry_run, products }",
        )
    if not isinstance(products, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="products must be an array",
        )
    normalized: List[Dict[str, Any]] = []
    for item in products:
        if not isinstance(item, dict):
            continue
        sku = str(item.get("sku") or "").strip()
        if not sku:
            continue
        name_raw = item.get("name")
        barcode_raw = item.get("barcode")
        normalized.append(
            {
                "sku": sku,
                "name": str(name_raw).strip() if name_raw else None,
                "price": _parse_product_price(item),
                "barcode": str(barcode_raw).strip() if barcode_raw else None,
            }
        )
    return normalized, dry_run


@router.post(
    "/woocommerce/webhook/order",
    response_model=WooWebhookResponse,
    status_code=status.HTTP_200_OK,
)
async def woocommerce_order_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_optional),
    x_nexorux_webhook_secret: Optional[str] = Header(None, alias="X-Nexorux-Webhook-Secret"),
    x_nexorux_tenant_id: Optional[str] = Header(None, alias="X-Nexorux-Tenant-Id"),
    x_nexorux_company_id: Optional[str] = Header(None, alias="X-Nexorux-Company-Id"),
):
    """Accept WooCommerce order webhooks and create a draft invoice (MVP)."""
    auth = await _resolve_auth(
        db=db,
        token=token,
        webhook_secret=x_nexorux_webhook_secret,
        tenant_header=x_nexorux_tenant_id,
        company_header=x_nexorux_company_id,
    )

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected JSON object")

    order_id = payload.get("id")
    order_status = str(payload.get("status") or "").lower().strip()
    if order_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing order id")

    if order_status in {"refunded"}:
        parent = await find_invoice_by_woo_order(db, tenant_id=auth.tenant_id, order_id=order_id)
        if not parent:
            return WooWebhookResponse(
                created=False,
                ignored=True,
                detail=f"No invoice found for Woo order {order_id} to refund",
            )
        try:
            nc, created = await create_credit_note_from_invoice(
                db,
                parent=parent,
                order_id=order_id,
                refund_id=payload.get("refund_id") or order_id,
                notes=f"NC automática WooCommerce order {order_id} (refunded)",
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        return WooWebhookResponse(
            invoice_id=nc.id,
            created=created,
            ignored=not created,
            detail=None if created else "Credit note already exists for this Woo refund",
        )

    if order_status not in {"processing", "completed"}:
        return WooWebhookResponse(
            created=False,
            ignored=True,
            detail=f"Ignored status '{order_status}' (only processing|completed|refunded)",
        )

    # Idempotency: existing invoice with metadata.woocommerce_order_id
    existing_stmt = select(Invoice).where(Invoice.tenant_id == auth.tenant_id)
    existing_result = await db.execute(existing_stmt)
    tenant_invoices = list(existing_result.scalars().all())
    order_id_str = str(order_id)
    for inv in tenant_invoices:
        meta = inv.metadata_json or {}
        if str(meta.get("woocommerce_order_id")) == order_id_str:
            logger.info("woocommerce_order_idempotent", order_id=order_id, invoice_id=str(inv.id))
            return WooWebhookResponse(invoice_id=inv.id, created=False)

    billing = payload.get("billing") or {}
    email = (billing.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="billing.email required")

    rut = _extract_rut(payload)
    has_rut = bool(rut and rut not in {"00000000", "0", "CF"})
    final_consumer = not has_rut
    document_type = "111" if has_rut else "101"

    # Upsert customer by email
    cust_stmt = select(Customer).where(
        Customer.tenant_id == auth.tenant_id,
        Customer.email == email,
    )
    cust_result = await db.execute(cust_stmt)
    customer = cust_result.scalar_one_or_none()
    legal_name = _customer_legal_name(billing)

    if customer:
        customer.legal_name = legal_name or customer.legal_name
        if has_rut:
            customer.rut = rut  # type: ignore[assignment]
            customer.customer_type = "company"
        else:
            customer.customer_type = "final_consumer"
            if not customer.rut:
                customer.rut = "00000000"
        customer.is_active = True
    else:
        customer = Customer(
            tenant_id=auth.tenant_id,
            company_id=auth.company_id,
            customer_type="final_consumer" if final_consumer else "company",
            legal_name=legal_name,
            rut=rut if has_rut else "00000000",
            email=email,
            currency="UYU",
            credit_limit=0,
            is_active=True,
        )
        db.add(customer)
        await db.flush()

    line_items = payload.get("line_items") or []
    if not isinstance(line_items, list) or not line_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="line_items required",
        )

    skus = []
    for item in line_items:
        sku = (item.get("sku") or "").strip() if isinstance(item, dict) else ""
        skus.append(sku)

    missing = [sku for sku in skus if not sku]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "line_items missing sku", "missing_skus": missing},
        )

    unique_skus = list({s for s in skus})
    prod_stmt = select(Product).where(
        Product.tenant_id == auth.tenant_id,
        Product.sku.in_(unique_skus),
    )
    prod_result = await db.execute(prod_stmt)
    products = {p.sku: p for p in prod_result.scalars().all()}
    missing_skus = [sku for sku in unique_skus if sku not in products]
    if missing_skus:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Unknown product SKUs", "missing_skus": missing_skus},
        )

    branch_stmt = (
        select(Branch)
        .where(Branch.tenant_id == auth.tenant_id, Branch.company_id == auth.company_id, Branch.is_active.is_(True))
        .limit(1)
    )
    branch = (await db.execute(branch_stmt)).scalar_one_or_none()
    if not branch:
        branch_any = (
            await db.execute(
                select(Branch).where(Branch.tenant_id == auth.tenant_id).limit(1)
            )
        ).scalar_one_or_none()
        branch = branch_any
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No branch configured for tenant/company",
        )

    wh_stmt = (
        select(Warehouse)
        .where(
            Warehouse.tenant_id == auth.tenant_id,
            Warehouse.company_id == auth.company_id,
            Warehouse.is_active.is_(True),
        )
        .limit(1)
    )
    warehouse = (await db.execute(wh_stmt)).scalar_one_or_none()
    if not warehouse:
        warehouse = (
            await db.execute(
                select(Warehouse).where(Warehouse.tenant_id == auth.tenant_id).limit(1)
            )
        ).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No warehouse configured for tenant/company",
        )

    series = "A"
    company_invoices = [i for i in tenant_invoices if str(i.company_id) == str(auth.company_id)]
    number = _next_invoice_number(company_invoices, series)

    now = datetime.now(timezone.utc)
    due = now + timedelta(days=30)

    built_lines: List[Dict[str, Any]] = []
    subtotal = 0.0
    tax_total = 0.0
    for raw in line_items:
        product = products[str(raw.get("sku")).strip()]
        qty = float(raw.get("quantity") or 0)
        unit_price = float(raw.get("price") if raw.get("price") is not None else product.sales_price or 0)
        tax_rate = float(product.tax_rate or 0)
        net = _money(max(qty * unit_price, 0))
        tax_amount = _money(net * tax_rate / 100.0)
        line_total = _money(net + tax_amount)
        subtotal = _money(subtotal + net)
        tax_total = _money(tax_total + tax_amount)
        built_lines.append(
            {
                "product": product,
                "quantity": qty,
                "unit_price": unit_price,
                "tax_amount": tax_amount,
                "total": line_total,
                "description": raw.get("name") or product.name,
            }
        )

    invoice = Invoice(
        tenant_id=auth.tenant_id,
        company_id=auth.company_id,
        customer_id=customer.id,
        branch_id=branch.id,
        warehouse_id=warehouse.id,
        document_type=document_type,
        series=series,
        number=number,
        status="draft",
        issue_date=now,
        due_date=due,
        subtotal=subtotal,
        tax_total=tax_total,
        discount_total=0,
        total=_money(subtotal + tax_total),
        currency="UYU",
        exchange_rate=1,
        notes=f"WooCommerce order {order_id}",
        metadata_json={
            "woocommerce_order_id": order_id,
            "woocommerce_status": order_status,
            "woocommerce_order_number": str(payload.get("number") or order_id),
        },
    )
    db.add(invoice)
    await db.flush()

    for line in built_lines:
        db.add(
            InvoiceItem(
                tenant_id=auth.tenant_id,
                company_id=auth.company_id,
                invoice_id=invoice.id,
                product_id=line["product"].id,
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                discount=0,
                tax_amount=line["tax_amount"],
                total=line["total"],
                description=line["description"],
            )
        )

    await db.commit()
    await db.refresh(invoice)
    logger.info(
        "woocommerce_order_invoice_created",
        order_id=order_id,
        invoice_id=str(invoice.id),
        document_type=document_type,
    )
    return WooWebhookResponse(invoice_id=invoice.id, created=True)


@router.post(
    "/woocommerce/sync/products",
    response_model=WooProductSyncResponse,
    status_code=status.HTTP_200_OK,
)
async def woocommerce_sync_products(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_optional),
    x_nexorux_webhook_secret: Optional[str] = Header(None, alias="X-Nexorux-Webhook-Secret"),
    x_nexorux_tenant_id: Optional[str] = Header(None, alias="X-Nexorux-Tenant-Id"),
    x_nexorux_company_id: Optional[str] = Header(None, alias="X-Nexorux-Company-Id"),
):
    """Upsert products by tenant+SKU from a WooCommerce-style catalog payload."""
    auth = await _resolve_auth(
        db=db,
        token=token,
        webhook_secret=x_nexorux_webhook_secret,
        tenant_header=x_nexorux_tenant_id,
        company_header=x_nexorux_company_id,
        allowed_permissions=[PERMISSION_INVOICES_CREATE, PERMISSION_PRODUCTS_UPDATE],
    )

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from exc

    products, dry_run = _normalize_woo_products(body)
    if not products:
        return WooProductSyncResponse(
            dry_run=dry_run,
            created=0,
            updated=0,
            skipped=0,
            total=0,
            detail="No products with sku in payload",
        )

    skus = [p["sku"] for p in products]
    existing_stmt = select(Product).where(
        Product.tenant_id == auth.tenant_id,
        Product.sku.in_(skus),
    )
    existing_result = await db.execute(existing_stmt)
    by_sku = {p.sku: p for p in existing_result.scalars().all()}

    created = 0
    updated = 0
    skipped = 0

    for item in products:
        sku = item["sku"]
        name = item["name"]
        price = item["price"]
        barcode = item["barcode"]
        existing = by_sku.get(sku)

        if existing:
            if dry_run:
                updated += 1
                continue
            if name:
                existing.name = name
            if price is not None:
                existing.sales_price = price
            if barcode:
                existing.barcode = barcode
            updated += 1
            continue

        if not name:
            skipped += 1
            continue
        if dry_run:
            created += 1
            continue

        product = Product(
            tenant_id=auth.tenant_id,
            company_id=auth.company_id,
            name=name,
            sku=sku,
            barcode=barcode,
            sales_price=price if price is not None else 0,
            cost_price=0,
            tax_rate=22,
            product_type="good",
            unit_of_measure="unit",
            is_service=False,
            is_active=True,
            metadata_json={"source": "woocommerce_sync"},
        )
        db.add(product)
        by_sku[sku] = product
        created += 1

    if not dry_run:
        await db.commit()

    logger.info(
        "woocommerce_products_synced",
        created=created,
        updated=updated,
        skipped=skipped,
        dry_run=dry_run,
        tenant_id=str(auth.tenant_id),
    )
    return WooProductSyncResponse(
        dry_run=dry_run,
        created=created,
        updated=updated,
        skipped=skipped,
        total=len(products),
    )


@router.get(
    "/woocommerce/orders",
    response_model=List[WooOrderListItem],
)
async def woocommerce_list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_INVOICES_READ)),
):
    """List invoices linked to WooCommerce orders via metadata.woocommerce_order_id."""
    stmt = select(Invoice).where(Invoice.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    invoices = list(result.scalars().all())

    items: List[WooOrderListItem] = []
    for inv in invoices:
        meta = inv.metadata_json or {}
        if not isinstance(meta, dict):
            continue
        if meta.get("woocommerce_order_id") is None:
            continue
        items.append(
            WooOrderListItem(
                id=inv.id,
                series=inv.series,
                number=inv.number,
                total=float(inv.total or 0),
                status=inv.status or "",
                woocommerce_order_id=meta.get("woocommerce_order_id"),
                woocommerce_status=meta.get("woocommerce_status"),
                woocommerce_order_number=(
                    str(meta.get("woocommerce_order_number"))
                    if meta.get("woocommerce_order_number") is not None
                    else None
                ),
            )
        )
    items.sort(key=lambda x: (x.series, x.number), reverse=True)
    return items


@router.post(
    "/woocommerce/sync/stock",
    response_model=WooStockSyncResponse,
    status_code=status.HTTP_200_OK,
)
async def woocommerce_sync_stock(
    payload: WooStockSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permissions(PERMISSION_STOCK_MOVEMENTS_READ, PERMISSION_PRODUCTS_READ)
    ),
):
    """Export Nexorux on-hand stock by SKU and optionally push to WooCommerce REST API."""
    items_raw = await build_stock_export(
        db,
        tenant_id=current_user.tenant_id,
        warehouse_id=payload.warehouse_id,
        skus=payload.skus,
    )
    items = [WooStockSyncItem(**row) for row in items_raw]
    configured = woo_api_configured()

    if payload.dry_run or not payload.push:
        return WooStockSyncResponse(
            dry_run=payload.dry_run,
            pushed=False,
            configured=configured,
            updated=0,
            skipped=0,
            failed=0,
            total=len(items),
            items=items,
            detail=(
                "Dry run / export only"
                if payload.dry_run or not payload.push
                else None
            ),
        )

    if not configured:
        return WooStockSyncResponse(
            dry_run=False,
            pushed=False,
            configured=False,
            updated=0,
            skipped=len(items),
            failed=0,
            total=len(items),
            items=items,
            detail=(
                "Set WOOCOMMERCE_URL, WOOCOMMERCE_CONSUMER_KEY and "
                "WOOCOMMERCE_CONSUMER_SECRET to push stock to Woo"
            ),
        )

    updated, skipped, failed, details = await push_stock_to_woo(items_raw)
    return WooStockSyncResponse(
        dry_run=False,
        pushed=True,
        configured=True,
        updated=updated,
        skipped=skipped,
        failed=failed,
        total=len(items),
        items=items,
        details=details,
    )


@router.post(
    "/woocommerce/webhook/refund",
    response_model=WooWebhookResponse,
    status_code=status.HTTP_200_OK,
)
async def woocommerce_refund_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_optional),
    x_nexorux_webhook_secret: Optional[str] = Header(None, alias="X-Nexorux-Webhook-Secret"),
    x_nexorux_tenant_id: Optional[str] = Header(None, alias="X-Nexorux-Tenant-Id"),
    x_nexorux_company_id: Optional[str] = Header(None, alias="X-Nexorux-Company-Id"),
):
    """Accept WooCommerce refund webhooks and create a credit note (102/112)."""
    auth = await _resolve_auth(
        db=db,
        token=token,
        webhook_secret=x_nexorux_webhook_secret,
        tenant_header=x_nexorux_tenant_id,
        company_header=x_nexorux_company_id,
    )

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected JSON object")

    # Woo refund payload usually has order_id; sometimes nested in order
    order_id = payload.get("order_id") or (payload.get("order") or {}).get("id")
    refund_id = payload.get("id")
    if order_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing order_id on refund payload",
        )

    parent = await find_invoice_by_woo_order(db, tenant_id=auth.tenant_id, order_id=order_id)
    if not parent:
        return WooWebhookResponse(
            created=False,
            ignored=True,
            detail=f"No invoice found for Woo order {order_id}",
        )

    try:
        nc, created = await create_credit_note_from_invoice(
            db,
            parent=parent,
            order_id=order_id,
            refund_id=refund_id or order_id,
            notes=f"NC automática WooCommerce refund {refund_id or ''} order {order_id}".strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    logger.info(
        "woocommerce_refund_credit_note",
        order_id=order_id,
        refund_id=refund_id,
        invoice_id=str(nc.id),
        created=created,
    )
    return WooWebhookResponse(
        invoice_id=nc.id,
        created=created,
        ignored=not created,
        detail=None if created else "Credit note already exists for this Woo refund",
    )
