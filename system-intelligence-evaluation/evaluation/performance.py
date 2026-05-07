"""Performance Optimization Layer — caching, sampling, and latency reduction."""
import time
from functools import lru_cache
from typing import List, Dict

# Cache for correlation results (pod_pair -> correlation_value)
_correlation_cache: Dict[tuple, tuple] = {}
_cache_ttl = 30  # seconds

def filter_top_anomalies(anomalies: List[dict], limit: int = 10) -> List[dict]:
    """Reduce correlation workload by only processing top anomalies."""
    return sorted(anomalies, key=lambda x: abs(x.get("z_score", 0)), reverse=True)[:limit]

def cache_correlation(pod_a: str, pod_b: str, correlation: float, lag: int):
    """Store correlation result with timestamp."""
    key = tuple(sorted([pod_a, pod_b]))
    _correlation_cache[key] = (correlation, lag, time.time())

def get_cached_correlation(pod_a: str, pod_b: str) -> dict | None:
    """Retrieve cached correlation if still valid."""
    key = tuple(sorted([pod_a, pod_b]))
    if key in _correlation_cache:
        corr, lag, ts = _correlation_cache[key]
        if time.time() - ts < _cache_ttl:
            return {"correlation": corr, "lag": lag, "cached": True}
    return None

def sample_metrics(metrics: List[dict], rate: int = 2) -> List[dict]:
    """Downsample metrics to reduce processing load (keep every Nth sample)."""
    return metrics[::rate]

def clear_old_cache():
    """Remove expired cache entries."""
    now = time.time()
    expired = [k for k, (_, _, ts) in _correlation_cache.items() if now - ts > _cache_ttl]
    for k in expired:
        del _correlation_cache[k]

@lru_cache(maxsize=128)
def compute_threshold_cached(metric: str, k: float) -> float:
    """Cached threshold computation to avoid redundant calculations."""
    return k  # Placeholder; actual logic in adaptive_threshold.py
