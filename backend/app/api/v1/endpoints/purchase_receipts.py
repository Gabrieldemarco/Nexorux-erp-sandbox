from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db, reload_after_commit
from app.db.tenant_delete import delete_tenant_entity
from app.models.purchase_receipt import PurchaseReceipt, PurchaseReceiptItem
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse
from app.models.stock_movement import StockMovement
from app.schemas.purchase_receipt import PurchaseReceiptCreate, PurchaseReceiptResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_STOCK_MOVEMENTS_CREATE,
    PERMISSION_STOCK_MOVEMENTS_DELETE,
    PERMISSION_STOCK_MOVEMENTS_READ,
)
from app.services.inventory import REF_PURCHASE_RECEIPT_ITEM, create_purchase_stock_in
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


async def _next_receipt_number(db: AsyncSession, tenant_id) -> str:
    stmt = select(func.count()).select_from(PurchaseReceipt).where(PurchaseReceipt.tenant_id == tenant_id)
    count = (await db.execute(stmt)).scalar() or 0
    return f"ER-{int(count) + 1:06d}"


@router.post("/", response_model=PurchaseReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_receipt(
    payload: PurchaseReceiptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_CREATE)),
):
    """Receive goods from a supplier and increase stock (one movement per line)."""
    logger.info(
        "create_purchase_receipt_called",
        supplier_id=str(payload.supplier_id),
        warehouse_id=str(payload.warehouse_id),
        lines=len(payload.items),
    )

    if str(payload.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a purchase receipt for a different tenant",
        )

    supplier = (
        await db.execute(
            select(Supplier).where(
                Supplier.id == payload.supplier_id,
                Supplier.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    warehouse = (
        await db.execute(
            select(Warehouse).where(
                Warehouse.id == payload.warehouse_id,
                Warehouse.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    product_ids = {line.product_id for line in payload.items}
    products = (
        await db.execute(
            select(Product).where(
                Product.tenant_id == current_user.tenant_id,
                Product.id.in_(product_ids),
            )
        )
    ).scalars().all()
    by_id = {p.id: p for p in products}
    if len(by_id) != len(product_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more products not found")

    for line in payload.items:
        product = by_id[line.product_id]
        if product.is_service or (product.product_type or "").lower() == "service":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {product.sku} is a service and cannot enter stock",
            )

    number = (payload.number or "").strip() or await _next_receipt_number(db, current_user.tenant_id)

    receipt = PurchaseReceipt(
        tenant_id=payload.tenant_id,
        company_id=payload.company_id,
        supplier_id=payload.supplier_id,
        warehouse_id=payload.warehouse_id,
        number=number,
        receipt_date=payload.receipt_date,
        notes=payload.notes,
        status="received",
    )
    db.add(receipt)
    await db.flush()

    for line in payload.items:
        product = by_id[line.product_id]
        item = PurchaseReceiptItem(
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            receipt_id=receipt.id,
            product_id=line.product_id,
            quantity=line.quantity,
            unit_cost=line.unit_cost,
            description=line.description or product.name,
        )
        db.add(item)
        await db.flush()
        await create_purchase_stock_in(
            db,
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            warehouse_id=payload.warehouse_id,
            product_id=line.product_id,
            quantity=line.quantity,
            reference_id=item.id,
            movement_date=payload.receipt_date,
        )

    await db.commit()

    receipt = await reload_after_commit(db, receipt, current_user.tenant_id)
    items_stmt = select(PurchaseReceiptItem).where(PurchaseReceiptItem.receipt_id == receipt.id)
    receipt.items = (await db.execute(items_stmt)).scalars().all()
    return receipt


@router.get("/", response_model=List[PurchaseReceiptResponse])
async def list_purchase_receipts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_READ)),
):
    logger.info("list_purchase_receipts_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = (
        select(PurchaseReceipt)
        .where(PurchaseReceipt.tenant_id == current_user.tenant_id)
        .options(selectinload(PurchaseReceipt.items))
        .order_by(PurchaseReceipt.receipt_date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{receipt_id}", response_model=PurchaseReceiptResponse)
async def get_purchase_receipt(
    receipt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_READ)),
):
    stmt = (
        select(PurchaseReceipt)
        .where(
            PurchaseReceipt.id == receipt_id,
            PurchaseReceipt.tenant_id == current_user.tenant_id,
        )
        .options(selectinload(PurchaseReceipt.items))
    )
    receipt = (await db.execute(stmt)).scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase receipt not found")
    return receipt


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_receipt(
    receipt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_DELETE)),
):
    """Delete receipt and reverse linked stock-in movements."""
    logger.info("delete_purchase_receipt_called", receipt_id=receipt_id)
    stmt = (
        select(PurchaseReceipt)
        .where(
            PurchaseReceipt.id == receipt_id,
            PurchaseReceipt.tenant_id == current_user.tenant_id,
        )
        .options(selectinload(PurchaseReceipt.items))
    )
    receipt = (await db.execute(stmt)).scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase receipt not found")

    item_ids = [item.id for item in (receipt.items or [])]
    if item_ids:
        mov_stmt = select(StockMovement).where(
            StockMovement.tenant_id == current_user.tenant_id,
            StockMovement.reference_type == REF_PURCHASE_RECEIPT_ITEM,
            StockMovement.reference_id.in_(item_ids),
        )
        movements = (await db.execute(mov_stmt)).scalars().all()
        for mov in movements:
            await db.delete(mov)

    await delete_tenant_entity(
        db,
        PurchaseReceipt,
        receipt_id,
        current_user.tenant_id,
        not_found_detail="Purchase receipt not found",
    )
    return None
