"""Compatibility package for the Project KORAL AI/ML engine.

The implementation lives in :mod:`ai_core`, but the tests and README use the
legacy ``koral_ai_ml`` import path.
"""

from ai_core.anomaly import RollingZScoreDetector
from ai_core.incident import build_incident
from ai_core.pipeline import process_events
from ai_core.rca import determine_root_cause
from ai_core.validator import ValidationError, validate_event, validate_events

__all__ = [
    "RollingZScoreDetector",
    "ValidationError",
    "build_incident",
    "determine_root_cause",
    "process_events",
    "validate_event",
    "validate_events",
]