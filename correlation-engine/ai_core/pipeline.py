"""End-to-end Project KORAL anomaly and incident pipeline."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from .anomaly import IsolationForestDetector
from .incident import build_incident
from .schema import Incident, KoralEvent

IncidentKey = Tuple[str, int]


def process_events(
    raw_events: Iterable[dict],
    *,
    z_threshold: float = 3.0,
    window_size: int = 300,
) -> List[Incident]:
    """Validate events, detect anomalies, run RCA, and build incidents.

    Incidents are grouped by namespace and timestamp window so multiple pods
    reporting correlated anomalies are represented in one object.
    """

    detector = IsolationForestDetector(z_threshold=z_threshold, window_size=window_size)
    scored_events = detector.detect_many(raw_events)
    anomalies = [event for event in scored_events if event["is_anomaly"]]
    grouped = _group_anomalies(anomalies, window_size)
    return [build_incident(events) for _, events in sorted(grouped.items())]


def _group_anomalies(anomalies: Iterable[KoralEvent], window_size: int) -> Dict[IncidentKey, List[KoralEvent]]:
    grouped: Dict[IncidentKey, List[KoralEvent]] = defaultdict(list)
    for event in anomalies:
        bucket_start = event["timestamp"] - (event["timestamp"] % window_size)
        grouped[(event["namespace"], bucket_start)].append(event)
    return grouped
