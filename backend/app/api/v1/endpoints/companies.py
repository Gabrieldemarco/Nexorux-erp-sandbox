from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.db.tenant_delete import delete_tenant_entity
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_COMPANIES_CREATE,
    PERMISSION_COMPANIES_DELETE,
    PERMISSION_COMPANIES_READ,
    PERMISSION_COMPANIES_UPDATE,
)
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_COMPANIES_CREATE)),
):
    """Create a new company within the current user's tenant."""
    logger.info("create_company_called", legal_name=company.legal_name, tenant_id=company.tenant_id)

    if str(company.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a company for a different tenant",
        )

    company_obj = Company(
        tenant_id=current_user.tenant_id,
        legal_name=company.legal_name,
        trade_name=company.trade_name,
        rut=company.rut,
        fiscal_address=company.fiscal_address,
        phone=company.phone,
        email=company.email,
        website=company.website,
        country=company.country,
        department=company.department,
        locality=company.locality,
        currency=company.currency,
        tax_regime=company.tax_regime,
    )
    db.add(company_obj)
    await db.commit()
    await db.refresh(company_obj)
    return company_obj


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_COMPANIES_READ)),
):
    """List companies for the current user's tenant."""
    logger.info("list_companies_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(Company).where(Company.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    companies = result.scalars().all()
    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_COMPANIES_READ)),
):
    """Get a specific company by ID for the current tenant."""
    logger.info("get_company_called", company_id=company_id, tenant_id=current_user.tenant_id)
    stmt = select(Company).where(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    company_obj = result.scalar_one_or_none()
    if not company_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return company_obj


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_COMPANIES_UPDATE)),
):
    """Update a company by ID for the current tenant."""
    logger.info("update_company_called", company_id=company_id, tenant_id=current_user.tenant_id)
    stmt = select(Company).where(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    company_obj = result.scalar_one_or_none()
    if not company_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    update_data = company.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(company_obj, field, value)

    await db.commit()
    await db.refresh(company_obj)
    return company_obj


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_COMPANIES_DELETE)),
):
    """Delete a company by ID for the current tenant."""
    logger.info("delete_company_called", company_id=company_id, tenant_id=current_user.tenant_id)
    await delete_tenant_entity(
        db,
        Company,
        company_id,
        current_user.tenant_id,
        not_found_detail="Company not found",
    )
