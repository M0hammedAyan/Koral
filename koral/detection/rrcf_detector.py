"""
RRCF Streaming Detector — Real-time anomaly detection using Robust Random Cut Forest.

CHARACTERISTICS:
- Online: no training required, updates on every data point
- O(log n) per update
- Maintains sliding window tree forest
- Returns anomaly score per point, not binary label
- Score > threshold = anomaly candidate (not confirmed anomaly)

USE FOR: spiky metrics (error rate, OOM, pod restarts)
DO NOT USE FOR: seasonal metrics (use STL+IF instead)
"""
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import rrcf

from koral.config import settings
from koral.detection.base import AnomalyResult, DetectorBase

logger = logging.getLogger(__name__)


class RRCFStreamDetector(DetectorBase):
    """
    Real-time streaming anomaly detection using Robust Random Cut Forest.

    Per the spec (Section 7.2): one detector instance per metric series.
    Must be thread-safe for concurrent pod metrics.
    """

    def __init__(
        self,
        metric_name: str = "",
        pod_name: str = "",
        namespace: str = "",
        num_trees: int = settings.rrcf_num_trees,
        tree_size: int = settings.rrcf_tree_size,
        shingle_size: int = settings.rrcf_shingle_size,
        threshold: float = settings.rrcf_anomaly_threshold,
    ):
        self.metric_name = metric_name
        self.pod_name = pod_name
        self.namespace = namespace
        self.num_trees = num_trees
        self.tree_size = tree_size
        self.shingle_size = shingle_size
        self.threshold = threshold

        # Initialize forest
        self._forest: list[rrcf.RCTree] = [rrcf.RCTree() for _ in range(num_trees)]
        self._buffer: deque = deque(maxlen=shingle_size)
        self._point_index: int = 0
        self._scores: deque = deque(maxlen=tree_size)

    @property
    def detector_type(self) -> str:
        return "rrcf"

    def detect(self, value: float, timestamp: datetime, **kwargs) -> AnomalyResult:
        """
        Process one data point. Returns AnomalyResult immediately.
        Side effect: updates internal forest.

        Steps:
        1. Add value to shingle buffer
        2. If buffer not full: return score=0.0 (warm-up)
        3. Create shingle from buffer
        4. Insert shingle into each tree
        5. Compute codisp (anomaly score) per tree
        6. Average across forest
        7. Normalize to 0.0-1.0 range
        """
        self._buffer.append(value)

        # Not enough data for a full shingle yet — warming up
        if len(self._buffer) < self.shingle_size:
            return AnomalyResult(
                metric_name=self.metric_name,
                pod_name=self.pod_name,
                namespace=self.namespace,
                timestamp=timestamp,
                value=value,
                anomaly_score=0.0,
                is_anomaly=False,
                detector_type="rrcf",
                confidence=0.0,
                metadata={"warmup": True, "buffer_size": len(self._buffer)},
            )

        # Create shingle (sliding window of recent values)
        shingle = np.array(list(self._buffer), dtype=float)
        self._point_index += 1

        # Insert into each tree and compute codisp
        codisps = []
        for tree in self._forest:
            # If tree is full, remove oldest point
            if len(tree.leaves) >= self.tree_size:
                oldest = min(tree.leaves.keys())
                tree.forget_point(oldest)

            # Insert new point
            tree.insert_point(shingle, index=self._point_index)

            # Compute collusive displacement
            try:
                codisp = tree.codisp(self._point_index)
                codisps.append(codisp)
            except Exception:
                codisps.append(0.0)

        # Average codisp across forest
        avg_codisp = float(np.mean(codisps)) if codisps else 0.0

        # Normalize score to 0.0 - 1.0 range
        # Codisp values typically range from 0 to ~tree_size/2
        # We normalize using a sigmoid-like transformation
        normalized_score = self._normalize_score(avg_codisp)
        self._scores.append(normalized_score)

        is_anomaly = normalized_score > self.threshold

        return AnomalyResult(
            metric_name=self.metric_name,
            pod_name=self.pod_name,
            namespace=self.namespace,
            timestamp=timestamp,
            value=value,
            anomaly_score=round(normalized_score, 6),
            is_anomaly=is_anomaly,
            detector_type="rrcf",
            confidence=self._compute_confidence(normalized_score),
            metadata={
                "raw_codisp": round(avg_codisp, 4),
                "threshold": self.threshold,
                "point_index": self._point_index,
                "trees_active": len(self._forest),
            },
        )

    def detect_many(self, series, **kwargs) -> list[AnomalyResult]:
        """Batch variant: processes series sequentially, returns all results."""
        results = []
        if hasattr(series, 'items'):
            # pandas Series
            for timestamp, value in series.items():
                result = self.detect(value=float(value), timestamp=timestamp)
                results.append(result)
        else:
            # list of (timestamp, value) tuples
            for timestamp, value in series:
                result = self.detect(value=float(value), timestamp=timestamp)
                results.append(result)
        return results

    def get_score(self) -> float:
        """Returns most recent anomaly score without updating tree."""
        if not self._scores:
            return 0.0
        return self._scores[-1]

    def _normalize_score(self, raw_codisp: float) -> float:
        """
        Normalize raw codisp to 0.0 - 1.0 using adaptive percentile.

        Uses historical scores to determine what's "normal" vs "anomalous".
        If not enough history: use fixed normalization.
        """
        if len(self._scores) < 20:
            # Fixed normalization during warmup
            # Scale based on tree_size — typical normal codisp ≈ shingle_size
            # Anomalous codisp ≈ tree_size / 4
            normal_baseline = self.shingle_size * 2.0
            return min(1.0, max(0.0, (raw_codisp - normal_baseline) / (self.tree_size / 4)))

        # Adaptive: use historical distribution
        scores_arr = np.array(list(self._scores))
        median = float(np.median(scores_arr))
        p95 = float(np.percentile(scores_arr, 95))

        if p95 <= median or p95 <= 0:
            return min(1.0, max(0.0, raw_codisp / max(self.tree_size / 4, 1.0)))

        # Normalize: median=0.0, p95=0.5, outliers above p95 → 0.5-1.0
        if raw_codisp <= median:
            return 0.0
        range_to_p95 = p95 - median
        if range_to_p95 <= 0:
            return 0.0
        normalized = (raw_codisp - median) / (range_to_p95 * 2)
        return min(1.0, max(0.0, normalized))

    def _compute_confidence(self, score: float) -> float:
        """
        Confidence based on how far above/below threshold the score is.
        Score at threshold = 0.5 confidence.
        Score at 2x threshold = ~0.9 confidence.
        """
        if score <= 0:
            return 0.0
        ratio = score / self.threshold
        # Sigmoid-like confidence
        confidence = 1.0 - (1.0 / (1.0 + ratio))
        return min(1.0, round(confidence, 4))
