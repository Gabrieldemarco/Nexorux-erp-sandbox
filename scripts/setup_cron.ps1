# Setup automated backup scheduled tasks for NEXORUX ERP (Windows)
# Usage: .\scripts\setup_cron.ps1 (Run as Administrator)

$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ROOT

Write-Host "Setting up automated backup scheduled tasks for NEXORUX ERP..." -ForegroundColor Green

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    exit 1
}

# Create backups directory if it doesn't exist
$backupDir = Join-Path $ROOT "backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "Created backup directory: $backupDir" -ForegroundColor Green
}

# Task 1: Daily backup at 2:00 AM
$taskName = "NexoruxBackup_Daily"
$backupScript = Join-Path $ROOT "scripts\backup_postgres.ps1"
$logFile = Join-Path $backupDir "backup.log"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Write-Host "Scheduled task '$taskName' already exists" -ForegroundColor Yellow
} else {
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"$backupScript`" >> `"$logFile`" 2>&1" -WorkingDirectory $ROOT
    $trigger = New-ScheduledTaskTrigger -Daily -At 2am
    $settings = New-ScheduledTaskSettings -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Daily backup of NEXORUX ERP database" -Force | Out-Null
    Write-Host "Created scheduled task: $taskName (Daily at 2:00 AM)" -ForegroundColor Green
}

# Task 2: Health check every 5 minutes
$healthTaskName = "NexoruxHealthCheck"
$healthScript = Join-Path $ROOT "scripts\check_health.ps1"
$healthLogFile = Join-Path $backupDir "health.log"

if (Get-ScheduledTask -TaskName $healthTaskName -ErrorAction SilentlyContinue) {
    Write-Host "Scheduled task '$healthTaskName' already exists" -ForegroundColor Yellow
} else {
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"$healthScript`" >> `"$healthLogFile`" 2>&1" -WorkingDirectory $ROOT
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
    $settings = New-ScheduledTaskSettings -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $healthTaskName -Action $action -Trigger $trigger -Settings $settings -Description "Health check every 5 minutes for NEXORUX ERP" -Force | Out-Null
    Write-Host "Created scheduled task: $healthTaskName (Every 5 minutes)" -ForegroundColor Green
}

# Task 3: Weekly log cleanup (Sundays at 3:00 AM)
$logCleanupTaskName = "NexoruxLogCleanup"

if (Get-ScheduledTask -TaskName $logCleanupTaskName -ErrorAction SilentlyContinue) {
    Write-Host "Scheduled task '$logCleanupTaskName' already exists" -ForegroundColor Yellow
} else {
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "Get-ChildItem -Path `"$backupDir` -Filter '*.log' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force" -WorkingDirectory $backupDir
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
    $settings = New-ScheduledTaskSettings -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $logCleanupTaskName -Action $action -Trigger $trigger -Settings $settings -Description "Weekly cleanup of old log files (older than 30 days)" -Force | Out-Null
    Write-Host "Created scheduled task: $logCleanupTaskName (Weekly on Sundays at 3:00 AM)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Scheduled tasks configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To view scheduled tasks:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask" -ForegroundColor White
Write-Host ""
Write-Host "To view task details:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask -TaskName NexoruxBackup_Daily" -ForegroundColor White
Write-Host ""
Write-Host "To run backup manually:" -ForegroundColor Cyan
Write-Host "  .\scripts\backup_postgres.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To view backup logs:" -ForegroundColor Cyan
Write-Host "  Get-Content $backupDir\backup.log -Tail 20" -ForegroundColor White
Write-Host ""
Write-Host "To remove scheduled tasks:" -ForegroundColor Cyan
Write-Host "  Unregister-ScheduledTask -TaskName NexoruxBackup_Daily" -ForegroundColor White
Write-Host "  Unregister-ScheduledTask -TaskName NexoruxHealthCheck" -ForegroundColor White
Write-Host "  Unregister-ScheduledTask -TaskName NexoruxLogCleanup" -ForegroundColor White
