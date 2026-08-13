from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.permissions import (
    PERMISSION_CUSTOMERS_CREATE,
    PERMISSION_CUSTOMERS_DELETE,
    PERMISSION_CUSTOMERS_READ,
    PERMISSION_CUSTOMERS_UPDATE,
)
from app.core.rbac import require_permissions
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CUSTOMERS_CREATE)),
):
    """Create a new customer."""
    logger.info("create_customer_called", tenant_id=customer.tenant_id, company_id=customer.company_id)

    if str(customer.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a customer for a different tenant",
        )

    data = customer.model_dump()
    if "metadata" in data:
        data["metadata_json"] = data.pop("metadata")
    customer_obj = Customer(**data)
    db.add(customer_obj)
    await db.commit()
    await db.refresh(customer_obj)
    return customer_obj


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CUSTOMERS_READ)),
):
    """List customers for the current user's tenant."""
    logger.info("list_customers_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Customer).where(Customer.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    customers = result.scalars().all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CUSTOMERS_READ)),
):
    """Get a specific customer by ID for the current tenant."""
    logger.info("get_customer_called", customer_id=customer_id, tenant_id=current_user.tenant_id)
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    customer_obj = result.scalar_one_or_none()
    if not customer_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer_obj


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CUSTOMERS_UPDATE)),
):
    """Update a customer by ID for the current tenant."""
    logger.info("update_customer_called", customer_id=customer_id)
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    customer_obj = result.scalar_one_or_none()
    if not customer_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    update_data = customer.model_dump(exclude_none=True)
    for field, value in update_data.items():
        model_field = "metadata_json" if field == "metadata" else field
        setattr(customer_obj, model_field, value)

    await db.commit()
    await db.refresh(customer_obj)
    return customer_obj


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_CUSTOMERS_DELETE)),
):
    """Delete a customer by ID for the current tenant."""
    logger.info("delete_customer_called", customer_id=customer_id)
    await delete_tenant_entity(
        db,
        Customer,
        customer_id,
        current_user.tenant_id,
        not_found_detail="Customer not found",
    )
