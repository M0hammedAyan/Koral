param(
  [ValidateSet("cpu","memory","storage","log_error","all")]
  [string]$Target = "all",
  [string]$HostBase = "http://localhost"
)

$map = @{
  cpu      = 8001
  memory   = 8002
  storage  = 8003
  log_error = 8004
}

function Invoke-Spike($name) {
  $port = $map[$name]
  $url = "$HostBase`:$port/debug/spike"
  Write-Host "Triggering spike on $name via $url"
  try {
    Invoke-RestMethod -Method Post -Uri $url | Out-Host
  } catch {
    Write-Host "FAILED: $name ($($_.Exception.Message))"
  }
}

if ($Target -eq "all") {
  Invoke-Spike "cpu"
  Start-Sleep -Seconds 1
  Invoke-Spike "memory"
  Start-Sleep -Seconds 1
  Invoke-Spike "storage"
  Start-Sleep -Seconds 1
  Invoke-Spike "log_error"
} else {
  Invoke-Spike $Target
}

