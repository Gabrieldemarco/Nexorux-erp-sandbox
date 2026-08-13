from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.price_list import PriceList
from app.schemas.price_list import PriceListCreate, PriceListUpdate, PriceListResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_PRICE_LISTS_CREATE,
    PERMISSION_PRICE_LISTS_DELETE,
    PERMISSION_PRICE_LISTS_READ,
    PERMISSION_PRICE_LISTS_UPDATE
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=PriceListResponse)
async def create_price_list(
    price_list: PriceListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRICE_LISTS_CREATE)),
):
    """Create a new price list within the current user's tenant."""
    logger.info("create_price_list_called", name=price_list.name, tenant_id=price_list.tenant_id)

    if str(price_list.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a price list for a different tenant",
        )

    price_list_obj = PriceList(
        tenant_id=current_user.tenant_id,
        company_id=price_list.company_id,
        name=price_list.name,
        currency=price_list.currency,
        valid_from=price_list.valid_from,
        valid_to=price_list.valid_to,
        is_default=price_list.is_default,
    )
    db.add(price_list_obj)
    await db.commit()
    await db.refresh(price_list_obj)
    return price_list_obj


@router.get("/", response_model=List[PriceListResponse])
async def list_price_lists(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRICE_LISTS_READ)),
):
    """List price lists for the current user's tenant."""
    logger.info("list_price_lists_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(PriceList).where(PriceList.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    price_lists = result.scalars().all()
    return price_lists


@router.get("/{price_list_id}", response_model=PriceListResponse)
async def get_price_list(
    price_list_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRICE_LISTS_READ)),
):
    """Get a specific price list by ID for the current tenant."""
    logger.info("get_price_list_called", price_list_id=price_list_id, tenant_id=current_user.tenant_id)
    stmt = select(PriceList).where(
        PriceList.id == price_list_id,
        PriceList.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    price_list_obj = result.scalar_one_or_none()
    if not price_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price list not found",
        )
    return price_list_obj


@router.put("/{price_list_id}", response_model=PriceListResponse)
async def update_price_list(
    price_list_id: str,
    price_list: PriceListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRICE_LISTS_UPDATE)),
):
    """Update a price list by ID for the current tenant."""
    logger.info("update_price_list_called", price_list_id=price_list_id, tenant_id=current_user.tenant_id)
    stmt = select(PriceList).where(
        PriceList.id == price_list_id,
        PriceList.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    price_list_obj = result.scalar_one_or_none()
    if not price_list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price list not found",
        )
    update_data = price_list.model_dump()
    for field, value in update_data.items():
        if value is not None:
            setattr(price_list_obj, field, value)
    await db.commit()
    await db.refresh(price_list_obj)
    return price_list_obj


@router.delete("/{price_list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_list(
    price_list_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRICE_LISTS_DELETE)),
):
    """Delete a price list by ID for the current tenant."""
    logger.info("delete_price_list_called", price_list_id=price_list_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        PriceList,
        price_list_id,
        current_user.tenant_id,
        not_found_detail="Price list not found",
    )
    return None