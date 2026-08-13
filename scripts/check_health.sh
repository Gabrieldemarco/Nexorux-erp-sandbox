#!/usr/bin/env bash
# Probe app health endpoints (local or public URL).
# Usage:
#   ./scripts/check_health.sh
#   HEALTH_URL=https://erp.example.com/health ./scripts/check_health.sh
set -euo pipefail

URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
FALLBACK="${HEALTH_FALLBACK_URL:-https://127.0.0.1/health}"

check() {
  local target="$1"
  local code
  code="$(curl -sk -o /tmp/nexorux_health_body.txt -w "%{http_code}" --connect-timeout 5 --max-time 10 "$target" || true)"
  if [[ "$code" == "200" ]]; then
    echo "OK $target → HTTP $code"
    cat /tmp/nexorux_health_body.txt
    echo
    return 0
  fi
  echo "FAIL $target → HTTP ${code:-000}"
  return 1
}

if check "$URL"; then
  exit 0
fi

if [[ "$URL" != "$FALLBACK" ]]; then
  check "$FALLBACK" && exit 0
fi

exit 1
