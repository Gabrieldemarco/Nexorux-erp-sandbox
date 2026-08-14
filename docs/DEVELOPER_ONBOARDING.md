# NEXORUX ERP - Guía de Onboarding para Developers

**Versión:** 1.0  
**Fecha:** 2026-08-13  
**Para:** Desarrolladores nuevos en el proyecto

---

## Índice

1. [Bienvenida](#1-bienvenida)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Configuración del Entorno de Desarrollo](#4-configuración-del-entorno-de-desarrollo)
5. [Estructura del Proyecto](#5-estructura-del-proyecto)
6. [Flujo de Trabajo](#6-flujo-de-trabajo)
7. [Convenios de Código](#7-convenios-de-código)
8. [Testing](#8-testing)
9. [Despliegue](#9-despliegue)
10. [Documentación](#10-documentación)
11. [Primeros Pasos](#11-primeros-pasos)
12. [Recursos](#12-recursos)

---

## 1. Bienvenida

### 1.1 Sobre NEXORUX ERP

NEXORUX ERP es un sistema de planificación de recursos empresariales multiempresa diseñado específicamente para el mercado uruguayo, con énfasis en facturación electrónica (CFE) según normativa DGI.

**Características principales:**
- Multiempresa y multitenancy
- Facturación electrónica (CFE) según normativa DGI
- Gestión de inventario
- Punto de venta profesional
- Gestión de proveedores
- Cuenta corriente
- Reportes y auditoría

### 1.2 Visión del Proyecto

**Objetivo:** Crear un ERP SaaS profesional, mantenible, seguro y preparado para producción, cuya capa fiscal esté diseñada siguiendo estrictamente la documentación oficial vigente de Uruguay.

**NO es:** Un demo o prototipo. Es un sistema production-ready con arquitectura enterprise.

### 1.3 Valores del Equipo

- **Seguridad:** Primero. Nunca comprometer seguridad por velocidad.
- **Calidad:** Code review, tests, documentación.
- **Compliance:** Estricto cumplimiento de normativa DGI.
- **Transparencia:** Documentar decisiones, cambios, y estado.
- **Colaboración:** Work in progress visible, comunicación abierta.

---

## 2. Arquitectura del Sistema

### 2.1 Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  React + TypeScript + Vite + Tailwind CSS              │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  FastAPI + Pydantic + SQLAlchemy + Celery               │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Data Layer (PostgreSQL)                     │
│  PostgreSQL + Row-Level Security (RLS)                 │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Cache & Queue (Redis)                       │
│  Redis + Celery Queue                                    │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Arquitectura Fiscal

```
┌─────────────────────────────────────────────────────────┐
│               ERP Core (Backend)                         │
│  Sales, Purchases, Inventory, Cash, etc.                │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Fiscal Engine                               │
│  Tax calculation, CFE generation, validation             │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│            XML/CFE Generation                            │
│  XML builder, XSD validation                             │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Digital Signature                           │
│  Certificate management, signing                          │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              DGI Adapter                                 │
│  SOAP client, response parsing                           │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              DGI Web Services                             │
│  ePrueba, eHomologación, Producción                      │
└──────────────────────────────────────────────────────────┘
```

### 2.3 Multitenancy

**Arquitectura:**
- Platform → Tenant → Company → Users → Roles
- PostgreSQL Row-Level Security (RLS) para aislamiento de datos
- JWT incluye `tenant_id` para contexto de tenant
- `get_db` setea GUC de tenant en cada query

**Aislamiento garantizado:**
- Los usuarios no pueden acceder a datos de otros tenants
- RLS forza el aislamiento a nivel de base de datos
- Ownership validation en aplicación
- Automated isolation tests

---

## 3. Stack Tecnológico

### 3.1 Frontend

- **Framework:** React 18
- **Lenguaje:** TypeScript
- **Build:** Vite
- **Estilos:** Tailwind CSS
- **Testing:** Vitest + Playwright
- **Router:** React Router
- **HTTP Client:** Axios / Fetch
- **State Management:** React hooks

### 3.2 Backend

- **Framework:** FastAPI
- **Lenguaje:** Python 3.11
- **Validación:** Pydantic
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Queue:** Celery
- **Cache:** Redis
- **Async:** asyncio
- **Logging:** structlog

### 3.3 Database

- **RDBMS:** PostgreSQL 15+
- **Connection Pool:** SQLAlchemy pool
- **Migrations:** Alembic
- **Security:** Row-Level Security (RLS)

### 3.4 Infrastructure

- **Containerization:** Docker
- **Orchestration:** Docker Compose
- **Reverse Proxy:** Caddy
- **CI/CD:** GitHub Actions
- **Monitoring:** Health checks + external monitoring
- **Storage:** S3-compatible object storage

### 3.5 Security

- **Authentication:** JWT (access + refresh tokens)
- **Authorization:** RBAC (roles + permissions)
- **Rate Limiting:** Redis-based
- **CORS:** Configurable origins
- **Security Headers:** HSTS, CSP, etc.
- **Secrets:** Environment variables + secret management

---

## 4. Configuración del Entorno de Desarrollo

### 4.1 Prerrequisitos

**Software requerido:**
- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Git
- Node.js 18+ (para frontend)
- Python 3.11 (o usar .venv311)
- PostgreSQL 15+ (opcional, usar Docker)
- Redis (opcional, usar Docker)

**Herramientas recomendadas:**
- VS Code con extensiones:
  - Python
  - Pylance
  - ESLint
  - Prettier
  - Docker
  - GitLens
- Git
- curl / Postman (para testing de API)

### 4.2 Clonar el Repositorio

```bash
# Clonar repositorio
git clone https://github.com/Gabrieldemarco/Nexorux-erp.git
cd Nexorux-erp

# Crear ramas para tu trabajo
git checkout -b feature/tu-feature
```

### 4.3 Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp backend/.env.example backend/.env

# Editar variables según necesidades
# backend/.env
```

**Variables críticas:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://nexorux:password@localhost:5432/nexorux_dev
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5

# Security
SECRET_KEY=tu-secret-key-aqui
JWT_SECRET_KEY=tu-jwt-secret-key-aqui
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# RLS
RLS_TENANT_CONTEXT_ENABLED=true

# Stock
STOCK_ALLOW_NEGATIVE=false

# DGI (opcional para desarrollo)
DGI_ENVIRONMENT=testing
DGI_CERT_PATH=/path/to/cert.pem
DGI_KEY_PATH=/path/to/key.pem
```

### 4.4 Iniciar Servicios de Desarrollo

```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar que estén corriendo
docker-compose ps

# Ver logs
docker-compose logs -f backend
```

### 4.5 Configurar Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev

# Acceder en http://localhost:5173
```

### 4.6 Configurar Backend

```bash
cd backend

# Crear entorno virtual (si no existe)
python -m venv .venv311

# Activar entorno virtual
# Windows
.venv311\Scripts\activate
# Linux/Mac
source .venv311/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Acceder en http://localhost:8000
```

### 4.7 Verificar Instalación

```bash
# Verificar health check
curl http://localhost:8000/health

# Verificar API health
curl http://localhost:8000/api/v1/health/

# Verificar frontend
# Abrir http://localhost:5173 en navegador
```

---

## 5. Estructura del Proyecto

### 5.1 Estructura de Directorios

```
nexorux-erp/
├── backend/
│   ├── app/
│   │   ├── api/              # API routers
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   ├── core/             # Core functionality
│   │   │   ├── config.py     # Configuration
│   │   │   └── security.py   # Security functions
│   │   ├── db/               # Database
│   │   │   └── session.py    # Database session
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Backend tests
│   ├── alembic/              # Database migrations
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend Docker image
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   ├── hooks/            # Custom hooks
│   │   ├── types/            # TypeScript types
│   │   ├── utils/            # Utility functions
│   │   ├── App.tsx           # Main app component
│   │   └── main.tsx          # Entry point
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite configuration
│   └── Dockerfile            # Frontend Docker image
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── .github/
│   └── workflows/            # GitHub Actions
├── docker-compose.yml        # Development compose
├── docker-compose.prod.yml   # Production compose
└── README.md                 # Project README
```

### 5.2 Backend: Estructura de API

```
app/api/v1/endpoints/
├── health.py                 # Health check endpoint
├── auth.py                   # Authentication endpoints
├── tenants.py                # Tenant CRUD
├── companies.py              # Company CRUD
├── users.py                  # User CRUD
├── customers.py              # Customer CRUD
├── suppliers.py              # Supplier CRUD
├── products.py               # Product CRUD
├── invoices.py               # Invoice CRUD
├── payments.py               # Payment CRUD
├── fiscal_documents.py       # Fiscal document CRUD
├── certificates.py           # Certificate CRUD
├── tax_configurations.py     # Tax configuration CRUD
└── ...
```

### 5.3 Frontend: Estructura de Páginas

```
src/pages/
├── Dashboard.tsx             # Dashboard
├── Login.tsx                 # Login page
├── Register.tsx              # Registration page
├── Tenants.tsx               # Tenant management
├── Companies.tsx             # Company management
├── Customers.tsx             # Customer management
├── Suppliers.tsx             # Supplier management
├── Products.tsx              # Product management
├── Invoices.tsx              # Invoice management
├── Payments.tsx              # Payment management
├── FiscalDocuments.tsx       # Fiscal document management
├── Certificates.tsx         # Certificate management
├── TaxConfigurations.tsx     # Tax configuration management
└── ...
```

---

## 6. Flujo de Trabajo

### 6.1 Branch Strategy

**Branches principales:**
- `main`: Producción (solo merges verificados)
- `develop`: Desarrollo (integración continua)

**Branches de feature:**
- `feature/tu-feature`: Nueva funcionalidad
- `fix/tu-fix`: Corrección de bug
- `hotfix/tu-hotfix`: Hotfix urgente para producción

### 6.2 Proceso de Desarrollo

1. **Crear branch:**
   ```bash
   git checkout -b feature/tu-feature
   ```

2. **Desarrollar:**
   - Escribir código
   - Escribir tests
   - Documentar cambios

3. **Commit:**
   ```bash
   git add .
   git commit -m "feat: add tu feature description"
   ```

4. **Push:**
   ```bash
   git push origin feature/tu-feature
   ```

5. **Pull Request:**
   - Crear PR en GitHub
   - Request review
   - Address feedback
   - Merge cuando aprobado

### 6.3 Convenciones de Commit

**Formato:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (sin lógica)
- `refactor`: Refactorización
- `perf`: Mejora de performance
- `test`: Agregar/modificar tests
- `chore`: Cambios en build process

**Ejemplos:**
```
feat(invoices): add invoice payment status

fix(auth): correct token expiration validation

docs(readme): update installation instructions

test(products): add product validation tests
```

### 6.4 Code Review

**Guidelines:**
- Todo código debe ser reviewado antes de merge
- Reviewers deben verificar:
  - Funcionalidad correcta
  - Tests suficientes
  - Documentación actualizada
  - Seguridad no comprometida
  - Performance aceptable
  - Code style consistente

**Checklist de review:**
- [ ] Funcionalidad implementada correctamente
- [ ] Tests agregados/actualizados
- [ ] Documentation actualizada
- [ ] No introduce nuevos warnings
- [ ] Linting pasa
- [ ] Security headers/validations presentes
- [ ] RLS enforcement verificado (si aplica)
- [ ] Multi-tenancy considerado (si aplica)

---

## 7. Convenios de Código

### 7.1 Python (Backend)

**Style:**
- Seguir PEP 8
- Usar black para formatting
- Usar flake8 para linting
- Usar mypy para type checking

**Naming:**
- Variables: `snake_case`
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Docstrings:**
```python
def calculate_tax(amount: float, rate: float) -> float:
    """
    Calculate tax amount based on rate.
    
    Args:
        amount: Base amount to calculate tax on
        rate: Tax rate as percentage (e.g., 22 for 22%)
    
    Returns:
        Tax amount
    
    Example:
        >>> calculate_tax(1000, 22)
        220.0
    """
    return amount * (rate / 100)
```

**Type hints:**
```python
from typing import Optional, List

def get_customers(
    db: Session,
    tenant_id: str,
    active_only: bool = True
) -> List[Customer]:
    pass
```

### 7.2 TypeScript (Frontend)

**Style:**
- Seguir Airbnb style guide
- Usar ESLint
- Usar Prettier
- Strict mode enabled

**Naming:**
- Variables: `camelCase`
- Functions: `camelCase`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Components: `PascalCase`

**Components:**
```typescript
interface CustomerListProps {
  customers: Customer[];
  onEdit: (customer: Customer) => void;
  onDelete: (customerId: string) => void;
}

export const CustomerList: React.FC<CustomerListProps> = ({
  customers,
  onEdit,
  onDelete,
}) => {
  // Component logic
};
```

### 7.3 SQL (Database)

**Naming:**
- Tables: `snake_case`
- Columns: `snake_case`
- Foreign keys: `table_id` (ej. `customer_id`)
- Indexes: `idx_table_column`
- Constraints: `constraint_name`

**Migrations:**
```python
# alembic/versions/xxxxx_add_customer_email_index.py
def upgrade():
    op.create_index(
        'idx_customer_email',
        'customer',
        ['email'],
        unique=True
    )

def downgrade():
    op.drop_index('idx_customer_email', 'customer')
```

---

## 8. Testing

### 8.1 Backend Testing

**Framework:** pytest

**Estructura de tests:**
```
tests/
├── conftest.py               # Test fixtures
├── test_auth.py              # Auth tests
├── test_customers.py         # Customer tests
├── test_invoices.py          # Invoice tests
├── test_fiscal.py            # Fiscal tests
└── ...
```

**Ejemplo de test:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_customer():
    response = client.post(
        "/api/v1/customers/",
        json={
            "name": "Test Customer",
            "email": "test@example.com",
            "rut": "12345678901"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

**Ejecutar tests:**
```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_customers.py

# Con coverage
pytest --cov=app

# Verbose
pytest -v
```

### 8.2 Frontend Testing

**Framework:** Vitest

**Estructura de tests:**
```
src/test/
├── setup.ts                  # Test setup
├── components.test.tsx       # Component tests
├── pages.test.tsx            # Page tests
└── services.test.ts         # Service tests
```

**Ejemplo de test:**
```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CustomerList } from '../components/CustomerList';

describe('CustomerList', () => {
  it('renders customer list', () => {
    const customers = [
      { id: '1', name: 'Customer 1', email: 'customer1@example.com' },
      { id: '2', name: 'Customer 2', email: 'customer2@example.com' },
    ];
    
    render(<CustomerList customers={customers} />);
    
    expect(screen.getByText('Customer 1')).toBeInTheDocument();
    expect(screen.getByText('Customer 2')).toBeInTheDocument();
  });
});
```

**Ejecutar tests:**
```bash
# Todos los tests
npm test

# Watch mode
npm test -- --watch

# Con coverage
npm test -- --coverage
```

### 8.3 E2E Testing

**Framework:** Playwright

**Estructura de tests:**
```
e2e/
├── auth.spec.ts              # Auth E2E tests
├── invoice.spec.ts           # Invoice E2E tests
└── ...
```

**Ejemplo de test:**
```typescript
import { test, expect } from '@playwright/test';

test('create invoice', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.click('text=Invoices');
  await page.click('text=Add Invoice');
  await page.fill('[name="customer_id"]', 'customer-1');
  await page.click('text=Save');
  await expect(page.locator('text=Invoice created')).toBeVisible();
});
```

**Ejecutar tests:**
```bash
# E2E tests
npx playwright test

# Headed mode
npx playwright test --headed

# Specific test
npx playwright test invoice.spec.ts
```

---

## 9. Despliegue

### 9.1 Development

**Iniciar servicios:**
```bash
docker-compose up -d
```

**Reiniciar servicios:**
```bash
docker-compose restart backend
```

**Ver logs:**
```bash
docker-compose logs -f backend
```

### 9.2 Production

**Archivo:** `docker-compose.prod.yml`

**Desplegar:**
```bash
# En servidor de producción
docker-compose -f docker-compose.prod.yml up -d

# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**Verificar health:**
```bash
curl https://tu-dominio.com/health
```

### 9.3 CI/CD

**GitHub Actions:** `.github/workflows/ci.yml`

**Pipeline ejecuta:**
- Linting (Python + TypeScript)
- Tests (Backend + Frontend)
- Type checking (TypeScript)
- Docker Compose validation
- Security scanning

**Para deployment manual:**
```bash
# Merge a main
git checkout main
git pull

# Build images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

---

## 10. Documentación

### 10.1 Documentación Técnica

**Documentos existentes:**
- `ARCHITECTURE.md` - Arquitectura del sistema
- `DATABASE.md` - Schema de base de datos
- `DGI_DISCOVERY.md` - Investigación DGI
- `DGI_COMPLIANCE_MATRIX.md` - Matriz de compliance DGI
- `RLS.md` - Row-Level Security
- `PRODUCTION.md` - Guía de producción
- `EMAIL.md` - Configuración de email
- `WOOCOMMERCE_CONNECTOR_MVP.md` - Conector WooCommerce

### 10.2 Documentación de Usuario

**Documentos existentes:**
- `USER_MANUAL.md` - Manual de usuario
- `TROUBLESHOOTING.md` - Manual de troubleshooting
- `RUNBOOKS.md` - Runbooks de incidentes
- `MONITORING.md` - Configuración de monitoreo
- `BACKUP_SCHEDULE.md` - Programación de backups

### 10.3 Documentación de API

**Generar con FastAPI:**
```bash
# Acceder a documentación Swagger
http://localhost:8000/docs

# Documentación ReDoc
http://localhost:8000/redoc
```

### 10.4 Actualizar Documentación

**Cuando actualizar:**
- Agregar nueva funcionalidad
- Cambiar arquitectura
- Cambiar proceso de despliegue
- Corregir errores en documentación existente

**Dónde actualizar:**
- Código: Docstrings y comentarios
- API: Descripción en endpoints
- Documentación: Archivos en `docs/`
- README: Instrucciones de instalación/uso

---

## 11. Primeros Pasos

### 11.1 Día 1: Setup

**Objetivos:**
- [ ] Configurar entorno de desarrollo
- [ ] Clonar repositorio
- [ ] Iniciar servicios Docker
- [ ] Ejecutar tests backend
- [ ] Ejecutar tests frontend
- [ ] Familiarizarse con código existente

**Tareas:**
1. Configurar entorno (sección 4)
2. Clonar repositorio
3. Iniciar `docker-compose up -d`
4. Ejecutar `pytest` en backend
5. Ejecutar `npm test` en frontend
6. Leer `ARCHITECTURE.md`
7. Leer `DATABASE.md`

### 11.2 Día 2: Exploración

**Objetivos:**
- [ ] Entender arquitectura
- [ ] Entender flujo de auth
- [ ] Entender multitenancy
- [ ] Entender RLS
- [ ] Hacer un pequeño cambio

**Tareas:**
1. Leer `ARCHITECTURE.md` completo
2. Leer `RLS.md`
3. Explorar código de auth (`app/api/v1/endpoints/auth.py`)
4. Explorar código de multitenancy (`app/core/security.py`)
5. Hacer un pequeño cambio (ej. agregar un endpoint simple)
6. Escribir test para el cambio
7. Hacer PR

### 11.3 Día 3: Funcionalidad

**Objetivos:**
- [ ] Entender módulo fiscal
- [ ] Entender facturación
- [ ] Entender inventario
- [ ] Hacer un feature pequeño

**Tareas:**
1. Leer `DGI_DISCOVERY.md`
2. Leer `DGI_COMPLIANCE_MATRIX.md`
3. Explorar código fiscal (`app/services/fiscal/`)
4. Explorar código de facturación (`app/api/v1/endpoints/invoices.py`)
5. Hacer un feature pequeño (ej. agregar un campo a customer)
6. Escribir tests
7. Hacer PR

### 11.4 Semana 1: Proyecto

**Objetivos:**
- [ ] Contribuir a un feature real
- [ ] Entender flujo de trabajo completo
- [ ] Participar en code review
- [ ] Contribuir a documentación

**Tareas:**
1. Elegir un issue o feature del backlog
2. Implementar
3. Escribir tests
4. Actualizar documentación
5. Hacer PR
6. Participar en review de otros
7. Participar en retrospectiva

---

## 12. Recursos

### 12.1 Documentación Interna

**Documentos críticos:**
- `README.md` - Resumen del proyecto
- `ARCHITECTURE.md` - Arquitectura detallada
- `DATABASE.md` - Schema de base de datos
- `DGI_DISCOVERY.md` - Investigación DGI
- `DGI_COMPLIANCE_MATRIX.md` - Compliance DGI
- `STATUS.md` - Estado actual del proyecto

### 12.2 Documentación Externa

**DGI (Uruguay):**
- Portal eFactura: https://www.efactura.dgi.gub.uy/
- Documentación técnica: https://www.gub.uy/direccion-general-impositiva/
- Servicios automatizados: https://servicios.dgi.gub.uy/

**Tecnologías:**
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker: https://docs.docker.com/

### 12.3 Comunicación

**Canales:**
- GitHub Issues: Reportar bugs y feature requests
- GitHub Discussions: Discusiones técnicas
- Email: [equipo email]
- Slack/Teams: [equipo workspace]

**Cuándo usar cada canal:**
- **GitHub Issues:** Bugs, feature requests, tareas
- **GitHub Discussions:** Preguntas técnicas, diseño
- **Email:** Asuntos privados o urgentes
- **Slack/Teams:** Chat diario, coordinación

### 12.4 Soporte

**Para ayuda técnica:**
- Revisar documentación existente
- Buscar en GitHub Issues
- Crear nuevo issue si no existe
- Pregregar en GitHub Discussions
- Contactar al equipo si es urgente

**Para ayuda DGI:**
- Portal de DGI
- Línea de atención DGI
- Guías de usuario DGI

---

## Checklist de Onboarding

### Semana 1

**Configuración:**
- [ ] Entorno de desarrollo configurado
- [ ] Docker instalado y funcionando
- [ ] Servicios corriendo correctamente
- [ ] Tests ejecutando correctamente

**Conocimiento:**
- [ ] Arquitectura entendida
- [ ] Stack tecnológico entendido
- [ ] Estructura de proyecto entendida
- [ ] Flujo de trabajo entendido

**Práctica:**
- [ ] Primer PR realizado
- [ ] Primer feature implementado
- [ ] Tests escritos
- [ ] Code review participado

### Semana 2

**Funcionalidad:**
- [ ] Auth y multitenancy entendidos
- [ ] Módulo fiscal entendido
- [ ] Facturación entendida
- [ ] Inventario entendido

**Calidad:**
- [ ] Linting configurado
- [ ] Type checking configurado
- [ ] Tests de integración escritos
- [ ] Documentación actualizada

### Semana 3

**Producción:**
- [ ] Despliegue entendido
- [ ] CI/CD entendido
- [ ] Monitoreo entendido
- [ ] Backups entendidos

**Independencia:**
- [ ] Feature completo implementado
- [ ] Documentación de feature escrita
- [ ] Presentación de feature realizada
- [ ] Mentoreo de otros desarrolladores

---

## Bienvenido al Equipo

¡Gracias por unirte al equipo de NEXORUX ERP! Estamos construyendo un sistema ERP profesional para Uruguay, y tu contribución es valiosa.

Si tienes preguntas, no dudes en preguntar. Estamos aquí para ayudarte a tener éxito.

**Contacto del equipo:**
- **Tech Lead:** [nombre y email]
- **Product Owner:** [nombre y email]
- **Team Lead:** [nombre y email]

---

**Versión de la guía:** 1.0  
**Última actualización:** 2026-08-13  
**Sistema:** NEXORUX ERP v0.1.0
