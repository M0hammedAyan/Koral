"""Evaluation Metrics Engine — precision, recall, FPR, detection latency."""
from typing import List


def precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def false_positive_rate(fp: int, total_alerts: int) -> float:
    return fp / total_alerts if total_alerts > 0 else 0.0


def detection_latency_ms(event_time: float, detection_time: float) -> float:
    """Both times as Unix timestamps (seconds)."""
    return (detection_time - event_time) * 1000


def evaluate(ground_truth: List[dict], detected: List[dict]) -> dict:
    """
    ground_truth: [{"pod": "pod-A", "metric": "cpu", "timestamp": 1710000000}, ...]
    detected:     [{"pod": "pod-A", "metric": "cpu", "timestamp": 1710000001, "is_anomaly": True}, ...]
    """
    gt_keys = {(e["pod"], e["metric"]) for e in ground_truth}
    det_map = {(e["pod"], e["metric"]): e for e in detected if e.get("is_anomaly")}

    tp = len(gt_keys & det_map.keys())
    fp = len(det_map.keys() - gt_keys)
    fn = len(gt_keys - det_map.keys())

    latencies = []
    for e in ground_truth:
        key = (e["pod"], e["metric"])
        if key in det_map:
            latencies.append(detection_latency_ms(e["timestamp"], det_map[key]["timestamp"]))

    total_alerts = tp + fp
    return {
        "precision": round(precision(tp, fp), 4),
        "recall": round(recall(tp, fn), 4),
        "false_positive_rate": round(false_positive_rate(fp, total_alerts), 4),
        "latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "tp": tp, "fp": fp, "fn": fn
    }
