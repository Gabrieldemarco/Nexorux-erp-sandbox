from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_ALL,
    PERMISSION_TENANTS_CREATE,
    PERMISSION_TENANTS_DELETE,
    PERMISSION_TENANTS_READ,
    PERMISSION_TENANTS_UPDATE,
)
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


def _user_can_access_tenant(current_user: User, tenant_id) -> bool:
    if PERMISSION_ALL in getattr(current_user, "permission_codes", []):
        return True
    return str(current_user.tenant_id) == str(tenant_id)


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    tenant: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TENANTS_CREATE)),
):
    """Create a new tenant."""
    logger.info("create_tenant_called", name=tenant.name, current_user=current_user.id)

    tenant_obj = Tenant(
        name=tenant.name,
        status=tenant.status,
        settings=tenant.settings or {},
    )
    db.add(tenant_obj)
    await db.commit()
    await db.refresh(tenant_obj)
    return tenant_obj


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TENANTS_READ)),
):
    """List tenants visible to the current user."""
    logger.info("list_tenants_called", skip=skip, limit=limit, current_user=current_user.id)
    stmt = select(Tenant)
    if PERMISSION_ALL not in getattr(current_user, "permission_codes", []):
        stmt = stmt.where(Tenant.id == current_user.tenant_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    tenants = result.scalars().all()
    return tenants


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TENANTS_READ)),
):
    """Get a specific tenant by ID."""
    logger.info("get_tenant_called", tenant_id=tenant_id, current_user=current_user.id)
    if not _user_can_access_tenant(current_user, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant_obj = result.scalar_one_or_none()
    if not tenant_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return tenant_obj


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TENANTS_UPDATE)),
):
    """Update a tenant by ID."""
    logger.info("update_tenant_called", tenant_id=tenant_id, current_user=current_user.id)
    if not _user_can_access_tenant(current_user, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant_obj = result.scalar_one_or_none()
    if not tenant_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    update_data = tenant.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(tenant_obj, field, value)

    await db.commit()
    await db.refresh(tenant_obj)
    return tenant_obj


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_TENANTS_DELETE)),
):
    """Delete a tenant by ID."""
    logger.info("delete_tenant_called", tenant_id=tenant_id, current_user=current_user.id)
    if not _user_can_access_tenant(current_user, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    result = await db.execute(delete(Tenant).where(Tenant.id == tenant_id))
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    await db.commit()
