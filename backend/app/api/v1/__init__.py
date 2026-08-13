from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, tenants, companies
from app.api.v1.endpoints import (
    products,
    customers,
    suppliers,
    branches,
    warehouses,
    price_lists,
    tax_configurations,
    certificates,
    roles,
    permissions,
    invoices,
    invoice_items,
    payments,
    stock_movements,
    purchase_receipts,
    fiscal_documents,
    fiscal_responses,
    audit_logs,
    woocommerce,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(branches.router, prefix="/branches", tags=["branches"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(price_lists.router, prefix="/price-lists", tags=["price-lists"])
api_router.include_router(tax_configurations.router, prefix="/tax-configurations", tags=["tax-configurations"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(invoice_items.router, prefix="/invoice-items", tags=["invoice-items"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(stock_movements.router, prefix="/stock-movements", tags=["stock-movements"])
api_router.include_router(
    purchase_receipts.router, prefix="/purchase-receipts", tags=["purchase-receipts"]
)
api_router.include_router(fiscal_documents.router, prefix="/fiscal-documents", tags=["fiscal-documents"])
api_router.include_router(fiscal_responses.router, prefix="/fiscal-responses", tags=["fiscal-responses"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(woocommerce.router, prefix="/integrations", tags=["integrations"])
