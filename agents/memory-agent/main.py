import os
import sys
import asyncio
import httpx
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
NAMESPACE = os.getenv("NAMESPACE", "koral-system")
POD_NAME = os.getenv("POD_NAME", "memory-agent")

QUERY = f'sum(container_memory_working_set_bytes{{namespace="{NAMESPACE}"}}) by (pod)'


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(metric="memory", pod=POD_NAME, unit="MB")

    async def fetch_value(self) -> float:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": QUERY})
            results = r.json().get("data", {}).get("result", [])
            if not results:
                return 0.0
            total_bytes = sum(float(item["value"][1]) for item in results)
            return total_bytes / (1024 ** 2)


if __name__ == "__main__":
    asyncio.run(MemoryAgent().run())
