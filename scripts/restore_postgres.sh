#!/usr/bin/env bash
# Restore a gzipped pg_dump into the prod compose postgres.
# Usage: ./scripts/restore_postgres.sh backups/nexorux_prod_YYYYMMDD_HHMMSS.sql.gz
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DUMP="${1:-}"
if [[ -z "$DUMP" || ! -f "$DUMP" ]]; then
  echo "Usage: $0 path/to/nexorux_prod_YYYYMMDD_HHMMSS.sql.gz" >&2
  exit 1
fi

COMPOSE=(docker compose -f docker-compose.prod.yml)

echo "WARNING: this replaces data in nexorux_prod from $DUMP"
read -r -p "Type RESTORE to continue: " confirm
if [[ "$confirm" != "RESTORE" ]]; then
  echo "Aborted."
  exit 1
fi

gunzip -c "$DUMP" | "${COMPOSE[@]}" exec -T postgres \
  psql -U nexorux -d nexorux_prod -v ON_ERROR_STOP=1

echo "Restore finished from $DUMP"
