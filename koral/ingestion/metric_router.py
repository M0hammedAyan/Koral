"""
Metric Router — Routes incoming metrics to the correct detector type.

This is the entry point for all metric data flowing into KORAL's detection engine.
Metrics are classified into types (spiky/seasonal/drift/multivariate) and routed
to the appropriate detector (RRCF for spiky, STL+IF for seasonal, etc.).
"""
import logging
from typing import Optional

from koral.config import settings

logger = logging.getLogger(__name__)


# Metric type classification map
# Every metric is classified before routing to a detector
METRIC_TYPE_MAP = {
    "spiky": [
        "kube_pod_container_status_restarts_total",
        "container_oom_events_total",
        "kube_deployment_status_replicas_unavailable",
        "http_requests_error_rate",
        "kube_pod_status_phase",
    ],
    "seasonal": [
        "container_cpu_usage_seconds_total",
        "container_memory_usage_bytes",
        "http_requests_total",
        "nginx_ingress_controller_requests",
        "container_network_receive_bytes_total",
        "container_network_transmit_bytes_total",
    ],
    "drift": [
        "container_memory_working_set_bytes",
        "kube_persistentvolumeclaim_resource_requests_storage_bytes",
        "container_fs_usage_bytes",
        "container_fs_writes_bytes_total",
    ],
}

# Multivariate groups — analyzed together when any single metric in the group fires
MULTIVARIATE_GROUPS = [
    (
        "container_cpu_usage_seconds_total",
        "container_memory_usage_bytes",
        "container_network_transmit_bytes_total",
        "container_network_receive_bytes_total",
        "http_requests_total",
        "http_requests_error_rate",
    ),
]


def classify_metric(metric_name: str) -> str:
    """
    Classify a metric into its detection type.

    Returns one of: "spiky", "seasonal", "drift"
    Defaults to "seasonal" for unknown metrics.
    """
    for metric_type, patterns in METRIC_TYPE_MAP.items():
        for pattern in patterns:
            if metric_name == pattern or metric_name.startswith(pattern):
                return metric_type
    return "seasonal"


def get_multivariate_group(metric_name: str) -> Optional[tuple]:
    """
    Check if a metric belongs to a multivariate group.
    Returns the group tuple if found, None otherwise.

    Multivariate analysis is triggered as a CONFIRMATION layer
    only after the primary detector (RRCF or STL+IF) fires.
    """
    for group in MULTIVARIATE_GROUPS:
        if metric_name in group:
            return group
    return None


def get_detector_for_type(metric_type: str) -> str:
    """
    Map metric type to the detector that should handle it.

    Returns detector identifier string.
    """
    mapping = {
        "spiky": "rrcf",           # Real-time streaming, no seasonal assumption
        "seasonal": "stl_if",      # STL decomposition + Isolation Forest on residual
        "drift": "stl_if",         # STL captures drift in trend component
    }
    return mapping.get(metric_type, "stl_if")
