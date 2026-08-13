from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_WAREHOUSES_CREATE,
    PERMISSION_WAREHOUSES_DELETE,
    PERMISSION_WAREHOUSES_READ,
    PERMISSION_WAREHOUSES_UPDATE
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=WarehouseResponse)
async def create_warehouse(
    warehouse: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_WAREHOUSES_CREATE)),
):
    """Create a new warehouse."""
    logger.info("create_warehouse_called", tenant_id=warehouse.tenant_id, company_id=warehouse.company_id)

    if str(warehouse.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a warehouse for a different tenant",
        )

    warehouse_obj = Warehouse(**warehouse.model_dump())
    db.add(warehouse_obj)
    await db.commit()
    await db.refresh(warehouse_obj)
    return warehouse_obj


@router.get("/", response_model=List[WarehouseResponse])
async def list_warehouses(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_WAREHOUSES_READ)),
):
    """List warehouses for the current user's tenant."""
    logger.info("list_warehouses_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Warehouse).where(Warehouse.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    warehouses = result.scalars().all()
    return warehouses


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_WAREHOUSES_READ)),
):
    """Get a specific warehouse by ID for the current tenant."""
    logger.info("get_warehouse_called", warehouse_id=warehouse_id, tenant_id=current_user.tenant_id)
    stmt = select(Warehouse).where(
        Warehouse.id == warehouse_id,
        Warehouse.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    warehouse_obj = result.scalar_one_or_none()
    if not warehouse_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    return warehouse_obj


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    warehouse: WarehouseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_WAREHOUSES_UPDATE)),
):
    """Update a warehouse by ID for the current tenant."""
    logger.info("update_warehouse_called", warehouse_id=warehouse_id)
    stmt = select(Warehouse).where(
        Warehouse.id == warehouse_id,
        Warehouse.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    warehouse_obj = result.scalar_one_or_none()
    if not warehouse_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )

    update_data = warehouse.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(warehouse_obj, field, value)

    await db.commit()
    await db.refresh(warehouse_obj)
    return warehouse_obj


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_WAREHOUSES_DELETE)),
):
    """Delete a warehouse by ID for the current tenant."""
    logger.info("delete_warehouse_called", warehouse_id=warehouse_id)
    await delete_tenant_entity(
        db,
        Warehouse,
        warehouse_id,
        current_user.tenant_id,
        not_found_detail="Warehouse not found",
    )
    return None