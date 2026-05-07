"""Dynamic Anomaly Threshold System — adaptive k-sigma thresholds per metric."""
import json
import os
from collections import deque
from statistics import mean, stdev

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "thresholds.json")

DEFAULT_K = 2.5
NOISE_K = 3.0
NOISE_RATIO = 0.3          # if >30% of recent window are anomalies → noisy
WINDOW_SIZE = 30           # samples per metric window

_windows: dict[str, deque] = {}


def _load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def _save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get_threshold(metric: str) -> float:
    cfg = _load_config()
    return cfg.get(f"{metric}_threshold", DEFAULT_K)


def update_threshold(metric: str, value: float, is_anomaly: bool) -> float:
    """Feed a new sample; returns the current k threshold for this metric."""
    if metric not in _windows:
        _windows[metric] = deque(maxlen=WINDOW_SIZE)
    _windows[metric].append((value, is_anomaly))

    window = _windows[metric]
    if len(window) < 5:
        return get_threshold(metric)

    anomaly_ratio = sum(1 for _, a in window if a) / len(window)
    k = NOISE_K if anomaly_ratio > NOISE_RATIO else DEFAULT_K

    cfg = _load_config()
    cfg[f"{metric}_threshold"] = round(k, 2)
    _save_config(cfg)
    return k


def compute_dynamic_threshold(values: list[float], k: float = DEFAULT_K) -> float:
    """Returns mean + k * std for a list of recent metric values."""
    if len(values) < 2:
        return float("inf")
    m = mean(values)
    s = stdev(values)
    return m + k * s
