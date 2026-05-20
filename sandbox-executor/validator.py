from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Any, Dict

import httpx
import pybreaker
import yaml


_BLOCKED = {"rm", "del", "powershell", "cmd", "bash", "curl", "wget", "shutdown", "format", "shell=True"}
_SAFE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    error: str | None = None


class SandboxValidator:
    def __init__(self, allowed_file: str):
        with open(allowed_file, "r", encoding="utf-8") as handle:
            self.allowed = yaml.safe_load(handle) or {}
        self.approval_url = os.getenv("APPROVAL_ENGINE_URL", "http://approval-engine:8008")
        self.breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

    def validate(self, command: str, params: Dict[str, Any], approval_id: str) -> ValidationResult:
        if command not in self.allowed:
            return ValidationResult(False, f"Command '{command}' not allowed")
        if not approval_id:
            return ValidationResult(False, "approval required")
        if any(token in command for token in _BLOCKED):
            return ValidationResult(False, "blocked command")
        for value in params.values():
            if isinstance(value, str) and any(token in value for token in _BLOCKED):
                return ValidationResult(False, "blocked argument")
        if "namespace" in params and params["namespace"] and not _SAFE.match(str(params["namespace"])):
            return ValidationResult(False, "invalid namespace")
        return ValidationResult(True)

    async def ensure_approved(self, approval_id: str) -> ValidationResult:
        def _check() -> ValidationResult:
            response = httpx.get(f"{self.approval_url}/status/{approval_id}", timeout=5)
            if response.status_code != 200:
                return ValidationResult(False, "approval lookup failed")
            status = response.json().get("status")
            if status != "approved":
                return ValidationResult(False, f"approval status is {status}")
            return ValidationResult(True)

        return await asyncio.to_thread(self.breaker.call, _check)
