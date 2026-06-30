"""
STL + Isolation Forest Detector — Batch anomaly detection for seasonal metrics.

Combines STL decomposition with Isolation Forest:
1. Decompose time series into trend + seasonal + residual (STL)
2. Run Isolation Forest ONLY on the residual component
3. Anomalies in the residual = genuine deviations from expected seasonal behavior

USE FOR: seasonal metrics (CPU%, memory%, request rate, latency)
DO NOT USE FOR: spiky metrics (use RRCF instead)

This is a BATCH detector: runs every 5 minutes on the full available window.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from koral.config import settings
from koral.detection.base import AnomalyResult, DetectorBase
from koral.detection.stl_preprocessor import STLDecomposer

logger = logging.getLogger(__name__)


class STLIFDetector(DetectorBase):
    """
    Batch detector combining STL decomposition with Isolation Forest.

    When sufficient data is available (2+ seasonal periods):
      - STL strips the seasonal component
      - IF runs on the residual (deviations from expected pattern)

    When insufficient data:
      - IF runs on the raw signal (graceful fallback)
    """

    def __init__(
        self,
        metric_name: str = "",
        pod_name: str = "",
        namespace: str = "",
        contamination: float = settings.if_contamination,
        period: int = 144,  # 10min scrapes × 144 = 24h
        seasonal: int = 7,
        n_estimators: int = 100,
    ):
        self.metric_name = metric_name
        self.pod_name = pod_name
        self.namespace = namespace
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.stl = STLDecomposer(period=period, seasonal=seasonal)
        self._last_fit_scores: Optional[np.ndarray] = None

    @property
    def detector_type(self) -> str:
        return "stl_if"

    def detect(self, value: float, timestamp: datetime, **kwargs) -> AnomalyResult:
        """
        NOT the primary interface for this detector.
        STL+IF is batch-only. Use detect_many() instead.
        Returns a neutral result with confidence=0.
        """
        return AnomalyResult(
            metric_name=self.metric_name,
            pod_name=self.pod_name,
            namespace=self.namespace,
            timestamp=timestamp,
            value=value,
            anomaly_score=0.0,
            is_anomaly=False,
            detector_type="stl_if",
            confidence=0.0,
            metadata={"error": "STLIFDetector is batch-only. Use detect_many()."},
        )

    def detect_many(self, series: pd.Series, **kwargs) -> list[AnomalyResult]:
        """
        Batch detection on a time series.

        Steps:
        1. If sufficient data → decompose with STL → run IF on residual
        2. If insufficient data → run IF on raw series
        3. Map IF predictions back to original timestamps
        4. Compute anomaly scores from IF decision function
        """
        if series is None or len(series) == 0:
            return []

        # Determine whether to use STL or raw
        use_stl = self.stl.has_sufficient_data(series)

        if use_stl:
            components = self.stl.decompose(series)
            if components is not None and components.has_valid_residual:
                detection_signal = components.residual
            else:
                detection_signal = series
                use_stl = False
        else:
            detection_signal = series

        # Prepare data for Isolation Forest
        values = detection_signal.dropna().values.reshape(-1, 1)
        if len(values) < 10:
            # Not enough data points for meaningful IF
            return self._empty_results(series)

        # Fit Isolation Forest
        model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=42,
        )
        model.fit(values)

        # Get predictions and decision scores
        predictions = model.predict(values)  # 1 = normal, -1 = anomaly
        decision_scores = model.decision_function(values)  # higher = more normal

        # Store scores for later reference
        self._last_fit_scores = decision_scores

        # Build results
        results = []
        clean_index = detection_signal.dropna().index

        for i, (timestamp, _) in enumerate(detection_signal.dropna().items()):
            # Map decision_function to anomaly score (0-1)
            # IF decision_function: positive = normal, negative = anomalous
            raw_score = -decision_scores[i]  # flip: positive = more anomalous
            anomaly_score = self._normalize_if_score(raw_score, decision_scores)
            is_anomaly = predictions[i] == -1

            # Get original value (not residual) for the result
            orig_value = float(series.iloc[i]) if i < len(series) else float(detection_signal.iloc[i])

            results.append(AnomalyResult(
                metric_name=self.metric_name,
                pod_name=self.pod_name,
                namespace=self.namespace,
                timestamp=timestamp,
                value=orig_value,
                anomaly_score=round(float(anomaly_score), 6),
                is_anomaly=is_anomaly,
                detector_type="stl_if",
                confidence=self._compute_confidence(anomaly_score, is_anomaly),
                metadata={
                    "stl_applied": use_stl,
                    "if_decision_score": round(float(decision_scores[i]), 4),
                    "contamination": self.contamination,
                    "sample_count": len(values),
                },
            ))

        return results

    def _normalize_if_score(self, raw_score: float, all_scores: np.ndarray) -> float:
        """
        Normalize IF decision score to 0.0 - 1.0 range.

        IF decision_function ranges roughly from -0.5 (anomalous) to +0.5 (normal).
        We flip and normalize to: 0.0 = clearly normal, 1.0 = clearly anomalous.
        """
        # raw_score is already flipped (positive = anomalous)
        # Typical range: -0.3 (normal) to +0.5 (anomalous)
        score_range = float(np.max(-all_scores) - np.min(-all_scores))
        if score_range <= 0:
            return 0.0

        # Normalize to 0-1 using min-max of the batch
        min_score = float(np.min(-all_scores))
        normalized = (raw_score - min_score) / score_range
        return max(0.0, min(1.0, normalized))

    def _compute_confidence(self, score: float, is_anomaly: bool) -> float:
        """Confidence based on how clearly anomalous/normal the point is."""
        if not is_anomaly:
            return 1.0 - score  # High confidence it's normal
        # For anomalies: higher score = higher confidence
        return min(1.0, score * 1.5)

    def _empty_results(self, series: pd.Series) -> list[AnomalyResult]:
        """Return neutral results when insufficient data."""
        results = []
        for timestamp, value in series.items():
            results.append(AnomalyResult(
                metric_name=self.metric_name,
                pod_name=self.pod_name,
                namespace=self.namespace,
                timestamp=timestamp,
                value=float(value),
                anomaly_score=0.0,
                is_anomaly=False,
                detector_type="stl_if",
                confidence=0.0,
                metadata={"error": "insufficient_data", "sample_count": len(series)},
            ))
        return results
