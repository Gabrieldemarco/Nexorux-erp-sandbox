from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.stock_movement import StockMovement
from app.schemas.stock_movement import StockMovementCreate, StockMovementUpdate, StockMovementResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_STOCK_MOVEMENTS_CREATE,
    PERMISSION_STOCK_MOVEMENTS_DELETE,
    PERMISSION_STOCK_MOVEMENTS_READ,
    PERMISSION_STOCK_MOVEMENTS_UPDATE
)
from app.services.inventory import list_stock_balances

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class StockBalanceRow(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity: float

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=StockMovementResponse)
async def create_stock_movement(
    movement: StockMovementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_CREATE)),
):
    """Create a new stock movement within the current user's tenant."""
    logger.info("create_stock_movement_called", movement_type=movement.movement_type, tenant_id=movement.tenant_id)

    if str(movement.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a stock movement for a different tenant",
        )

    movement_obj = StockMovement(
        tenant_id=current_user.tenant_id,
        company_id=movement.company_id,
        warehouse_id=movement.warehouse_id,
        product_id=movement.product_id,
        quantity=movement.quantity,
        movement_type=movement.movement_type,
        reference_id=movement.reference_id,
        reference_type=movement.reference_type,
        movement_date=movement.movement_date,
    )
    db.add(movement_obj)
    await db.commit()
    await db.refresh(movement_obj)
    return movement_obj


@router.get("/balances", response_model=List[StockBalanceRow])
async def get_stock_balances(
    warehouse_id: Optional[str] = None,
    product_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_READ)),
):
    """On-hand stock balances aggregated from movements."""
    logger.info(
        "get_stock_balances_called",
        tenant_id=current_user.tenant_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )
    return await list_stock_balances(
        db,
        tenant_id=current_user.tenant_id,
        warehouse_id=UUID(warehouse_id) if warehouse_id else None,
        product_id=UUID(product_id) if product_id else None,
    )


@router.get("/", response_model=List[StockMovementResponse])
async def list_stock_movements(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_READ)),
):
    """List stock movements for the current user's tenant."""
    logger.info("list_stock_movements_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(StockMovement).where(StockMovement.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    movements = result.scalars().all()
    return movements


@router.get("/{movement_id}", response_model=StockMovementResponse)
async def get_stock_movement(
    movement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_READ)),
):
    """Get a specific stock movement by ID for the current tenant."""
    logger.info("get_stock_movement_called", movement_id=movement_id, tenant_id=current_user.tenant_id)
    stmt = select(StockMovement).where(
        StockMovement.id == movement_id,
        StockMovement.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    movement_obj = result.scalar_one_or_none()
    if not movement_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock movement not found",
        )
    return movement_obj


@router.put("/{movement_id}", response_model=StockMovementResponse)
async def update_stock_movement(
    movement_id: str,
    movement: StockMovementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_UPDATE)),
):
    """Update a stock movement within the current user's tenant."""
    logger.info("update_stock_movement_called", movement_id=movement_id, tenant_id=current_user.tenant_id)
    stmt = select(StockMovement).where(
        StockMovement.id == movement_id,
        StockMovement.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    movement_obj = result.scalar_one_or_none()
    if not movement_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock movement not found",
        )

    if movement.quantity is not None:
        movement_obj.quantity = movement.quantity
    if movement.movement_type is not None:
        movement_obj.movement_type = movement.movement_type
    if movement.reference_id is not None:
        movement_obj.reference_id = movement.reference_id
    if movement.reference_type is not None:
        movement_obj.reference_type = movement.reference_type
    if movement.movement_date is not None:
        movement_obj.movement_date = movement.movement_date
    if movement.company_id is not None:
        movement_obj.company_id = movement.company_id
    if movement.warehouse_id is not None:
        movement_obj.warehouse_id = movement.warehouse_id
    if movement.product_id is not None:
        movement_obj.product_id = movement.product_id

    await db.commit()
    await db.refresh(movement_obj)
    return movement_obj


@router.delete("/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_movement(
    movement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_STOCK_MOVEMENTS_DELETE)),
):
    """Delete a stock movement within the current user's tenant."""
    logger.info("delete_stock_movement_called", movement_id=movement_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        StockMovement,
        movement_id,
        current_user.tenant_id,
        not_found_detail="Stock movement not found",
    )