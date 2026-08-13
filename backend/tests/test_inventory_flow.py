"""Tests for purchase stock-in and sale stock-out inventory behavior."""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.branches import create_branch
from app.api.v1.endpoints.customers import create_customer
from app.api.v1.endpoints.invoice_items import create_invoice_item
from app.api.v1.endpoints.invoices import create_invoice
from app.api.v1.endpoints.products import create_product
from app.api.v1.endpoints.stock_movements import get_stock_balances
from app.api.v1.endpoints.warehouses import create_warehouse
from app.core.config import settings
from app.core.security import verify_password
from app.schemas.branch import BranchCreate
from app.schemas.customer import CustomerCreate
from app.schemas.invoice import InvoiceCreate
from app.schemas.invoice_item import InvoiceItemCreate
from app.schemas.product import ProductCreate
from app.schemas.warehouse import WarehouseCreate
from app.services.inventory import (
    create_purchase_stock_in,
    list_stock_balances,
)
from app.api.v1.endpoints.auth import change_current_user_password, update_current_user
from app.schemas.user import PasswordChangeRequest, UserProfileUpdate


async def _seed_catalog(fake_db, fake_user, fake_tenant, fake_company):
    customer = await create_customer(
        CustomerCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_type="final_consumer",
            legal_name="Consumidor Final",
            rut="00000000",
            currency="UYU",
            credit_limit=0,
        ),
        fake_db,
        fake_user,
    )
    branch = await create_branch(
        BranchCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Sucursal Test",
            code="BR-T",
        ),
        fake_db,
        fake_user,
    )
    warehouse = await create_warehouse(
        WarehouseCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            branch_id=branch.id,
            name="Depósito Test",
            code="WH-T",
        ),
        fake_db,
        fake_user,
    )
    product = await create_product(
        ProductCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Producto Stock",
            sku="STK-001",
            product_type="good",
            unit_of_measure="unit",
            sales_price=100.0,
            cost_price=40.0,
            tax_rate=22.0,
            is_service=False,
        ),
        fake_db,
        fake_user,
    )
    return customer, branch, warehouse, product


@pytest.mark.asyncio
async def test_purchase_stock_in_increases_balance(fake_db, fake_user, fake_tenant, fake_company):
    _, _, warehouse, product = await _seed_catalog(fake_db, fake_user, fake_tenant, fake_company)
    await create_purchase_stock_in(
        fake_db,
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        warehouse_id=warehouse.id,
        product_id=product.id,
        quantity=15,
        reference_id=product.id,
        movement_date=datetime.now(timezone.utc),
    )
    await fake_db.commit()

    balances = await list_stock_balances(
        fake_db,
        tenant_id=fake_tenant.id,
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    assert len(balances) == 1
    assert balances[0]["quantity"] == 15.0

    api_balances = await get_stock_balances(db=fake_db, current_user=fake_user)
    assert any(
        float(getattr(b, "quantity", None) if hasattr(b, "quantity") else b["quantity"]) == 15.0
        and str(getattr(b, "product_id", None) if hasattr(b, "product_id") else b["product_id"])
        == str(product.id)
        for b in api_balances
    )


@pytest.mark.asyncio
async def test_paid_sale_decreases_stock(fake_db, fake_user, fake_tenant, fake_company, monkeypatch):
    monkeypatch.setattr(settings, "STOCK_ALLOW_NEGATIVE", False)
    customer, branch, warehouse, product = await _seed_catalog(
        fake_db, fake_user, fake_tenant, fake_company
    )
    await create_purchase_stock_in(
        fake_db,
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        warehouse_id=warehouse.id,
        product_id=product.id,
        quantity=10,
        reference_id=product.id,
    )
    await fake_db.commit()

    invoice = await create_invoice(
        InvoiceCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_id=customer.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            document_type="101",
            series="A",
            number="00000042",
            status="paid",
            issue_date="2024-06-01T00:00:00",
            due_date="2024-06-01T00:00:00",
            subtotal=200.0,
            tax_total=44.0,
            discount_total=0.0,
            total=244.0,
            currency="UYU",
            exchange_rate=1.0,
        ),
        fake_db,
        fake_user,
    )

    item = await create_invoice_item(
        InvoiceItemCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            invoice_id=invoice.id,
            product_id=product.id,
            quantity=4.0,
            unit_price=50.0,
            discount=0.0,
            tax_amount=44.0,
            total=244.0,
            description="Venta test",
        ),
        fake_db,
        fake_user,
    )
    assert item is not None

    balances = await list_stock_balances(
        fake_db,
        tenant_id=fake_tenant.id,
        warehouse_id=warehouse.id,
        product_id=product.id,
    )
    assert balances[0]["quantity"] == 6.0

    movements = fake_db._store.get("stock_movement", [])
    outs = [m for m in movements if m.movement_type == "out"]
    assert len(outs) == 1
    assert float(outs[0].quantity) == 4.0
    assert outs[0].reference_type == "invoice_item"


@pytest.mark.asyncio
async def test_sale_blocked_when_insufficient_stock(
    fake_db, fake_user, fake_tenant, fake_company, monkeypatch
):
    monkeypatch.setattr(settings, "STOCK_ALLOW_NEGATIVE", False)
    customer, branch, warehouse, product = await _seed_catalog(
        fake_db, fake_user, fake_tenant, fake_company
    )
    await create_purchase_stock_in(
        fake_db,
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        warehouse_id=warehouse.id,
        product_id=product.id,
        quantity=2,
        reference_id=product.id,
    )
    await fake_db.commit()

    invoice = await create_invoice(
        InvoiceCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_id=customer.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            document_type="101",
            series="A",
            number="00000043",
            status="paid",
            issue_date="2024-06-01T00:00:00",
            due_date="2024-06-01T00:00:00",
            subtotal=500.0,
            tax_total=0.0,
            discount_total=0.0,
            total=500.0,
            currency="UYU",
            exchange_rate=1.0,
        ),
        fake_db,
        fake_user,
    )

    with pytest.raises(HTTPException) as excinfo:
        await create_invoice_item(
            InvoiceItemCreate(
                tenant_id=fake_tenant.id,
                company_id=fake_company.id,
                invoice_id=invoice.id,
                product_id=product.id,
                quantity=5.0,
                unit_price=100.0,
                discount=0.0,
                tax_amount=0.0,
                total=500.0,
                description="Oversell",
            ),
            fake_db,
            fake_user,
        )
    assert excinfo.value.status_code == 409
    assert "Stock insuficiente" in str(excinfo.value.detail)

    balances = await list_stock_balances(
        fake_db,
        tenant_id=fake_tenant.id,
        product_id=product.id,
    )
    assert balances[0]["quantity"] == 2.0


@pytest.mark.asyncio
async def test_update_profile_and_change_password(fake_db, fake_user):
    updated = await update_current_user(
        UserProfileUpdate(full_name="Nombre Nuevo", username="existing_user"),
        current_user=fake_user,
        db=fake_db,
    )
    assert updated.full_name == "Nombre Nuevo"

    with pytest.raises(HTTPException) as bad:
        await change_current_user_password(
            PasswordChangeRequest(current_password="wrong-pass", new_password="newpass99"),
            current_user=fake_user,
            db=fake_db,
        )
    assert bad.value.status_code == 400

    result = await change_current_user_password(
        PasswordChangeRequest(current_password="secret123", new_password="newpass99"),
        current_user=fake_user,
        db=fake_db,
    )
    assert result["message"]
    assert verify_password("newpass99", fake_user.password_hash)
