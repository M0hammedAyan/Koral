"""
STL Decomposer — Seasonal-Trend decomposition using LOESS.

Decomposes time series into trend + seasonal + residual.
Isolation Forest runs ONLY on the residual component.

THIS IS THE FIX FOR FALSE POSITIVES ON SEASONAL METRICS.
Without STL, IF flags every Monday morning traffic spike as anomalous.
With STL, the seasonal component is stripped — IF only sees deviations
from expected seasonal behavior.

MINIMUM DATA REQUIREMENT: 2 full periods (48 hours for daily seasonality)
Before 2 periods are available: fall back to raw IF on the full signal.
"""
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

from koral.config import settings

logger = logging.getLogger(__name__)


@dataclass
class STLComponents:
    """Result of STL decomposition."""
    trend: pd.Series
    seasonal: pd.Series
    residual: pd.Series
    original: pd.Series

    @property
    def has_valid_residual(self) -> bool:
        """Check that residual has non-null values."""
        return self.residual is not None and len(self.residual.dropna()) > 0


class STLDecomposer:
    """
    Decomposes time series into trend + seasonal + residual using STL.

    Parameters:
        period: Number of data points per seasonal cycle.
                Default 144 = 24 hours at 10-minute scrape interval.
        seasonal: Smoothing parameter for seasonal component.
                  Must be odd. Default 7 (7-period smoothing window).
    """

    def __init__(
        self,
        period: int = 144,  # 144 x 10min = 24 hours
        seasonal: int = 7,  # 7-period smoothing
    ):
        if period < 2:
            raise ValueError("period must be >= 2")
        if seasonal < 3:
            raise ValueError("seasonal must be >= 3")
        if seasonal % 2 == 0:
            seasonal += 1  # Must be odd for LOESS

        self.period = period
        self.seasonal = seasonal

    def has_sufficient_data(self, series: pd.Series) -> bool:
        """
        Returns True only if series spans >= 2 full periods.
        STL needs at minimum 2 complete cycles to extract seasonal pattern.
        """
        non_null = series.dropna()
        if len(non_null) < self.period * 2:
            return False
        return True

    def decompose(self, series: pd.Series) -> Optional[STLComponents]:
        """
        Decompose a time series into trend, seasonal, and residual.

        Returns STLComponents or None if decomposition fails.
        The series must have a DatetimeIndex or integer index.
        NaN values are forward-filled before decomposition.
        """
        if series is None or len(series) == 0:
            return None

        # Clean the series
        clean = series.copy()

        # Fill NaN with forward fill, then backward fill for leading NaN
        clean = clean.ffill().bfill()

        if len(clean) < self.period * 2:
            logger.debug(
                f"[stl] Insufficient data for decomposition: "
                f"{len(clean)} points < {self.period * 2} required"
            )
            return None

        try:
            stl = STL(
                clean,
                period=self.period,
                seasonal=self.seasonal,
                robust=True,  # Robust to outliers in the seasonal estimation
            )
            result = stl.fit()

            return STLComponents(
                trend=result.trend,
                seasonal=result.seasonal,
                residual=result.resid,
                original=clean,
            )
        except Exception as e:
            logger.warning(f"[stl] Decomposition failed: {e}")
            return None

    def get_residual(self, series: pd.Series) -> pd.Series:
        """
        Convenience: decompose and return only the residual.
        If decomposition fails or insufficient data, returns the original series.
        """
        if not self.has_sufficient_data(series):
            return series

        components = self.decompose(series)
        if components is None or not components.has_valid_residual:
            return series

        return components.residual

    def detect_trend_drift(self, series: pd.Series, slope_threshold: float = 0.01) -> bool:
        """
        Check if the trend component shows significant monotonic drift.
        Used by the classifier to identify SEASONAL_DRIFT root cause.

        Returns True if the trend slope exceeds threshold (normalized by series std).
        """
        if not self.has_sufficient_data(series):
            return False

        components = self.decompose(series)
        if components is None:
            return False

        trend = components.trend.dropna()
        if len(trend) < 10:
            return False

        # Compute normalized slope (slope / series std)
        x = np.arange(len(trend), dtype=float)
        coeffs = np.polyfit(x, trend.values, 1)
        slope = coeffs[0]

        series_std = series.std()
        if series_std == 0:
            return False

        normalized_slope = abs(slope) / series_std
        return normalized_slope > slope_threshold
