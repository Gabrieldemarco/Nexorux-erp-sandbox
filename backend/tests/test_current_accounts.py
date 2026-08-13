"""Current accounts (cuenta corriente) from invoices + payment records."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.branches import create_branch
from app.api.v1.endpoints.current_accounts import get_account, list_accounts
from app.api.v1.endpoints.customers import create_customer
from app.api.v1.endpoints.invoices import create_invoice, get_invoice
from app.api.v1.endpoints.payments import create_payment
from app.api.v1.endpoints.warehouses import create_warehouse
from app.core.catalog import INVOICE_STATUSES, PAYMENT_STATUSES, build_catalog
from app.schemas.branch import BranchCreate
from app.schemas.customer import CustomerCreate
from app.schemas.invoice import InvoiceCreate
from app.schemas.payment import PaymentCreate
from app.schemas.warehouse import WarehouseCreate
from app.services.current_accounts import COMPLETED_PAYMENT_STATUSES, RECEIVABLE_STATUSES


async def _setup_customer(fake_db, fake_user, fake_tenant, fake_company, credit_limit=1000.0):
    customer = await create_customer(
        CustomerCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_type="company",
            legal_name="Cliente CC",
            rut="211111110019",
            currency="UYU",
            credit_limit=credit_limit,
        ),
        fake_db,
        fake_user,
    )
    branch = await create_branch(
        BranchCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Casa central",
            code="CC-1",
        ),
        fake_db,
        fake_user,
    )
    warehouse = await create_warehouse(
        WarehouseCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            branch_id=branch.id,
            name="Depósito",
            code="WH-CC",
        ),
        fake_db,
        fake_user,
    )
    return customer, branch, warehouse


async def _issue_invoice(
    fake_db,
    fake_user,
    fake_tenant,
    fake_company,
    customer,
    branch,
    warehouse,
    *,
    total=122.0,
    status="issued",
    document_type="111",
    number="0001",
    due_date=None,
):
    return await create_invoice(
        InvoiceCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_id=customer.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            document_type=document_type,
            series="A",
            number=number,
            status=status,
            issue_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            due_date=due_date or datetime(2024, 1, 31, tzinfo=timezone.utc),
            subtotal=100.0,
            tax_total=22.0,
            discount_total=0.0,
            total=total,
            currency="UYU",
            exchange_rate=1.0,
        ),
        fake_db,
        fake_user,
    )


def test_receivable_flags_come_from_catalog():
    expected = {row["value"] for row in INVOICE_STATUSES if row["affects_receivable"]}
    assert RECEIVABLE_STATUSES == expected
    assert "draft" not in RECEIVABLE_STATUSES
    assert "cancelled" not in RECEIVABLE_STATUSES
    assert "issued" in RECEIVABLE_STATUSES
    paid_statuses = {row["value"] for row in PAYMENT_STATUSES if row["counts_as_paid"]}
    assert COMPLETED_PAYMENT_STATUSES == paid_statuses
    assert "completed" in COMPLETED_PAYMENT_STATUSES
    catalog = build_catalog()
    assert catalog["defaults"]["invoice_paid_status"] == "paid"
    assert catalog["defaults"]["invoice_open_status"] == "issued"


@pytest.mark.asyncio
async def test_open_invoice_creates_customer_balance(fake_db, fake_user, fake_tenant, fake_company):
    customer, branch, warehouse = await _setup_customer(fake_db, fake_user, fake_tenant, fake_company)
    await _issue_invoice(fake_db, fake_user, fake_tenant, fake_company, customer, branch, warehouse)

    rows = await list_accounts(db=fake_db, current_user=fake_user)
    assert len(rows) == 1
    row = rows[0]
    assert row.customer_id == customer.id
    assert row.invoiced == 122.0
    assert row.paid == 0.0
    assert row.balance == 122.0
    assert row.open_invoices == 1
    assert row.available_credit == 878.0


@pytest.mark.asyncio
async def test_draft_invoice_does_not_affect_receivable(fake_db, fake_user, fake_tenant, fake_company):
    customer, branch, warehouse = await _setup_customer(fake_db, fake_user, fake_tenant, fake_company)
    await _issue_invoice(
        fake_db, fake_user, fake_tenant, fake_company, customer, branch, warehouse, status="draft"
    )
    rows = await list_accounts(db=fake_db, current_user=fake_user)
    assert rows[0].balance == 0.0
    assert rows[0].invoiced == 0.0


@pytest.mark.asyncio
async def test_completed_payment_clears_balance_and_marks_invoice_paid(
    fake_db, fake_user, fake_tenant, fake_company
):
    customer, branch, warehouse = await _setup_customer(fake_db, fake_user, fake_tenant, fake_company)
    invoice = await _issue_invoice(
        fake_db, fake_user, fake_tenant, fake_company, customer, branch, warehouse
    )
    await create_payment(
        PaymentCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            invoice_id=invoice.id,
            customer_id=None,
            payment_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            amount=122.0,
            currency="UYU",
            payment_method="transfer",
            status="completed",
        ),
        fake_db,
        fake_user,
    )

    refreshed = await get_invoice(str(invoice.id), fake_db, fake_user)
    assert refreshed.status == "paid"

    statement = await get_account(customer.id, db=fake_db, current_user=fake_user)
    assert statement.balance == 0.0
    assert statement.paid == 122.0
    assert statement.invoices[0].balance == 0.0
    assert len(statement.payments) == 1
    assert statement.payments[0].invoice_id == invoice.id


@pytest.mark.asyncio
async def test_pending_payment_does_not_reduce_balance(fake_db, fake_user, fake_tenant, fake_company):
    customer, branch, warehouse = await _setup_customer(fake_db, fake_user, fake_tenant, fake_company)
    invoice = await _issue_invoice(
        fake_db, fake_user, fake_tenant, fake_company, customer, branch, warehouse
    )
    await create_payment(
        PaymentCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            invoice_id=invoice.id,
            customer_id=customer.id,
            payment_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            amount=122.0,
            currency="UYU",
            payment_method="cash",
            status="pending",
        ),
        fake_db,
        fake_user,
    )
    rows = await list_accounts(db=fake_db, current_user=fake_user)
    assert rows[0].balance == 122.0
    refreshed = await get_invoice(str(invoice.id), fake_db, fake_user)
    assert refreshed.status == "issued"


@pytest.mark.asyncio
async def test_partial_payment_and_credit_note(fake_db, fake_user, fake_tenant, fake_company):
    customer, branch, warehouse = await _setup_customer(fake_db, fake_user, fake_tenant, fake_company)
    invoice = await _issue_invoice(
        fake_db, fake_user, fake_tenant, fake_company, customer, branch, warehouse
    )
    await create_payment(
        PaymentCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            invoice_id=invoice.id,
            customer_id=customer.id,
            payment_date=datetime(2024, 1, 10, tzinfo=timezone.utc),
            amount=50.0,
            currency="UYU",
            payment_method="cash",
            status="completed",
        ),
        fake_db,
        fake_user,
    )
    await _issue_invoice(
        fake_db,
        fake_user,
        fake_tenant,
        fake_company,
        customer,
        branch,
        warehouse,
        total=22.0,
        document_type="102",
        number="NC-1",
    )
    statement = await get_account(customer.id, db=fake_db, current_user=fake_user)
    assert statement.invoiced == 100.0  # 122 - 22 NC
    assert statement.paid == 50.0
    assert statement.balance == 50.0
    refreshed = await get_invoice(str(invoice.id), fake_db, fake_user)
    assert refreshed.status == "issued"


@pytest.mark.asyncio
async def test_overdue_open_invoice(fake_db, fake_user, fake_tenant, fake_company):
    customer, branch, warehouse = await _setup_customer(fake_db, fake_user, fake_tenant, fake_company)
    past = datetime.now(timezone.utc) - timedelta(days=10)
    await _issue_invoice(
        fake_db,
        fake_user,
        fake_tenant,
        fake_company,
        customer,
        branch,
        warehouse,
        due_date=past,
    )
    rows = await list_accounts(db=fake_db, current_user=fake_user)
    assert rows[0].overdue == 122.0


@pytest.mark.asyncio
async def test_missing_customer_statement_404(fake_db, fake_user):
    from uuid import uuid4

    with pytest.raises(HTTPException) as exc:
        await get_account(uuid4(), db=fake_db, current_user=fake_user)
    assert exc.value.status_code == 404
