"""
Detection Base Classes — ABC interface for all KORAL detectors.

Every detector (RRCF, STL+IF, LSTM) must implement this interface.
The existing IsolationForestDetector in correlation-engine/ also conforms.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import pandas as pd


@dataclass
class AnomalyResult:
    """Standard anomaly detection result from any KORAL detector."""

    metric_name: str
    pod_name: str
    namespace: str
    timestamp: datetime
    value: float
    anomaly_score: float          # 0.0 = normal, 1.0 = maximum anomaly
    is_anomaly: bool              # score > detector threshold
    detector_type: str            # "rrcf" | "stl_if" | "lstm"
    confidence: float             # detector-specific confidence (0.0 - 1.0)
    metadata: dict = field(default_factory=dict)

    @property
    def severity(self) -> str:
        """Map anomaly score to severity level."""
        if self.anomaly_score >= 0.9:
            return "critical"
        elif self.anomaly_score >= 0.7:
            return "high"
        elif self.anomaly_score >= 0.5:
            return "medium"
        return "low"


@dataclass
class ConfirmationResult:
    """Result from the LSTM confirmation layer."""

    confirmed: bool
    confidence: float
    per_feature_reconstruction_error: dict = field(default_factory=dict)
    dominant_anomalous_feature: Optional[str] = None
    reason: str = ""


class DetectorBase(ABC):
    """
    Abstract base class for all KORAL anomaly detectors.

    All detectors must implement at least one of:
      - detect(): single data point (streaming)
      - detect_many(): batch of data points

    Convention:
      - Streaming detectors (RRCF): implement detect(), detect_many() calls detect() in loop
      - Batch detectors (STL+IF): implement detect_many(), detect() raises NotImplementedError
    """

    @abstractmethod
    def detect(self, value: float, timestamp: datetime, **kwargs) -> AnomalyResult:
        """
        Process a single data point and return an AnomalyResult.
        For streaming detectors (RRCF). Updates internal state.
        """
        raise NotImplementedError

    def detect_many(self, series: pd.Series, **kwargs) -> list[AnomalyResult]:
        """
        Process a batch of data points. Default implementation calls detect() in loop.
        Batch detectors (STL+IF) should override this.
        """
        results = []
        for timestamp, value in series.items():
            result = self.detect(value=float(value), timestamp=timestamp, **kwargs)
            results.append(result)
        return results

    @property
    @abstractmethod
    def detector_type(self) -> str:
        """Return detector type identifier (e.g., 'rrcf', 'stl_if', 'lstm')."""
        pass
