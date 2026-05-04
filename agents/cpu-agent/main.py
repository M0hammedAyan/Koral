import os
import asyncio
import httpx
from base_agent import BaseAgent

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
NAMESPACE = os.getenv("NAMESPACE", "koral-system")
POD_NAME = os.getenv("POD_NAME", "cpu-agent")

QUERY = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{NAMESPACE}"}}[1m])) by (pod)'


class CpuAgent(BaseAgent):
    def __init__(self):
        super().__init__(metric="cpu", pod=POD_NAME)

    async def fetch_value(self) -> float:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": QUERY})
            results = r.json().get("data", {}).get("result", [])
            if not results:
                return 0.0
            # aggregate across all pods
            return sum(float(item["value"][1]) for item in results) * 100


if __name__ == "__main__":
    asyncio.run(CpuAgent().run())
