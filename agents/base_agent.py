import os
import asyncio
import httpx
from collections import deque
from statistics import mean, stdev
from datetime import datetime, timezone

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "2.5"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
NAMESPACE = os.getenv("NAMESPACE", "koral-system")
HISTORY_SIZE = 30


def compute_z_score(history: deque, value: float) -> float:
    if len(history) < 2:
        return 0.0
    m, s = mean(history), stdev(history)
    return (value - m) / s if s > 0 else 0.0


class BaseAgent:
    def __init__(self, metric: str, pod: str, unit: str = "value"):
        self.metric = metric
        self.pod = pod
        self.unit = unit
        self.history: deque = deque(maxlen=HISTORY_SIZE)

    async def fetch_value(self) -> float:
        raise NotImplementedError

    async def run(self):
        while True:
            try:
                value = await self.fetch_value()
                z = compute_z_score(self.history, value)
                self.history.append(value)
                payload = {
                    "timestamp": int(datetime.now(timezone.utc).timestamp()),
                    "pod": self.pod,
                    "namespace": NAMESPACE,
                    "metric": self.metric,
                    "value": round(value, 4),
                    "unit": self.unit,
                    "z_score": round(z, 4),
                    "is_anomaly": abs(z) > Z_THRESHOLD,
                    "window_size": HISTORY_SIZE * POLL_INTERVAL,
                    "source": f"{self.metric}-agent",
                }
                async with httpx.AsyncClient(timeout=5) as client:
                    await client.post(f"{BACKEND_URL}/anomalies", json=payload)
            except Exception as e:
                print(f"[{self.metric}] error: {e}")
            await asyncio.sleep(POLL_INTERVAL)
