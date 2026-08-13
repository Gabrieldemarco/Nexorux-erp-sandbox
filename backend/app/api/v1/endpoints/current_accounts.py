from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PERMISSION_PAYMENTS_READ
from app.core.rbac import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.current_account import CurrentAccountBalance, CurrentAccountStatement
from app.services.current_accounts import get_current_account, list_current_accounts

router = APIRouter()


@router.get("/", response_model=List[CurrentAccountBalance])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PAYMENTS_READ)),
):
    """List customer current-account balances for the current tenant."""
    return await list_current_accounts(
        db,
        current_user.tenant_id,
        company_id=current_user.company_id,
    )


@router.get("/{customer_id}", response_model=CurrentAccountStatement)
async def get_account(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_PAYMENTS_READ)),
):
    """Invoice and payment ledger for one customer."""
    statement = await get_current_account(
        db,
        current_user.tenant_id,
        customer_id,
        company_id=current_user.company_id,
    )
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return statement
