import os
import sys
import asyncio
import httpx
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

FLUENTD_HOST = os.getenv("FLUENTD_HOST", "fluentd")
FLUENTD_PORT = os.getenv("FLUENTD_PORT", "9880")
NAMESPACE = os.getenv("NAMESPACE", "koral-system")
POD_NAME = os.getenv("POD_NAME", "log-agent")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

QUERY = 'sum(increase(fluentd_output_status_emit_records_total{tag=~"koral.*"}[1m]))'


class LogAgent(BaseAgent):
    def __init__(self):
        super().__init__(metric="log_error", pod=POD_NAME, unit="count")

    async def fetch_value(self) -> float:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": QUERY})
                results = r.json().get("data", {}).get("result", [])
                if results:
                    return float(results[0]["value"][1])
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"http://{FLUENTD_HOST}:{FLUENTD_PORT}/api/plugins.json")
                plugins = r.json().get("plugins", [])
                return float(sum(
                    p.get("emit_records", 0)
                    for p in plugins
                    if "error" in p.get("tag", "").lower()
                ))
        except Exception:
            return 0.0


if __name__ == "__main__":
    asyncio.run(LogAgent().run())
