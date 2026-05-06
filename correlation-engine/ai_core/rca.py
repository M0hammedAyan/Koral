"""Rule-based root cause analysis for anomalous KORAL events."""

from __future__ import annotations

from typing import Iterable, List, Tuple

from .schema import KoralEvent


def determine_root_cause(anomalies: Iterable[KoralEvent]) -> str:
    """Classify root cause using deterministic metric-priority rules."""

    events = list(anomalies)
    metrics = {event["metric"] for event in events}

    if "oom_kill" in metrics or {"memory", "restart"}.issubset(metrics):
        return "memory_pressure_or_oom"
    if "pvc_io" in metrics or "disk" in metrics:
        return "storage_io_bottleneck"
    if "network" in metrics and "latency" in metrics:
        return "network_latency_degradation"
    if "log_error" in metrics and "restart" in metrics:
        return "application_crash_loop"
    if "cpu" in metrics:
        return "cpu_saturation"
    if "latency" in metrics:
        return "service_latency_spike"
    if "restart" in metrics:
        return "pod_restart_spike"
    if "log_error" in metrics:
        return "application_error_spike"
    return "unknown_anomalous_behavior"


def determine_severity(anomalies: Iterable[KoralEvent]) -> str:
    """Map anomalous evidence into an incident severity."""

    events = list(anomalies)
    if any(event["metric"] in {"oom_kill", "restart"} and abs(event["z_score"]) >= 3 for event in events):
        return "critical"
    if any(abs(event["z_score"]) >= 4 for event in events):
        return "critical"
    if any(abs(event["z_score"]) >= 3 for event in events):
        return "high"
    return "medium"


def primary_metric(anomalies: Iterable[KoralEvent]) -> str:
    """Pick the strongest signal as the primary metric for the incident."""

    ranked: List[Tuple[float, str]] = [
        (abs(event["z_score"]), event["metric"])
        for event in anomalies
    ]
    if not ranked:
        return "unknown"
    return sorted(ranked, reverse=True)[0][1]
