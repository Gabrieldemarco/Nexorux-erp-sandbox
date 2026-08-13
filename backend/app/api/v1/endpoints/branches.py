from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.branch import Branch
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_BRANCHES_CREATE,
    PERMISSION_BRANCHES_DELETE,
    PERMISSION_BRANCHES_READ,
    PERMISSION_BRANCHES_UPDATE
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=BranchResponse)
async def create_branch(
    branch: BranchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_BRANCHES_CREATE)),
):
    """Create a new branch."""
    logger.info("create_branch_called", tenant_id=branch.tenant_id, company_id=branch.company_id)

    if str(branch.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a branch for a different tenant",
        )

    branch_obj = Branch(**branch.model_dump())
    db.add(branch_obj)
    await db.commit()
    await db.refresh(branch_obj)
    return branch_obj


@router.get("/", response_model=List[BranchResponse])
async def list_branches(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_BRANCHES_READ)),
):
    """List branches for the current user's tenant."""
    logger.info("list_branches_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Branch).where(Branch.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    branches = result.scalars().all()
    return branches


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_BRANCHES_READ)),
):
    """Get a specific branch by ID for the current tenant."""
    logger.info("get_branch_called", branch_id=branch_id, tenant_id=current_user.tenant_id)
    stmt = select(Branch).where(
        Branch.id == branch_id,
        Branch.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    branch_obj = result.scalar_one_or_none()
    if not branch_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    return branch_obj


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    branch: BranchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_BRANCHES_UPDATE)),
):
    """Update a branch by ID for the current tenant."""
    logger.info("update_branch_called", branch_id=branch_id)
    stmt = select(Branch).where(
        Branch.id == branch_id,
        Branch.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    branch_obj = result.scalar_one_or_none()
    if not branch_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )

    update_data = branch.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(branch_obj, field, value)

    await db.commit()
    await db.refresh(branch_obj)
    return branch_obj


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_BRANCHES_DELETE)),
):
    """Delete a branch by ID for the current tenant."""
    logger.info("delete_branch_called", branch_id=branch_id)
    await delete_tenant_entity(
        db,
        Branch,
        branch_id,
        current_user.tenant_id,
        not_found_detail="Branch not found",
    )
    return None