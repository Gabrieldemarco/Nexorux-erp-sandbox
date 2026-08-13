from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_PAYMENTS_CREATE,
    PERMISSION_PAYMENTS_DELETE,
    PERMISSION_PAYMENTS_READ,
    PERMISSION_PAYMENTS_UPDATE
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PAYMENTS_CREATE)),
):
    """Create a new payment within the current user's tenant."""
    logger.info("create_payment_called", amount=payment.amount, tenant_id=payment.tenant_id)

    if str(payment.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a payment for a different tenant",
        )

    payment_obj = Payment(
        tenant_id=current_user.tenant_id,
        company_id=payment.company_id,
        invoice_id=payment.invoice_id,
        customer_id=payment.customer_id,
        payment_date=payment.payment_date,
        amount=payment.amount,
        currency=payment.currency,
        payment_method=payment.payment_method,
        reference=payment.reference,
        status=payment.status or "pending",
    )
    db.add(payment_obj)
    await db.commit()
    await db.refresh(payment_obj)
    return payment_obj


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PAYMENTS_READ)),
):
    """List payments for the current user's tenant."""
    logger.info("list_payments_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Payment).where(Payment.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    payments = result.scalars().all()
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PAYMENTS_READ)),
):
    """Get a specific payment by ID for the current tenant."""
    logger.info("get_payment_called", payment_id=payment_id, tenant_id=current_user.tenant_id)
    stmt = select(Payment).where(
        Payment.id == payment_id,
        Payment.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    payment_obj = result.scalar_one_or_none()
    if not payment_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment_obj


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: str,
    payment: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PAYMENTS_UPDATE)),
):
    """Update a payment within the current user's tenant."""
    logger.info("update_payment_called", payment_id=payment_id, tenant_id=current_user.tenant_id)
    stmt = select(Payment).where(
        Payment.id == payment_id,
        Payment.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    payment_obj = result.scalar_one_or_none()
    if not payment_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if payment.payment_date is not None:
        payment_obj.payment_date = payment.payment_date
    if payment.amount is not None:
        payment_obj.amount = payment.amount
    if payment.currency is not None:
        payment_obj.currency = payment.currency
    if payment.payment_method is not None:
        payment_obj.payment_method = payment.payment_method
    if payment.reference is not None:
        payment_obj.reference = payment.reference
    if payment.status is not None:
        payment_obj.status = payment.status
    if payment.company_id is not None:
        payment_obj.company_id = payment.company_id
    if payment.invoice_id is not None:
        payment_obj.invoice_id = payment.invoice_id
    if payment.customer_id is not None:
        payment_obj.customer_id = payment.customer_id

    await db.commit()
    await db.refresh(payment_obj)
    return payment_obj


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PAYMENTS_DELETE)),
):
    """Delete a payment within the current user's tenant."""
    logger.info("delete_payment_called", payment_id=payment_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        Payment,
        payment_id,
        current_user.tenant_id,
        not_found_detail="Payment not found",
    )