param(
  [string]$Backend = "http://localhost:8000",
  [string]$Prometheus = "http://localhost:9090",
  [string]$Grafana = "http://localhost:3001",
  [string]$Frontend = "http://localhost:3000"
)

$checks = @(
  @{ name="backend"; url="$Backend/health" },
  @{ name="correlation-engine"; url="http://localhost:8005/health" },
  @{ name="ai-engine"; url="http://localhost:8006/health" },
  @{ name="cpu-agent"; url="http://localhost:8001/health" },
  @{ name="memory-agent"; url="http://localhost:8002/health" },
  @{ name="storage-agent"; url="http://localhost:8003/health" },
  @{ name="log-agent"; url="http://localhost:8004/health" },
  @{ name="prometheus"; url="$Prometheus/-/healthy" },
  @{ name="grafana"; url="$Grafana/api/health" }
)

foreach ($c in $checks) {
  Write-Host "Checking $($c.name) -> $($c.url)"
  try {
    $resp = Invoke-RestMethod -Uri $c.url -TimeoutSec 5
    $resp | ConvertTo-Json -Depth 5 | Write-Host
  } catch {
    Write-Host "FAILED: $($c.name) ($($_.Exception.Message))"
  }
  Write-Host ""
}

Write-Host "Open URLs:"
Write-Host "Frontend:  $Frontend"
Write-Host "Prometheus: $Prometheus/targets"
Write-Host "Grafana:   $Grafana (admin / configured password)"

