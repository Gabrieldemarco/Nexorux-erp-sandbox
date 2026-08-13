import pytest
import uuid
from fastapi import HTTPException
from app.api.v1.endpoints.tenants import (
    create_tenant,
    list_tenants,
    get_tenant,
    update_tenant,
    delete_tenant,
)
from app.api.v1.endpoints.companies import (
    create_company,
    list_companies,
    get_company,
    update_company,
    delete_company,
)
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.schemas.company import CompanyCreate, CompanyUpdate


@pytest.mark.asyncio
async def test_create_tenant(fake_db, fake_user):
    tenant_data = TenantCreate(name="New Tenant", status="active", settings={})
    tenant = await create_tenant(tenant_data, fake_db, fake_user)
    assert tenant is not None
    assert tenant.name == "New Tenant"


@pytest.mark.asyncio
async def test_list_tenants(fake_db, fake_user):
    tenants = await list_tenants(db=fake_db, current_user=fake_user)
    assert isinstance(tenants, list)
    assert len(tenants) == 1


@pytest.mark.asyncio
async def test_get_tenant(fake_db, fake_user, fake_tenant):
    tenant = await get_tenant(str(fake_tenant.id), fake_db, fake_user)
    assert tenant is not None
    assert tenant.id == fake_tenant.id


@pytest.mark.asyncio
async def test_update_tenant(fake_db, fake_user, fake_tenant):
    update_data = TenantUpdate(name="Updated Tenant", status="inactive")
    tenant = await update_tenant(str(fake_tenant.id), update_data, fake_db, fake_user)
    assert tenant.name == "Updated Tenant"
    assert tenant.status == "inactive"


@pytest.mark.asyncio
async def test_delete_tenant(fake_db, fake_user, fake_tenant):
    await delete_tenant(str(fake_tenant.id), fake_db, fake_user)
    tenants = await list_tenants(db=fake_db, current_user=fake_user)
    assert len(tenants) == 0


@pytest.mark.asyncio
async def test_get_tenant_different_tenant(fake_db, fake_user, fake_tenant):
    fake_user.tenant_id = uuid.uuid4()
    fake_user.permission_codes = ["tenants.read"]
    with pytest.raises(HTTPException) as excinfo:
        await get_tenant(str(fake_tenant.id), fake_db, fake_user)
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_create_company(fake_db, fake_user, fake_tenant):
    company_data = CompanyCreate(
        tenant_id=str(fake_tenant.id),
        legal_name="New Company",
        rut="12345678-9",
        fiscal_address="Address",
        phone="+598123456",
        email="company@example.com",
        website="https://company.example.com",
        country="UY",
        department="Montevideo",
        locality="Montevideo",
        currency="UYU",
        tax_regime="General",
    )
    company = await create_company(company_data, fake_db, fake_user)
    assert company is not None
    assert company.legal_name == "New Company"
    assert company.tenant_id == fake_user.tenant_id


@pytest.mark.asyncio
async def test_list_companies(fake_db, fake_user):
    companies = await list_companies(db=fake_db, current_user=fake_user)
    assert isinstance(companies, list)
    assert len(companies) == 1


@pytest.mark.asyncio
async def test_get_company(fake_db, fake_user, fake_company):
    company = await get_company(str(fake_company.id), fake_db, fake_user)
    assert company is not None
    assert company.id == fake_company.id


@pytest.mark.asyncio
async def test_update_company(fake_db, fake_user, fake_company):
    update_data = CompanyUpdate(legal_name="Updated Company", trade_name="Updated Trade")
    company = await update_company(str(fake_company.id), update_data, fake_db, fake_user)
    assert company.legal_name == "Updated Company"
    assert company.trade_name == "Updated Trade"


@pytest.mark.asyncio
async def test_delete_company(fake_db, fake_user, fake_company):
    await delete_company(str(fake_company.id), fake_db, fake_user)
    companies = await list_companies(db=fake_db, current_user=fake_user)
    assert len(companies) == 0


@pytest.mark.asyncio
async def test_get_company_different_tenant(fake_db, fake_user, fake_company):
    other_tenant_id = str(uuid.uuid4())
    fake_user.tenant_id = other_tenant_id
    with pytest.raises(HTTPException) as excinfo:
        await get_company(str(fake_company.id), fake_db, fake_user)
    assert excinfo.value.status_code == 404
