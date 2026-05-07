"""Incident construction for Project KORAL anomaly output."""

from __future__ import annotations

from typing import Iterable, List

from .rca import determine_root_cause, determine_severity, primary_metric
from .schema import Incident, KoralEvent


def build_incident(anomalies: Iterable[KoralEvent]) -> Incident:
    """Build a stable incident object from one or more anomalous events."""

    evidence: List[KoralEvent] = sorted(
        [event for event in anomalies if event["is_anomaly"]],
        key=lambda event: (event["timestamp"], event["namespace"], event["pod"], event["metric"]),
    )
    if not evidence:
        raise ValueError("cannot build an incident without anomalous evidence")

    namespace = evidence[0]["namespace"]
    timestamp = max(event["timestamp"] for event in evidence)
    affected_pods = sorted({event["pod"] for event in evidence})
    metric = primary_metric(evidence)
    root_cause = determine_root_cause(evidence)
    severity = determine_severity(evidence)
    pod_label = ", ".join(affected_pods)

    return {
        "incident_id": f"inc-{namespace}-{affected_pods[0]}-{metric}-{timestamp}",
        "timestamp": timestamp,
        "namespace": namespace,
        "severity": severity,
        "root_cause": root_cause,
        "summary": f"{metric} anomaly in {namespace} affecting {pod_label}",
        "affected_pods": affected_pods,
        "primary_metric": metric,
        "evidence": evidence,
        "metadata": {
            "event_count": len(evidence),
            "sources": sorted({event["source"] for event in evidence}),
            "window_size": evidence[0]["window_size"],
        },
    }
