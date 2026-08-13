#!/usr/bin/env bash
# Backup PostgreSQL from docker-compose.prod.yml into ./backups
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${BACKUP_DIR:-$ROOT/backups}"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/nexorux_prod_${STAMP}.sql.gz"

COMPOSE=(docker compose -f docker-compose.prod.yml)

echo "Backing up nexorux_prod → $OUT_FILE"
"${COMPOSE[@]}" exec -T postgres \
  pg_dump -U nexorux -d nexorux_prod --no-owner --no-acl \
  | gzip -c > "$OUT_FILE"

# Keep last 14 dumps by default
KEEP="${BACKUP_KEEP:-14}"
ls -1t "$OUT_DIR"/nexorux_prod_*.sql.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | xargs -r rm -f

echo "Done: $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"
