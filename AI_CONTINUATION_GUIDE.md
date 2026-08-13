# Guía de continuidad para la siguiente IA

> **Actualizado:** 2026-08-12
> **Fuente de verdad del estado del proyecto:** [`STATUS.md`](STATUS.md)

Este documento orienta a la siguiente persona o IA que continúe el desarrollo de Nexorux ERP.

---

## Estado actual (resumen)

El proyecto avanzó significativamente desde la FASE 0 inicial:

- **Backend**: ~107 endpoints, 20 modelos, RBAC completo, 104 tests passing
- **Frontend**: 12 páginas, auth funcional, listas de lectura (CRUD sin cablear)
- **Fiscal**: motor CFE completo en código, sin validación DGI real
- **Infra**: Docker Compose, CI/CD, rate limiter Redis en producción

Ver [`STATUS.md`](STATUS.md) para el detalle completo y verificado.

---

## Reglas para continuar

1. **Consultar `STATUS.md` primero** — no confiar en claims del README sin verificar
2. **No marcar requisitos DGI como verificados** sin evidencia en `compliance/dgi/evidence/`
3. **No escribir "homologado por DGI"** hasta tener aprobación oficial
4. **Mantener ERP separado del motor fiscal** — el adaptador DGI es intercambiable
5. **Usar Python 3.11** (`backend/.venv311`) — Python 3.14 es incompatible
6. **Correr tests antes de declarar algo como hecho**: `pytest tests/ -q`

---

## Tareas prioritarias (post Prioridad 1)

### Prioridad 2 — Frontend usable
- Cablear formularios CRUD en Products, Customers, Suppliers, Companies
- Implementar refresh token automático en el interceptor axios
- Agregar tests frontend (ProtectedRoute, AuthProvider, al menos una página CRUD)

### Prioridad 3 — Fiscal DGI real
- Descargar documentación oficial a `compliance/dgi/evidence/`
- Validar XML contra XSD oficial
- Primera prueba en sandbox ePrueba
- Completar `compliance/dgi/requirements.md` con referencias verificables

### Prioridad 4 — Seguridad
- Row Level Security (RLS) en PostgreSQL
- Lockout de cuenta en Redis (hoy en memoria)
- Audit log automático via middleware

---

## Archivos clave

| Archivo | Propósito |
|---------|-----------|
| `STATUS.md` | Estado verificado del proyecto |
| `DGI_DISCOVERY.md` | Investigación fiscal (conservador, honesto) |
| `DGI_COMPLIANCE_MATRIX.md` | Matriz de requisitos con estados reales |
| `ARCHITECTURE.md` | Diseño del sistema |
| `DATABASE.md` | Modelo de datos |
| `backend/app/services/fiscal/` | Motor fiscal CFE |
| `backend/scripts/seed_demo.py` | Datos de demo idempotentes |

---

## Documentos obsoletos o parcialmente desactualizados

- Este archivo reemplaza la versión anterior que describía solo Tenant/Company
- `RELEASE_NOTES.md` tiene conteos de tests desactualizados — verificar contra `STATUS.md`
- `compliance/dgi/requirements.md` es un esqueleto pendiente de completar

---

## Comandos útiles

```bash
# Backend tests
cd backend && .venv311\Scripts\python.exe -m pytest tests/ -q

# Frontend dev
cd frontend && npm run dev

# Docker
docker compose up -d

# Migrations
cd backend && alembic upgrade head

# Seed demo
cd backend && python scripts/seed_demo.py
```
