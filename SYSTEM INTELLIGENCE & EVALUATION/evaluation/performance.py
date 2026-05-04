"""Performance Optimization — caching, top-N filtering, sampling for correlation engine."""
import time
from typing import List

TOP_N = 10                  # only correlate top anomalies
CORRELATION_INTERVAL = 30   # seconds between correlation runs
SAMPLE_EVERY = 3            # keep 1 in N metric samples to reduce data size

_last_run: float = 0.0
_cache: dict = {}


def filter_top_anomalies(anomalies: List[dict]) -> List[dict]:
    """Return only the TOP_N anomalies sorted by z_score descending."""
    return sorted(anomalies, key=lambda x: x.get("z_score", 0), reverse=True)[:TOP_N]


def should_run_correlation() -> bool:
    """Rate-limit correlation to once every CORRELATION_INTERVAL seconds."""
    global _last_run
    now = time.time()
    if now - _last_run >= CORRELATION_INTERVAL:
        _last_run = now
        return True
    return False


def sample_metrics(metrics: List[dict]) -> List[dict]:
    """Downsample metric list to reduce volume sent to correlation engine."""
    return metrics[::SAMPLE_EVERY]


def cached_result(key: str, compute_fn, *args):
    """Simple in-memory cache; returns cached value if key exists."""
    if key not in _cache:
        _cache[key] = compute_fn(*args)
    return _cache[key]


def invalidate_cache(key: str = None):
    """Clear one key or entire cache."""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()
