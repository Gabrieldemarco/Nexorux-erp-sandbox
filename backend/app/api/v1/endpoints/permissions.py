from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_PERMISSIONS_CREATE,
    PERMISSION_PERMISSIONS_DELETE,
    PERMISSION_PERMISSIONS_READ,
    PERMISSION_PERMISSIONS_UPDATE
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=PermissionResponse)
async def create_permission(
    permission: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PERMISSIONS_CREATE)),
):
    """Create a new permission within the current user's tenant."""
    logger.info("create_permission_called", name=permission.name, tenant_id=permission.tenant_id)

    if str(permission.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a permission for a different tenant",
        )

    permission_obj = Permission(
        tenant_id=current_user.tenant_id,
        name=permission.name,
        code=permission.code,
        description=permission.description,
    )
    db.add(permission_obj)
    await db.commit()
    await db.refresh(permission_obj)
    return permission_obj


@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PERMISSIONS_READ)),
):
    """List permissions for the current user's tenant."""
    logger.info("list_permissions_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Permission).where(Permission.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    permissions = result.scalars().all()
    return permissions


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PERMISSIONS_READ)),
):
    """Get a specific permission by ID for the current tenant."""
    logger.info("get_permission_called", permission_id=permission_id, tenant_id=current_user.tenant_id)
    stmt = select(Permission).where(
        Permission.id == permission_id,
        Permission.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    permission_obj = result.scalar_one_or_none()
    if not permission_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return permission_obj


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    permission: PermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PERMISSIONS_UPDATE)),
):
    """Update a permission by ID for the current tenant."""
    logger.info("update_permission_called", permission_id=permission_id, tenant_id=current_user.tenant_id)
    stmt = select(Permission).where(
        Permission.id == permission_id,
        Permission.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    permission_obj = result.scalar_one_or_none()
    if not permission_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    update_data = permission.model_dump()
    for field, value in update_data.items():
        if value is not None:
            setattr(permission_obj, field, value)
    await db.commit()
    await db.refresh(permission_obj)
    return permission_obj


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PERMISSIONS_DELETE)),
):
    """Delete a permission by ID for the current tenant."""
    logger.info("delete_permission_called", permission_id=permission_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        Permission,
        permission_id,
        current_user.tenant_id,
        not_found_detail="Permission not found",
    )
    return None