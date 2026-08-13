# NEXORUX ERP

Multi-company ERP with electronic invoicing (CFE) for Uruguay.

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Backend:** Python + FastAPI + Pydantic + SQLAlchemy
- **Database:** PostgreSQL 15
- **Cache/Queue:** Redis + Celery
- **Infrastructure:** Docker + Docker Compose
- **CI/CD:** GitHub Actions

## Project Structure

```
nexorux-erp/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration, security, RBAC, Celery
│   │   ├── db/             # Database session and models
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   │   └── fiscal/     # DGI/CFE engine, XML builder, signer, SOAP client, state machine
│   │   └── tasks/          # Celery tasks
│   ├── tests/              # Backend tests
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Python dependencies
│   ├── scripts/            # Utilities (seed_demo.py)
│   └── Dockerfile
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── types/         # TypeScript types
│   │   ├── hooks/         # Custom React hooks
│   │   └── test/          # Frontend tests
│   ├── public/            # Static assets
│   ├── package.json       # Node dependencies
│   └── Dockerfile
├── .github/
│   └── workflows/         # CI/CD pipelines
├── docker-compose.yml        # Development environment
├── docker-compose.prod.yml   # Production environment
├── secrets/                  # Production secrets (git-ignored)
├── STATUS.md                 # Project status (source of truth)
├── ARCHITECTURE.md           # System architecture
├── DGI_COMPLIANCE_MATRIX.md  # DGI fiscal compliance
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development; a ready environment is available at `backend/.venv311`)
- Node.js 20+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

## Quick Start with Docker

### 1. Clone the repository

```bash
git clone <repository-url>
cd nexorux-erp
```

### 2. Start the development environment

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API on port 8000
- Frontend on port 3000

### 3. Access the application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 4. Stop the environment

```bash
docker-compose down
```

## Local Development

### Backend Setup

```bash
cd backend

# Create virtual environment (Python 3.11+)
py -3.11 -m venv .venv311
.venv311\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run migrations
alembic upgrade head

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

## Environment Variables

See `backend/.env.example` for all available environment variables.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key (change in production)
- `DGI_ENVIRONMENT`: DGI environment (testing/homologacion/produccion)

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint
- `GET /api/v1/health/` - API health check

### Authentication
- `POST /api/v1/auth/token` - Login (OAuth2 form)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### CRUD Entities (tenant-scoped, RBAC-protected)
- Tenants, Companies, Products, Customers, Suppliers
- Branches, Warehouses, Invoices, Invoice Items
- Payments, Stock Movements
- Fiscal Documents (with actions: issue, send, query-status, retry)
- Roles, Permissions, Certificates, Tax Configurations, Price Lists
- Audit Logs (read-only)

API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Testing

### Backend Tests

```bash
cd backend
.venv311\Scripts\python.exe -m pytest tests/ -v --cov=app
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Code Quality

### Backend

```bash
cd backend

# Activate virtual environment
.venv311\Scripts\activate

# Format code
black app
isort app

# Lint
flake8 app

# Type check
mypy app
```

### Frontend

```bash
cd frontend

# Lint
npm run lint

# Tests
npm test

# Build
npm run build
```

## Database Migrations

```bash
cd backend

# Activate virtual environment
.venv311\Scripts\activate

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## CI/CD

The project uses GitHub Actions for CI/CD:

- **Backend workflow:** `.github/workflows/backend.yml`
  - Python 3.11
  - Lint: black, isort, flake8
  - Tests: pytest
  - Type check: mypy

- **Frontend workflow:** `.github/workflows/frontend.yml`
  - Node.js 20
  - Install: npm ci
  - Lint: ESLint
  - Tests: vitest
  - Build: vite build

## Development Workflow

1. Create a feature branch from `develop`
2. Make your changes
3. Run tests and linting locally
4. Commit with conventional commits
5. Push and create a pull request
6. CI/CD will run automatically
7. Merge after approval

## Documentation

| Document | Description |
|----------|-------------|
| [`STATUS.md`](STATUS.md) | **Single source of truth** for project state |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System design and security |
| [`DATABASE.md`](DATABASE.md) | Database schema and design |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Production deployment guide |
| [`DGI_DISCOVERY.md`](DGI_DISCOVERY.md) | DGI research notes |
| [`DGI_COMPLIANCE_MATRIX.md`](DGI_COMPLIANCE_MATRIX.md) | Fiscal compliance tracking |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution guidelines |
| [`RELEASE_NOTES.md`](RELEASE_NOTES.md) | Version history |
| [`USER_HANDOFF.md`](USER_HANDOFF.md) | Operations and support guide |
| [`AI_CONTINUATION_GUIDE.md`](AI_CONTINUATION_GUIDE.md) | Guide for continuing development |

## Status

**Current Phase:** FASE 1 — Core ERP implementation (backend mature, frontend in progress)

See [`STATUS.md`](STATUS.md) for the full verified project state.

**Highlights:**
- Backend: 104 tests passing, ~107 API endpoints, full RBAC
- Frontend: auth + read-only entity lists (CRUD UI pending)
- Fiscal engine: implemented in code, **not validated against DGI**
- Rate limiting: in-memory (debug), Redis (production)

**Not production-ready for fiscal operations.** DGI homologation has not been started.

## Remaining Work

See [`STATUS.md`](STATUS.md) for the prioritized backlog. Key items:

- Frontend CRUD forms and token refresh
- DGI sandbox validation and homologation
- PostgreSQL RLS and Redis-backed lockout

> **Note:** Use `backend/.venv311` (Python 3.11). Python 3.14 is incompatible with project dependencies.

## Support

For support, please open an issue in the repository.
