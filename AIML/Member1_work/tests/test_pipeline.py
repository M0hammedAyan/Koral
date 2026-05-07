import json
from pathlib import Path

from koral_ai_ml import RollingZScoreDetector, determine_root_cause, process_events


def raw_event(timestamp, pod, metric, value, source="cpu-agent"):
    return {
        "timestamp": timestamp,
        "pod": pod,
        "namespace": "koral-system",
        "metric": metric,
        "value": value,
        "unit": "percent",
        "window_size": 300,
        "source": source,
    }


def test_z_score_detector_flags_anomaly_after_baseline():
    detector = RollingZScoreDetector(z_threshold=3.0, window_size=300)
    values = [50.0, 51.0, 49.0, 52.0, 50.5, 95.0]
    scored = [
        detector.detect(raw_event(1710000000 + index * 30, "pod-A", "cpu", value))
        for index, value in enumerate(values)
    ]

    assert scored[-1]["is_anomaly"] is True
    assert scored[-1]["z_score"] >= 3.0


def test_rule_based_rca_prioritizes_memory_oom():
    anomalies = [
        {
            "timestamp": 1710000000,
            "pod": "pod-A",
            "namespace": "koral-system",
            "metric": "memory",
            "value": 2048.0,
            "unit": "mb",
            "z_score": 3.4,
            "is_anomaly": True,
            "window_size": 300,
            "source": "memory-agent",
        },
        {
            "timestamp": 1710000030,
            "pod": "pod-A",
            "namespace": "koral-system",
            "metric": "restart",
            "value": 5.0,
            "unit": "count",
            "z_score": 3.1,
            "is_anomaly": True,
            "window_size": 300,
            "source": "kube-agent",
        },
    ]

    assert determine_root_cause(anomalies) == "memory_pressure_or_oom"


def test_pipeline_builds_integration_ready_incident_with_affected_pods():
    events = []
    for index, value in enumerate([50.0, 51.0, 49.0, 52.0, 50.5]):
        timestamp = 1710000000 + index * 30
        events.append(raw_event(timestamp, "pod-A", "cpu", value))
        events.append(raw_event(timestamp, "pod-B", "cpu", value))
    events.append(raw_event(1710000180, "pod-A", "cpu", 95.0))
    events.append(raw_event(1710000180, "pod-B", "cpu", 96.0))

    incidents = process_events(events, z_threshold=3.0, window_size=300)

    assert len(incidents) == 1
    incident = incidents[0]
    assert incident["root_cause"] == "cpu_saturation"
    assert incident["severity"] in {"high", "critical"}
    assert incident["affected_pods"] == ["pod-A", "pod-B"]
    assert incident["primary_metric"] == "cpu"
    assert all(event["is_anomaly"] is True for event in incident["evidence"])
    assert {
        "incident_id",
        "timestamp",
        "namespace",
        "severity",
        "root_cause",
        "summary",
        "affected_pods",
        "primary_metric",
        "evidence",
        "metadata",
    }.issubset(incident)


def test_pipeline_processes_dummy_data_file():
    dummy_path = Path(__file__).resolve().parents[1] / "data" / "dummy_events.json"
    events = json.loads(dummy_path.read_text(encoding="utf-8"))

    incidents = process_events(events, z_threshold=3.0, window_size=300)

    assert len(incidents) == 1
    assert incidents[0]["affected_pods"] == ["pod-A", "pod-B"]
