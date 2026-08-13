from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.permission import Permission
from app.models.role import Role
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RolePermissionsUpdate,
)
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_ROLES_CREATE,
    PERMISSION_ROLES_DELETE,
    PERMISSION_ROLES_READ,
    PERMISSION_ROLES_UPDATE,
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


async def _load_role(db: AsyncSession, role_id: str, tenant_id) -> Role | None:
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id, Role.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _permissions_for_tenant(
    db: AsyncSession,
    tenant_id,
    permission_ids: List[UUID],
) -> List[Permission]:
    if not permission_ids:
        return []
    stmt = select(Permission).where(
        Permission.tenant_id == tenant_id,
        Permission.id.in_(permission_ids),
    )
    result = await db.execute(stmt)
    perms = list(result.scalars().all())
    if len(perms) != len(set(permission_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more permission_ids are invalid for this tenant",
        )
    return perms


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_ROLES_CREATE)),
):
    """Create a new role within the current user's tenant."""
    logger.info("create_role_called", name=role.name, tenant_id=role.tenant_id)

    if str(role.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a role for a different tenant",
        )

    role_obj = Role(
        tenant_id=current_user.tenant_id,
        name=role.name,
        key=role.key,
        description=role.description,
        is_default=role.is_default,
    )
    if role.permission_ids is not None:
        role_obj.permissions = await _permissions_for_tenant(
            db, current_user.tenant_id, role.permission_ids
        )
    db.add(role_obj)
    await db.commit()
    loaded = await _load_role(db, str(role_obj.id), current_user.tenant_id)
    return loaded


@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_ROLES_READ)),
):
    """List roles for the current user's tenant."""
    logger.info("list_roles_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = (
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_ROLES_READ)),
):
    """Get a specific role by ID for the current tenant."""
    logger.info("get_role_called", role_id=role_id, tenant_id=current_user.tenant_id)
    role_obj = await _load_role(db, role_id, current_user.tenant_id)
    if not role_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role_obj


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_ROLES_UPDATE)),
):
    """Update a role by ID for the current tenant."""
    logger.info("update_role_called", role_id=role_id, tenant_id=current_user.tenant_id)
    role_obj = await _load_role(db, role_id, current_user.tenant_id)
    if not role_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    update_data = role.model_dump(exclude_unset=True)
    permission_ids = update_data.pop("permission_ids", None)
    for field, value in update_data.items():
        setattr(role_obj, field, value)
    if permission_ids is not None:
        role_obj.permissions = await _permissions_for_tenant(
            db, current_user.tenant_id, permission_ids
        )
    await db.commit()
    return await _load_role(db, role_id, current_user.tenant_id)


@router.put("/{role_id}/permissions", response_model=RoleResponse)
async def set_role_permissions(
    role_id: str,
    payload: RolePermissionsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_ROLES_UPDATE)),
):
    """Replace all permissions assigned to a role."""
    logger.info(
        "set_role_permissions_called",
        role_id=role_id,
        count=len(payload.permission_ids),
        tenant_id=current_user.tenant_id,
    )
    role_obj = await _load_role(db, role_id, current_user.tenant_id)
    if not role_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    role_obj.permissions = await _permissions_for_tenant(
        db, current_user.tenant_id, payload.permission_ids
    )
    await db.commit()
    return await _load_role(db, role_id, current_user.tenant_id)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_ROLES_DELETE)),
):
    """Delete a role by ID for the current tenant."""
    logger.info("delete_role_called", role_id=role_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        Role,
        role_id,
        current_user.tenant_id,
        not_found_detail="Role not found",
    )
    return None
