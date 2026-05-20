from __future__ import annotations

from typing import Dict, Any


class DryRunExecutor:
    def render(self, argv: list[str]) -> str:
        return "Would execute: " + " ".join(argv)

    def result(self, execution_id: str, plan_id: str, command: str, argv: list[str]) -> Dict[str, Any]:
        return {
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "success",
            "command": command,
            "exit_code": 0,
            "stdout": self.render(argv),
            "stderr": "",
            "duration_ms": 0,
            "pod_failures": [],
            "blast_radius": 0,
        }
