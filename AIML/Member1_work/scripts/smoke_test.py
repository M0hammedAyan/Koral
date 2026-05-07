"""No-dependency smoke tests for the Project KORAL package."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from ai_core import ValidationError, process_events, validate_event


    valid_event = {
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
    assert validate_event(valid_event)["metric"] == "cpu"

    invalid_event = dict(valid_event)
    invalid_event["metric"] = "not-real"
    try:
        validate_event(invalid_event)
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid metric should fail validation")

    events_path = repo_root / "data" / "dummy_events.json"
    events = json.loads(events_path.read_text(encoding="utf-8"))
    incidents = process_events(events, z_threshold=3.0, window_size=300)

    assert len(incidents) == 1
    incident = incidents[0]
    assert incident["root_cause"] == "cpu_saturation"
    assert incident["affected_pods"] == ["pod-A", "pod-B"]
    assert incident["metadata"]["event_count"] == 2
    assert all(event["is_anomaly"] for event in incident["evidence"])

    print("Project KORAL smoke tests passed")


if __name__ == "__main__":
    main()
