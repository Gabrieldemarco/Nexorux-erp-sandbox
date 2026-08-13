# Probe app health endpoints (local or public URL).
# Usage:
#   powershell -File scripts/check_health.ps1
#   $env:HEALTH_URL = "https://erp.example.com/health"; powershell -File scripts/check_health.ps1
$ErrorActionPreference = "Continue"

$Url = if ($env:HEALTH_URL) { $env:HEALTH_URL } else { "http://127.0.0.1:8000/health" }
$Fallback = if ($env:HEALTH_FALLBACK_URL) { $env:HEALTH_FALLBACK_URL } else { "https://127.0.0.1/health" }

function Test-HealthUrl([string]$Target) {
  try {
    $params = @{
      Uri             = $Target
      UseBasicParsing = $true
      TimeoutSec      = 10
    }
    # PowerShell 7+
    if ((Get-Command Invoke-WebRequest).Parameters.ContainsKey("SkipCertificateCheck")) {
      $params.SkipCertificateCheck = $true
    }
    $resp = Invoke-WebRequest @params
    if ([int]$resp.StatusCode -eq 200) {
      Write-Host "OK $Target → HTTP $($resp.StatusCode)"
      Write-Host $resp.Content
      return $true
    }
    Write-Host "FAIL $Target → HTTP $($resp.StatusCode)"
    return $false
  } catch {
    Write-Host "FAIL $Target → $($_.Exception.Message)"
    return $false
  }
}

if (Test-HealthUrl $Url) { exit 0 }
if ($Url -ne $Fallback -and (Test-HealthUrl $Fallback)) { exit 0 }
exit 1
