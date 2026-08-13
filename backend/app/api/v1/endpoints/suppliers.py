from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_SUPPLIERS_CREATE,
    PERMISSION_SUPPLIERS_DELETE,
    PERMISSION_SUPPLIERS_READ,
    PERMISSION_SUPPLIERS_UPDATE
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=SupplierResponse)
async def create_supplier(
    supplier: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_SUPPLIERS_CREATE)),
):
    """Create a new supplier."""
    logger.info("create_supplier_called", tenant_id=supplier.tenant_id, company_id=supplier.company_id)

    if str(supplier.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a supplier for a different tenant",
        )

    data = supplier.model_dump()
    if "metadata" in data:
        data["metadata_json"] = data.pop("metadata")
    supplier_obj = Supplier(**data)
    db.add(supplier_obj)
    await db.commit()
    await db.refresh(supplier_obj)
    return supplier_obj


@router.get("/", response_model=List[SupplierResponse])
async def list_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_SUPPLIERS_READ)),
):
    """List suppliers for the current user's tenant."""
    logger.info("list_suppliers_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Supplier).where(Supplier.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    suppliers = result.scalars().all()
    return suppliers


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_SUPPLIERS_READ)),
):
    """Get a specific supplier by ID for the current tenant."""
    logger.info("get_supplier_called", supplier_id=supplier_id, tenant_id=current_user.tenant_id)
    stmt = select(Supplier).where(
        Supplier.id == supplier_id,
        Supplier.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    supplier_obj = result.scalar_one_or_none()
    if not supplier_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )
    return supplier_obj


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    supplier: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_SUPPLIERS_UPDATE)),
):
    """Update a supplier by ID for the current tenant."""
    logger.info("update_supplier_called", supplier_id=supplier_id)
    stmt = select(Supplier).where(
        Supplier.id == supplier_id,
        Supplier.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    supplier_obj = result.scalar_one_or_none()
    if not supplier_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    update_data = supplier.model_dump(exclude_none=True)
    for field, value in update_data.items():
        model_field = "metadata_json" if field == "metadata" else field
        setattr(supplier_obj, model_field, value)

    await db.commit()
    await db.refresh(supplier_obj)
    return supplier_obj


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_SUPPLIERS_DELETE)),
):
    """Delete a supplier by ID for the current tenant."""
    logger.info("delete_supplier_called", supplier_id=supplier_id)
    await delete_tenant_entity(
        db,
        Supplier,
        supplier_id,
        current_user.tenant_id,
        not_found_detail="Supplier not found",
    )
