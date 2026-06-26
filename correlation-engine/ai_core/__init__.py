"""Project KORAL AI/ML validation, anomaly detection, and RCA package."""

from ai_core.anomaly import IsolationForestDetector
from ai_core.incident import build_incident
from ai_core.pipeline import process_events
from ai_core.rca import determine_root_cause
from ai_core.validator import ValidationError, validate_event, validate_events

# Backwards-compatible alias
RollingZScoreDetector = IsolationForestDetector

__all__ = [
    "IsolationForestDetector",
    "RollingZScoreDetector",
    "ValidationError",
    "build_incident",
    "determine_root_cause",
    "process_events",
    "validate_event",
    "validate_events",
]
