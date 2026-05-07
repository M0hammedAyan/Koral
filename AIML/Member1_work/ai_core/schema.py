"""Shared Project KORAL event and incident schema constants."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict

MetricName = Literal[
    "cpu",
    "memory",
    "pvc_io",
    "disk",
    "network",
    "log_error",
    "restart",
    "oom_kill",
    "latency",
]

ALLOWED_METRICS = {
    "cpu",
    "memory",
    "pvc_io",
    "disk",
    "network",
    "log_error",
    "restart",
    "oom_kill",
    "latency",
}

CORE_EVENT_FIELDS = {
    "timestamp",
    "pod",
    "namespace",
    "metric",
    "value",
    "unit",
    "window_size",
    "source",
}

FINAL_EVENT_FIELDS = CORE_EVENT_FIELDS | {"z_score", "is_anomaly"}


class KoralEvent(TypedDict):
    timestamp: int
    pod: str
    namespace: str
    metric: MetricName
    value: float
    unit: str
    z_score: float
    is_anomaly: bool
    window_size: int
    source: str


class Incident(TypedDict):
    incident_id: str
    timestamp: int
    namespace: str
    severity: str
    root_cause: str
    summary: str
    affected_pods: List[str]
    primary_metric: str
    evidence: List[KoralEvent]
    metadata: Dict[str, Any]
