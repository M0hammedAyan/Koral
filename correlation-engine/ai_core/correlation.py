"""Cross-pod, cross-service, cross-namespace correlation for batch events."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from .schema import KoralEvent
from .rca import determine_root_cause, determine_severity, primary_metric
from .incident import build_incident


def _window_key(timestamp: int, window_seconds: int) -> int:
    return timestamp // window_seconds


def correlate_batch(
    events: List[KoralEvent],
    window_seconds: int = 60,
) -> List[dict]:
    """
    Group anomalous events by namespace + time window, then by root-cause bucket.
    Returns one incident dict per correlated group.
    """
    anomalous = [e for e in events if e.get("is_anomaly")]
    if not anomalous:
        return []

    # Group by (namespace, time-window)
    groups: Dict[Tuple[str, int], List[KoralEvent]] = defaultdict(list)
    for event in anomalous:
        key = (event["namespace"], _window_key(event["timestamp"], window_seconds))
        groups[key].append(event)

    incidents = []
    for (namespace, _window), group_events in groups.items():
        try:
            incident = build_incident(group_events)
        except ValueError:
            continue

        pods = incident["affected_pods"]
        services = sorted({_service_from_pod(p) for p in pods})
        namespaces = sorted({e["namespace"] for e in group_events})

        confidence = round(
            min(
                sum(abs(e.get("z_score", 0)) for e in group_events) / (len(group_events) * 5.0),
                1.0,
            ),
            2,
        )

        incidents.append({
            **incident,
            "confidence": confidence,
            "correlated_pods": pods,
            "correlated_services": services,
            "correlated_namespaces": namespaces,
            "event_count": len(group_events),
            "cross_pod": len(pods) > 1,
            "cross_service": len(services) > 1,
            "cross_namespace": len(namespaces) > 1,
        })

    # Most severe first
    _sev = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    incidents.sort(key=lambda i: _sev.get(i.get("severity", "low"), 3))
    return incidents


def _service_from_pod(pod_name: str) -> str:
    parts = pod_name.rsplit("-", 2)
    return parts[0] if len(parts) >= 2 else pod_name
