import os
import asyncio
import httpx
from base_agent import BaseAgent

FLUENTD_HOST = os.getenv("FLUENTD_HOST", "fluentd")
FLUENTD_PORT = os.getenv("FLUENTD_PORT", "9880")  # Fluentd HTTP input port
NAMESPACE = os.getenv("NAMESPACE", "koral-system")
POD_NAME = os.getenv("POD_NAME", "log-agent")

# Prometheus query for error log count via Fluentd metrics (if available)
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
QUERY = f'sum(increase(fluentd_output_status_emit_records_total{{tag=~"koral.*"}}[1m]))'


class LogAgent(BaseAgent):
    def __init__(self):
        super().__init__(metric="logs", pod=POD_NAME)
        self._error_count = 0.0

    async def fetch_value(self) -> float:
        # Try Prometheus fluentd metrics first
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": QUERY})
                results = r.json().get("data", {}).get("result", [])
                if results:
                    return float(results[0]["value"][1])
        except Exception:
            pass

        # Fallback: query Fluentd HTTP input for error count
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(
                    f"http://{FLUENTD_HOST}:{FLUENTD_PORT}/api/plugins.json"
                )
                plugins = r.json().get("plugins", [])
                error_count = sum(
                    p.get("emit_records", 0)
                    for p in plugins
                    if "error" in p.get("tag", "").lower()
                )
                return float(error_count)
        except Exception:
            return 0.0


if __name__ == "__main__":
    asyncio.run(LogAgent().run())
