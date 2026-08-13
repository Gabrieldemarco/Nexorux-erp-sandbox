# DATABASE

## Objetivo

Diseñar el modelo de datos relacional profesional para Nexorux ERP, basado en multitenancy segura y preparado para integrar posteriormente el motor fiscal de facturación electrónica.

## Estrategia de multitenancy

- Se utiliza una sola base de datos con un esquema compartido.
- Cada entidad relevante contiene `tenant_id`.
- Las tablas que dependen de empresas también contienen `company_id`.
- El acceso a datos siempre debe filtrar por `tenant_id` y `company_id` donde corresponda.
- Se debe implementar Row Level Security (RLS) en una fase posterior.
- Las operaciones fiscales y de documento deben validar `tenant_id` y `company_id` en cada capa.

## Convenciones generales

- Claves primarias: `UUID`.
- Dinero: `NUMERIC(18, 6)`.
- Fechas: `TIMESTAMP WITH TIME ZONE`.
- Texto: `VARCHAR`, `TEXT` según longitud.
- Configuración dinámica: `JSONB` para settings y parámetros.
- Campos comunes:
  - `id`
  - `tenant_id`
  - `company_id`
  - `created_at`
  - `updated_at`
  - `status`
  - `is_active`

## Entidades principales

### Tenant

- `id`
- `name`
- `status`
- `settings`
- `created_at`
- `updated_at`

### Company

- `id`
- `tenant_id`
- `legal_name`
- `trade_name`
- `rut`
- `fiscal_address`
- `phone`
- `email`
- `website`
- `country`
- `department`
- `locality`
- `currency`
- `tax_regime`
- `created_at`
- `updated_at`

### Branch

- `id`
- `tenant_id`
- `company_id`
- `name`
- `code`
- `address`
- `phone`
- `email`
- `is_active`

### Warehouse

- `id`
- `tenant_id`
- `company_id`
- `branch_id`
- `name`
- `code`
- `description`
- `is_active`

### User

- `id`
- `tenant_id`
- `company_id`
- `email`
- `full_name`
- `username`
- `password_hash`
- `is_active`
- `last_login_at`
- `role`
- `settings`

### Role

- `id`
- `tenant_id`
- `name`
- `key`
- `description`
- `is_default`

### Permission

- `id`
- `tenant_id`
- `name`
- `code`
- `description`

### Customer

- `id`
- `tenant_id`
- `company_id`
- `customer_type`
- `legal_name`
- `trade_name`
- `rut`
- `document_type`
- `address`
- `email`
- `phone`
- `currency`
- `credit_limit`
- `payment_terms`
- `is_active`

### Supplier

- `id`
- `tenant_id`
- `company_id`
- `legal_name`
- `trade_name`
- `rut`
- `document_type`
- `address`
- `email`
- `phone`
- `currency`
- `payment_terms`
- `is_active`

### Product

- `id`
- `tenant_id`
- `company_id`
- `name`
- `sku`
- `barcode`
- `description`
- `product_type`
- `unit_of_measure`
- `sales_price`
- `cost_price`
- `tax_rate`
- `is_service`
- `is_active`

### StockMovement

- `id`
- `tenant_id`
- `company_id`
- `warehouse_id`
- `product_id`
- `quantity`
- `movement_type`
- `reference_id`
- `reference_type`
- `movement_date`
- `created_at`

### PriceList

- `id`
- `tenant_id`
- `company_id`
- `name`
- `currency`
- `valid_from`
- `valid_to`
- `is_default`

### Invoice

- `id`
- `tenant_id`
- `company_id`
- `customer_id`
- `branch_id`
- `warehouse_id`
- `document_type`
- `series`
- `number`
- `status`
- `issue_date`
- `due_date`
- `subtotal`
- `tax_total`
- `discount_total`
- `total`
- `currency`
- `exchange_rate`
- `notes`

### InvoiceItem

- `id`
- `invoice_id`
- `product_id`
- `quantity`
- `unit_price`
- `discount`
- `tax_amount`
- `total`
- `description`

### Payment

- `id`
- `tenant_id`
- `company_id`
- `invoice_id`
- `customer_id`
- `payment_date`
- `amount`
- `currency`
- `payment_method`
- `reference`
- `status`

### FiscalDocument

- `id`
- `tenant_id`
- `company_id`
- `invoice_id`
- `document_type`
- `series`
- `number`
- `state`
- `issued_at`
- `xml_reference`
- `signed_at`
- `sent_at`
- `response_at`
- `is_contingency`
- `raw_payload`

### FiscalResponse

- `id`
- `tenant_id`
- `company_id`
- `fiscal_document_id`
- `request_id`
- `correlation_id`
- `status_code`
- `status_message`
- `raw_response`
- `received_at`
- `retry_count`

### Certificate

- `id`
- `tenant_id`
- `company_id`
- `name`
- `thumbprint`
- `issued_at`
- `expires_at`
- `metadata`
- `usage`
- `is_active`

### TaxConfiguration

- `id`
- `tenant_id`
- `company_id`
- `tax_code`
- `description`
- `rate`
- `effective_from`
- `effective_to`
- `metadata`

### AuditLog

- `id`
- `tenant_id`
- `company_id`
- `user_id`
- `action`
- `entity`
- `entity_id`
- `changes`
- `timestamp`
- `ip_address`
- `request_id`

## Reglas de integridad

- `tenant_id` y `company_id` en todas las tablas de negocio.
- `uniq` por serie+numero+empresa en documentos fiscales.
- `check` para cantidades no negativas.
- `foreign keys` para integridad referencial.
- `indexes` en `tenant_id`, `company_id`, `invoice_id`, `customer_id`, `product_id`, `status`.
- `NOT NULL` para campos críticos.

## Ejemplo conceptual SQL

```sql
CREATE TABLE tenant (
  id uuid PRIMARY KEY,
  name varchar(255) NOT NULL,
  status varchar(50) NOT NULL DEFAULT 'active',
  settings jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE company (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  legal_name varchar(255) NOT NULL,
  trade_name varchar(255),
  rut varchar(20) NOT NULL,
  fiscal_address varchar(500),
  country varchar(100) NOT NULL DEFAULT 'Uruguay',
  currency varchar(10) NOT NULL DEFAULT 'UYU',
  tax_regime varchar(50),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE (tenant_id, rut)
);

CREATE TABLE fiscal_document (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  company_id uuid NOT NULL REFERENCES company(id) ON DELETE CASCADE,
  invoice_id uuid NOT NULL REFERENCES invoice(id) ON DELETE CASCADE,
  document_type varchar(50) NOT NULL,
  series varchar(20) NOT NULL,
  number varchar(50) NOT NULL,
  state varchar(50) NOT NULL,
  issued_at timestamptz,
  signed_at timestamptz,
  sent_at timestamptz,
  raw_payload jsonb,
  UNIQUE (tenant_id, company_id, series, number)
);
```

## Observaciones

- El modelo inicial describe las entidades mínimas necesarias para el MVP y para la integración futura con CFE.
- Las tablas fiscales se diseñan con un enfoque genérico; los detalles de campos del CFE deben confirmarse con documentación oficial antes de fijarlos.
- El modelo está pensado para ser ampliado por fases, sin sacrificar el aislamiento entre tenants.

## Siguientes pasos

1. Revisar el modelo con el equipo fiscal y validar con documentación DGI.
2. Implementar migraciones Alembic basadas en este diseño.
3. Añadir RLS en PostgreSQL cuando el esquema se estabilice.
4. Definir los detalles del CFE y los documentos fiscales con base en DGI oficial.
