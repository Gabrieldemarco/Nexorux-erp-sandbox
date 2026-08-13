# Row Level Security (RLS)

Nexorux isolates tenant data with PostgreSQL RLS on core business tables.

## What is enabled

- Migration `e4f7a9c1b2d3`:
  ENABLE RLS + tenant policy on product, customer, supplier, branch, warehouse,
  invoice, invoice_item, payment, stock_movement, fiscal_document, fiscal_response,
  certificate, tax_configuration, price_list, audit_log
- Migration `f8a2b4c6d0e1`: FORCE RLS on the same tables
- Migration `a1b2c3d4e5f6`: purchase_receipt + purchase_receipt_item with ENABLE+FORCE RLS

## App responsibility

When `RLS_TENANT_CONTEXT_ENABLED=true`, `get_db` sets the session GUC
`app.current_tenant_id` from the JWT (`tenant_id` claim, or user lookup), and
clears it when the request ends.

Access tokens issued by `/auth/token` and `/auth/refresh` include `tenant_id`.
**Cerrá sesión y volvé a entrar** después de actualizar el backend para recibir
un token nuevo.

Without that GUC, FORCE RLS returns no rows (or blocks writes) for those tables.
Keep the flag **true** in local `.env` so demo/API requests remain tenant-scoped.

Migration `b2c3d4e5f6a7` hardens policies: empty `app.current_tenant_id` no longer
casts `''::uuid` (which caused HTTP 500). Missing GUC now simply denies access.

## Config

```env
# Required when FORCE RLS is applied — app must set app.current_tenant_id
RLS_TENANT_CONTEXT_ENABLED=true
```

See `backend/.env.example` and `backend/app/db/session.py`.
