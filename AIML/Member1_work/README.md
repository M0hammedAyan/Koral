# Project KORAL AI/ML Incident Engine

This package validates incoming pod metric events, computes rolling Z-score
anomalies, applies rule-based root cause analysis, and emits integration-ready
incident objects.

## Structure

```text
koral_ai_ml/
  __init__.py
  anomaly.py      # rolling Z-score detection
  incident.py     # incident object construction
  pipeline.py     # end-to-end processing API
  rca.py          # rule-based root cause classification
  schema.py       # shared constants and event/incident contracts
  validator.py    # incoming/final event validation
data/
  dummy_events.json
tests/
  test_pipeline.py
  test_validator.py
requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
pytest
```

To run the bundled dummy data without any test framework:

```bash
python scripts/run_dummy.py
```

For a no-dependency verification path:

```bash
python scripts/smoke_test.py
```

## Integration API

```python
from koral_ai_ml import process_events

incidents = process_events(events, z_threshold=3.0, window_size=300)
```

Each returned incident is a plain `dict`:

```json
{
  "incident_id": "inc-koral-system-pod-A-cpu-1710000180",
  "timestamp": 1710000180,
  "namespace": "koral-system",
  "severity": "high",
  "root_cause": "cpu_saturation",
  "summary": "cpu anomaly in koral-system affecting pod-A, pod-B",
  "affected_pods": ["pod-A", "pod-B"],
  "primary_metric": "cpu",
  "evidence": [],
  "metadata": {
    "event_count": 2,
    "sources": ["cpu-agent"],
    "window_size": 300
  }
}
```

## Event Schema

Final validated events use the Project KORAL contract:

```json
{
  "timestamp": 1710000000,
  "pod": "pod-A",
  "namespace": "koral-system",
  "metric": "cpu",
  "value": 85.2,
  "unit": "percent",
  "z_score": 3.1,
  "is_anomaly": true,
  "window_size": 300,
  "source": "cpu-agent"
}
```

Raw collector events may omit `z_score` and `is_anomaly`; the detector will
compute them before incident creation. Allowed metrics are:

```text
cpu | memory | pvc_io | disk | network | log_error | restart | oom_kill | latency
```