# NEXORUX ERP — Project Status

> Last verified: 2026-08-13 (POS modo caja, logo, SMTP Gmail recovery, RLS cert fix).  
> Single source of truth — update when significant changes land.

## Summary

NEXORUX ERP is a multi-company ERP with electronic invoicing (CFE) for Uruguay.
Backend and frontend are operational for day-to-day ERP use (CRUD, **POS profesional**,
inventario, facturas, Woo MVP, branding). Infra de despliegue prod existe (Caddy,
migrate-on-deploy, SMTP Gmail verificado, backups). **No está listo para producción
fiscal real**: falta certificado de firma DGI, homologación, y varios pasos de go-live.

| Layer | Status | Maturity |
|-------|--------|----------|
| Backend API | Operational + inventory + Woo + SMTP recovery | ~95% |
| Frontend UI | CRUD + POS kiosk + logo + recover UX | ~97% |
| Fiscal / DGI | Code + XSD + red ePrueba OK; sin envío firmado real | ~88% |
| Tests (backend) | Inventory + auth + email/password recovery | ~92% |
| Tests (frontend) | Profile + login/logo + Vitest suite | ~82% |
| Documentation | STATUS + DGI + Woo + RLS + PRODUCTION + EMAIL | ~90% |
| Production readiness | Compose/Caddy/SMTP/backups; go-live incompleto | ~72% |

**Verdict:** usable en demo / piloto interno (caja + recovery por mail reales).  
**No go-live comercial con facturación electrónica** hasta cerrar el bloque DGI + checklist abajo.

---

## Qué falta para producción

Ordenado por criticidad. Detalle operativo: `docs/PRODUCTION.md`, correo: `docs/EMAIL.md`.

### Bloqueantes (sin esto no hay producción seria)

| # | Ítem | Por qué importa | Quién / cómo |
|---|------|-----------------|--------------|
| 1 | **Certificado de firma CFE** (`DGI_CERT_PATH` / `DGI_KEY_PATH`) | Sin firma no hay SOAP válido a DGI | Cliente / proveedor de certificado |
| 2 | **Primer envío real a ePrueba** | Validar XML firmado + respuesta DGI | Dev + cert; hoy **bloqueado** por #1 |
| 3 | **Homologación DGI** + CAE / ambiente homologación → producción | Requisito legal para emitir CFE reales | Proceso DGI; ver `DGI_COMPLIANCE_MATRIX.md` |
| 4 | **Dominio público + TLS real** | Quitar `tls internal` del `Caddyfile`, DNS, Let's Encrypt | Ops; set `NEXORUX_DOMAIN`, CORS, `TRUSTED_HOSTS` |
| 5 | **Secrets rotados** | `secrets/*.txt` fuertes; rotar app password Gmail si se filtró | Ops |
| 6 | **Cambiar password demo** (`admin@demo.com` / `demo1234`) | Credencial conocida en el seed | Ops post-deploy |
| 7 | **Backups programados + drill de restore** | Scripts existen; falta cron + restore probado | Ops; `scripts/backup_postgres.*` |

### Importantes (recomendados antes de clientes reales)

| # | Ítem | Notas |
|---|------|--------|
| 8 | Monitoreo externo de `/health` | UptimeRobot / similar |
| 9 | Backups off-host | Hoy dumps en `./backups/` |
| 10 | Confirmar `RLS_TENANT_CONTEXT_ENABLED=true` y `STOCK_ALLOW_NEGATIVE=false` | Defaults docs/compose |
| 11 | Re-corrida completa de tests en CI de release | Suite backend + frontend |
| 12 | Agregador de logs | Hoy: rotación Docker 10m×5 |

### Diferible (post go-live)

| # | Ítem | Notas |
|---|------|--------|
| 13 | Observabilidad (Prometheus / tracing) | No bloquea MVP |
| 14 | Plugin WordPress WooCommerce | API/webhook MVP existe |
| 15 | Auto-emisión DGI desde pedidos Woo | Emit fiscal desde UI hoy |
| 16 | Celery autodiscover / más tareas | Solo `send_cfe_async` |
| 17 | Contabilidad avanzada | Fuera de alcance actual |

### Ya resuelto (no listar como pendiente)

- Caddy + compose prod + migrate-on-deploy + log rotation  
- **SMTP Gmail real** para recuperación (probado envío; ver `docs/EMAIL.md`)  
- UI recovery: correo registrado → token por mail → nueva contraseña  
- Rate limit, lockout Redis, headers, trusted hosts, CORS  
- RLS ENABLE + FORCE + **fix cast vacío** (`b2c3d4e5f6a7`)  
- Alta de certificados UI endurecida (menos 500 por RLS)  
- Inventario: entradas proveedor → stock IN; venta → stock OUT  
- POS: layout profesional, modo caja fullscreen (sin menú), atajos, espera, vuelto  
- Branding: logo `nexorux-erp-logo.png` en login / register / recover / layout / POS  

---

## Backend

### Implemented

- **21+ API routers** bajo `/api/v1` (integrations + purchase-receipts)
- **Alembic** incl. ENABLE/FORCE RLS; purchase_receipt; **`b2c3d4e5f6a7`** (RLS NULLIF GUC)
- **Inventory**: purchase receipts → stock `in`; ventas paid/issued → `out`; NC 102/112 → `in`;
  balances; 409 si stock insuficiente
- **Auth**: JWT, register, **password forgot/reset por SMTP** (sin filtrar token fuera de DEBUG),
  profile, lockout
- **Email**: `app/services/email.py` — SMTP / outbox; `scripts/test_smtp.py`
- **RBAC** + `/auth/me` permission codes
- **CRUD** entidades ERP + certificates (create/list/update/delete endurecido)
- **Fiscal engine** + Celery `send_cfe_async`
- **WooCommerce MVP**: webhook, refund→NC, sync products/stock
- **Ops**: structlog (PrintLogger-safe), entrypoint secrets + migrate, config SMTP/TRUSTED_HOSTS

### Tests

```
Baseline ~148 + test_email / test_password_recovery (Python 3.11, .venv311)
```

### Known gaps

- **DGI live SOAP send blocked** — signing certificate material
- Celery: una sola task
- Woo: sin plugin WP ni auto-DGI

---

## Frontend

### Implemented

- **25+ pages** — POS kiosk, PurchaseReceipts, Invoices, RecoverPassword, Profile, Woo, Reports,
  Roles, Certificates, etc.
- **BrandLogo** (`/nexorux-erp-logo.png` desde `docs/nexorux-erp-logo.png` → `frontend/public/`)
- **POS**: dos columnas, medios de pago, vuelto, acceso rápido, ticket en espera, autoimprimir,
  sonido, resumen del día, **Modo caja** (portal fullscreen, menú oculto, F11)
- Nav por permisos; proxy API → `:8002` en dev (`vite.config.js` / `scripts/dev.mjs`)

### Tests

```
Vitest: login/logo + layout + suite previa — tsc --noEmit clean (2026-08-13 spot checks)
```

---

## Fiscal / DGI

### Code status: IMPLEMENTED_IN_CODE

### DGI validation status: IN_PROGRESS — **cert block remains**

| Requirement | Status |
|-------------|--------|
| Network TLS to ePrueba `:6443` | DONE |
| SOAP send ePrueba | **BLOCKED** — needs signing certificate |
| Homologation / production | NOT_STARTED |

**This system is NOT homologated or approved by DGI.**

UI **Certificados** permite cargar metadata (`cert_path` / `key_path`) para el motor;
sigue haciendo falta el material PEM real para el envío DGI.

---

## Integrations

- **WooCommerce**: webhook + product/stock sync + refunds→NC + UI.  
  Docs: `docs/WOOCOMMERCE_CONNECTOR_MVP.md`. Pendiente: plugin WP.

---

## Infrastructure / RLS

- Dev: `docker-compose.yml` + `Dockerfile.dev` (+ Mailpit opcional)
- Prod: `docker-compose.prod.yml` + Caddy + Celery + secrets
- Ops: `docs/PRODUCTION.md`, `docs/EMAIL.md`, `secrets/README.md`
- CI: lint/test + compose config validate
- RLS: `docs/RLS.md` — ENABLE + FORCE + GUC-safe policies (`b2c3d4e5f6a7`)  
  Flag: `RLS_TENANT_CONTEXT_ENABLED=true`

---

## Environment notes

- **Python**: `backend/.venv311` (3.11). Python 3.14 incompatible.
- **API local**: a menudo `:8002` (si `:8000` da WinError 10013); alinear proxy Vite.
- **SMTP**: Gmail vía `SMTP_HOST=smtp.gmail.com` + app password; guía `docs/EMAIL.md`
- **Password reset URL**: `PASSWORD_RESET_URL_BASE` (ej. `http://localhost:5173/recover-password`)
- **RLS**: `RLS_TENANT_CONTEXT_ENABLED=true`
- **DGI**: `DGI_CERT_PATH` / `DGI_KEY_PATH` — **blocker #1**
- **Demo**: admin@demo.com / demo1234 — **cambiar antes de prod**
- **Logo**: `docs/nexorux-erp-logo.png` (fuente) / `frontend/public/nexorux-erp-logo.png` (app)
