import asyncio
from datetime import datetime
from app.core.config import settings
from app.core.permissions import (
    PERMISSION_AUDIT_LOGS_READ,
    PERMISSION_BRANCHES_CREATE,
    PERMISSION_BRANCHES_DELETE,
    PERMISSION_BRANCHES_READ,
    PERMISSION_BRANCHES_UPDATE,
    PERMISSION_CERTIFICATES_CREATE,
    PERMISSION_CERTIFICATES_DELETE,
    PERMISSION_CERTIFICATES_READ,
    PERMISSION_CERTIFICATES_UPDATE,
    PERMISSION_COMPANIES_CREATE,
    PERMISSION_COMPANIES_DELETE,
    PERMISSION_COMPANIES_READ,
    PERMISSION_COMPANIES_UPDATE,
    PERMISSION_CUSTOMERS_CREATE,
    PERMISSION_CUSTOMERS_DELETE,
    PERMISSION_CUSTOMERS_READ,
    PERMISSION_CUSTOMERS_UPDATE,
    PERMISSION_FISCAL_DOCUMENTS_CREATE,
    PERMISSION_FISCAL_DOCUMENTS_DELETE,
    PERMISSION_FISCAL_RESPONSES_READ,
    PERMISSION_FISCAL_RESPONSES_CREATE,
    PERMISSION_FISCAL_RESPONSES_UPDATE,
    PERMISSION_FISCAL_RESPONSES_DELETE,
    PERMISSION_FISCAL_DOCUMENTS_ISSUE,
    PERMISSION_FISCAL_DOCUMENTS_QUERY,
    PERMISSION_FISCAL_DOCUMENTS_READ,
    PERMISSION_FISCAL_DOCUMENTS_RETRY,
    PERMISSION_FISCAL_DOCUMENTS_SEND,
    PERMISSION_FISCAL_DOCUMENTS_UPDATE,
    PERMISSION_INVOICE_ITEMS_CREATE,
    PERMISSION_INVOICE_ITEMS_DELETE,
    PERMISSION_INVOICE_ITEMS_READ,
    PERMISSION_INVOICE_ITEMS_UPDATE,
    PERMISSION_INVOICES_CREATE,
    PERMISSION_INVOICES_DELETE,
    PERMISSION_INVOICES_READ,
    PERMISSION_INVOICES_UPDATE,
    PERMISSION_PAYMENTS_CREATE,
    PERMISSION_PAYMENTS_DELETE,
    PERMISSION_PAYMENTS_READ,
    PERMISSION_PAYMENTS_UPDATE,
    PERMISSION_PERMISSIONS_CREATE,
    PERMISSION_PERMISSIONS_DELETE,
    PERMISSION_PERMISSIONS_READ,
    PERMISSION_PERMISSIONS_UPDATE,
    PERMISSION_PRICE_LISTS_CREATE,
    PERMISSION_PRICE_LISTS_DELETE,
    PERMISSION_PRICE_LISTS_READ,
    PERMISSION_PRICE_LISTS_UPDATE,
    PERMISSION_PRODUCTS_CREATE,
    PERMISSION_PRODUCTS_DELETE,
    PERMISSION_PRODUCTS_READ,
    PERMISSION_PRODUCTS_UPDATE,
    PERMISSION_ROLES_CREATE,
    PERMISSION_ROLES_DELETE,
    PERMISSION_ROLES_READ,
    PERMISSION_ROLES_UPDATE,
    PERMISSION_STOCK_MOVEMENTS_CREATE,
    PERMISSION_STOCK_MOVEMENTS_DELETE,
    PERMISSION_STOCK_MOVEMENTS_READ,
    PERMISSION_STOCK_MOVEMENTS_UPDATE,
    PERMISSION_SUPPLIERS_CREATE,
    PERMISSION_SUPPLIERS_DELETE,
    PERMISSION_SUPPLIERS_READ,
    PERMISSION_SUPPLIERS_UPDATE,
    PERMISSION_TAX_CONFIGURATIONS_CREATE,
    PERMISSION_TAX_CONFIGURATIONS_DELETE,
    PERMISSION_TAX_CONFIGURATIONS_READ,
    PERMISSION_TAX_CONFIGURATIONS_UPDATE,
    PERMISSION_TENANTS_CREATE,
    PERMISSION_TENANTS_DELETE,
    PERMISSION_TENANTS_READ,
    PERMISSION_TENANTS_UPDATE,
    PERMISSION_WAREHOUSES_CREATE,
    PERMISSION_WAREHOUSES_DELETE,
    PERMISSION_WAREHOUSES_READ,
    PERMISSION_WAREHOUSES_UPDATE,
    PERMISSION_ALL,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.branch import Branch
from app.models.warehouse import Warehouse
from app.models.price_list import PriceList
from app.models.tax_configuration import TaxConfiguration
from app.models.certificate import Certificate
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.payment import Payment
from app.models.stock_movement import StockMovement
from app.models.fiscal_document import FiscalDocument
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash


DEMO_TENANT_NAME = "Demo Tenant"
DEMO_COMPANY_RUT = "12345678901"
DEMO_ADMIN_EMAIL = "admin@demo.com"

DEMO_PERMISSIONS = [
    PERMISSION_PRODUCTS_READ,
    PERMISSION_PRODUCTS_CREATE,
    PERMISSION_PRODUCTS_UPDATE,
    PERMISSION_PRODUCTS_DELETE,
    PERMISSION_CUSTOMERS_READ,
    PERMISSION_CUSTOMERS_CREATE,
    PERMISSION_CUSTOMERS_UPDATE,
    PERMISSION_CUSTOMERS_DELETE,
    PERMISSION_SUPPLIERS_READ,
    PERMISSION_SUPPLIERS_CREATE,
    PERMISSION_SUPPLIERS_UPDATE,
    PERMISSION_SUPPLIERS_DELETE,
    PERMISSION_BRANCHES_READ,
    PERMISSION_BRANCHES_CREATE,
    PERMISSION_BRANCHES_UPDATE,
    PERMISSION_BRANCHES_DELETE,
    PERMISSION_WAREHOUSES_READ,
    PERMISSION_WAREHOUSES_CREATE,
    PERMISSION_WAREHOUSES_UPDATE,
    PERMISSION_WAREHOUSES_DELETE,
    PERMISSION_INVOICES_READ,
    PERMISSION_INVOICES_CREATE,
    PERMISSION_INVOICES_UPDATE,
    PERMISSION_INVOICES_DELETE,
    PERMISSION_INVOICE_ITEMS_READ,
    PERMISSION_INVOICE_ITEMS_CREATE,
    PERMISSION_INVOICE_ITEMS_UPDATE,
    PERMISSION_INVOICE_ITEMS_DELETE,
    PERMISSION_PAYMENTS_READ,
    PERMISSION_PAYMENTS_CREATE,
    PERMISSION_PAYMENTS_UPDATE,
    PERMISSION_PAYMENTS_DELETE,
    PERMISSION_STOCK_MOVEMENTS_READ,
    PERMISSION_STOCK_MOVEMENTS_CREATE,
    PERMISSION_STOCK_MOVEMENTS_UPDATE,
    PERMISSION_STOCK_MOVEMENTS_DELETE,
    PERMISSION_FISCAL_DOCUMENTS_READ,
    PERMISSION_FISCAL_DOCUMENTS_CREATE,
    PERMISSION_FISCAL_DOCUMENTS_UPDATE,
    PERMISSION_FISCAL_DOCUMENTS_ISSUE,
    PERMISSION_FISCAL_DOCUMENTS_SEND,
    PERMISSION_FISCAL_DOCUMENTS_QUERY,
    PERMISSION_FISCAL_DOCUMENTS_RETRY,
    PERMISSION_FISCAL_DOCUMENTS_DELETE,
    PERMISSION_FISCAL_RESPONSES_READ,
    PERMISSION_FISCAL_RESPONSES_CREATE,
    PERMISSION_FISCAL_RESPONSES_UPDATE,
    PERMISSION_FISCAL_RESPONSES_DELETE,
    PERMISSION_ROLES_READ,
    PERMISSION_ROLES_CREATE,
    PERMISSION_ROLES_UPDATE,
    PERMISSION_ROLES_DELETE,
    PERMISSION_PERMISSIONS_READ,
    PERMISSION_PERMISSIONS_CREATE,
    PERMISSION_PERMISSIONS_UPDATE,
    PERMISSION_PERMISSIONS_DELETE,
    PERMISSION_CERTIFICATES_READ,
    PERMISSION_CERTIFICATES_CREATE,
    PERMISSION_CERTIFICATES_UPDATE,
    PERMISSION_CERTIFICATES_DELETE,
    PERMISSION_TAX_CONFIGURATIONS_READ,
    PERMISSION_TAX_CONFIGURATIONS_CREATE,
    PERMISSION_TAX_CONFIGURATIONS_UPDATE,
    PERMISSION_TAX_CONFIGURATIONS_DELETE,
    PERMISSION_PRICE_LISTS_READ,
    PERMISSION_PRICE_LISTS_CREATE,
    PERMISSION_PRICE_LISTS_UPDATE,
    PERMISSION_PRICE_LISTS_DELETE,
    PERMISSION_COMPANIES_READ,
    PERMISSION_COMPANIES_CREATE,
    PERMISSION_COMPANIES_UPDATE,
    PERMISSION_COMPANIES_DELETE,
    PERMISSION_TENANTS_READ,
    PERMISSION_TENANTS_CREATE,
    PERMISSION_TENANTS_UPDATE,
    PERMISSION_TENANTS_DELETE,
    PERMISSION_AUDIT_LOGS_READ,
    PERMISSION_ALL,
]


async def get_or_create(session, model, defaults=None, **kwargs):
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        return obj, False
    data = {**kwargs, **(defaults or {})}
    obj = model(**data)
    session.add(obj)
    await session.flush()
    return obj, True


async def ensure_permissions(session, tenant_id) -> dict[str, Permission]:
    permissions_by_code: dict[str, Permission] = {}
    for code in DEMO_PERMISSIONS:
        perm, _ = await get_or_create(
            session,
            Permission,
            tenant_id=tenant_id,
            code=code,
            defaults={"name": code, "description": f"Permission {code}"},
        )
        permissions_by_code[code] = perm
    return permissions_by_code


async def ensure_role_permissions(session, role_id, permissions_by_code: dict[str, Permission]):
    for code, perm in permissions_by_code.items():
        await session.execute(
            text("INSERT INTO role_permission (role_id, permission_id) VALUES (:role_id, :permission_id) ON CONFLICT DO NOTHING"),
            {"role_id": role_id, "permission_id": perm.id},
        )


async def ensure_user_role(session, user_id, role_id):
    await session.execute(
        text("INSERT INTO user_role (user_id, role_id) VALUES (:user_id, :role_id) ON CONFLICT DO NOTHING"),
        {"user_id": user_id, "role_id": role_id},
    )


async def main():
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async with AsyncSession(engine) as session:
        tenant, _ = await get_or_create(
            session,
            Tenant,
            name=DEMO_TENANT_NAME,
            defaults={"status": "active", "settings": {}},
        )

        company, _ = await get_or_create(
            session,
            Company,
            rut=DEMO_COMPANY_RUT,
            defaults={
                "tenant_id": tenant.id,
                "legal_name": "Demo Company SA",
                "trade_name": "Demo Co",
                "fiscal_address": "Calle Falsa 123",
                "phone": "099123456",
                "email": "info@democo.com",
                "website": "https://demo.co",
                "country": "UY",
                "department": "Montevideo",
                "locality": "Montevideo",
                "currency": "UYU",
                "tax_regime": "General",
            },
        )

        admin_user, _ = await get_or_create(
            session,
            User,
            email=DEMO_ADMIN_EMAIL,
            defaults={
                "username": "admin",
                "full_name": "Admin Demo",
                "tenant_id": tenant.id,
                "company_id": company.id,
                "password_hash": get_password_hash("demo1234"),
                "is_active": True,
                "settings": {},
            },
        )

        role, _ = await get_or_create(
            session,
            Role,
            tenant_id=tenant.id,
            key="admin",
            defaults={"name": "Administrator", "description": "Admin role", "is_default": True},
        )

        permissions_by_code = await ensure_permissions(session, tenant.id)
        await ensure_role_permissions(session, role.id, permissions_by_code)
        await ensure_user_role(session, admin_user.id, role.id)

        customer, _ = await get_or_create(
            session,
            Customer,
            tenant_id=tenant.id,
            company_id=company.id,
            rut="12345678",
            defaults={
                "customer_type": "company",
                "legal_name": "Cliente Empresa Demo",
                "trade_name": "Cliente Demo",
                "currency": "UYU",
                "credit_limit": 1000.0,
                "is_active": True,
                "metadata": {},
            },
        )

        final_customer, _ = await get_or_create(
            session,
            Customer,
            tenant_id=tenant.id,
            company_id=company.id,
            rut="00000000",
            defaults={
                "customer_type": "final_consumer",
                "legal_name": "Consumidor Final",
                "trade_name": "Consumidor Final",
                "currency": "UYU",
                "credit_limit": 0.0,
                "is_active": True,
                "metadata": {},
            },
        )

        supplier, _ = await get_or_create(
            session,
            Supplier,
            tenant_id=tenant.id,
            company_id=company.id,
            rut="87654321",
            defaults={
                "legal_name": "Proveedor Demo",
                "trade_name": "Proveedor Demo",
                "currency": "UYU",
                "is_active": True,
                "metadata": {},
            },
        )

        product, _ = await get_or_create(
            session,
            Product,
            tenant_id=tenant.id,
            company_id=company.id,
            sku="DEMO-001",
            defaults={
                "name": "Producto Demo",
                "barcode": "7730000000001",
                "description": "Producto de prueba",
                "product_type": "good",
                "unit_of_measure": "unit",
                "sales_price": 100.0,
                "cost_price": 50.0,
                "tax_rate": 22.0,
                "is_service": False,
                "is_active": True,
                "metadata": {},
            },
        )

        branch, _ = await get_or_create(
            session,
            Branch,
            tenant_id=tenant.id,
            company_id=company.id,
            code="BR-DEMO",
            defaults={"name": "Sucursal Demo", "is_active": True},
        )

        warehouse, _ = await get_or_create(
            session,
            Warehouse,
            tenant_id=tenant.id,
            company_id=company.id,
            branch_id=branch.id,
            code="WH-DEMO",
            defaults={"name": "Depósito Demo", "description": "Depósito central", "is_active": True},
        )

        price_list, _ = await get_or_create(
            session,
            PriceList,
            tenant_id=tenant.id,
            company_id=company.id,
            name="Lista Demo",
            defaults={
                "currency": "UYU",
                "valid_from": datetime(2024, 1, 1),
                "valid_to": datetime(2025, 12, 31),
                "is_default": True,
            },
        )

        tax_config, _ = await get_or_create(
            session,
            TaxConfiguration,
            tenant_id=tenant.id,
            company_id=company.id,
            tax_code="IVA",
            defaults={
                "description": "Impuesto al Valor Agregado",
                "rate": 22.0,
                "effective_from": datetime(2024, 1, 1),
                "metadata": {},
            },
        )

        certificate, _ = await get_or_create(
            session,
            Certificate,
            tenant_id=tenant.id,
            company_id=company.id,
            name="Certificado Demo",
            defaults={
                "thumbprint": "DEMO_THUMBPRINT",
                "usage": "firma",
                "is_active": True,
                "metadata": {"cert_path": "", "key_path": ""},
            },
        )

        invoice, _ = await get_or_create(
            session,
            Invoice,
            tenant_id=tenant.id,
            company_id=company.id,
            customer_id=customer.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            series="A",
            number="00000001",
            defaults={
                "document_type": "111",
                "status": "draft",
                "issue_date": datetime(2024, 1, 1),
                "due_date": datetime(2024, 1, 31),
                "subtotal": 100.0,
                "tax_total": 22.0,
                "discount_total": 0.0,
                "total": 122.0,
                "currency": "UYU",
                "exchange_rate": 1.0,
                "notes": "Factura demo empresa",
                "metadata": {},
            },
        )

        ticket_invoice, _ = await get_or_create(
            session,
            Invoice,
            tenant_id=tenant.id,
            company_id=company.id,
            customer_id=final_customer.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            series="A",
            number="00000002",
            defaults={
                "document_type": "101",
                "status": "draft",
                "issue_date": datetime(2024, 1, 2),
                "due_date": datetime(2024, 1, 2),
                "subtotal": 100.0,
                "tax_total": 22.0,
                "discount_total": 0.0,
                "total": 122.0,
                "currency": "UYU",
                "exchange_rate": 1.0,
                "notes": "e-Ticket consumidor final",
                "metadata": {},
            },
        )

        invoice_item, _ = await get_or_create(
            session,
            InvoiceItem,
            tenant_id=tenant.id,
            company_id=company.id,
            invoice_id=invoice.id,
            product_id=product.id,
            defaults={
                "quantity": 1.0,
                "unit_price": 100.0,
                "discount": 0.0,
                "tax_amount": 22.0,
                "total": 122.0,
                "description": "Item demo",
            },
        )

        ticket_item, _ = await get_or_create(
            session,
            InvoiceItem,
            tenant_id=tenant.id,
            company_id=company.id,
            invoice_id=ticket_invoice.id,
            product_id=product.id,
            defaults={
                "quantity": 1.0,
                "unit_price": 100.0,
                "discount": 0.0,
                "tax_amount": 22.0,
                "total": 122.0,
                "description": "Producto Demo",
            },
        )

        payment, _ = await get_or_create(
            session,
            Payment,
            tenant_id=tenant.id,
            company_id=company.id,
            invoice_id=invoice.id,
            customer_id=customer.id,
            amount=122.0,
            defaults={
                "payment_date": datetime(2024, 1, 15),
                "currency": "UYU",
                "payment_method": "transfer",
                "status": "completed",
            },
        )

        stock_movement, _ = await get_or_create(
            session,
            StockMovement,
            tenant_id=tenant.id,
            company_id=company.id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            quantity=10.0,
            movement_type="in",
            defaults={
                "movement_date": datetime(2024, 1, 1),
            },
        )

        fiscal_document, _ = await get_or_create(
            session,
            FiscalDocument,
            tenant_id=tenant.id,
            company_id=company.id,
            invoice_id=invoice.id,
            document_type="111",
            series="A",
            number="00000001",
            defaults={
                "state": "draft",
            },
        )

        audit_log, _ = await get_or_create(
            session,
            AuditLog,
            tenant_id=tenant.id,
            company_id=company.id,
            user_id=admin_user.id,
            action="seed",
            entity="seed",
            entity_id=tenant.id,
            defaults={
                "changes": {"seed": "demo"},
            },
        )

        tenant_id = str(tenant.id)
        company_id = str(company.id)
        user_id = str(admin_user.id)
        role_id = str(role.id)
        permission_count = len(permissions_by_code)
        customer_id = str(customer.id)
        final_customer_id = str(final_customer.id)
        supplier_id = str(supplier.id)
        product_id = str(product.id)
        branch_id = str(branch.id)
        warehouse_id = str(warehouse.id)
        price_list_id = str(price_list.id)
        tax_config_id = str(tax_config.id)
        certificate_id = str(certificate.id)
        invoice_id = str(invoice.id)
        ticket_invoice_id = str(ticket_invoice.id)
        invoice_item_id = str(invoice_item.id)
        ticket_item_id = str(ticket_item.id)
        payment_id = str(payment.id)
        stock_movement_id = str(stock_movement.id)
        fiscal_document_id = str(fiscal_document.id)
        audit_log_id = str(audit_log.id)

        await session.commit()
        print("Seed data idempotent completed.")
        print("tenant_id", tenant_id)
        print("company_id", company_id)
        print("user_id", user_id)
        print("role_id", role_id)
        print("permission_count", permission_count)
        print("customer_id", customer_id)
        print("final_customer_id", final_customer_id)
        print("supplier_id", supplier_id)
        print("product_id", product_id)
        print("branch_id", branch_id)
        print("warehouse_id", warehouse_id)
        print("price_list_id", price_list_id)
        print("tax_config_id", tax_config_id)
        print("certificate_id", certificate_id)
        print("invoice_id", invoice_id)
        print("ticket_invoice_id", ticket_invoice_id)
        print("invoice_item_id", invoice_item_id)
        print("ticket_item_id", ticket_item_id)
        print("payment_id", payment_id)
        print("stock_movement_id", stock_movement_id)
        print("fiscal_document_id", fiscal_document_id)
        print("audit_log_id", audit_log_id)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
