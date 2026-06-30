"""
Cardinality Guard — prevents label explosion in VictoriaMetrics.

High-cardinality labels (request_id, trace_id, user_id) create millions of unique
time series, crashing any TSDB. This guard rejects writes containing forbidden labels
and alerts when any label exceeds the configured cardinality limit.

FORBIDDEN labels: request_id, trace_id, user_id, session_id, transaction_id
MAX cardinality per label: 1000 unique values (configurable)
"""
import logging
from typing import Optional

from koral.config import settings

logger = logging.getLogger(__name__)


class CardinalityViolation(Exception):
    """Raised when a metric would violate cardinality rules."""
    pass


class CardinalityGuard:
    """
    Enforces cardinality rules on all metric labels before storage.

    Rules:
    1. Reject any metric with a forbidden label name
    2. Track unique values per label; reject if exceeding max
    3. Required labels: namespace, pod must be present
    """

    FORBIDDEN = set(settings.forbidden_labels.split(","))
    MAX_CARDINALITY = settings.max_label_cardinality
    REQUIRED_LABELS = {"namespace", "pod"}

    def __init__(self):
        self._cardinality_tracker: dict[str, set] = {}

    def validate(self, labels: dict[str, str]) -> None:
        """
        Validate labels against cardinality rules.
        Raises CardinalityViolation on failure.
        """
        # Check forbidden labels
        for label_name in labels:
            if label_name in self.FORBIDDEN:
                raise CardinalityViolation(
                    f"Forbidden label '{label_name}'. "
                    f"Labels {self.FORBIDDEN} are banned due to high cardinality."
                )

        # Check required labels
        missing = self.REQUIRED_LABELS - set(labels.keys())
        if missing:
            raise CardinalityViolation(
                f"Missing required labels: {missing}. "
                f"Every metric must have: {self.REQUIRED_LABELS}"
            )

        # Check cardinality limits
        for label_name, label_value in labels.items():
            if label_name not in self._cardinality_tracker:
                self._cardinality_tracker[label_name] = set()

            self._cardinality_tracker[label_name].add(label_value)

            if len(self._cardinality_tracker[label_name]) > self.MAX_CARDINALITY:
                raise CardinalityViolation(
                    f"Label '{label_name}' exceeds cardinality limit "
                    f"({len(self._cardinality_tracker[label_name])} > {self.MAX_CARDINALITY})"
                )

    def get_stats(self) -> dict[str, int]:
        """Return current cardinality counts per label."""
        return {k: len(v) for k, v in self._cardinality_tracker.items()}

    def reset(self) -> None:
        """Reset cardinality tracking. Call at guard rotation intervals."""
        self._cardinality_tracker.clear()


# Global instance
guard = CardinalityGuard()
