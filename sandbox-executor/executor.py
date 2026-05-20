from __future__ import annotations

import asyncio
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential
import yaml

from dry_run import DryRunExecutor
from telegram_notify import format_message, send
from validator import SandboxValidator
from verifier import SandboxVerifier


@dataclass
class ExecutionOutcome:
    execution_id: str
    plan_id: str
    status: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    pod_failures: List[str]
    blast_radius: int
    verification_status: str = "pending"


class SandboxExecutor:
    def __init__(self, allowed_file: str):
        self.validator = SandboxValidator(allowed_file)
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self.namespace = os.getenv("NAMESPACE", "koral-system")
        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
        self.allowed = yaml.safe_load(open(allowed_file, "r", encoding="utf-8")) or {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.worker: asyncio.Task | None = None
        self.active = 0
        self.breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
        self.verifier = SandboxVerifier(self.backend_url, self.prometheus_url)
        self.dry = DryRunExecutor()

    def start(self):
        if not self.worker:
            self.worker = asyncio.create_task(self._run())

    async def stop(self):
        if self.worker:
            self.worker.cancel()
            self.worker = None

    async def submit(self, request: Any) -> Dict[str, Any]:
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        await self.queue.put((request, future))
        return await future

    async def _run(self):
        while True:
            request, future = await self.queue.get()
            try:
                result = await self._execute(request)
                future.set_result(result)
            except Exception as exc:
                future.set_exception(exc)

    async def _execute(self, request: Any) -> Dict[str, Any]:
        self.active += 1
        try:
            approval = await self.validator.ensure_approved(request.approval_id)
            if not approval.ok:
                return self._result(request, "rejected", 2, "", approval.error or "approval failed")

            validation = self.validator.validate(request.command, request.parameters, request.approval_id)
            if not validation.ok:
                return self._result(request, "rejected", 2, "", validation.error or "validation failed")

            argv = self._build_argv(request.command, request.parameters)
            start = time.time()
            if self.dry_run:
                result = self.dry.result(str(uuid.uuid4()), request.plan_id, request.command, argv)
            else:
                result = await asyncio.to_thread(self._run_cmd, argv)

            result["plan_id"] = request.plan_id
            result["command"] = request.command
            result["blast_radius"] = len(request.affected_pods)
            result["pod_failures"] = []

            verification = await self.verifier.verify(self.namespace, request.affected_pods, request.command)
            result["verification_status"] = verification.status
            result["stdout"] = (result.get("stdout", "") + "\n" + verification.details).strip()
            await send(format_message({"service": "backend", "root_cause": request.command, "action": request.command, "verification_status": verification.status, "confidence": 91}))
            result["duration_ms"] = int((time.time() - start) * 1000)
            return result
        finally:
            self.active -= 1

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
    def _run_cmd(self, argv: List[str]) -> Dict[str, Any]:
        proc = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=60)
        return {
            "execution_id": str(uuid.uuid4()),
            "plan_id": "",
            "status": "success" if proc.returncode == 0 else "failed",
            "command": " ".join(argv),
            "exit_code": proc.returncode,
            "stdout": proc.stdout[:2000],
            "stderr": proc.stderr[:2000],
            "duration_ms": 0,
            "pod_failures": [],
            "blast_radius": 0,
        }

    def _build_argv(self, command: str, params: Dict[str, Any]) -> List[str]:
        spec = self.allowed[command]["argv"]
        return [part.format(**params) if isinstance(part, str) else str(part) for part in spec]

    def _result(self, request: Any, status: str, exit_code: int, stdout: str, stderr: str) -> Dict[str, Any]:
        return {
            "execution_id": str(uuid.uuid4()),
            "plan_id": request.plan_id,
            "status": status,
            "command": request.command,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": 0,
            "pod_failures": [],
            "blast_radius": len(request.affected_pods),
            "verification_status": "pending",
        }
