# Deployment Guide

This guide covers production deployment of NEXORUX ERP.

## Prerequisites

- Docker and Docker Compose
- A server with at least 2GB RAM and 20GB disk
- Domain name configured with DNS pointing to your server
- TLS certificate (Let's Encrypt recommended)

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url> /opt/nexorux-erp
cd /opt/nexorux-erp
```

### 2. Create secrets

```bash
mkdir -p secrets
chmod 600 secrets

# Database password
openssl rand -hex 32 > secrets/db_password.txt

# Redis password
openssl rand -hex 32 > secrets/redis_password.txt

# JWT secret key (at least 32 bytes)
openssl rand -hex 32 > secrets/secret_key.txt
```

### 3. Configure environment

Edit `docker-compose.prod.yml` if needed:
- Update domain names in Traefik labels
- Update worker count for backend
- Adjust resource limits

### 4. Deploy

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 5. Run migrations

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 6. Seed demo data (optional)

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_demo.py
```

## Architecture

```
Internet
    |
    +---> Traefik (reverse proxy, TLS termination)
            |
            +---> Frontend (port 3000)
            +---> Backend API (port 8000)
            +---> API Docs (port 8000/docs)
```

## Security

### Secrets Management

Never commit secrets to version control. Use one of:

1. **Docker secrets** (recommended for single-server deployments)
2. **HashiCorp Vault** (for multi-server, enterprise)
3. **AWS Secrets Manager / GCP Secret Manager** (for cloud deployments)
4. **Kubernetes Secrets** (if deploying to K8s)

### Firewall

```bash
# Allow only necessary ports
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP (redirects to HTTPS)
ufw allow 443/tcp     # HTTPS
ufw enable
```

### SSL/TLS

Use Let's Encrypt with Traefik:

```bash
# Traefik will automatically obtain and renew certificates
# Ensure DNS is configured before starting
```

## Monitoring

### Health Checks

- Backend: `GET /health`
- Frontend: `GET /health` (if configured)
- Database: PostgreSQL healthcheck in compose file
- Redis: Redis healthcheck in compose file

### Logs

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Structured logging is enabled by default (JSON format)
```

## Backup

### Database Backup

```bash
# Daily backup script
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U nexorux nexorux_prod > backup_$(date +%Y%m%d).sql
```

### Redis Backup

Redis data is persisted in the `redis_data` volume. To backup:

```bash
docker compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE
docker cp nexorux-redis-prod:/data/dump.rdb ./redis_backup.rdb
```

## Scaling

### Backend Workers

Adjust the `--workers` flag in `docker-compose.prod.yml`:

```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Rule of thumb: `(2 * num_cores) + 1`

### Database

For production, consider:
- Connection pooling (pgBouncer)
- Read replicas for reporting
- Automated backups

## Troubleshooting

### Backend won't start

Check logs:
```bash
docker compose -f docker-compose.prod.yml logs backend
```

Common issues:
- Database not ready: wait for healthcheck or restart
- Missing secrets: verify `/run/secrets/*` files exist
- Port already in use: change host port mapping

### Frontend can't connect to backend

Verify:
- Backend is healthy: `curl http://localhost:8000/health`
- CORS configuration includes frontend domain
- Network mode allows communication

## Updates

```bash
cd /opt/nexorux-erp
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```
