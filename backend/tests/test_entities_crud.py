import uuid
import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.products import create_product, list_products, get_product, update_product, delete_product
from app.api.v1.endpoints.customers import create_customer, list_customers, get_customer, update_customer, delete_customer
from app.api.v1.endpoints.suppliers import create_supplier, list_suppliers, get_supplier, update_supplier, delete_supplier
from app.api.v1.endpoints.branches import create_branch, list_branches, get_branch, update_branch, delete_branch
from app.api.v1.endpoints.warehouses import create_warehouse, list_warehouses, get_warehouse, update_warehouse, delete_warehouse
from app.api.v1.endpoints.invoices import create_invoice, list_invoices, get_invoice, update_invoice, delete_invoice
from app.api.v1.endpoints.invoice_items import create_invoice_item, list_invoice_items, get_invoice_item, update_invoice_item, delete_invoice_item
from app.api.v1.endpoints.payments import create_payment, list_payments, get_payment, update_payment, delete_payment
from app.api.v1.endpoints.stock_movements import create_stock_movement, list_stock_movements, get_stock_movement, update_stock_movement, delete_stock_movement
from app.api.v1.endpoints.roles import create_role, list_roles, get_role, update_role, delete_role
from app.api.v1.endpoints.permissions import create_permission, list_permissions, get_permission, update_permission, delete_permission
from app.api.v1.endpoints.fiscal_documents import create_fiscal_document, list_fiscal_documents, get_fiscal_document, update_fiscal_document, delete_fiscal_document
from app.api.v1.endpoints.audit_logs import list_audit_logs, get_audit_log

from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.schemas.branch import BranchCreate, BranchUpdate
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate
from app.schemas.invoice_item import InvoiceItemCreate, InvoiceItemUpdate
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.schemas.stock_movement import StockMovementCreate, StockMovementUpdate
from app.schemas.role import RoleCreate, RoleUpdate
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.schemas.fiscal_document import FiscalDocumentCreate, FiscalDocumentUpdate
from app.schemas.audit_log import AuditLogCreate


@pytest.mark.asyncio
async def test_product_crud(fake_db, fake_user, fake_tenant, fake_company):
    product_data = ProductCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Test Product",
        sku="SKU-001",
        product_type="good",
        unit_of_measure="unit",
        sales_price=100.0,
        cost_price=50.0,
        tax_rate=22.0,
    )
    product = await create_product(product_data, fake_db, fake_user)
    assert product is not None
    assert product.name == "Test Product"
    assert product.tenant_id == fake_user.tenant_id

    products = await list_products(db=fake_db, current_user=fake_user)
    assert isinstance(products, list)
    assert len(products) == 1

    found = await get_product(str(product.id), fake_db, fake_user)
    assert found.id == product.id

    update_data = ProductUpdate(name="Updated Product", sales_price=120.0)
    updated = await update_product(str(product.id), update_data, fake_db, fake_user)
    assert updated.name == "Updated Product"
    assert updated.sales_price == 120.0

    await delete_product(str(product.id), fake_db, fake_user)
    products = await list_products(db=fake_db, current_user=fake_user)
    assert len(products) == 0


@pytest.mark.asyncio
async def test_customer_crud(fake_db, fake_user, fake_tenant, fake_company):
    customer_data = CustomerCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_type="company",
        legal_name="Test Customer",
        rut="12345678-9",
        currency="UYU",
        credit_limit=1000.0,
    )
    customer = await create_customer(customer_data, fake_db, fake_user)
    assert customer is not None
    assert customer.legal_name == "Test Customer"

    customers = await list_customers(db=fake_db, current_user=fake_user)
    assert len(customers) == 1

    found = await get_customer(str(customer.id), fake_db, fake_user)
    assert found.id == customer.id

    update_data = CustomerUpdate(legal_name="Updated Customer", credit_limit=2000.0)
    updated = await update_customer(str(customer.id), update_data, fake_db, fake_user)
    assert updated.legal_name == "Updated Customer"

    await delete_customer(str(customer.id), fake_db, fake_user)
    customers = await list_customers(db=fake_db, current_user=fake_user)
    assert len(customers) == 0


@pytest.mark.asyncio
async def test_supplier_crud(fake_db, fake_user, fake_tenant, fake_company):
    supplier_data = SupplierCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        legal_name="Test Supplier",
        rut="87654321-0",
        currency="UYU",
    )
    supplier = await create_supplier(supplier_data, fake_db, fake_user)
    assert supplier is not None
    assert supplier.legal_name == "Test Supplier"

    suppliers = await list_suppliers(db=fake_db, current_user=fake_user)
    assert len(suppliers) == 1

    found = await get_supplier(str(supplier.id), fake_db, fake_user)
    assert found.id == supplier.id

    update_data = SupplierUpdate(legal_name="Updated Supplier")
    updated = await update_supplier(str(supplier.id), update_data, fake_db, fake_user)
    assert updated.legal_name == "Updated Supplier"

    await delete_supplier(str(supplier.id), fake_db, fake_user)
    suppliers = await list_suppliers(db=fake_db, current_user=fake_user)
    assert len(suppliers) == 0


@pytest.mark.asyncio
async def test_branch_crud(fake_db, fake_user, fake_tenant, fake_company):
    branch_data = BranchCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Main Branch",
        code="BR-001",
    )
    branch = await create_branch(branch_data, fake_db, fake_user)
    assert branch is not None
    assert branch.name == "Main Branch"

    branches = await list_branches(db=fake_db, current_user=fake_user)
    assert len(branches) == 1

    found = await get_branch(str(branch.id), fake_db, fake_user)
    assert found.id == branch.id

    update_data = BranchUpdate(name="Updated Branch")
    updated = await update_branch(str(branch.id), update_data, fake_db, fake_user)
    assert updated.name == "Updated Branch"

    await delete_branch(str(branch.id), fake_db, fake_user)
    branches = await list_branches(db=fake_db, current_user=fake_user)
    assert len(branches) == 0


@pytest.mark.asyncio
async def test_warehouse_crud(fake_db, fake_user, fake_tenant, fake_company):
    branch_data = BranchCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Main Branch",
        code="BR-001",
    )
    branch = await create_branch(branch_data, fake_db, fake_user)

    warehouse_data = WarehouseCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        branch_id=branch.id,
        name="Main Warehouse",
        code="WH-001",
    )
    warehouse = await create_warehouse(warehouse_data, fake_db, fake_user)
    assert warehouse is not None
    assert warehouse.name == "Main Warehouse"

    warehouses = await list_warehouses(db=fake_db, current_user=fake_user)
    assert len(warehouses) == 1

    found = await get_warehouse(str(warehouse.id), fake_db, fake_user)
    assert found.id == warehouse.id

    update_data = WarehouseUpdate(name="Updated Warehouse")
    updated = await update_warehouse(str(warehouse.id), update_data, fake_db, fake_user)
    assert updated.name == "Updated Warehouse"

    await delete_warehouse(str(warehouse.id), fake_db, fake_user)
    warehouses = await list_warehouses(db=fake_db, current_user=fake_user)
    assert len(warehouses) == 0


@pytest.mark.asyncio
async def test_role_crud(fake_db, fake_user, fake_tenant):
    role_data = RoleCreate(
        tenant_id=fake_tenant.id,
        name="Admin",
        key="admin",
        description="Administrator role",
    )
    role = await create_role(role_data, fake_db, fake_user)
    assert role is not None
    assert role.name == "Admin"

    roles = await list_roles(db=fake_db, current_user=fake_user)
    assert len(roles) == 1

    found = await get_role(str(role.id), fake_db, fake_user)
    assert found.id == role.id

    update_data = RoleUpdate(name="Super Admin")
    updated = await update_role(str(role.id), update_data, fake_db, fake_user)
    assert updated.name == "Super Admin"

    await delete_role(str(role.id), fake_db, fake_user)
    roles = await list_roles(db=fake_db, current_user=fake_user)
    assert len(roles) == 0


@pytest.mark.asyncio
async def test_permission_crud(fake_db, fake_user, fake_tenant):
    permission_data = PermissionCreate(
        tenant_id=fake_tenant.id,
        name="Read Users",
        code="users.read",
        description="Read user data",
    )
    permission = await create_permission(permission_data, fake_db, fake_user)
    assert permission is not None
    assert permission.name == "Read Users"

    permissions = await list_permissions(db=fake_db, current_user=fake_user)
    assert len(permissions) == 1

    found = await get_permission(str(permission.id), fake_db, fake_user)
    assert found.id == permission.id

    update_data = PermissionUpdate(name="Write Users")
    updated = await update_permission(str(permission.id), update_data, fake_db, fake_user)
    assert updated.name == "Write Users"

    await delete_permission(str(permission.id), fake_db, fake_user)
    permissions = await list_permissions(db=fake_db, current_user=fake_user)
    assert len(permissions) == 0


@pytest.mark.asyncio
async def test_invoice_crud(fake_db, fake_user, fake_tenant, fake_company):
    customer_data = CustomerCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_type="company",
        legal_name="Test Customer",
        rut="12345678-9",
        currency="UYU",
        credit_limit=1000.0,
    )
    customer = await create_customer(customer_data, fake_db, fake_user)

    branch_data = BranchCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Main Branch",
        code="BR-001",
    )
    branch = await create_branch(branch_data, fake_db, fake_user)

    warehouse_data = WarehouseCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        branch_id=branch.id,
        name="Main Warehouse",
        code="WH-001",
    )
    warehouse = await create_warehouse(warehouse_data, fake_db, fake_user)

    invoice_data = InvoiceCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_id=customer.id,
        branch_id=branch.id,
        warehouse_id=warehouse.id,
        document_type="e-Factura",
        series="A",
        number="0001-00000001",
        issue_date="2024-01-01T00:00:00",
        due_date="2024-01-31T00:00:00",
        subtotal=100.0,
        tax_total=22.0,
        discount_total=0.0,
        total=122.0,
        currency="UYU",
        exchange_rate=1.0,
    )
    invoice = await create_invoice(invoice_data, fake_db, fake_user)
    assert invoice is not None
    assert invoice.document_type == "e-Factura"

    invoices = await list_invoices(db=fake_db, current_user=fake_user)
    assert len(invoices) == 1

    found = await get_invoice(str(invoice.id), fake_db, fake_user)
    assert found.id == invoice.id

    update_data = InvoiceUpdate(status="issued", notes="Paid")
    updated = await update_invoice(str(invoice.id), update_data, fake_db, fake_user)
    assert updated.status == "issued"

    await delete_invoice(str(invoice.id), fake_db, fake_user)
    invoices = await list_invoices(db=fake_db, current_user=fake_user)
    assert len(invoices) == 0


@pytest.mark.asyncio
async def test_invoice_item_crud(fake_db, fake_user, fake_tenant, fake_company):
    customer_data = CustomerCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_type="company",
        legal_name="Test Customer",
        rut="12345678-9",
        currency="UYU",
        credit_limit=1000.0,
    )
    customer = await create_customer(customer_data, fake_db, fake_user)

    branch_data = BranchCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Main Branch",
        code="BR-001",
    )
    branch = await create_branch(branch_data, fake_db, fake_user)

    warehouse_data = WarehouseCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        branch_id=branch.id,
        name="Main Warehouse",
        code="WH-001",
    )
    warehouse = await create_warehouse(warehouse_data, fake_db, fake_user)

    invoice_data = InvoiceCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_id=customer.id,
        branch_id=branch.id,
        warehouse_id=warehouse.id,
        document_type="e-Factura",
        series="A",
        number="0001-00000001",
        issue_date="2024-01-01T00:00:00",
        due_date="2024-01-31T00:00:00",
        subtotal=100.0,
        tax_total=22.0,
        discount_total=0.0,
        total=122.0,
        currency="UYU",
        exchange_rate=1.0,
    )
    invoice = await create_invoice(invoice_data, fake_db, fake_user)

    product_data = ProductCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Test Product",
        sku="SKU-001",
        product_type="good",
        unit_of_measure="unit",
        sales_price=100.0,
        cost_price=50.0,
        tax_rate=22.0,
    )
    product = await create_product(product_data, fake_db, fake_user)

    item_data = InvoiceItemCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        invoice_id=invoice.id,
        product_id=product.id,
        quantity=2.0,
        unit_price=50.0,
        discount=0.0,
        tax_amount=22.0,
        total=122.0,
        description="Test item",
    )
    item = await create_invoice_item(item_data, fake_db, fake_user)
    assert item is not None
    assert item.invoice_id == invoice.id

    items = await list_invoice_items(db=fake_db, current_user=fake_user)
    assert len(items) == 1

    found = await get_invoice_item(str(item.id), fake_db, fake_user)
    assert found.id == item.id

    update_data = InvoiceItemUpdate(quantity=3.0, total=183.0)
    updated = await update_invoice_item(str(item.id), update_data, fake_db, fake_user)
    assert updated.quantity == 3.0

    await delete_invoice_item(str(item.id), fake_db, fake_user)
    items = await list_invoice_items(db=fake_db, current_user=fake_user)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_payment_crud(fake_db, fake_user, fake_tenant, fake_company):
    customer_data = CustomerCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_type="company",
        legal_name="Test Customer",
        rut="12345678-9",
        currency="UYU",
        credit_limit=1000.0,
    )
    customer = await create_customer(customer_data, fake_db, fake_user)

    branch_data = BranchCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Main Branch",
        code="BR-001",
    )
    branch = await create_branch(branch_data, fake_db, fake_user)

    warehouse_data = WarehouseCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        branch_id=branch.id,
        name="Main Warehouse",
        code="WH-001",
    )
    warehouse = await create_warehouse(warehouse_data, fake_db, fake_user)

    invoice_data = InvoiceCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_id=customer.id,
        branch_id=branch.id,
        warehouse_id=warehouse.id,
        document_type="e-Factura",
        series="A",
        number="0001-00000001",
        issue_date="2024-01-01T00:00:00",
        due_date="2024-01-31T00:00:00",
        subtotal=100.0,
        tax_total=22.0,
        discount_total=0.0,
        total=122.0,
        currency="UYU",
        exchange_rate=1.0,
    )
    invoice = await create_invoice(invoice_data, fake_db, fake_user)

    payment_data = PaymentCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        invoice_id=invoice.id,
        customer_id=customer.id,
        payment_date="2024-01-15T00:00:00",
        amount=122.0,
        currency="UYU",
        payment_method="transfer",
        status="completed",
    )
    payment = await create_payment(payment_data, fake_db, fake_user)
    assert payment is not None
    assert payment.amount == 122.0

    payments = await list_payments(db=fake_db, current_user=fake_user)
    assert len(payments) == 1

    found = await get_payment(str(payment.id), fake_db, fake_user)
    assert found.id == payment.id

    update_data = PaymentUpdate(status="pending", reference="REF-001")
    updated = await update_payment(str(payment.id), update_data, fake_db, fake_user)
    assert updated.status == "pending"

    await delete_payment(str(payment.id), fake_db, fake_user)
    payments = await list_payments(db=fake_db, current_user=fake_user)
    assert len(payments) == 0


@pytest.mark.asyncio
async def test_stock_movement_crud(fake_db, fake_user, fake_tenant, fake_company):
    product_data = ProductCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Test Product",
        sku="SKU-001",
        product_type="good",
        unit_of_measure="unit",
        sales_price=100.0,
        cost_price=50.0,
        tax_rate=22.0,
    )
    product = await create_product(product_data, fake_db, fake_user)

    branch_data = BranchCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Main Branch",
        code="BR-001",
    )
    branch = await create_branch(branch_data, fake_db, fake_user)

    warehouse_data = WarehouseCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        branch_id=branch.id,
        name="Main Warehouse",
        code="WH-001",
    )
    warehouse = await create_warehouse(warehouse_data, fake_db, fake_user)

    movement_data = StockMovementCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        warehouse_id=warehouse.id,
        product_id=product.id,
        quantity=10.0,
        movement_type="inbound",
        movement_date="2024-01-01T00:00:00",
    )
    movement = await create_stock_movement(movement_data, fake_db, fake_user)
    assert movement is not None
    assert movement.quantity == 10.0

    movements = await list_stock_movements(db=fake_db, current_user=fake_user)
    assert len(movements) == 1

    found = await get_stock_movement(str(movement.id), fake_db, fake_user)
    assert found.id == movement.id

    update_data = StockMovementUpdate(quantity=20.0)
    updated = await update_stock_movement(str(movement.id), update_data, fake_db, fake_user)
    assert updated.quantity == 20.0

    await delete_stock_movement(str(movement.id), fake_db, fake_user)
    movements = await list_stock_movements(db=fake_db, current_user=fake_user)
    assert len(movements) == 0


@pytest.mark.asyncio
async def test_fiscal_document_crud(fake_db, fake_user, fake_tenant, fake_company):
    customer_data = CustomerCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_type="company",
        legal_name="Test Customer",
        rut="12345678-9",
        currency="UYU",
        credit_limit=1000.0,
    )
    customer = await create_customer(customer_data, fake_db, fake_user)

    branch_data = BranchCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Main Branch",
        code="BR-001",
    )
    branch = await create_branch(branch_data, fake_db, fake_user)

    warehouse_data = WarehouseCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        branch_id=branch.id,
        name="Main Warehouse",
        code="WH-001",
    )
    warehouse = await create_warehouse(warehouse_data, fake_db, fake_user)

    invoice_data = InvoiceCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        customer_id=customer.id,
        branch_id=branch.id,
        warehouse_id=warehouse.id,
        document_type="e-Factura",
        series="A",
        number="0001-00000001",
        issue_date="2024-01-01T00:00:00",
        due_date="2024-01-31T00:00:00",
        subtotal=100.0,
        tax_total=22.0,
        discount_total=0.0,
        total=122.0,
        currency="UYU",
        exchange_rate=1.0,
    )
    invoice = await create_invoice(invoice_data, fake_db, fake_user)

    fiscal_doc_data = FiscalDocumentCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        invoice_id=str(invoice.id),
        document_type="e-Factura",
        series="A",
        number="0001-00000001",
        state="draft",
    )
    fiscal_doc = await create_fiscal_document(fiscal_doc_data, fake_db, fake_user)
    assert fiscal_doc is not None
    assert fiscal_doc.state == "draft"

    docs = await list_fiscal_documents(db=fake_db, current_user=fake_user)
    assert len(docs) == 1

    found = await get_fiscal_document(str(fiscal_doc.id), fake_db, fake_user)
    assert found.id == fiscal_doc.id

    update_data = FiscalDocumentUpdate(state="issued")
    updated = await update_fiscal_document(str(fiscal_doc.id), update_data, fake_db, fake_user)
    assert updated.state == "issued"

    await delete_fiscal_document(str(fiscal_doc.id), fake_db, fake_user)
    docs = await list_fiscal_documents(db=fake_db, current_user=fake_user)
    assert len(docs) == 0


@pytest.mark.asyncio
async def test_audit_log_readonly(fake_db, fake_user, fake_tenant, fake_company):
    from app.models.audit_log import AuditLog

    log = AuditLog(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        user_id=fake_user.id,
        action="create",
        entity="product",
        entity_id=uuid.uuid4(),
        changes={"name": "Test"},
    )
    log.id = uuid.uuid4()
    fake_db._store.setdefault("audit_log", []).append(log)

    logs = await list_audit_logs(db=fake_db, current_user=fake_user)
    assert isinstance(logs, list)

    found = await get_audit_log(str(log.id), fake_db, fake_user)
    assert found.id == log.id


@pytest.mark.asyncio
async def test_certificate_crud(fake_db, fake_user, fake_tenant, fake_company):
    from app.api.v1.endpoints.certificates import create_certificate, list_certificates, get_certificate, update_certificate, delete_certificate
    from app.schemas.certificate import CertificateCreate, CertificateUpdate

    cert_data = CertificateCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Test Cert",
        thumbprint="ABCD1234",
        usage="signing",
    )
    cert = await create_certificate(cert_data, fake_db, fake_user)
    assert cert is not None
    assert cert.name == "Test Cert"

    certs = await list_certificates(db=fake_db, current_user=fake_user)
    assert len(certs) == 1

    found = await get_certificate(str(cert.id), fake_db, fake_user)
    assert found.id == cert.id

    update_data = CertificateUpdate(name="Updated Cert")
    updated = await update_certificate(str(cert.id), update_data, fake_db, fake_user)
    assert updated.name == "Updated Cert"

    await delete_certificate(str(cert.id), fake_db, fake_user)
    certs = await list_certificates(db=fake_db, current_user=fake_user)
    assert len(certs) == 0


@pytest.mark.asyncio
async def test_tax_configuration_crud(fake_db, fake_user, fake_tenant, fake_company):
    from app.api.v1.endpoints.tax_configurations import create_tax_configuration, list_tax_configurations, get_tax_configuration, update_tax_configuration, delete_tax_configuration
    from app.schemas.tax_configuration import TaxConfigurationCreate, TaxConfigurationUpdate

    tax_data = TaxConfigurationCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        tax_code="IVA",
        rate=22.0,
        description="Standard VAT",
    )
    tax = await create_tax_configuration(tax_data, fake_db, fake_user)
    assert tax is not None
    assert tax.tax_code == "IVA"

    taxes = await list_tax_configurations(db=fake_db, current_user=fake_user)
    assert len(taxes) == 1

    found = await get_tax_configuration(str(tax.id), fake_db, fake_user)
    assert found.id == tax.id

    update_data = TaxConfigurationUpdate(rate=23.0)
    updated = await update_tax_configuration(str(tax.id), update_data, fake_db, fake_user)
    assert updated.rate == 23.0

    await delete_tax_configuration(str(tax.id), fake_db, fake_user)
    taxes = await list_tax_configurations(db=fake_db, current_user=fake_user)
    assert len(taxes) == 0


@pytest.mark.asyncio
async def test_price_list_crud(fake_db, fake_user, fake_tenant, fake_company):
    from app.api.v1.endpoints.price_lists import create_price_list, list_price_lists, get_price_list, update_price_list, delete_price_list
    from app.schemas.price_list import PriceListCreate, PriceListUpdate

    price_list_data = PriceListCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        name="Standard Prices",
        currency="UYU",
    )
    price_list = await create_price_list(price_list_data, fake_db, fake_user)
    assert price_list is not None
    assert price_list.name == "Standard Prices"

    price_lists = await list_price_lists(db=fake_db, current_user=fake_user)
    assert len(price_lists) == 1

    found = await get_price_list(str(price_list.id), fake_db, fake_user)
    assert found.id == price_list.id

    update_data = PriceListUpdate(name="Updated Prices")
    updated = await update_price_list(str(price_list.id), update_data, fake_db, fake_user)
    assert updated.name == "Updated Prices"

    await delete_price_list(str(price_list.id), fake_db, fake_user)
    price_lists = await list_price_lists(db=fake_db, current_user=fake_user)
    assert len(price_lists) == 0


@pytest.mark.asyncio
async def test_fiscal_response_crud(fake_db, fake_user, fake_tenant, fake_company):
    from app.api.v1.endpoints.fiscal_responses import create_fiscal_response, list_fiscal_responses, get_fiscal_response, update_fiscal_response, delete_fiscal_response
    from app.schemas.fiscal_response import FiscalResponseCreate, FiscalResponseUpdate

    response_data = FiscalResponseCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        fiscal_document_id=uuid.uuid4(),
        status_code=200,
        status_message="OK",
    )
    response = await create_fiscal_response(response_data, fake_db, fake_user)
    assert response is not None
    assert response.status_code == 200

    responses = await list_fiscal_responses(db=fake_db, current_user=fake_user)
    assert len(responses) == 1

    found = await get_fiscal_response(str(response.id), fake_db, fake_user)
    assert found.id == response.id

    update_data = FiscalResponseUpdate(status_message="Updated")
    updated = await update_fiscal_response(str(response.id), update_data, fake_db, fake_user)
    assert updated.status_message == "Updated"

    await delete_fiscal_response(str(response.id), fake_db, fake_user)
    responses = await list_fiscal_responses(db=fake_db, current_user=fake_user)
    assert len(responses) == 0
