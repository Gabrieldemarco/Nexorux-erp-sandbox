# Backup PostgreSQL from docker-compose.prod.yml into .\backups
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = if ($env:BACKUP_DIR) { $env:BACKUP_DIR } else { Join-Path $Root "backups" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$OutFile = Join-Path $OutDir "nexorux_prod_$Stamp.sql"

Write-Host "Backing up nexorux_prod -> $OutFile"
docker compose -f docker-compose.prod.yml exec -T postgres `
  pg_dump -U nexorux -d nexorux_prod --no-owner --no-acl `
  | Set-Content -Path $OutFile -Encoding utf8

# Keep last 14 dumps
$Keep = if ($env:BACKUP_KEEP) { [int]$env:BACKUP_KEEP } else { 14 }
Get-ChildItem "$OutDir\nexorux_prod_*.sql" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -Skip $Keep |
  Remove-Item -Force

Write-Host "Done: $OutFile"
