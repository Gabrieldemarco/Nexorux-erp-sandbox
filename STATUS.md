# NEXORUX ERP — Project Status

> Last verified: 2026-08-13 (POS cobro RLS + F1 nueva venta; click fila → formulario detalle; brand/logo; monitoreo/backup/docs completados).  
> Single source of truth — update when significant changes land.

## Summary

NEXORUX ERP is a multi-company ERP with electronic invoicing (CFE) for Uruguay.
Backend and frontend are operational for day-to-day ERP use (CRUD, **POS profesional**,
inventario, facturas, **pagos / cuenta corriente**, Woo MVP, branding, certificados/impuestos). Infra de despliegue
prod existe (Caddy, migrate-on-deploy, SMTP Gmail verificado, backups). Código en
**GitHub privado**. **No está listo para producción fiscal real**: falta certificado
de firma DGI, homologación, y varios pasos de go-live.

| Layer | Status | Maturity |
|-------|--------|----------|
| Backend API | Operational + inventory + Woo + SMTP + RLS hardening (invoice/payment reload) | ~96% |
| Frontend UI | CRUD + **fila→detalle** + POS kiosk + cuenta corriente + logo + recover | ~98% |
| Fiscal / DGI | Code + XSD + red ePrueba OK; sin envío firmado real | ~88% |
| Tests (backend) | Auth/email + certificate/tax schema tests | ~93% |
| Tests (frontend) | Profile + login/logo + Vitest suite | ~82% |
| Documentation | STATUS + README + **BUILD_LOG_42H** + DGI + Woo + RLS + PRODUCTION + EMAIL + USER_MANUAL + TROUBLESHOOTING + RUNBOOKS + DEVELOPER_ONBOARDING + MONITORING + BACKUP_SCHEDULE | ~98% |
| Production readiness | Compose/Caddy/SMTP/backups+restore scripts/health probes/monitoring/cron/jobs; go-live incompleto | ~85% |
| Source control | Private GitHub repo pushed (`main`) | Done |

**Verdict:** usable en demo / piloto interno (caja + recovery por mail + alta cert/tax + entradas proveedor + cuenta corriente + detalle por fila).  
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
| 8 | ~~Monitoreo externo de `/health`~~ | **Hecho** — scripts listos + guía `docs/MONITORING.md` (UptimeRobot, Pingdom, StatusCake, etc.) |
| 9 | ~~Backups off-host~~ | **Hecho** — scripts `setup_cron.sh`/`setup_cron.ps1` + guía `docs/BACKUP_SCHEDULE.md` |
| 10 | ~~Confirmar `RLS_TENANT_CONTEXT_ENABLED=true` y `STOCK_ALLOW_NEGATIVE=false`~~ | **Hecho** en `docker-compose.yml` + `docker-compose.prod.yml` (+ celery) |
| 11 | ~~Re-corrida completa de tests en CI de release~~ | **Hecho** — CI endurecido (flags RLS/stock + `tsc --noEmit`); 175 tests pasan (legacy fails corregidos) |
| 12 | Agregador de logs | Hoy: rotación Docker 10m×5 |
| 13 | ~~Push de commits locales~~ | **Hecho** — `main` en https://github.com/Gabrieldemarco/Nexorux-erp (`055a394`) |
| 14 | ~~Documentación de usuario~~ | **Hecho** — `docs/USER_MANUAL.md` (910 líneas, guía completa) |
| 15 | ~~Manual de troubleshooting~~ | **Hecho** — `docs/TROUBLESHOOTING.md` (955 líneas, solución de problemas) |
| 16 | ~~Runbooks de incidentes~~ | **Hecho** — `docs/RUNBOOKS.md` (1358 líneas, 10 runbooks detallados) |
| 17 | ~~Guía de onboarding developers~~ | **Hecho** — `docs/DEVELOPER_ONBOARDING.md` (1066 líneas, guía completa) |

### Diferible (post go-live)

| # | Ítem | Notas |
|---|------|--------|
| 14 | Observabilidad (Prometheus / tracing) | No bloquea MVP |
| 15 | Plugin WordPress WooCommerce | API/webhook MVP existe |
| 16 | Auto-emisión DGI desde pedidos Woo | Emit fiscal desde UI hoy |
| 17 | Celery autodiscover / más tareas | Solo `send_cfe_async` |
| 18 | Contabilidad avanzada | Fuera de alcance actual |

### Ya resuelto (no listar como pendiente)

- Caddy + compose prod + migrate-on-deploy + log rotation  
- **SMTP Gmail real** para recuperación (probado envío; ver `docs/EMAIL.md`)  
- UI recovery: correo registrado → token por mail → nueva contraseña  
- Rate limit, lockout Redis, headers, trusted hosts, CORS  
- RLS ENABLE + FORCE + **fix cast vacío** (`b2c3d4e5f6a7`)  
- **JWT incluye `tenant_id`**; `get_db` setea GUC aunque el token viejo no tenga `type=access`  
- **Alta certificados + impuestos** verificada en API `:8002` (schema `metadata` vs SQLAlchemy MetaData; `effective_from` default; reload post-commit bajo FORCE RLS)  
- **Cobro POS / facturas / ítems / pagos**: `reload_after_commit` (ya no `db.refresh` post-commit) — evita `InvalidRequestError: Could not refresh instance '<Invoice…>'` con FORCE RLS  
- Inventario: entradas proveedor → stock IN (API verificada 201 + saldo); venta → stock OUT  
- UX **Entradas proveedor**: mismo depósito que caja, stock actual→después, buscador SKU, prerrequisitos con links; **click fila → detalle**  
- **README.md** alineado con la app (ya no dice frontend read-only)  
- POS: layout profesional, modo caja fullscreen (sin menú), atajos, espera, vuelto, **F1 nueva venta**, F2 buscar, F4 espera, F5–F7 pago, F9 cobrar, F11 modo caja, Esc vaciar  
- **Listas → detalle**: `EntityListRow` — click en registro abre formulario/modal (productos, clientes, facturas, pagos, proveedores, fiscal, etc.)  
- **Pagos + cuenta corriente**: cobros por factura/cliente; saldo = facturas que afectan CC − pagos completados; NC resta; factura pasa a pagada al cubrir el total  
- Branding: logo en login / register / recover / layout / POS  
- **Ops no-bloqueantes**: flags RLS/stock en compose dev+prod; `scripts/check_health.*`; backup con `BACKUP_COPY_TO` + `restore_postgres.*`; CI con flags + `tsc --noEmit`; `docs/PRODUCTION.md` actualizado  
- **Repo privado** en GitHub: https://github.com/Gabrieldemarco/Nexorux-erp (`main`)  

---

## Backend

### Implemented

- **21+ API routers** bajo `/api/v1` (integrations + purchase-receipts + current-accounts)
- **Alembic** incl. ENABLE/FORCE RLS; purchase_receipt; **`b2c3d4e5f6a7`** (RLS NULLIF GUC)
- **Inventory**: purchase receipts → stock `in`; ventas paid/issued → `out`; NC 102/112 → `in`;
  balances; 409 si stock insuficiente
- **Cuenta corriente**: `GET /current-accounts/` y `/{customer_id}` — saldo = facturas `affects_receivable` − pagos `counts_as_paid`; NC resta; cobro completo marca factura `paid`
- **Auth**: JWT (con `tenant_id`), register, **password forgot/reset por SMTP**,
  profile, lockout
- **Email**: `app/services/email.py` — SMTP / outbox; `scripts/test_smtp.py`
- **RBAC** + `/auth/me` permission codes
- **CRUD** entidades ERP + certificates / tax-configurations / **invoices / invoice-items / payments** endurecidos para RLS (`reload_after_commit`)
- **Fiscal engine** + Celery `send_cfe_async`
- **WooCommerce MVP**: webhook, refund→NC, sync products/stock
- **Ops**: structlog, entrypoint secrets + migrate, exception handlers más claros en DEBUG

### Tests

```
Baseline ~175 passed (Python 3.11, .venv311) — cert/tax/fiscal/HSTS legacy fails fixed
```

### Known gaps

- **DGI live SOAP send blocked** — signing certificate material (PEM paths en UI ≠ firma DGI lista)
- Celery: una sola task
- Woo: sin plugin WP ni auto-DGI

---

## Frontend

### Implemented

- **25+ pages** — POS kiosk, PurchaseReceipts, Invoices, **Payments**, **CurrentAccounts**, RecoverPassword, Profile, Woo, Reports,
  Roles, Certificates, TaxConfigurations, etc.
- **BrandLogo** (`/Nexorux-erp.png` / logo oficial en `docs/`)
- **POS**: dos columnas, medios de pago, vuelto, acceso rápido, ticket en espera, autoimprimir,
  sonido, resumen del día, **Modo caja** (portal fullscreen, menú oculto, F11), **F1 nueva venta**
- **Listas clicables**: `EntityListRow` — click abre formulario de detalle/edición (o panel de lectura en fiscal / entradas proveedor)
- Productos: formulario enriquecido (descripción, tipo, unidad) en modal `xl`
- Impuestos: `effective_from` default en formulario (API también defaulta a now UTC)
- **Entradas proveedor** (`/purchase-receipts`): forma recomendada de sumar stock; aviso de depósito vs caja; saldos en vivo; detalle al click
- **Stock** (`/stock-movements`): apunta a entradas proveedor para compras (ajustes manuales aparte)
- Catálogo funcional `/api/v1/catalog/` (estados, CFE, moneda, `affects_receivable` / `counts_as_paid`) — UI ya no hardcodea labels de factura
- **Cuenta corriente** (`/current-accounts`): saldo, vencido, límite de crédito, facturas abiertas, historial de cobros; **Pagos** registra cobros y actualiza la factura
- **UX visual**: menú más claro, tablas/botones/modales pulidos, panel con atajos, login en tarjeta
- **Marca NEXORUX**: logo oficial; fondo #F8FAFC; botones #0A2463; acentos #247BA0 / #3E92CC; texto #1E293B

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

UI **Certificados** permite metadata (`cert_path` / `key_path`) para el motor;
sigue haciendo falta el material PEM real para el envío DGI.

---

## Integrations

- **WooCommerce**: webhook + product/stock sync + refunds→NC + UI.  
  Docs: `docs/WOOCOMMERCE_CONNECTOR_MVP.md`. Pendiente: plugin WP.

---

## Infrastructure / RLS / Git

- Dev: `docker-compose.yml` + `Dockerfile.dev` (+ Mailpit opcional)
- Prod: `docker-compose.prod.yml` + Caddy + Celery + secrets
- Ops: `docs/PRODUCTION.md`, `docs/EMAIL.md`, `docs/RLS.md`, `secrets/README.md`  
- Scripts: `backup_postgres.*` (+ `BACKUP_COPY_TO`), `restore_postgres.*`, `check_health.*`  
- CI: lint/test + compose config validate + frontend `tsc --noEmit` + test env RLS/stock flags
- RLS: ENABLE + FORCE + GUC-safe policies; JWT `tenant_id` + `set_tenant_guc` / `reload_after_commit`
- Flag: `RLS_TENANT_CONTEXT_ENABLED=true` (**requerido**; sin GUC los INSERT fallan)
- **GitHub**: https://github.com/Gabrieldemarco/Nexorux-erp — **private**, branch `main`

---

## Environment notes

- **Python**: `backend/.venv311` (3.11). Python 3.14 incompatible.
- **API local**: a menudo `:8002` (si `:8000` da WinError 10013); alinear proxy Vite.
- **SMTP**: Gmail vía `SMTP_HOST=smtp.gmail.com` + app password; guía `docs/EMAIL.md`
- **Password reset URL**: `PASSWORD_RESET_URL_BASE` (ej. `http://localhost:5173/recover-password`)
- **RLS**: `RLS_TENANT_CONTEXT_ENABLED=true` — tras updates de auth, **re-login** para token con `tenant_id`
- **DGI**: `DGI_CERT_PATH` / `DGI_KEY_PATH` — **blocker #1**
- **Demo**: admin@demo.com / demo1234 — **cambiar antes de prod**
- **Logo**: oficial `docs/Nexorux-erp.png` → app vía `BrandLogo` / `frontend/public`

---

## Technical debt (prioritized)

Mitigated / closed:
- Diagnostic files with secrets (`backend/_diag_*.json/txt/py`) removed from index and ignored.
- Frontend `react-hooks/exhaustive-deps` warnings fixed (`useCatalog`, `FiscalDocuments`, `Invoices`).
- Removed deprecated `identifier` alias from password recovery API + frontend client + tests.
- `.gitignore` extended for local diagnostic artifacts.

Open:
- Backend tests currently cannot run on local Windows because `python` defaults to 3.14 and `.venv311` lacks `pip`; need a clean 3.11 venv or Dockerized test runner.
- Frontend dependencies are outdated/deprecated (`eslint@8`, `@typescript-eslint@6`, `react@18`, `vite@5`, `tailwindcss@3`); upgrade path should be planned.
- One intentional `eslint-disable-next-line react-hooks/exhaustive-deps` remains in `Pos.tsx` (POS keyboard shortcuts).
- Backend has broad `except Exception` blocks (`health`, `email`, `woo sync`, `dgi_eprueba_test`) justified for robustness, but should be narrowed where possible.
- `compliance/dgi/requirements.md` is still a skeleton.
- Demo credentials and secrets still need rotation before public exposure.
