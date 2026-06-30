"""
VictoriaMetrics Client — Remote write + MetricsQL query.

Handles:
  - Querying metric history (for STL decomposition, RRCF input)
  - Writing KORAL's self-monitoring metrics
  - Cardinality guard enforcement before any write
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
import pandas as pd

from koral.config import settings

logger = logging.getLogger(__name__)


class CardinalityViolation(Exception):
    """Raised when a metric write would exceed cardinality limits."""
    pass


class VictoriaMetricsClient:
    """
    VictoriaMetrics query and remote-write client.

    Query interface uses MetricsQL (superset of PromQL).
    Remote write uses Prometheus remote-write protocol.
    """

    FORBIDDEN_LABELS = set(settings.forbidden_labels.split(","))

    def __init__(
        self,
        query_url: str = settings.vm_query_url,
        write_url: str = settings.vm_remote_write_url,
        timeout: float = 10.0,
    ):
        self.query_url = query_url
        self.write_url = write_url
        self.timeout = timeout
        self._label_cardinality: dict[str, set] = {}

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "10s",
    ) -> pd.DataFrame:
        """
        Execute a range query against VictoriaMetrics.

        Returns DataFrame with 'timestamp' (datetime index) and 'value' columns.
        Returns empty DataFrame if query returns no results.
        """
        params = {
            "query": query,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": step,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(self.query_url, params=params)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("data", {}).get("result", [])

        if not results:
            return pd.DataFrame(columns=["timestamp", "value"])

        # Take first result series (single metric queries)
        values = results[0].get("values", [])
        if not values:
            return pd.DataFrame(columns=["timestamp", "value"])

        df = pd.DataFrame(values, columns=["timestamp", "value"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        df["value"] = df["value"].astype(float)
        df.set_index("timestamp", inplace=True)
        return df

    async def query_latest(self, query: str) -> Optional[float]:
        """
        Query the latest single value for a metric.
        Used by RRCF for streaming ingestion.

        Returns None if no data available.
        """
        instant_url = self.query_url.replace("query_range", "query")
        params = {"query": query}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(instant_url, params=params)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("data", {}).get("result", [])

        if not results:
            return None

        value = results[0].get("value", [None, None])
        if len(value) >= 2:
            return float(value[1])
        return None

    async def query_multi_series(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "10s",
    ) -> dict[str, pd.DataFrame]:
        """
        Query returning multiple series (e.g., per-pod results).
        Returns dict mapping label identifier → DataFrame.
        """
        params = {
            "query": query,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": step,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(self.query_url, params=params)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("data", {}).get("result", [])
        series_map = {}

        for result in results:
            metric_labels = result.get("metric", {})
            # Use pod name as key, or full label set
            key = metric_labels.get("pod", str(metric_labels))
            values = result.get("values", [])
            if values:
                df = pd.DataFrame(values, columns=["timestamp", "value"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
                df["value"] = df["value"].astype(float)
                df.set_index("timestamp", inplace=True)
                series_map[key] = df

        return series_map

    def check_cardinality(self, labels: dict[str, str]) -> None:
        """
        Enforce cardinality rules before writing.
        Raises CardinalityViolation if:
          - Any forbidden label is present
          - Any label exceeds max cardinality
        """
        for label_name in labels:
            if label_name in self.FORBIDDEN_LABELS:
                raise CardinalityViolation(
                    f"Forbidden label '{label_name}' rejected. "
                    f"High-cardinality labels are not permitted: {self.FORBIDDEN_LABELS}"
                )

        for label_name, label_value in labels.items():
            if label_name not in self._label_cardinality:
                self._label_cardinality[label_name] = set()
            self._label_cardinality[label_name].add(label_value)
            if len(self._label_cardinality[label_name]) > settings.max_label_cardinality:
                raise CardinalityViolation(
                    f"Label '{label_name}' cardinality ({len(self._label_cardinality[label_name])}) "
                    f"exceeds limit ({settings.max_label_cardinality})"
                )

    async def remote_write(self, metrics: list[dict]) -> bool:
        """
        Write KORAL's self-monitoring metrics to VictoriaMetrics.

        Each metric dict: {"name": str, "labels": dict, "value": float, "timestamp": int}

        Enforces cardinality guard before writing.
        Returns True on success, False on failure (never raises for write failures).
        """
        for metric in metrics:
            try:
                self.check_cardinality(metric.get("labels", {}))
            except CardinalityViolation as e:
                logger.warning(f"[vm] Cardinality violation, metric skipped: {e}")
                return False

        # Build Prometheus remote-write format (line protocol for VM)
        lines = []
        for m in metrics:
            label_str = ",".join(f'{k}="{v}"' for k, v in m.get("labels", {}).items())
            ts = m.get("timestamp", int(datetime.now(timezone.utc).timestamp()))
            lines.append(f'{m["name"]}{{{label_str}}} {m["value"]} {ts}')

        body = "\n".join(lines)

        try:
            import_url = self.write_url.replace("/api/v1/write", "/api/v1/import/prometheus")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    import_url,
                    content=body,
                    headers={"Content-Type": "text/plain"},
                )
                resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"[vm] Remote write failed: {e}")
            return False
