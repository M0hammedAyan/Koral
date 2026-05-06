"""Validation for Project KORAL metric events."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from .schema import ALLOWED_METRICS, CORE_EVENT_FIELDS, FINAL_EVENT_FIELDS, KoralEvent


class ValidationError(ValueError):
    """Raised when an incoming KORAL event violates the shared contract."""


def validate_event(event: Mapping[str, Any], *, final: bool = True) -> KoralEvent:
    """Validate and normalize a single KORAL event.

    Args:
        event: Incoming event-like mapping.
        final: When true, require detector fields ``z_score`` and
            ``is_anomaly``. Set false for raw collector events before anomaly
            detection.

    Returns:
        A normalized dictionary matching the final KORAL schema.
    """

    if not isinstance(event, Mapping):
        raise ValidationError("event must be a mapping")

    required_fields = FINAL_EVENT_FIELDS if final else CORE_EVENT_FIELDS
    missing = sorted(field for field in required_fields if field not in event)
    if missing:
        raise ValidationError(f"missing required field(s): {', '.join(missing)}")

    timestamp = _require_int(event["timestamp"], "timestamp")
    window_size = _require_int(event["window_size"], "window_size")
    if timestamp <= 0:
        raise ValidationError("timestamp must be a positive Unix epoch second")
    if window_size <= 0:
        raise ValidationError("window_size must be a positive number of seconds")

    pod = _require_non_empty_string(event["pod"], "pod")
    namespace = _require_non_empty_string(event["namespace"], "namespace")
    metric = _require_non_empty_string(event["metric"], "metric")
    unit = _require_non_empty_string(event["unit"], "unit")
    source = _require_non_empty_string(event["source"], "source")

    if metric not in ALLOWED_METRICS:
        allowed = " | ".join(sorted(ALLOWED_METRICS))
        raise ValidationError(f"metric must be one of: {allowed}")

    value = _require_number(event["value"], "value")
    z_score = _require_number(event.get("z_score", 0.0), "z_score")
    is_anomaly = event.get("is_anomaly", False)
    if not isinstance(is_anomaly, bool):
        raise ValidationError("is_anomaly must be a boolean")

    return {
        "timestamp": timestamp,
        "pod": pod,
        "namespace": namespace,
        "metric": metric,  # type: ignore[typeddict-item]
        "value": value,
        "unit": unit,
        "z_score": z_score,
        "is_anomaly": is_anomaly,
        "window_size": window_size,
        "source": source,
    }


def validate_events(events: Iterable[Mapping[str, Any]], *, final: bool = True) -> List[KoralEvent]:
    """Validate a batch of KORAL events."""

    return [validate_event(event, final=final) for event in events]


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field} must be an integer")
    return value


def _require_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be numeric")
    return float(value)


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    return value.strip()
