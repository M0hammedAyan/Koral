"""Compatibility package for the Project KORAL AI/ML engine.

The implementation lives in ``AIML/Member1_work/ai_core``, but tests and docs
still import ``koral_ai_ml`` from the repository root.
"""

from AIML.Member1_work.ai_core.anomaly import RollingZScoreDetector
from AIML.Member1_work.ai_core.incident import build_incident
from AIML.Member1_work.ai_core.pipeline import process_events
from AIML.Member1_work.ai_core.rca import determine_root_cause
from AIML.Member1_work.ai_core.validator import ValidationError, validate_event, validate_events

__all__ = [
    "RollingZScoreDetector",
    "ValidationError",
    "build_incident",
    "determine_root_cause",
    "process_events",
    "validate_event",
    "validate_events",
]