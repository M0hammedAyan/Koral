"""
Edge-Case Tests — no data, sudden spike, multiple anomalies, overlapping incidents.

Run with:  python -m pytest evaluation/edge_cases.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluation.metrics import evaluate, precision, recall, false_positive_rate
from evaluation.performance import filter_top_anomalies, sample_metrics, should_run_correlation
from threshold.adaptive_threshold import compute_dynamic_threshold


# ── No-data scenarios ────────────────────────────────────────────────────────

def test_evaluate_empty_inputs():
    result = evaluate([], [])
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["latency_ms"] is None

def test_evaluate_no_detections():
    gt = [{"pod": "pod-A", "metric": "cpu", "timestamp": 1000}]
    result = evaluate(gt, [])
    assert result["recall"] == 0.0
    assert result["fn"] == 1

def test_precision_zero_alerts():
    assert precision(0, 0) == 0.0

def test_recall_zero_ground_truth():
    assert recall(0, 0) == 0.0

def test_fpr_zero_alerts():
    assert false_positive_rate(0, 0) == 0.0

def test_dynamic_threshold_single_value():
    assert compute_dynamic_threshold([85.0]) == float("inf")


# ── Sudden spike ─────────────────────────────────────────────────────────────

def test_sudden_spike_detected():
    gt = [{"pod": "pod-A", "metric": "cpu", "timestamp": 1000}]
    detected = [{"pod": "pod-A", "metric": "cpu", "timestamp": 1001, "is_anomaly": True}]
    result = evaluate(gt, detected)
    assert result["tp"] == 1
    assert result["recall"] == 1.0
    assert result["latency_ms"] == 1000.0

def test_dynamic_threshold_spike():
    baseline = [10.0] * 20
    threshold = compute_dynamic_threshold(baseline, k=2.5)
    spike = 10.0 + 2.5 * 0  # std=0 for constant baseline → threshold = 10.0
    assert threshold == 10.0


# ── Multiple simultaneous anomalies ──────────────────────────────────────────

def test_multiple_anomalies_all_detected():
    gt = [
        {"pod": "pod-A", "metric": "cpu",     "timestamp": 1000},
        {"pod": "pod-B", "metric": "memory",  "timestamp": 1000},
        {"pod": "pod-C", "metric": "storage", "timestamp": 1000},
    ]
    detected = [
        {"pod": "pod-A", "metric": "cpu",     "timestamp": 1002, "is_anomaly": True},
        {"pod": "pod-B", "metric": "memory",  "timestamp": 1003, "is_anomaly": True},
        {"pod": "pod-C", "metric": "storage", "timestamp": 1001, "is_anomaly": True},
    ]
    result = evaluate(gt, detected)
    assert result["tp"] == 3
    assert result["fp"] == 0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0

def test_filter_top_anomalies_limits_to_10():
    anomalies = [{"pod": f"pod-{i}", "metric": "cpu", "z_score": float(i)} for i in range(20)]
    top = filter_top_anomalies(anomalies)
    assert len(top) == 10
    assert top[0]["z_score"] == 19.0   # highest first

def test_sample_metrics_reduces_volume():
    metrics = [{"v": i} for i in range(30)]
    sampled = sample_metrics(metrics)
    assert len(sampled) == 10   # every 3rd


# ── Overlapping incidents ─────────────────────────────────────────────────────

def test_overlapping_incidents_no_double_count():
    """Same pod+metric appearing twice in ground truth should not inflate TP."""
    gt = [
        {"pod": "pod-A", "metric": "cpu", "timestamp": 1000},
        {"pod": "pod-A", "metric": "cpu", "timestamp": 1005},  # duplicate key
    ]
    detected = [
        {"pod": "pod-A", "metric": "cpu", "timestamp": 1001, "is_anomaly": True},
    ]
    result = evaluate(gt, detected)
    # gt_keys is a set → deduplicates → 1 unique key
    assert result["tp"] == 1
    assert result["fn"] == 0

def test_false_positive_not_in_ground_truth():
    gt = [{"pod": "pod-A", "metric": "cpu", "timestamp": 1000}]
    detected = [
        {"pod": "pod-A", "metric": "cpu",    "timestamp": 1001, "is_anomaly": True},
        {"pod": "pod-Z", "metric": "memory", "timestamp": 1001, "is_anomaly": True},  # FP
    ]
    result = evaluate(gt, detected)
    assert result["fp"] == 1
    assert result["precision"] < 1.0


# ── Performance guards ────────────────────────────────────────────────────────

def test_should_run_correlation_first_call():
    import evaluation.performance as perf
    perf._last_run = 0.0   # reset
    assert should_run_correlation() is True

def test_should_run_correlation_too_soon():
    import time, evaluation.performance as perf
    perf._last_run = time.time()
    assert should_run_correlation() is False
