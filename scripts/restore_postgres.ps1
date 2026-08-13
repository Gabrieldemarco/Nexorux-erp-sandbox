# Restore a gzipped pg_dump into the prod compose postgres.
# Usage: powershell -File scripts/restore_postgres.ps1 -DumpFile backups\nexorux_prod_....sql.gz
param(
  [Parameter(Mandatory = $true)]
  [string]$DumpFile,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path $DumpFile)) {
  throw "Dump file not found: $DumpFile"
}

if (-not $Force) {
  $confirm = Read-Host "WARNING: replaces nexorux_prod. Type RESTORE to continue"
  if ($confirm -ne "RESTORE") {
    Write-Host "Aborted."
    exit 1
  }
}

Write-Host "Restoring from $DumpFile ..."
$fs = [System.IO.File]::OpenRead((Resolve-Path $DumpFile))
try {
  $gz = New-Object System.IO.Compression.GZipStream($fs, [System.IO.Compression.CompressionMode]::Decompress)
  try {
    $reader = New-Object System.IO.StreamReader($gz)
    $sql = $reader.ReadToEnd()
    $reader.Dispose()
  } finally {
    $gz.Dispose()
  }
} finally {
  $fs.Dispose()
}

$sql | docker compose -f docker-compose.prod.yml exec -T postgres `
  psql -U nexorux -d nexorux_prod -v ON_ERROR_STOP=1
if ($LASTEXITCODE -ne 0) {
  throw "psql restore failed with exit code $LASTEXITCODE"
}

Write-Host "Restore finished from $DumpFile"
