from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.fiscal_response import FiscalResponse
from app.schemas.fiscal_response import FiscalResponseCreate, FiscalResponseUpdate, FiscalResponseResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_FISCAL_RESPONSES_CREATE,
    PERMISSION_FISCAL_RESPONSES_DELETE,
    PERMISSION_FISCAL_RESPONSES_READ,
    PERMISSION_FISCAL_RESPONSES_UPDATE
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=FiscalResponseResponse)
async def create_fiscal_response(
    fiscal_response: FiscalResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_RESPONSES_CREATE)),
):
    """Create a new fiscal response within the current user's tenant."""
    logger.info("create_fiscal_response_called", tenant_id=fiscal_response.tenant_id)

    if str(fiscal_response.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a fiscal response for a different tenant",
        )

    data = fiscal_response.model_dump()
    data["tenant_id"] = current_user.tenant_id
    fiscal_response_obj = FiscalResponse(**data)
    db.add(fiscal_response_obj)
    await db.commit()
    await db.refresh(fiscal_response_obj)
    return fiscal_response_obj


@router.get("/", response_model=List[FiscalResponseResponse])
async def list_fiscal_responses(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_RESPONSES_READ)),
):
    """List fiscal responses for the current user's tenant."""
    logger.info("list_fiscal_responses_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(FiscalResponse).where(FiscalResponse.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    fiscal_responses = result.scalars().all()
    return fiscal_responses


@router.get("/{fiscal_response_id}", response_model=FiscalResponseResponse)
async def get_fiscal_response(
    fiscal_response_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_RESPONSES_READ)),
):
    """Get a specific fiscal response by ID for the current tenant."""
    logger.info("get_fiscal_response_called", fiscal_response_id=fiscal_response_id, tenant_id=current_user.tenant_id)
    stmt = select(FiscalResponse).where(
        FiscalResponse.id == fiscal_response_id,
        FiscalResponse.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    fiscal_response_obj = result.scalar_one_or_none()
    if not fiscal_response_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal response not found",
        )
    return fiscal_response_obj


@router.put("/{fiscal_response_id}", response_model=FiscalResponseResponse)
async def update_fiscal_response(
    fiscal_response_id: str,
    fiscal_response: FiscalResponseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_RESPONSES_UPDATE)),
):
    """Update a fiscal response within the current user's tenant."""
    logger.info("update_fiscal_response_called", fiscal_response_id=fiscal_response_id, tenant_id=current_user.tenant_id)
    stmt = select(FiscalResponse).where(
        FiscalResponse.id == fiscal_response_id,
        FiscalResponse.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    fiscal_response_obj = result.scalar_one_or_none()
    if not fiscal_response_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal response not found",
        )

    update_data = fiscal_response.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fiscal_response_obj, field, value)

    await db.commit()
    await db.refresh(fiscal_response_obj)
    return fiscal_response_obj


@router.delete("/{fiscal_response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fiscal_response(
    fiscal_response_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_FISCAL_RESPONSES_DELETE)),
):
    """Delete a fiscal response within the current user's tenant."""
    logger.info("delete_fiscal_response_called", fiscal_response_id=fiscal_response_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        FiscalResponse,
        fiscal_response_id,
        current_user.tenant_id,
        not_found_detail="Fiscal response not found",
    )
    return None