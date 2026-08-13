#!/bin/sh
set -eu

# Ensure writable storage (named volumes often mount as root)
mkdir -p /app/storage
if id appuser >/dev/null 2>&1; then
  chown -R appuser:appuser /app/storage 2>/dev/null || true
fi

# Load Docker secret files into env when present
if [ -n "${SECRET_KEY_FILE:-}" ] && [ -f "${SECRET_KEY_FILE}" ]; then
  export SECRET_KEY="$(cat "${SECRET_KEY_FILE}")"
fi
if [ -n "${DB_PASSWORD_FILE:-}" ] && [ -f "${DB_PASSWORD_FILE}" ]; then
  DB_PASSWORD="$(cat "${DB_PASSWORD_FILE}")"
  export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://nexorux:${DB_PASSWORD}@postgres:5432/nexorux_prod}"
fi
if [ -n "${REDIS_PASSWORD_FILE:-}" ] && [ -f "${REDIS_PASSWORD_FILE}" ]; then
  REDIS_PASSWORD="$(cat "${REDIS_PASSWORD_FILE}")"
  export REDIS_URL="${REDIS_URL:-redis://:${REDIS_PASSWORD}@redis:6379/0}"
fi
if [ -n "${SMTP_PASSWORD_FILE:-}" ] && [ -f "${SMTP_PASSWORD_FILE}" ]; then
  export SMTP_PASSWORD="$(cat "${SMTP_PASSWORD_FILE}")"
fi

if [ -z "${DATABASE_URL:-}" ] && [ -f /run/secrets/db_password ]; then
  export DATABASE_URL="postgresql+asyncpg://nexorux:$(cat /run/secrets/db_password)@postgres:5432/nexorux_prod"
fi
if [ -z "${REDIS_URL:-}" ] && [ -f /run/secrets/redis_password ]; then
  export REDIS_URL="redis://:$(cat /run/secrets/redis_password)@redis:6379/0"
fi
if [ -z "${SECRET_KEY:-}" ] && [ -f /run/secrets/secret_key ]; then
  export SECRET_KEY="$(cat /run/secrets/secret_key)"
fi

RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
if [ "${RUN_MIGRATIONS}" = "true" ]; then
  echo "Running alembic upgrade head..."
  alembic upgrade head
fi

drop_to_appuser() {
  if id appuser >/dev/null 2>&1 && [ "$(id -u)" = "0" ] && command -v gosu >/dev/null 2>&1; then
    exec gosu appuser "$@"
  fi
  exec "$@"
}

if [ "$#" -gt 0 ]; then
  drop_to_appuser "$@"
fi

WORKERS="${UVICORN_WORKERS:-4}"
drop_to_appuser uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WORKERS}"
