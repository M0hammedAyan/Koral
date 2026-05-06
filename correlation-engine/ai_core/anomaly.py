"""Rolling Z-score anomaly detection for Project KORAL events."""

from __future__ import annotations

from collections import defaultdict, deque
from math import sqrt
from typing import Deque, Dict, Iterable, List, Tuple

from .schema import KoralEvent
from .validator import validate_event

HistoryKey = Tuple[str, str, str]
HistoryPoint = Tuple[int, float]


class RollingZScoreDetector:
    """Compute Z-scores from a per-pod, per-metric rolling time window."""

    def __init__(
        self,
        *,
        z_threshold: float = 3.0,
        window_size: int = 300,
        min_history_points: int = 5,
    ) -> None:
        if z_threshold <= 0:
            raise ValueError("z_threshold must be positive")
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if min_history_points < 2:
            raise ValueError("min_history_points must be at least 2")
        self.z_threshold = z_threshold
        self.window_size = window_size
        self.min_history_points = min_history_points
        self._history: Dict[HistoryKey, Deque[HistoryPoint]] = defaultdict(deque)

    def detect(self, raw_event: dict) -> KoralEvent:
        """Validate, score, and annotate one event."""

        event = validate_event(raw_event, final=False)
        key = (event["namespace"], event["pod"], event["metric"])
        history = self._history[key]
        self._expire_old_points(history, event["timestamp"])

        history_values = [value for _, value in history]
        z_score = self._z_score(event["value"], history_values)
        if len(history_values) < self.min_history_points:
            z_score = 0.0
        is_anomaly = abs(z_score) >= self.z_threshold

        annotated: KoralEvent = {
            **event,
            "z_score": round(z_score, 6),
            "is_anomaly": is_anomaly,
            "window_size": self.window_size,
        }
        validate_event(annotated, final=True)

        history.append((event["timestamp"], event["value"]))
        return annotated

    def detect_many(self, raw_events: Iterable[dict]) -> List[KoralEvent]:
        """Score events in timestamp order to keep the rolling window stable."""

        ordered_events = sorted(raw_events, key=lambda item: item["timestamp"])
        return [self.detect(event) for event in ordered_events]

    def _expire_old_points(self, history: Deque[HistoryPoint], timestamp: int) -> None:
        cutoff = timestamp - self.window_size
        while history and history[0][0] < cutoff:
            history.popleft()

    @staticmethod
    def _z_score(value: float, history_values: List[float]) -> float:
        if len(history_values) < 2:
            return 0.0

        mean = sum(history_values) / len(history_values)
        variance = sum((sample - mean) ** 2 for sample in history_values) / len(history_values)
        stddev = sqrt(variance)
        if stddev == 0:
            return 0.0 if value == mean else 999.0
        return (value - mean) / stddev