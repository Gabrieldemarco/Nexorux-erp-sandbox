# Release Notes

## [0.2.0] - 2024-01-15

### Added
- Production-ready Docker Compose configuration
- Deployment documentation
- Architecture documentation
- DGI compliance matrix
- Contribution guidelines
- Security hardening (headers, rate limiting, account lockout)
- RBAC enforcement on all endpoints
- Celery task for async CFE sending
- Frontend auth flow and dashboard
- CI/CD workflows for backend and frontend

### Changed
- Updated Python requirement to 3.11+
- Improved test coverage to 68 tests
- Enhanced validation with RUT/email/phone validators

### Fixed
- Python 3.14 compatibility issues
- InvoiceItem tenant/company scoping
- Fiscal document issue workflow

## [0.1.0] - 2024-01-01

### Added
- Initial project structure
- FastAPI backend boilerplate
- React + TypeScript frontend boilerplate
- Core ERP entities (products, customers, suppliers, etc.)
- DGI/CFE fiscal engine
- Basic CRUD operations
- Authentication and authorization
- Database migrations with Alembic
- Seed/demo data script
