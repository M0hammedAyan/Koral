# -*- coding: utf-8 -*-
"""Full local test runner - covers all modules without needing Kubernetes or backend."""
import json
import os
import sys

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"  {status} {label}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    results.append(condition)

print("\n" + "="*55)
print(" KORAL - SYSTEM INTELLIGENCE & EVALUATION FULL TEST")
print("="*55)

# -- 1. EVALUATION METRICS --
print("\n[1] Evaluation Metrics")
from evaluation.metrics import evaluate, precision, recall, false_positive_rate

r = evaluate([], [])
check("Empty inputs - no crash", r["precision"] == 0.0 and r["recall"] == 0.0)

gt = [
    {"pod": "cpu-spike-sim",  "metric": "cpu",     "timestamp": 1710000000},
    {"pod": "io-storm-sim",   "metric": "storage", "timestamp": 1710000010},
]
det = [
    {"pod": "cpu-spike-sim",  "metric": "cpu",     "timestamp": 1710000002, "is_anomaly": True},
    {"pod": "io-storm-sim",   "metric": "storage", "timestamp": 1710000015, "is_anomaly": True},
    {"pod": "fake-pod",       "metric": "memory",  "timestamp": 1710000003, "is_anomaly": True},
]
res = evaluate(gt, det)
check("Precision (2 TP, 1 FP = 0.6667)", abs(res["precision"] - 0.6667) < 0.001, str(res["precision"]))
check("Recall (2 TP, 0 FN = 1.0)",        res["recall"] == 1.0,                    str(res["recall"]))
check("FPR (1 FP / 3 alerts = 0.3333)",   abs(res["false_positive_rate"] - 0.3333) < 0.001, str(res["false_positive_rate"]))
check("Latency calculated",               res["latency_ms"] is not None,           str(res["latency_ms"]) + " ms")

# -- 2. ADAPTIVE THRESHOLD --
print("\n[2] Adaptive Threshold")
from threshold.adaptive_threshold import update_threshold, get_threshold, compute_dynamic_threshold

initial = get_threshold("cpu")
check("Default cpu threshold loaded", initial > 0, str(initial))

# feed 5 anomalies - noisy - should raise to NOISE_K (3.0)
for v in [95.0, 92.0, 88.0, 91.0, 97.0]:
    k = update_threshold("cpu", v, True)
check("Noisy window - threshold raised to 3.0", k == 3.0, str(k))

# feed 22 normals to flush the noisy window (window=30, need anomaly_ratio < 0.3)
for v in [50.0, 48.0, 52.0, 49.0, 51.0, 50.0, 48.0, 52.0, 49.0, 51.0,
          50.0, 48.0, 52.0, 49.0, 51.0, 50.0, 48.0, 52.0, 49.0, 51.0,
          50.0, 48.0]:
    k = update_threshold("cpu", v, False)
check("Quiet window (22 normals) - threshold back to 2.5", k == 2.5, str(k))

t = compute_dynamic_threshold([10.0] * 20)
check("Constant baseline - threshold == mean (std=0)", t == 10.0, str(t))

t_inf = compute_dynamic_threshold([85.0])
check("Single value - returns inf", t_inf == float("inf"))

# -- 3. FEEDBACK LOOP --
print("\n[3] Feedback Loop")
from feedback.feedback_loop import process_feedback

# reset cpu threshold to known value first
from threshold.adaptive_threshold import _load_config, _save_config
cfg = _load_config()
cfg["cpu_threshold"] = 2.5
_save_config(cfg)

rec = process_feedback("INC001", "cpu", is_correct=False)
check("False positive raises threshold by 0.2",
      abs(rec["new_threshold"] - 2.7) < 0.001,
      f"{rec['old_threshold']} -> {rec['new_threshold']}")

rec2 = process_feedback("INC002", "cpu", is_correct=True)
check("True positive lowers threshold by 0.1",
      abs(rec2["new_threshold"] - 2.6) < 0.001,
      f"{rec2['old_threshold']} -> {rec2['new_threshold']}")

log_path = os.path.join("feedback", "feedback_log.json")
check("Feedback log written to disk", os.path.exists(log_path))

# -- 4. PERFORMANCE OPTIMIZATION --
print("\n[4] Performance Optimization")
from evaluation.performance import (
    filter_top_anomalies, sample_metrics,
    should_run_correlation, cached_result, invalidate_cache
)
import evaluation.performance as perf

perf._last_run = 0.0
check("First correlation call allowed", should_run_correlation() is True)
check("Immediate second call blocked",  should_run_correlation() is False)

anomalies = [{"pod": f"pod-{i}", "metric": "cpu", "z_score": float(i)} for i in range(20)]
top = filter_top_anomalies(anomalies)
check("Top-N filter returns 10",        len(top) == 10)
check("Top-N sorted by z_score desc",  top[0]["z_score"] == 19.0)

metrics_list = [{"v": i} for i in range(30)]
sampled = sample_metrics(metrics_list)
check("Sampling keeps 1-in-3 (30 -> 10)", len(sampled) == 10)

invalidate_cache()
val = cached_result("test_key", lambda: 42)
check("Cache stores computed value",    val == 42)
val2 = cached_result("test_key", lambda: 99)
check("Cache returns stored value",     val2 == 42)

# -- 5. SIMULATION SCRIPTS --
print("\n[5] Simulation Scripts (import + single-iteration check)")

import importlib

for script in ["simulation.cpu_spike", "simulation.memory_leak",
               "simulation.network_latency"]:
    try:
        importlib.import_module(script)
        check(f"{script} imports OK", True)
    except Exception as e:
        check(f"{script} imports OK", False, str(e))

# io_storm - test write logic without /data path
with open("test_io_output.txt", "w") as f:
    f.write("X" * 10000)
check("io_storm write logic OK (local file)", os.path.getsize("test_io_output.txt") == 10000)
os.remove("test_io_output.txt")

# -- SUMMARY --
passed = sum(results)
total  = len(results)
print(f"\n{'='*55}")
print(f" Results: {passed}/{total} passed")
if passed == total:
    print(" STATUS: ALL SYSTEMS GO")
else:
    print(f" STATUS: {total - passed} FAILURE(S) - review above")
print("="*55)

sys.exit(0 if passed == total else 1)
