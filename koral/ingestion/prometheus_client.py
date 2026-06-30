"""
Prometheus PromQL Query Wrapper.

Wraps prometheus-api-client for direct Prometheus queries.
Used when VictoriaMetrics is not yet available or as fallback.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
import pandas as pd

from koral.config import settings

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Direct Prometheus query client using PromQL."""

    def __init__(self, url: str = "http://prometheus:9090"):
        self.base_url = url.rstrip("/")
        self.timeout = 10.0

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "10s",
    ) -> pd.DataFrame:
        """Execute range query and return DataFrame."""
        params = {
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": step,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/api/v1/query_range", params=params)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("data", {}).get("result", [])

        if not results:
            return pd.DataFrame(columns=["timestamp", "value"])

        values = results[0].get("values", [])
        if not values:
            return pd.DataFrame(columns=["timestamp", "value"])

        df = pd.DataFrame(values, columns=["timestamp", "value"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        df["value"] = df["value"].astype(float)
        df.set_index("timestamp", inplace=True)
        return df

    async def query_instant(self, query: str) -> Optional[float]:
        """Query the latest instant value."""
        params = {"query": query}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/api/v1/query", params=params)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("data", {}).get("result", [])
        if not results:
            return None

        value = results[0].get("value", [None, None])
        return float(value[1]) if len(value) >= 2 else None

    async def health(self) -> bool:
        """Check Prometheus health."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/-/healthy")
                return resp.status_code == 200
        except Exception:
            return False
