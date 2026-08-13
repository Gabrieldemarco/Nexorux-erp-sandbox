# Architecture Documentation

## Overview

NEXORUX ERP is a multi-company ERP system with electronic invoicing (CFE) for Uruguay. The architecture follows a modern, scalable design with clear separation of concerns.

## System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Browser   │────▶│  Frontend    │────▶│  Backend API    │
│  (React)    │     │  React+TS    │     │  FastAPI+Python │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                  │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              │                              │
                    ▼                              ▼                              ▼
            ┌───────────────┐            ┌───────────────┐            ┌───────────────┐
            │   PostgreSQL  │            │     Redis     │            │  DGI SOAP WS  │
            │   Primary DB  │            │  Cache/Queue  │            │  eFactura     │
            └───────────────┘            └───────────────┘            └───────────────┘
```

## Backend Architecture

### Layers

1. **API Layer** (`app/api/v1/`)
   - FastAPI routers per entity
   - Dependency injection for auth, RBAC, database
   - Request/response serialization with Pydantic

2. **Service Layer** (`app/services/`)
   - Business logic for fiscal operations
   - DGI/CFE engine (XML builder, signer, SOAP client, state machine)
   - Transaction orchestration

3. **Data Layer** (`app/models/`, `app/db/`)
   - SQLAlchemy 2.0 async models
   - Alembic migrations
   - Tenant-scoped queries

4. **Core Layer** (`app/core/`)
   - Security (JWT, password hashing)
   - RBAC (permissions, roles)
   - Configuration (Pydantic settings)
   - Validators (RUT, email, phone)

### Key Patterns

- **Tenant Isolation**: All queries filter by `tenant_id`
- **RBAC**: Permission-based endpoint protection
- **Async/Await**: All database and external service calls are async
- **Structured Logging**: structlog with JSON output
- **Error Handling**: Global exception handlers with sanitized messages

## Frontend Architecture

### Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Route-level page components
├── services/       # API client functions
├── types/          # TypeScript interfaces
├── hooks/          # Custom React hooks (useAuth)
└── test/           # Test setup and utilities
```

### Key Patterns

- **Context API**: Auth state management via `AuthProvider`
- **Protected Routes**: Wrapper component for authenticated pages
- **API Services**: Centralized API calls with axios interceptors
- **Type Safety**: Full TypeScript coverage for API contracts

## Database Design

### Schema Overview

- **Multi-tenant**: All tables include `tenant_id` for data isolation
- **Audit Trail**: `created_at`, `updated_at` on all entities
- **Relationships**: Foreign keys with `ondelete=CASCADE` for tenant data
- **JSON Fields**: Flexible metadata storage where needed

### Key Tables

- `tenant`: Multi-tenant isolation
- `company`: Company master data
- `user`: Authentication and authorization
- `role`, `permission`, `user_role`, `role_permission`: RBAC
- `customer`, `supplier`: Business partners
- `product`: Catalog
- `invoice`, `invoice_item`: Billing
- `payment`, `stock_movement`: Transactions
- `fiscal_document`, `fiscal_response`: DGI integration
- `certificate`, `tax_configuration`: Fiscal setup
- `audit_log`: Change tracking

## Security Architecture

### Authentication

- JWT access tokens (30 min expiry)
- JWT refresh tokens (7 days expiry)
- Token type discrimination (access vs refresh)
- Password hashing with bcrypt

### Authorization

- Role-based access control (RBAC)
- Granular permissions per entity and action
- Tenant-scoped access (users can only access their tenant's data)
- Account lockout after 5 failed login attempts (15 min)

### API Security

- Security headers (X-Frame-Options, X-XSS-Protection, etc.)
- Rate limiting (60 req/min in debug mode)
- Trusted host middleware
- CORS configuration
- Global exception handling (no stack traces in production)

## DGI/CFE Integration

### Flow

1. **Invoice Creation**: User creates invoice in ERP
2. **Fiscal Document**: System creates fiscal document record
3. **Issue**: Build CFE XML, apply digital signature
4. **Send**: Submit to DGI WS (testing/homologacion/produccion)
5. **Query**: Check status if needed
6. **Retry**: Retry rejected documents

### State Machine

```
draft → pending_sign → pending_send → sent → accepted
                                    └──→ rejected → pending_send
                                    └──→ cancelled
```

### Components

- `cfe_types.py`: CFE type mappings
- `xml_builder.py`: XML generation from invoice data
- `signer.py`: Digital signature with X.509 certificates
- `soap_envelope.py`: SOAP envelope generation
- `dgi_client.py`: DGI web service client
- `state_machine.py`: Fiscal document state transitions
- `engine.py`: Orchestration of the CFE lifecycle

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic v2
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7, Celery 5
- **Security**: python-jose, passlib/bcrypt
- **Fiscal**: lxml, cryptography, xmlschema
- **Logging**: structlog
- **Testing**: pytest, pytest-asyncio, vitest
