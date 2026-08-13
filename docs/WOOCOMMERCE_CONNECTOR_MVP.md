# Nexorux × WooCommerce — MVP del conector

> Endpoints implementados:
> - `POST /api/v1/integrations/woocommerce/webhook/order` — pedido → factura draft; `refunded` → NC
> - `POST /api/v1/integrations/woocommerce/webhook/refund` — refund Woo → nota de crédito (102/112)
> - `POST /api/v1/integrations/woocommerce/sync/products` — upsert catálogo por SKU (`dry_run` opcional)
> - `POST /api/v1/integrations/woocommerce/sync/stock` — stock Nexorux → Woo (REST API opcional)
> - `GET /api/v1/integrations/woocommerce/orders` — listar facturas con `metadata.woocommerce_order_id`
>
> UI: `/woocommerce` (pedidos + sync catálogo + sync stock).

> Objetivo: que un pedido pagado en WooCommerce genere factura/stock en Nexorux
> (e-Ticket / e-Factura Uruguay), sin carga manual.
>
> Audiencia: dueño de producto / desarrollo Nexorux ERP.

---

## 1. Propuesta de valor

**Para el cliente final (pyme Uruguay):**

> Tu tienda WooCommerce vende → Nexorux factura a DGI y descuenta stock solo.

**Para Nexorux (producto):**

- Diferencial comercial frente a ERPs sin e-commerce
- Módulo vendible / upsell: “Conector WooCommerce”
- Encaje natural con el mercado local (WordPress + Woo es masivo)

---

## 2. Alcance del MVP (qué entra / qué no)

### Entra (MVP)

| Flujo | Descripción |
|-------|-------------|
| Pedido → Factura | Orden `processing`/`completed` en Woo → `invoice` + `invoice_items` en Nexorux |
| Cliente | Crear/actualizar `customer` (RUT si es empresa; consumidor final si no) |
| Tipo CFE | `101` e-Ticket (final) / `111` e-Factura (empresa con RUT) |
| Stock | Movimiento de egreso al confirmar (si hay depósito configurado) |
| Idempotencia | No duplicar factura si Woo reenvía el mismo pedido |
| Mapeo SKU | Líneas Woo se matchean por `sku` con productos Nexorux |

### No entra (fase 2+)

- Sync completo de catálogo/PIM Woo ↔ Nexorux (hoy: sync productos + stock parcial)
- Precios B2B / listas complejas bidireccionales
- ~~Notas de crédito automáticas desde refunds Woo~~ ✅
- ~~Sync stock Nexorux → Woo~~ ✅ (`POST .../sync/stock`)
- Multi-warehouse inteligente / reservas de stock en checkout
- Emisión DGI automática en el mismo instante (puede quedar draft + botón/cola)
- Plugin WordPress publicado en el directorio oficial (puede ser worker externo primero)

---

## 3. Arquitectura recomendada

```
WooCommerce
  │  webhook: order.updated / order.completed
  ▼
Conector (worker / plugin / servicio HTTP)
  │  JWT → Nexorux API
  ▼
Nexorux ERP
  - customers
  - products (lookup por SKU)
  - invoices + invoice_items
  - stock_movements
  - fiscal_documents (opcional en MVP+)
```

### Opciones de implementación

| Opción | Pros | Contras |
|--------|------|---------|
| **A. Worker en Nexorux** (Celery/FastAPI recibe webhooks) | Control total, mismo repo | Hay que exponer URL pública HTTPS |
| **B. Plugin WordPress** que llama a Nexorux | Cerca del evento Woo | Mantener PHP + auth |
| **C. n8n/Make** (no-code puente) | Rápido para demos | Menos control / menos “producto” |

**Recomendación producto:** A o B empaquetado como “Conector WooCommerce”.  
Para demo rápida: C.

---

## 4. Eventos WooCommerce a escuchar

| Evento | Acción Nexorux |
|--------|----------------|
| `order.created` / `order.updated` con status `processing` o `completed` | Crear/actualizar factura |
| `order.updated` → `refunded` | Nota de crédito (102/112) + restock |
| Refund webhook | `POST .../webhook/refund` → NC idempotente |

**Regla MVP:** solo procesar cuando el pedido pasa a **pagado/en proceso** (`processing` o `completed`), no en `pending`.

---

## 5. Mapeo de datos

### 5.1 Cliente

| WooCommerce | Nexorux | Notas |
|--------------|---------|-------|
| `billing.email` | buscar/crear customer | Clave de match secundaria |
| `billing.rut` / meta RUT (plugin CI/RUT) | `customer.rut` | Si hay RUT válido → empresa |
| `billing.company` / `billing.last_name` | `legal_name` | |
| Sin RUT | `customer_type = final_consumer` | e-Ticket 101 |

### 5.2 Producto / línea

| WooCommerce | Nexorux | Notas |
|--------------|---------|-------|
| `line_items[].sku` | `product.sku` | **Match obligatorio en MVP** |
| `quantity` | `invoice_item.quantity` | |
| `price` | `unit_price` | Definir si es neto o con IVA |
| nombre línea | `description` | Fallback si no hay producto |

Si el SKU no existe en Nexorux: **rechazar el sync** y dejar log/alerta (no inventar producto en MVP).

### 5.3 Cabecera factura

| Campo Nexorux | Origen |
|---------------|--------|
| `document_type` | `111` si cliente empresa con RUT; si no `101` |
| `series` / `number` | Config del conector / correlativo Nexorux |
| `status` | `draft` (MVP) o `issued` |
| `currency` | `UYU` (MVP) |
| `metadata.woocommerce_order_id` | `order.id` |
| `metadata.woocommerce_order_key` | `order.order_key` |
| `branch_id` / `warehouse_id` | Config fija por tienda |

---

## 6. Endpoints Nexorux a usar (existentes)

Base: `/api/v1`

1. `POST /auth/token` — JWT del usuario de integración
2. `GET /products/` — resolver SKU → `product_id`
3. `GET /customers/` + `POST /customers/` — upsert cliente
4. `POST /invoices/` — crear factura
5. `POST /invoice-items/` — líneas
6. `POST /stock_movements/` — egreso (si aplica)
7. (MVP+) `POST /fiscal-documents/` + issue/send

**Auth del conector:** usuario de servicio por tenant con permisos mínimos  
(`invoices.*`, `invoice_items.*`, `customers.*`, `products.read`, `stock_movements.create`).

---

## 7. Idempotencia (crítico)

Antes de crear factura:

```
Buscar invoice donde metadata.woocommerce_order_id == order.id
  → si existe: no crear otra; opcionalmente actualizar estado
  → si no: crear
```

Guardar siempre en `invoice.metadata`:

```json
{
  "woocommerce_order_id": 12345,
  "woocommerce_order_number": "12345",
  "woocommerce_status": "processing",
  "synced_at": "2026-08-12T18:00:00Z"
}
```

---

## 8. Configuración por tenant (mínimo)

```json
{
  "woocommerce": {
    "enabled": true,
    "store_url": "https://mitienda.com",
    "webhook_secret": "***",
    "default_branch_id": "uuid",
    "default_warehouse_id": "uuid",
    "default_series_ticket": "A",
    "default_series_factura": "A",
    "create_as_status": "draft",
    "auto_stock_out": true,
    "auto_fiscal_issue": false
  }
}
```

---

## 9. Flujo paso a paso (MVP)

1. Woo dispara webhook `order.updated` (status `processing`).
2. Conector valida firma HMAC del webhook.
3. Conector autentica contra Nexorux (JWT).
4. Si ya existe factura con ese `woocommerce_order_id` → fin OK.
5. Resolver/crear cliente.
6. Para cada línea: buscar producto por SKU.
7. Crear `invoice` + `invoice_items` con totales.
8. Si `auto_stock_out`: crear egreso por depósito default.
9. Responder `200` a Woo.
10. (Opcional UI) En Nexorux el usuario revisa y emite CFE.

---

## 10. Errores y operación

| Caso | Comportamiento MVP |
|------|--------------------|
| SKU inexistente | Fallar pedido sync + log; no crear factura parcial |
| RUT inválido | Tratar como e-Ticket o marcar error configurable |
| Nexorux caído | Woo reintenta webhook; conector debe ser idempotente |
| Firma webhook inválida | `401` / ignorar |

Cola de “pedidos pendientes de sync” (tabla o log) es muy recomendable aunque sea simple.

---

## 11. Criterios de aceptación del MVP

- [ ] Un pedido de prueba en Woo (consumidor final) crea e-Ticket draft en Nexorux
- [ ] Un pedido con RUT/empresa crea e-Factura draft
- [ ] Reenviar el mismo webhook no duplica la factura
- [ ] Stock baja una sola vez
- [ ] Líneas matchean por SKU
- [ ] Queda trazabilidad `woocommerce_order_id` en metadata
- [ ] Documentado cómo configurar webhook + usuario API

---

## 12. Roadmap sugerido

| Fase | Entrega |
|------|---------|
| **MVP** | Pedido → factura draft + stock + idempotencia |
| **1.1** | UI Nexorux: “Pedidos Woo” / sync catálogo JSON (`/woocommerce`) |
| **1.2** | Emisión CFE automática (cola Celery) |
| **2** | Sync stock Nexorux → Woo |
| **2.1** | Sync productos/precios básicos (API upsert por SKU ya disponible) |
| **3** | Refunds → notas de crédito 102/112 |

---

## 13. Prioridad respecto al resto del producto

1. ERP estable + CRUD  
2. Homologación / emisión DGI confiable  
3. **Conector WooCommerce MVP**  
4. Otros conectores (Shopify, etc.)

WooCommerce es el primer conector e-commerce recomendado para el mercado de Nexorux.

---

## 14. Mensaje comercial (1 línea)

> **Nexorux + WooCommerce:** vendé online y facturá en Uruguay sin cargar pedidos a mano.
