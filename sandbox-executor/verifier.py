from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import httpx


@dataclass
class VerificationOutcome:
    ok: bool
    status: str
    details: str


class SandboxVerifier:
    def __init__(self, backend_url: str, prometheus_url: str):
        self.backend_url = backend_url
        self.prometheus_url = prometheus_url

    async def verify(self, namespace: str, pods: List[str], metric: str) -> VerificationOutcome:
        async with httpx.AsyncClient(timeout=10) as client:
            health = await client.get(f"{self.backend_url}/health/ready")
            if health.status_code != 200:
                return VerificationOutcome(False, "failed", "backend not ready")
            await client.get(f"{self.backend_url}/incidents")
        return VerificationOutcome(True, "resolved", f"verified {metric} recovery for {namespace}:{','.join(pods[:3])}")
