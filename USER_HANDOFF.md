# User Handoff Guide

This document provides a guide for handing off NEXORUX ERP to operations or support teams.

## Handoff Note

This project is being continued with another AI assistant. The next pass should focus on:
- finishing DGI-grade fiscal hardening and real homologation validation (signing cert),
- optional observability / off-host backups,
- keeping the current ERP + prod baseline stable.

Current important context:
- The project has already been migrated away from the old Python 3.14 runtime issue for local development; use the working Python 3.11-compatible environment described in `README.md`.
- The fiscal engine exists, but still needs real-world DGI validation before it should be treated as production-ready.
- Profile editing and password change UX are in place (`/profile`); recovery supports SMTP email + `?token=` links (`docs/PRODUCTION.md`).
- Production ops baseline: Caddy TLS, migrate-on-deploy entrypoint, `docs/PRODUCTION.md` + backups + `docker-compose.prod.yml`.

## System Overview

NEXORUX ERP is a multi-company ERP system with electronic invoicing (CFE) for Uruguay. It consists of:
- Backend API (FastAPI + Python)
- Frontend (React + TypeScript)
- PostgreSQL database
- Redis cache/queue
- Celery workers for async tasks

## Access Information

### URLs
- Frontend: http://localhost:3000 (or configured domain)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Default Credentials (Development Only)
- Email: admin@demo.com
- Password: demo1234

**Important**: Change these credentials in production!

## Key Features

1. **Multi-Company Management**: Isolated tenant environments
2. **Electronic Invoicing**: DGI/CFE compliance for Uruguay
3. **Inventory Management**: Products, branches, warehouses, stock movements
4. **Accounting**: Invoices, payments, fiscal documents
5. **RBAC**: Role-based access control with granular permissions

## Common Operations

### Starting the System

```bash
# Development
docker compose up -d

# Production
docker compose -f docker-compose.prod.yml up -d
```

### Running Migrations

```bash
cd backend
alembic upgrade head
```

### Seeding Demo Data

```bash
cd backend
python scripts/seed_demo.py
```

### Viewing Logs

```bash
# Backend
docker compose logs -f backend

# Frontend
docker compose logs -f frontend

# Celery Worker
docker compose logs -f celery-worker
```

### Backup

```bash
# Database
docker compose exec postgres pg_dump -U nexorux nexorux_prod > backup.sql

# Redis
docker compose exec redis redis-cli BGSAVE
```

## Troubleshooting

### Backend won't start
1. Check database connectivity: `docker compose exec postgres pg_isready`
2. Check Redis connectivity: `docker compose exec redis redis-cli ping`
3. Review logs: `docker compose logs backend`

### DGI connection issues
1. Verify `DGI_ENVIRONMENT` setting
2. Check network connectivity to DGI endpoints
3. Verify certificate configuration

### Performance issues
1. Check database connection pool
2. Review Celery worker count
3. Check Redis memory usage

## Support Contacts

- Technical Issues: [Your team]
- DGI Compliance: [Your team]
- Infrastructure: [Your team]

## Useful Links

- [DGI e-Factura](https://www.dgi.gub.uy)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
