import uuid
import pytest
from datetime import datetime
from fastapi import HTTPException
from pydantic import ValidationError

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
from app.api.v1.endpoints.fiscal_documents import create_fiscal_document, list_fiscal_documents, get_fiscal_document
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
from app.core.permissions import PERMISSION_ALL


@pytest.mark.asyncio
async def test_get_product_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_product(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Product not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_product_not_found(fake_db, fake_user, fake_tenant):
    update_data = ProductUpdate(name="Updated")
    with pytest.raises(HTTPException) as exc_info:
        await update_product(str(uuid.uuid4()), update_data, fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Product not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_product_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await delete_product(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Product not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_product_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    product_data = ProductCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        name="Test Product",
        sku="SKU-002",
        product_type="good",
        unit_of_measure="unit",
        sales_price=100.0,
        cost_price=50.0,
        tax_rate=22.0,
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_product(product_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a product for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_products_empty(fake_db, fake_user, fake_tenant):
    products = await list_products(db=fake_db, current_user=fake_user)
    assert isinstance(products, list)
    assert len(products) == 0


@pytest.mark.asyncio
async def test_get_customer_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_customer(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Customer not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_customer_not_found(fake_db, fake_user, fake_tenant):
    update_data = CustomerUpdate(legal_name="Updated")
    with pytest.raises(HTTPException) as exc_info:
        await update_customer(str(uuid.uuid4()), update_data, fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Customer not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_customer_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await delete_customer(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Customer not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_customer_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    customer_data = CustomerCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        customer_type="company",
        legal_name="Test Customer",
        rut="12345678-9",
        currency="UYU",
        credit_limit=1000.0,
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_customer(customer_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a customer for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_invoice_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_invoice(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Invoice not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_invoice_not_found(fake_db, fake_user, fake_tenant):
    update_data = InvoiceUpdate(notes="Updated")
    with pytest.raises(HTTPException) as exc_info:
        await update_invoice(str(uuid.uuid4()), update_data, fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Invoice not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_invoice_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await delete_invoice(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Invoice not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_invoice_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    invoice_data = InvoiceCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        customer_id=str(uuid.uuid4()),
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
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_invoice(invoice_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create an invoice for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_fiscal_document_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_fiscal_document(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Fiscal document not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_fiscal_document_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    fiscal_data = FiscalDocumentCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        invoice_id=str(uuid.uuid4()),
        document_type="111",
        series="A",
        number="0001-00000001",
        state="draft",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_fiscal_document(fiscal_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a fiscal document for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_fiscal_documents_empty(fake_db, fake_user, fake_tenant):
    docs = await list_fiscal_documents(db=fake_db, current_user=fake_user)
    assert isinstance(docs, list)
    assert len(docs) == 0


@pytest.mark.asyncio
async def test_get_supplier_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_supplier(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Supplier not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_supplier_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    supplier_data = SupplierCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        legal_name="Test Supplier",
        rut="87654321-0",
        currency="UYU",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_supplier(supplier_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a supplier for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_suppliers_empty(fake_db, fake_user, fake_tenant):
    suppliers = await list_suppliers(db=fake_db, current_user=fake_user)
    assert isinstance(suppliers, list)
    assert len(suppliers) == 0


@pytest.mark.asyncio
async def test_get_branch_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_branch(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Branch not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_branch_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    branch_data = BranchCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        name="Test Branch",
        code="BR-002",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_branch(branch_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a branch for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_branches_empty(fake_db, fake_user, fake_tenant):
    branches = await list_branches(db=fake_db, current_user=fake_user)
    assert isinstance(branches, list)
    assert len(branches) == 0


@pytest.mark.asyncio
async def test_get_warehouse_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_warehouse(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Warehouse not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_warehouse_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    warehouse_data = WarehouseCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        branch_id=str(uuid.uuid4()),
        name="Test Warehouse",
        code="WH-002",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_warehouse(warehouse_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a warehouse for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_warehouses_empty(fake_db, fake_user, fake_tenant):
    warehouses = await list_warehouses(db=fake_db, current_user=fake_user)
    assert isinstance(warehouses, list)
    assert len(warehouses) == 0


@pytest.mark.asyncio
async def test_get_invoice_item_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_invoice_item(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Invoice item not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_invoice_item_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    item_data = InvoiceItemCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        invoice_id=str(uuid.uuid4()),
        product_id=str(uuid.uuid4()),
        quantity=1.0,
        unit_price=10.0,
        discount=0.0,
        tax_amount=2.2,
        total=12.2,
        description="Test item",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_invoice_item(item_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create an invoice item for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_invoice_items_empty(fake_db, fake_user, fake_tenant):
    items = await list_invoice_items(db=fake_db, current_user=fake_user)
    assert isinstance(items, list)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_get_payment_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_payment(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Payment not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_payment_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    payment_data = PaymentCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        invoice_id=str(uuid.uuid4()),
        customer_id=str(uuid.uuid4()),
        payment_date="2024-01-15T00:00:00",
        amount=100.0,
        currency="UYU",
        payment_method="transfer",
        status="completed",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_payment(payment_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a payment for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_payments_empty(fake_db, fake_user, fake_tenant):
    payments = await list_payments(db=fake_db, current_user=fake_user)
    assert isinstance(payments, list)
    assert len(payments) == 0


@pytest.mark.asyncio
async def test_get_stock_movement_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_stock_movement(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Stock movement not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_stock_movement_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    movement_data = StockMovementCreate(
        tenant_id=other_tenant_id,
        company_id=fake_company.id if hasattr(fake_db, 'fake_company') else uuid.uuid4(),
        warehouse_id=str(uuid.uuid4()),
        product_id=str(uuid.uuid4()),
        quantity=10.0,
        movement_type="inbound",
        movement_date="2024-01-01T00:00:00",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_stock_movement(movement_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a stock movement for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_stock_movements_empty(fake_db, fake_user, fake_tenant):
    movements = await list_stock_movements(db=fake_db, current_user=fake_user)
    assert isinstance(movements, list)
    assert len(movements) == 0


@pytest.mark.asyncio
async def test_get_role_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_role(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Role not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_role_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    role_data = RoleCreate(
        tenant_id=other_tenant_id,
        name="Admin",
        key="admin",
        description="Administrator role",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_role(role_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a role for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_roles_empty(fake_db, fake_user, fake_tenant):
    roles = await list_roles(db=fake_db, current_user=fake_user)
    assert isinstance(roles, list)
    assert len(roles) == 0


@pytest.mark.asyncio
async def test_get_permission_not_found(fake_db, fake_user, fake_tenant):
    with pytest.raises(HTTPException) as exc_info:
        await get_permission(str(uuid.uuid4()), fake_db, fake_user)
    assert exc_info.value.status_code == 404
    assert "Permission not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_permission_forbidden_for_different_tenant(fake_db, fake_user, fake_tenant):
    other_tenant_id = uuid.uuid4()
    permission_data = PermissionCreate(
        tenant_id=other_tenant_id,
        name="Read Users",
        code="users.read",
        description="Read user data",
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_permission(permission_data, fake_db, fake_user)
    assert exc_info.value.status_code == 403
    assert "Cannot create a permission for a different tenant" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_permissions_empty(fake_db, fake_user, fake_tenant):
    permissions = await list_permissions(db=fake_db, current_user=fake_user)
    assert isinstance(permissions, list)
    assert len(permissions) == 0
