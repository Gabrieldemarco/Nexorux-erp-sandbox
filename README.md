# NEXORUX ERP

Multi-company ERP with electronic invoicing (CFE) for Uruguay.

**Status:** demo / piloto interno usable. **Not** production-ready for live DGI fiscal billing  
until a signing certificate and homologation are in place. See [`STATUS.md`](STATUS.md).

**Repository:** https://github.com/Gabrieldemarco/Nexorux-erp (private)

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Backend:** Python 3.11 + FastAPI + Pydantic + SQLAlchemy (async)
- **Database:** PostgreSQL 15 (Row Level Security / FORCE RLS)
- **Cache/Queue:** Redis + Celery
- **Infrastructure:** Docker Compose, Caddy (prod TLS), GitHub Actions

## What works today

- Full ERP CRUD UI (products, customers, suppliers, invoices, **payments**, stock, …)
- **Cuenta corriente** (`/current-accounts`): saldo por cliente, facturas abiertas e historial de cobros
- **POS / caja rápida** (`/pos`) with fullscreen “modo caja”
- **Entradas proveedor** (`/purchase-receipts`) → stock IN (mismo depósito que caja); sales → stock OUT
- Auth: JWT (incl. `tenant_id`), register, refresh, **password recovery via SMTP**
- RBAC permissions, certificates & tax configurations UI
- Fiscal engine in code (XML / XSD / signer / SOAP) — **ePrueba send blocked without cert**
- WooCommerce connector MVP (webhook, sync, refunds → NC)
- Branding (Nexorux logo on auth + shell + POS)

## Project Structure

```
nexorux-erp/
├── backend/                 # FastAPI API
│   ├── app/api|core|db|models|schemas|services|tasks
│   ├── alembic/             # Migrations (incl. RLS)
│   ├── tests/
│   ├── scripts/             # seed_demo, SMTP test, DGI helpers
│   └── .venv311/            # Recommended local Python env
├── frontend/                # React + Vite app
├── docs/                    # PRODUCTION, EMAIL, RLS, WooCommerce, …
├── compliance/dgi/          # DGI evidence / XSDs
├── secrets/                 # Prod secrets (git-ignored; see secrets/README.md)
├── docker-compose.yml       # Dev stack (+ Mailpit)
├── docker-compose.prod.yml  # Prod stack + Caddy + Celery
├── Caddyfile
├── STATUS.md                # Source of truth for project state
└── README.md
```

## Prerequisites

- Docker and Docker Compose (optional but recommended)
- **Python 3.11** — use `backend/.venv311` (Python 3.14 is incompatible)
- Node.js 20+
- PostgreSQL 15+ and Redis 7+ (if not using Docker for those)

## Quick Start with Docker

```bash
git clone https://github.com/Gabrieldemarco/Nexorux-erp.git
cd Nexorux-erp   # or nexorux-erp
docker compose up -d
```

Typical published ports (`docker-compose.yml`):

| Service   | URL / port                          |
|-----------|-------------------------------------|
| Frontend  | http://localhost:3000               |
| Backend   | http://localhost:8001 (→ container 8000) |
| API docs  | http://localhost:8001/docs          |
| Mailpit   | http://localhost:8025 (SMTP UI)     |
| Postgres  | localhost:5432                      |
| Redis     | localhost:6379                      |

```bash
docker compose down
```

## Local Development (without full Docker app)

### Backend

```bash
cd backend
py -3.11 -m venv .venv311
.venv311\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env             # then edit
alembic upgrade head
python -m scripts.seed_demo        # optional demo data
```

On Windows, port **8000** often fails (`WinError 10013`). Prefer **8002** and keep the Vite proxy in sync:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

Required for FORCE RLS:

```env
RLS_TENANT_CONTEXT_ENABLED=true
```

After auth/RLS changes, **log out and log in again** so the JWT includes `tenant_id`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves http://localhost:5173 and proxies `/api` → `http://127.0.0.1:8002`  
(`frontend/scripts/dev.mjs` and `vite.config.js` — keep both aligned).

### Demo login

| Field    | Value            |
|----------|------------------|
| Email    | `admin@demo.com` |
| Password | `demo1234`       |

Change before any real deployment.

## Environment Variables

See `backend/.env.example`. Important ones:

| Variable | Notes |
|----------|--------|
| `DATABASE_URL` | Async SQLAlchemy URL (`postgresql+asyncpg://…`) |
| `REDIS_URL` | Redis for Celery / rate limit / lockout |
| `SECRET_KEY` | JWT secret — rotate in prod |
| `RLS_TENANT_CONTEXT_ENABLED` | Must be `true` with FORCE RLS |
| `SMTP_*` / `PASSWORD_RESET_URL_BASE` | Password recovery (see `docs/EMAIL.md`) |
| `DGI_ENVIRONMENT` | `testing` / `homologacion` / `produccion` |
| `DGI_CERT_PATH` / `DGI_KEY_PATH` | **Blocker** for live DGI send |

Production layout: `docs/PRODUCTION.md`, `secrets/README.md`.

## API surface (high level)

- `GET /health` — process health
- Auth: `/api/v1/auth/token`, `register`, `refresh`, `me`, password forgot/reset
- Tenant-scoped CRUD + RBAC: products, customers, suppliers, branches, warehouses,
  invoices, payments, stock, purchase-receipts, fiscal docs, certificates, tax configs,
  price lists, roles, audit, …
- Integrations: `/api/v1/integrations/woocommerce/…`

Interactive docs when `DEBUG=true`: `/docs`, `/redoc`.

## Testing

```bash
# Backend
cd backend
.venv311\Scripts\python.exe -m pytest tests/ -q

# Frontend
cd frontend
npm test
```

## Database Migrations

```bash
cd backend
.venv311\Scripts\activate
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## CI/CD

GitHub Actions:

- `.github/workflows/backend.yml` — Python 3.11, lint, pytest, mypy
- `.github/workflows/frontend.yml` — Node 20, ESLint, Vitest, build
- Compose prod config validation (see CI / STATUS)

## Documentation

| Document | Description |
|----------|-------------|
| [`STATUS.md`](STATUS.md) | **Source of truth** — maturity, blockers, what’s done |
| [`docs/PRODUCTION.md`](docs/PRODUCTION.md) | Production deploy checklist |
| [`docs/EMAIL.md`](docs/EMAIL.md) | SMTP / password recovery |
| [`docs/RLS.md`](docs/RLS.md) | PostgreSQL RLS + tenant GUC |
| [`docs/WOOCOMMERCE_CONNECTOR_MVP.md`](docs/WOOCOMMERCE_CONNECTOR_MVP.md) | Woo MVP |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System design |
| [`DATABASE.md`](DATABASE.md) | Schema notes |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Deployment notes |
| [`DGI_COMPLIANCE_MATRIX.md`](DGI_COMPLIANCE_MATRIX.md) | Fiscal compliance tracking |
| [`DGI_DISCOVERY.md`](DGI_DISCOVERY.md) | DGI research notes |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution guidelines |

## Status (summary)

| Area | State |
|------|--------|
| Backend / Frontend ERP | Operational for day-to-day demo |
| POS + inventory | Implemented (entradas proveedor UX + saldos) |
| Password recovery | SMTP (Gmail verified in local config) |
| RLS | ENABLE + FORCE; app sets `app.current_tenant_id` |
| DGI live send / homologation | **Blocked** — needs signing certificate |
| Prod go-live | Infra exists; domain/TLS/secrets/backups drills pending |

Full detail and backlog: **[`STATUS.md`](STATUS.md)**.

> Use `backend/.venv311` (Python 3.11). Python 3.14 is incompatible with project dependencies.

## Support

Open an issue in the private GitHub repository (collaborators only).
