#!/usr/bin/env bash
# Backup PostgreSQL from docker-compose.prod.yml into ./backups
# Optional off-host copy: set BACKUP_COPY_TO=/mnt/nas/nexorux
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${BACKUP_DIR:-$ROOT/backups}"
mkdir -p "$OUT_DIR"
NAME="nexorux_prod_${STAMP}.sql.gz"
OUT_FILE="$OUT_DIR/$NAME"

COMPOSE=(docker compose -f docker-compose.prod.yml)

echo "Backing up nexorux_prod → $OUT_FILE"
# Write inside the container volume mount ./backups → /backups (binary-safe)
"${COMPOSE[@]}" exec -T postgres \
  sh -c "pg_dump -U nexorux -d nexorux_prod --no-owner --no-acl | gzip -c > /backups/$NAME"

# Keep last 14 dumps by default
KEEP="${BACKUP_KEEP:-14}"
ls -1t "$OUT_DIR"/nexorux_prod_*.sql.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | xargs -r rm -f

echo "Done: $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"

if [[ -n "${BACKUP_COPY_TO:-}" ]]; then
  mkdir -p "$BACKUP_COPY_TO"
  cp -f "$OUT_FILE" "$BACKUP_COPY_TO/"
  echo "Copied to off-host path: $BACKUP_COPY_TO/$NAME"
fi
