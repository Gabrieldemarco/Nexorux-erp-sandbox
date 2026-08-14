# Backup Schedule Configuration Guide

## Overview

This guide explains how to configure automated backups for NEXORUX ERP using cron jobs (Linux) or Task Scheduler (Windows).

## Prerequisites

- **Linux:** cron installed (default on most Linux distributions)
- **Windows:** PowerShell with Task Scheduler access
- **Scripts:** Backup and health check scripts must be executable

## Linux Setup (Cron Jobs)

### Quick Setup

Run the setup script:

```bash
cd /path/to/nexorux-erp
sudo ./scripts/setup_cron.sh
```

This will configure:
1. **Daily backup** at 2:00 AM
2. **Health check** every 5 minutes
3. **Log cleanup** weekly (Sundays at 3:00 AM)

### Manual Cron Configuration

If you prefer manual configuration:

```bash
# Edit crontab
crontab -e
```

Add these lines:

```bash
# Daily backup at 2:00 AM
0 2 * * * cd /path/to/nexorux-erp && ./scripts/backup_postgres.sh >> /path/to/nexorux-erp/backups/backup.log 2>&1

# Health check every 5 minutes
*/5 * * * * cd /path/to/nexorux-erp && ./scripts/check_health.sh >> /path/to/nexorux-erp/backups/health.log 2>&1

# Weekly log cleanup (Sundays at 3:00 AM)
0 3 * * 0 cd /path/to/nexorux-erp && find ./backups -name '*.log' -mtime +30 -delete
```

### Verify Cron Jobs

```bash
# List current cron jobs
crontab -l

# View cron logs
tail -f /path/to/nexorux-erp/backups/backup.log
tail -f /path/to/nexorux-erp/backups/health.log
```

## Windows Setup (Task Scheduler)

### Quick Setup

Run the setup script as Administrator:

```powershell
cd C:\path\to\nexorux-erp
.\scripts\setup_cron.ps1
```

This will configure:
1. **Daily backup** at 2:00 AM
2. **Health check** every 5 minutes
3. **Log cleanup** weekly (Sundays at 3:00 AM)

### Manual Task Scheduler Configuration

If you prefer manual configuration:

1. Open **Task Scheduler** (taskschd.msc)
2. Create the following tasks:

#### Task 1: Daily Backup

- **Name:** NexoruxBackup_Daily
- **Trigger:** Daily at 2:00 AM
- **Action:** Start a program
  - **Program:** PowerShell.exe
  - **Arguments:** `-File "C:\path\to\nexorux-erp\scripts\backup_postgres.ps1" >> "C:\path\to\nexorux-erp\backups\backup.log" 2>&1`
  - **Start in:** C:\path\to\nexorux-erp
- **Settings:**
  - Run whether user is logged on or not
  - Do not stop if the task runs on batteries

#### Task 2: Health Check

- **Name:** NexoruxHealthCheck
- **Trigger:** Daily, repeat every 5 minutes
- **Action:** Start a program
  - **Program:** PowerShell.exe
  - **Arguments:** `-File "C:\path\to\nexorux-erp\scripts\check_health.ps1" >> "C:\path\to\nexorux-erp\backups\health.log" 2>&1`
  - **Start in:** C:\path\to\nexorux-erp
- **Settings:**
  - Run whether user is logged on or not
  - Do not stop if the task runs on batteries

#### Task 3: Log Cleanup

- **Name:** NexoruxLogCleanup
- **Trigger:** Weekly on Sundays at 3:00 AM
- **Action:** Start a program
  - **Program:** PowerShell.exe
  - **Arguments:** `Get-ChildItem -Path "C:\path\to\nexorux-erp\backups" -Filter '*.log' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force`
  - **Start in:** C:\path\to\nexorux-erp\backups
- **Settings:**
  - Run whether user is logged on or not

### Verify Task Scheduler

```powershell
# List all tasks
Get-ScheduledTask

# View task details
Get-ScheduledTask -TaskName NexoruxBackup_Daily

# View task history
Get-ScheduledTaskInfo -TaskName NexoruxBackup_Daily | Select-Object -ExpandProperty TaskExecutionHistory
```

## Backup Configuration

### Environment Variables

Configure backup behavior with environment variables:

```bash
# Backup directory (default: ./backups)
BACKUP_DIR=/path/to/backups

# Number of backups to keep (default: 14)
BACKUP_KEEP=30

# Off-host copy destination (optional)
BACKUP_COPY_TO=/mnt/nas/nexorux

# Database name (default: nexorux_prod)
DB_NAME=nexorux_prod
```

### Backup Retention

By default, the backup script keeps the last 14 backups. To change this:

```bash
# Keep last 30 backups
BACKUP_KEEP=30 ./scripts/backup_postgres.sh
```

### Off-Host Backup

To copy backups to an off-host location (NAS, cloud storage, etc.):

```bash
# Linux
BACKUP_COPY_TO=/mnt/nas/nexorux ./scripts/backup_postgres.sh

# Windows (set environment variable before running script)
$env:BACKUP_COPY_TO = "\\nas\nexorux"
.\scripts\backup_postgres.ps1
```

## Health Check Configuration

### Environment Variables

Configure health check behavior:

```bash
# Primary health endpoint (default: http://127.0.0.1:8000/health)
HEALTH_URL=https://your-domain.com/health

# Fallback health endpoint (default: https://127.0.0.1/health)
HEALTH_FALLBACK_URL=https://your-domain.com/api/v1/health/
```

### Health Check Interval

Recommended intervals:
- **Development:** Every 10 minutes
- **Staging:** Every 5 minutes
- **Production:** Every 1 minute

## Monitoring Backup Success

### Linux (Cron Logs)

```bash
# View backup logs
tail -f /path/to/nexorux-erp/backups/backup.log

# Check last backup
ls -lt /path/to/nexorux-erp/backups/nexorux_prod_*.sql.gz | head -1
```

### Windows (Task Scheduler)

```powershell
# View backup logs
Get-Content C:\path\to\nexorux-erp\backups\backup.log -Tail 20

# Check last backup
Get-ChildItem C:\path\to\nexorux-erp\backups\nexorux_prod_*.sql.gz | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### External Monitoring

Configure external monitoring (UptimeRobot, etc.) to:
1. Monitor the `/health` endpoint
2. Send alerts if the endpoint is down
3. Monitor backup file creation in the backups directory

## Restore Procedure

### Automated Restore Test

Schedule a monthly restore test to verify backup integrity:

```bash
# Linux cron (monthly on first day at 4:00 AM)
0 4 1 * * cd /path/to/nexorux-erp && ./scripts/restore_postgres.sh >> /path/to/nexorux-erp/backups/restore.log 2>&1

# Windows Task Scheduler (monthly on first day at 4:00 AM)
# Create task: NexoruxRestoreTest
# Trigger: Monthly on day 1 at 4:00 AM
# Action: PowerShell.exe -File "C:\path\to\nexorux-erp\scripts\restore_postgres.ps1"
```

### Manual Restore

```bash
# Linux
cd /path/to/nexorux-erp
./scripts/restore_postgres.sh

# Windows
cd C:\path\to\nexorux-erp
.\scripts\restore_postgres.ps1
```

## Troubleshooting

### Cron Job Not Running

**Check:**
```bash
# Check if cron service is running
sudo systemctl status cron

# Check cron logs
sudo grep CRON /var/log/syslog

# Verify script permissions
ls -la /path/to/nexorux-erp/scripts/backup_postgres.sh
```

**Fix:**
```bash
# Make script executable
chmod +x /path/to/nexorux-erp/scripts/backup_postgres.sh

# Restart cron service
sudo systemctl restart cron
```

### Task Scheduler Not Running

**Check:**
```powershell
# Check if task exists
Get-ScheduledTask -TaskName NexoruxBackup_Daily

# Check task history
Get-ScheduledTaskInfo -TaskName NexoruxBackup_Daily | Select-Object -ExpandProperty TaskExecutionHistory
```

**Fix:**
- Verify the task is enabled
- Check the account running the task has appropriate permissions
- Verify the script path is correct
- Check the task history for error messages

### Backup File Not Created

**Check:**
```bash
# Check disk space
df -h

# Check backup directory permissions
ls -la /path/to/nexorux-erp/backups

# Check database connectivity
docker exec nexorux-postgres pg_isready -U nexorux
```

**Fix:**
- Ensure sufficient disk space
- Verify directory permissions
- Verify Docker containers are running
- Check database credentials

### Health Check Failing

**Check:**
```bash
# Test health endpoint manually
curl http://localhost:8000/health

# Check backend logs
docker-compose logs backend

# Check database connection
docker-compose exec postgres pg_isready -U nexorux
```

**Fix:**
- Verify backend service is running
- Check database connectivity
- Verify environment variables
- Check firewall rules

## Best Practices

### Backup Schedule

- **Daily backups:** Minimum requirement
- **Weekly full backups:** Recommended for production
- **Incremental backups:** Consider for large databases
- **Off-site copies:** Critical for disaster recovery

### Backup Verification

- **Weekly:** Verify backup files are being created
- **Monthly:** Perform a restore test
- **Quarterly:** Review backup retention policy
- **Annually:** Test disaster recovery procedure

### Monitoring

- **Immediate:** Alert on backup failure
- **Daily:** Review backup logs
- **Weekly:** Review backup size trends
- **Monthly:** Review retention compliance

### Security

- **Encrypt backups:** For sensitive data
- **Secure backup location:** Restrict access
- **Rotate encryption keys:** Regularly
- **Audit backup access:** Log who accesses backups

## Related Documentation

- [PRODUCTION.md](./PRODUCTION.md) - Production deployment guide
- [MONITORING.md](./MONITORING.md) - Monitoring configuration
- [backup_postgres.sh](../scripts/backup_postgres.sh) - Backup script
- [restore_postgres.sh](../scripts/restore_postgres.sh) - Restore script
- [check_health.sh](../scripts/check_health.sh) - Health check script

---

**Last Updated:** 2026-08-13
