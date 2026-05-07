import pytest

from koral_ai_ml import ValidationError, validate_event


def valid_event():
    return {
        "timestamp": 1710000000,
        "pod": "pod-A",
        "namespace": "koral-system",
        "metric": "cpu",
        "value": 85.2,
        "unit": "percent",
        "z_score": 3.1,
        "is_anomaly": True,
        "window_size": 300,
        "source": "cpu-agent",
    }


def test_validate_event_accepts_project_koral_schema():
    event = validate_event(valid_event())

    assert event["metric"] == "cpu"
    assert event["is_anomaly"] is True
    assert event["value"] == 85.2


def test_validate_event_rejects_missing_required_field():
    event = valid_event()
    event.pop("pod")

    with pytest.raises(ValidationError, match="missing required field"):
        validate_event(event)


def test_validate_event_rejects_unknown_metric():
    event = valid_event()
    event["metric"] = "random"

    with pytest.raises(ValidationError, match="metric must be one of"):
        validate_event(event)


def test_raw_validation_allows_detector_fields_to_be_absent():
    event = valid_event()
    event.pop("z_score")
    event.pop("is_anomaly")

    validated = validate_event(event, final=False)

    assert validated["z_score"] == 0.0
    assert validated["is_anomaly"] is False
