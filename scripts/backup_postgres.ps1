# Backup PostgreSQL from docker-compose.prod.yml into .\backups
# Optional off-host copy: $env:BACKUP_COPY_TO = "D:\Backups\nexorux"
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = if ($env:BACKUP_DIR) { $env:BACKUP_DIR } else { Join-Path $Root "backups" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Name = "nexorux_prod_$Stamp.sql.gz"
$OutFile = Join-Path $OutDir $Name

Write-Host "Backing up nexorux_prod -> $OutFile"
# Binary-safe: write inside postgres container (/backups is ./backups mount)
docker compose -f docker-compose.prod.yml exec -T postgres `
  sh -c "pg_dump -U nexorux -d nexorux_prod --no-owner --no-acl | gzip -c > /backups/$Name"
if ($LASTEXITCODE -ne 0) {
  throw "pg_dump failed with exit code $LASTEXITCODE"
}

$Keep = if ($env:BACKUP_KEEP) { [int]$env:BACKUP_KEEP } else { 14 }
Get-ChildItem "$OutDir\nexorux_prod_*.sql.gz" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -Skip $Keep |
  Remove-Item -Force

Write-Host "Done: $OutFile"

if ($env:BACKUP_COPY_TO) {
  New-Item -ItemType Directory -Force -Path $env:BACKUP_COPY_TO | Out-Null
  Copy-Item -Force $OutFile (Join-Path $env:BACKUP_COPY_TO $Name)
  Write-Host "Copied to off-host path: $($env:BACKUP_COPY_TO)"
}
