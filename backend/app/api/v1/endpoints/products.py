from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.core.permissions import (
    PERMISSION_PRODUCTS_CREATE,
    PERMISSION_PRODUCTS_DELETE,
    PERMISSION_PRODUCTS_READ,
    PERMISSION_PRODUCTS_UPDATE,
)
from app.core.rbac import require_permissions
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRODUCTS_CREATE)),
):
    """Create a new product."""
    logger.info("create_product_called", tenant_id=product.tenant_id, company_id=product.company_id)

    if str(product.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a product for a different tenant",
        )

    data = product.model_dump()
    if "metadata" in data:
        data["metadata_json"] = data.pop("metadata")
    product_obj = Product(**data)
    db.add(product_obj)
    await db.commit()
    await db.refresh(product_obj)
    return product_obj


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRODUCTS_READ)),
):
    """List products for the current user's tenant."""
    logger.info("list_products_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Product).where(Product.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRODUCTS_READ)),
):
    """Get a specific product by ID for the current tenant."""
    logger.info("get_product_called", product_id=product_id, tenant_id=current_user.tenant_id)
    stmt = select(Product).where(
        Product.id == product_id,
        Product.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    product_obj = result.scalar_one_or_none()
    if not product_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product_obj


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRODUCTS_UPDATE)),
):
    """Update a product by ID for the current tenant."""
    logger.info("update_product_called", product_id=product_id)
    stmt = select(Product).where(
        Product.id == product_id,
        Product.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    product_obj = result.scalar_one_or_none()
    if not product_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product.model_dump(exclude_none=True)
    for field, value in update_data.items():
        model_field = "metadata_json" if field == "metadata" else field
        setattr(product_obj, model_field, value)

    await db.commit()
    await db.refresh(product_obj)
    return product_obj


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PRODUCTS_DELETE)),
):
    """Delete a product by ID for the current tenant."""
    logger.info("delete_product_called", product_id=product_id)
    await delete_tenant_entity(
        db,
        Product,
        product_id,
        current_user.tenant_id,
        not_found_detail="Product not found",
    )
