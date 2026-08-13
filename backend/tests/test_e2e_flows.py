import uuid
import pytest
from datetime import datetime
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.endpoints.products import create_product, list_products, get_product
from app.api.v1.endpoints.customers import create_customer, list_customers
from app.api.v1.endpoints.suppliers import create_supplier, list_suppliers
from app.api.v1.endpoints.branches import create_branch, list_branches
from app.api.v1.endpoints.warehouses import create_warehouse, list_warehouses
from app.api.v1.endpoints.invoices import create_invoice, list_invoices
from app.api.v1.endpoints.invoice_items import create_invoice_item
from app.api.v1.endpoints.payments import create_payment, list_payments
from app.api.v1.endpoints.stock_movements import create_stock_movement, list_stock_movements
from app.api.v1.endpoints.certificates import create_certificate, list_certificates
from app.api.v1.endpoints.fiscal_documents import (
    create_fiscal_document,
    issue_fiscal_document,
    send_fiscal_document,
    query_fiscal_document_status,
    retry_fiscal_document,
)
from app.schemas.product import ProductCreate
from app.schemas.customer import CustomerCreate
from app.schemas.supplier import SupplierCreate
from app.schemas.branch import BranchCreate
from app.schemas.warehouse import WarehouseCreate
from app.schemas.invoice import InvoiceCreate
from app.schemas.invoice_item import InvoiceItemCreate
from app.schemas.payment import PaymentCreate
from app.schemas.stock_movement import StockMovementCreate
from app.schemas.certificate import CertificateCreate
from app.schemas.fiscal_document import FiscalDocumentCreate, FiscalDocumentIssueRequest, FiscalDocumentSendRequest, FiscalDocumentRetryRequest


@pytest.mark.asyncio
async def test_pagination_products(fake_db, fake_user, fake_tenant, fake_company):
    for i in range(5):
        data = ProductCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name=f"Product {i}",
            sku=f"SKU-{i}",
            product_type="good",
            unit_of_measure="unit",
            sales_price=100.0,
            cost_price=50.0,
            tax_rate=22.0,
        )
        await create_product(data, fake_db, fake_user)

    page1 = await list_products(db=fake_db, current_user=fake_user, skip=0, limit=2)
    assert len(page1) == 2
    assert page1[0].name == "Product 0"

    page2 = await list_products(db=fake_db, current_user=fake_user, skip=2, limit=2)
    assert len(page2) == 2
    assert page2[0].name == "Product 2"


@pytest.mark.asyncio
async def test_pagination_customers(fake_db, fake_user, fake_tenant, fake_company):
    for i in range(3):
        data = CustomerCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_type="company",
            legal_name=f"Customer {i}",
            rut=f"1234567{i}",
            currency="UYU",
            credit_limit=1000.0,
        )
        await create_customer(data, fake_db, fake_user)

    all_customers = await list_customers(db=fake_db, current_user=fake_user, skip=0, limit=100)
    assert len(all_customers) == 3

    page1 = await list_customers(db=fake_db, current_user=fake_user, skip=0, limit=2)
    assert len(page1) == 2


@pytest.mark.asyncio
async def test_create_invalid_rut_rejected(fake_db, fake_user, fake_tenant, fake_company):
    with pytest.raises(ValidationError):
        await create_customer(
            CustomerCreate(
                tenant_id=fake_tenant.id,
                company_id=fake_company.id,
                customer_type="company",
                legal_name="Bad RUT",
                rut="ABC-123",
                currency="UYU",
                credit_limit=1000.0,
            ),
            fake_db,
            fake_user,
        )


@pytest.mark.asyncio
async def test_create_invalid_email_rejected(fake_db, fake_user, fake_tenant, fake_company):
    with pytest.raises(ValidationError):
        await create_customer(
            CustomerCreate(
                tenant_id=fake_tenant.id,
                company_id=fake_company.id,
                customer_type="company",
                legal_name="Bad Email",
                rut="12345678-9",
                email="not-an-email",
                currency="UYU",
                credit_limit=1000.0,
            ),
            fake_db,
            fake_user,
        )


@pytest.mark.asyncio
async def test_end_to_end_fiscal_flow(fake_db, fake_user, fake_tenant, fake_company):
    customer = await create_customer(
        CustomerCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_type="company",
            legal_name="Fiscal Customer",
            rut="87654321-0",
            currency="UYU",
            credit_limit=5000.0,
        ),
        fake_db,
        fake_user,
    )

    invoice = await create_invoice(
        InvoiceCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_id=str(customer.id),
            branch_id=str(uuid.uuid4()),
            warehouse_id=str(uuid.uuid4()),
            document_type="111",
            series="A",
            number="0001-00000001",
            issue_date=datetime(2024, 1, 1),
            due_date=datetime(2024, 1, 31),
            subtotal=100.0,
            tax_total=22.0,
            discount_total=0.0,
            total=122.0,
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
            invoice_id=str(invoice.id),
            product_id=str(uuid.uuid4()),
            quantity=1.0,
            unit_price=100.0,
            discount=0.0,
            tax_amount=22.0,
            total=122.0,
            description="Test item",
        ),
        fake_db,
        fake_user,
    )

    fiscal_doc = await create_fiscal_document(
        FiscalDocumentCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            invoice_id=str(invoice.id),
            document_type="111",
            series="A",
            number="0001-00000001",
            state="draft",
        ),
        fake_db,
        fake_user,
    )

    from app.services.fiscal.engine import FiscalEngine

    class FakeFiscalEngine:
        def __init__(self, db):
            pass

        async def issue_cfe(self, invoice_id, certificate_id, tenant_id, request_id=None):
            from app.models.fiscal_document import FiscalDocument
            doc = FiscalDocument(
                tenant_id=tenant_id,
                company_id=fake_company.id,
                invoice_id=invoice_id,
                document_type="111",
                series="A",
                number="0001-00000001",
                state="pending_sign",
                issued_at=datetime.utcnow(),
                signed_at=datetime.utcnow(),
                raw_payload={},
            )
            doc.id = fiscal_doc.id
            return doc

        async def send_cfe(self, fiscal_document_id, tenant_id, environment=None, certificate_id=None):
            return {"status_code": "aceptado", "status_message": "OK"}

        async def query_status(self, fiscal_document_id, tenant_id, environment=None):
            return {"status_code": "aceptado", "status_message": "OK"}

        async def retry_cfe(self, fiscal_document_id, tenant_id):
            from app.models.fiscal_document import FiscalDocument
            doc = FiscalDocument(
                tenant_id=tenant_id,
                company_id=fake_company.id,
                invoice_id=uuid.uuid4(),
                document_type="111",
                series="A",
                number="0001-00000001",
                state="pending_send",
            )
            doc.id = fiscal_document_id
            return doc

    original_init = FiscalEngine.__init__
    FiscalEngine.__init__ = lambda self, db: None
    for attr in ['issue_cfe', 'send_cfe', 'query_status', 'retry_cfe']:
        setattr(FiscalEngine, attr, FakeFiscalEngine(None).__getattribute__(attr))

    try:
        issued = await issue_fiscal_document(
            str(fiscal_doc.id),
            FiscalDocumentIssueRequest(certificate_id=uuid.uuid4()),
            fake_db,
            fake_user,
        )
        assert issued.state == "pending_sign"

        import app.api.v1.endpoints.fiscal_documents as fiscal_endpoints

        class FakeTask:
            id = "e2e-task-id"

        original_delay = fiscal_endpoints.send_cfe_async.delay
        fiscal_endpoints.send_cfe_async.delay = lambda *args, **kwargs: FakeTask()
        try:
            send_result = await send_fiscal_document(
                str(issued.id),
                FiscalDocumentSendRequest(environment="testing"),
                fake_db,
                fake_user,
            )
            assert send_result.task_id == "e2e-task-id"
            assert send_result.status == "queued"
        finally:
            fiscal_endpoints.send_cfe_async.delay = original_delay

        query_result = await query_fiscal_document_status(
            str(issued.id),
            environment="testing",
            db=fake_db,
            current_user=fake_user,
        )
        assert query_result["status_code"] == "aceptado"

        retry_result = await retry_fiscal_document(
            str(issued.id),
            FiscalDocumentRetryRequest(),
            fake_db,
            fake_user,
        )
        assert retry_result.id == issued.id
    finally:
        FiscalEngine.__init__ = original_init
        for attr in ['issue_cfe', 'send_cfe', 'query_status', 'retry_cfe']:
            if hasattr(FiscalEngine, attr):
                try:
                    delattr(FiscalEngine, attr)
                except AttributeError:
                    pass


@pytest.mark.asyncio
async def test_end_to_end_supplier_invoice_payment_flow(fake_db, fake_user, fake_tenant, fake_company):
    from app.api.v1.endpoints.suppliers import create_supplier, list_suppliers
    from app.api.v1.endpoints.invoices import create_invoice, list_invoices
    from app.api.v1.endpoints.payments import create_payment, list_payments
    from app.schemas.supplier import SupplierCreate
    from app.schemas.invoice import InvoiceCreate
    from app.schemas.payment import PaymentCreate

    supplier = await create_supplier(
        SupplierCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            legal_name="Test Supplier",
            rut="87654321-0",
            currency="UYU",
        ),
        fake_db,
        fake_user,
    )

    customer = await create_customer(
        CustomerCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_type="company",
            legal_name="Test Customer",
            rut="12345678-9",
            currency="UYU",
            credit_limit=1000.0,
        ),
        fake_db,
        fake_user,
    )

    branch = await create_branch(
        BranchCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Main Branch",
            code="BR-001",
        ),
        fake_db,
        fake_user,
    )

    warehouse = await create_warehouse(
        WarehouseCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            branch_id=branch.id,
            name="Main Warehouse",
            code="WH-001",
        ),
        fake_db,
        fake_user,
    )

    invoice = await create_invoice(
        InvoiceCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_id=customer.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            document_type="111",
            series="A",
            number="0001-00000001",
            issue_date=datetime(2024, 1, 1),
            due_date=datetime(2024, 1, 31),
            subtotal=100.0,
            tax_total=22.0,
            discount_total=0.0,
            total=122.0,
            currency="UYU",
            exchange_rate=1.0,
        ),
        fake_db,
        fake_user,
    )

    payment = await create_payment(
        PaymentCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            invoice_id=invoice.id,
            customer_id=customer.id,
            payment_date="2024-01-15T00:00:00",
            amount=122.0,
            currency="UYU",
            payment_method="transfer",
            status="completed",
        ),
        fake_db,
        fake_user,
    )

    assert len(await list_suppliers(db=fake_db, current_user=fake_user)) == 1
    assert len(await list_invoices(db=fake_db, current_user=fake_user)) == 1
    assert len(await list_payments(db=fake_db, current_user=fake_user)) == 1
    assert payment.invoice_id == invoice.id


@pytest.mark.asyncio
async def test_end_to_end_stock_movement_flow(fake_db, fake_user, fake_tenant, fake_company):
    from app.api.v1.endpoints.products import create_product, list_products
    from app.api.v1.endpoints.branches import create_branch
    from app.api.v1.endpoints.warehouses import create_warehouse
    from app.api.v1.endpoints.stock_movements import create_stock_movement, list_stock_movements
    from app.schemas.product import ProductCreate
    from app.schemas.stock_movement import StockMovementCreate

    product = await create_product(
        ProductCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Test Product",
            sku="SKU-001",
            product_type="good",
            unit_of_measure="unit",
            sales_price=100.0,
            cost_price=50.0,
            tax_rate=22.0,
        ),
        fake_db,
        fake_user,
    )

    branch = await create_branch(
        BranchCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Main Branch",
            code="BR-001",
        ),
        fake_db,
        fake_user,
    )

    warehouse = await create_warehouse(
        WarehouseCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            branch_id=branch.id,
            name="Main Warehouse",
            code="WH-001",
        ),
        fake_db,
        fake_user,
    )

    movement = await create_stock_movement(
        StockMovementCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            quantity=10.0,
            movement_type="inbound",
            movement_date="2024-01-01T00:00:00",
        ),
        fake_db,
        fake_user,
    )

    assert len(await list_products(db=fake_db, current_user=fake_user)) == 1
    assert len(await list_stock_movements(db=fake_db, current_user=fake_user)) == 1
    assert movement.quantity == 10.0


@pytest.mark.asyncio
async def test_end_to_end_certificate_fiscal_flow(fake_db, fake_user, fake_tenant, fake_company):
    from app.api.v1.endpoints.certificates import create_certificate, list_certificates
    from app.api.v1.endpoints.customers import create_customer
    from app.api.v1.endpoints.invoices import create_invoice
    from app.api.v1.endpoints.fiscal_documents import create_fiscal_document
    from app.schemas.certificate import CertificateCreate
    from app.schemas.customer import CustomerCreate
    from app.schemas.invoice import InvoiceCreate
    from app.schemas.fiscal_document import FiscalDocumentCreate

    certificate = await create_certificate(
        CertificateCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Signing Cert",
            thumbprint="ABCD1234",
            usage="signing",
        ),
        fake_db,
        fake_user,
    )

    customer = await create_customer(
        CustomerCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_type="company",
            legal_name="Fiscal Customer",
            rut="87654321-0",
            currency="UYU",
            credit_limit=5000.0,
        ),
        fake_db,
        fake_user,
    )

    branch = await create_branch(
        BranchCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            name="Main Branch",
            code="BR-001",
        ),
        fake_db,
        fake_user,
    )

    warehouse = await create_warehouse(
        WarehouseCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            branch_id=branch.id,
            name="Main Warehouse",
            code="WH-001",
        ),
        fake_db,
        fake_user,
    )

    invoice = await create_invoice(
        InvoiceCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            customer_id=customer.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            document_type="111",
            series="A",
            number="0001-00000001",
            issue_date=datetime(2024, 1, 1),
            due_date=datetime(2024, 1, 31),
            subtotal=100.0,
            tax_total=22.0,
            discount_total=0.0,
            total=122.0,
            currency="UYU",
            exchange_rate=1.0,
        ),
        fake_db,
        fake_user,
    )

    fiscal_doc = await create_fiscal_document(
        FiscalDocumentCreate(
            tenant_id=fake_tenant.id,
            company_id=fake_company.id,
            invoice_id=str(invoice.id),
            document_type="111",
            series="A",
            number="0001-00000001",
            state="draft",
        ),
        fake_db,
        fake_user,
    )

    assert len(await list_certificates(db=fake_db, current_user=fake_user)) == 1
    assert fiscal_doc.invoice_id == str(invoice.id)
    assert fiscal_doc.state == "draft"
