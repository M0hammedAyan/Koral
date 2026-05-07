# SYSTEM INTELLIGENCE & EVALUATION — Member 5

> QA + Data Scientist + Simulation Engineer

---

## Directory Structure

```
SYSTEM INTELLIGENCE & EVALUATION/
├── simulation/
│   ├── cpu_spike.py          # Maxes CPU → triggers cpu-agent
│   ├── memory_leak.py        # Leaks RAM → triggers memory-agent
│   ├── io_storm.py           # PVC I/O loop → triggers storage-agent
│   └── network_latency.py    # JSON error burst → triggers log-agent
├── evaluation/
│   ├── metrics.py            # Precision, Recall, FPR, Latency
│   └── performance.py        # Top-N filter, rate-limit, cache, sampling
├── threshold/
│   ├── adaptive_threshold.py # Dynamic k-sigma threshold per metric
│   └── thresholds.json       # Live threshold config (read by agents)
├── feedback/
│   └── feedback_loop.py      # Adjusts thresholds from backend feedback
├── Dockerfile                # Simulation runner image
└── requirements.txt
```

---

## Simulation

Each script runs inside a Kubernetes pod. DevOps deploys them via existing YAMLs in `infra/k8s/simulation/`.

| Script | Scenario | Triggers |
|---|---|---|
| `cpu_spike.py` | Tight compute loop | cpu-agent |
| `memory_leak.py` | Unbounded list growth | memory-agent |
| `io_storm.py` | Continuous PVC writes | storage-agent |
| `network_latency.py` | JSON ERROR log burst | log-agent |

---

## Evaluation

```python
from evaluation.metrics import evaluate

results = evaluate(ground_truth_events, detected_anomalies)
# {"precision": 0.91, "recall": 0.87, "false_positive_rate": 0.09, "latency_ms": 1200}
```

---

## Adaptive Thresholds

`threshold/thresholds.json` is the live config file agents read.

```python
from threshold.adaptive_threshold import update_threshold, get_threshold

k = update_threshold("cpu", value=85.2, is_anomaly=True)
current_k = get_threshold("cpu")   # → 2.7
```

Threshold increases to `3.0` automatically when >30% of recent samples are anomalies (noisy environment).

---

## Feedback Loop

Backend sends feedback after human review:

```json
{"incident_id": "INC123", "metric": "cpu", "is_correct": false}
```

```python
from feedback.feedback_loop import process_feedback

record = process_feedback("INC123", "cpu", is_correct=False)
# {"old_threshold": 2.7, "new_threshold": 2.9, ...}
```

All adjustments are logged to `feedback/feedback_log.json`.

---

## Performance Optimization

```python
from evaluation.performance import filter_top_anomalies, should_run_correlation, sample_metrics

top = filter_top_anomalies(all_anomalies)   # top 10 by z_score
if should_run_correlation():                # rate-limited to every 30s
    sampled = sample_metrics(metrics)       # 1-in-3 sampling
```

---

## Integration Points

| Connects To | How |
|---|---|
| Member 1 (Correlation Engine) | `thresholds.json` + `performance.py` top-N filter |
| Member 2 (DevOps) | `Dockerfile` + simulation scripts deployed as pods |
| Member 3 (Backend) | `feedback_loop.py` consumes `/feedback` endpoint |
| Member 4 (Frontend) | `evaluate()` output surfaced via backend `/metrics` |
