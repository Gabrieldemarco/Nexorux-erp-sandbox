#!/usr/bin/env bash
# Setup automated backup cron jobs for NEXORUX ERP
# Usage: sudo ./scripts/setup_cron.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Setting up automated backup cron jobs for NEXORUX ERP..."

# Install cron if not present (Debian/Ubuntu)
if ! command -v crontab &> /dev/null; then
    echo "Installing cron..."
    sudo apt-get update
    sudo apt-get install -y cron
fi

# Create cron job for daily backup at 2:00 AM
CRON_JOB="0 2 * * * cd $ROOT && ./scripts/backup_postgres.sh >> $ROOT/backups/backup.log 2>&1"

# Add to crontab if not already present
if crontab -l 2>/dev/null | grep -q "backup_postgres.sh"; then
    echo "Cron job for backup_postgres.sh already exists"
else
    echo "Adding cron job for daily backup at 2:00 AM..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
fi

# Create cron job for health check every 5 minutes
HEALTH_CRON="*/5 * * * * cd $ROOT && ./scripts/check_health.sh >> $ROOT/backups/health.log 2>&1"

if crontab -l 2>/dev/null | grep -q "check_health.sh"; then
    echo "Cron job for check_health.sh already exists"
else
    echo "Adding cron job for health check every 5 minutes..."
    (crontab -l 2>/dev/null; echo "$HEALTH_CRON") | crontab -
fi

# Create cron job for weekly cleanup of old logs (Sundays at 3:00 AM)
LOG_CLEANUP="0 3 * * 0 cd $ROOT && find ./backups -name '*.log' -mtime +30 -delete"

if crontab -l 2>/dev/null | grep -q "log cleanup"; then
    echo "Cron job for log cleanup already exists"
else
    echo "Adding cron job for weekly log cleanup..."
    (crontab -l 2>/dev/null; echo "$LOG_CLEANUP") | crontab -
fi

echo "Cron jobs configured successfully!"
echo ""
echo "Current crontab:"
crontab -l
echo ""
echo "To edit crontab manually: crontab -e"
echo "To view cron logs: tail -f $ROOT/backups/backup.log"
