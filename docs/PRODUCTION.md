# Production operations — Nexorux ERP

## Stack (`docker-compose.prod.yml`)

| Service | Role |
|---------|------|
| caddy | TLS reverse proxy (80/443) → frontend + `/api` |
| frontend | Nginx static SPA |
| backend | FastAPI (`alembic upgrade` on start, `/health`) |
| celery | Async fiscal tasks (`RUN_MIGRATIONS=false`) |
| postgres | Primary DB (Docker secret password) |
| redis | Cache / Celery broker (Docker secret password) |

Secrets live in `./secrets/*.txt` (gitignored). See `secrets/README.md`.  
The backend entrypoint builds `DATABASE_URL` / `REDIS_URL` from `/run/secrets/*`.

## Quick start (prod compose)

```bash
mkdir -p secrets
openssl rand -base64 32 > secrets/db_password.txt
openssl rand -base64 32 > secrets/redis_password.txt
openssl rand -base64 48 > secrets/secret_key.txt

# Optional: public domain + SMTP
# export NEXORUX_DOMAIN=erp.tudominio.com
# export CADDY_ACME_EMAIL=ops@tudominio.com
# export NEXORUX_CORS_ORIGINS=https://erp.tudominio.com
# export NEXORUX_TRUSTED_HOSTS=erp.tudominio.com,localhost,127.0.0.1,backend
# export PASSWORD_RESET_URL_BASE=https://erp.tudominio.com/recover-password
# export SMTP_ENABLED=true SMTP_HOST=... SMTP_USER=... SMTP_FROM=...

docker compose -f docker-compose.prod.yml up -d --build
```

App URL: `https://localhost` (browser warning with `tls internal`) or your domain after removing `tls internal` from `Caddyfile`.

## TLS (Caddy)

- Default `Caddyfile` uses **`tls internal`** (self-signed) so localhost works offline.
- For a real public domain: set `NEXORUX_DOMAIN`, open 80/443, **remove `tls internal`**, restart Caddy — Let's Encrypt via ACME.

## Password recovery (SMTP)

Flow: correo **registrado** → se envía token al mail → usuario pega token / abre enlace → nueva contraseña.

1. Set `SMTP_ENABLED=true` and host/user/from (password via env or `SMTP_PASSWORD_FILE`).
2. Set `PASSWORD_RESET_URL_BASE` to the public UI URL ending in `/recover-password`.
3. Local: Mailpit (`docker compose up -d mailpit`) UI http://localhost:8025, SMTP `127.0.0.1:1025`.
4. Local sin Mailpit: `EMAIL_BACKEND=outbox` or DEBUG fallback writes `storage/mail_outbox/`.
5. With `DEBUG=false`, reset tokens are **never** returned in the API JSON.

## Migrations

Backend container runs `alembic upgrade head` when `RUN_MIGRATIONS=true` (default).  
Celery sets `RUN_MIGRATIONS=false`.

## Health / monitoring

```bash
curl -fk https://127.0.0.1/health
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f caddy backend
```

Suggested external checks every 1–5 min on `https://<host>/health`.  
Docker json-file logs rotate at 10m × 5 files per service.

## Backups

```bash
# Linux / macOS / Git Bash
chmod +x scripts/backup_postgres.sh
./scripts/backup_postgres.sh

# Windows PowerShell
powershell -File scripts/backup_postgres.ps1
```

Dumps land in `./backups/` (mounted on postgres as `/backups`).  
Retention: last 14 files (`BACKUP_KEEP` to override).

Cron example (daily 02:30):

```
30 2 * * * cd /path/to/nexorux-erp && ./scripts/backup_postgres.sh >> /var/log/nexorux-backup.log 2>&1
```

Restore sketch:

```bash
gunzip -c backups/nexorux_prod_YYYYMMDD_HHMMSS.sql.gz \
  | docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U nexorux -d nexorux_prod
```

## Checklist before go-live

- [ ] Rotate `secrets/db_password.txt`, `redis_password.txt`, `secret_key.txt`
- [ ] `DEBUG=false` (compose prod default)
- [ ] Public domain: DNS + remove `tls internal` + CORS/TRUSTED_HOSTS/PASSWORD_RESET_URL_BASE
- [ ] SMTP enabled and tested (password recovery email)
- [ ] Scheduled backups verified (restore drill once)
- [ ] DGI signing cert paths set if emitting live
- [ ] Change demo admin password
- [ ] Health URL monitored
- [ ] Confirm `RLS_TENANT_CONTEXT_ENABLED=true` and `STOCK_ALLOW_NEGATIVE=false`
