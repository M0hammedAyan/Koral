"""
KORAL Configuration — Pydantic Settings v2.

All configuration is environment-based. No config files, no hardcoded values.
Load via: from koral.config import settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class KoralSettings(BaseSettings):
    """All KORAL environment variables. Grouped by subsystem."""

    # ── Kubernetes ────────────────────────────────────────────────────
    koral_namespace: str = "koral-system"
    koral_target_namespace: str = "default"
    kubeconfig: Optional[str] = None

    # ── VictoriaMetrics ───────────────────────────────────────────────
    vm_url: str = "http://victoria-metrics:8428"
    vm_remote_write_url: str = "http://victoria-metrics:8428/api/v1/write"
    vm_query_url: str = "http://victoria-metrics:8428/api/v1/query_range"

    # ── PostgreSQL ────────────────────────────────────────────────────
    postgres_url: str = "postgresql://koral:password@postgres:5432/koral"
    pgvector_enabled: bool = True

    # ── Alerting ──────────────────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    slack_webhook_url: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email_to: str = ""
    pagerduty_routing_key: str = ""

    # ── LLM ───────────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    llm_primary: str = "anthropic"
    llm_fallback: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    # ── Detection Thresholds ──────────────────────────────────────────
    rrcf_shingle_size: int = 4
    rrcf_tree_size: int = 256
    rrcf_num_trees: int = 40
    rrcf_anomaly_threshold: float = 0.65
    stl_period_hours: int = 24
    stl_seasonal_smoothing: int = 7
    if_contamination: float = 0.05
    lstm_sequence_length: int = 60
    lstm_confidence_threshold: float = 0.75

    # ── Classification ────────────────────────────────────────────────
    classifier_attack_confidence_threshold: float = 0.80
    classifier_overload_confidence_threshold: float = 0.70
    causal_lag_window_seconds: int = 120

    # ── Policy ────────────────────────────────────────────────────────
    shutdown_require_3of3: bool = True
    quarantine_grace_period_seconds: int = 30
    port_shift_grace_period_seconds: int = 30
    port_shift_range_min: int = 49152
    port_shift_range_max: int = 65535
    stateful_pod_auto_shutdown: bool = False

    # ── Alerting Behavior ─────────────────────────────────────────────
    alert_dedup_window_seconds: int = 300
    alert_escalation_warning_seconds: int = 900
    alert_escalation_critical_seconds: int = 300
    alert_cooldown_after_action_seconds: int = 600

    # ── Cardinality Guard ─────────────────────────────────────────────
    max_label_cardinality: int = 1000
    forbidden_labels: str = "request_id,trace_id,user_id,session_id"

    # ── Resource Optimizer ────────────────────────────────────────────
    optimizer_schedule_cron: str = "0 2 * * *"
    over_provisioned_threshold: float = 0.40
    under_provisioned_threshold: float = 0.85

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = KoralSettings()
