import os
import sys
import asyncio
import httpx
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
NAMESPACE = os.getenv("NAMESPACE", "koral-system")
POD_NAME = os.getenv("POD_NAME", "storage-agent")

QUERY = f'sum(rate(container_fs_writes_bytes_total{{namespace="{NAMESPACE}"}}[1m])) by (pod)'


class StorageAgent(BaseAgent):
    def __init__(self):
        super().__init__(metric="storage", pod=POD_NAME, unit="KB/s")

    async def fetch_value(self) -> float:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": QUERY})
            results = r.json().get("data", {}).get("result", [])
            if not results:
                return 0.0
            total_bytes = sum(float(item["value"][1]) for item in results)
            return total_bytes / 1024


if __name__ == "__main__":
    asyncio.run(StorageAgent().run())
