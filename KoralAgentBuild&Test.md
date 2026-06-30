# KORAL — Complete Agent Build & Test Specification
**Version:** 2.0 | **Author:** Research synthesis from full design session  
**Target Agent:** Claude Code / Cline (qwen2.5-coder:7b local fallback)  
**Project Path:** `D:\MY_Projects\KORAL` (Windows, 16GB RAM)  
**Status:** Detection engine exists (Isolation Forest). Everything below is the target state.

---

## 0. PRIME DIRECTIVE FOR AGENT

Read this entire document before writing a single line of code.  
Build in the exact layer order specified in Section 10.  
Never skip a validation gate. If a gate fails, stop and report — do not proceed.  
Every function must have a corresponding test before being marked complete.  
Synthetic data is forbidden for calibration. Use only real cluster data or published benchmark datasets (Google Cluster Traces 2019, Alibaba Cluster Trace v2018).

---

## 1. WHAT KORAL IS

KORAL is a self-hosted, open-source, namespace-scoped AIOps platform for Kubernetes.

**Core value proposition:**
- Monitors pods in real time across 6 layers
- Classifies every anomaly into exactly one of 3 root cause classes: Seasonal Drift / Workload Overload / External Attack
- Responds proportionally per class — never takes the same action for different root causes
- Alerts developers at every layer with structured, deduplicated, tiered messages
- Autonomously remediates safe actions; requires human approval for dangerous ones
- Shifts service ports under attack without container restarts (zero-downtime)
- Optimizes resource allocation nightly by profiling pod usage patterns
- Explains every decision in plain English via LLM with in-context learning

**What KORAL is NOT:**
- Not a cluster-wide admin tool (namespace-scoped only)
- Not a replacement for Prometheus/Grafana (integrates with them)
- Not dependent on cloud providers (fully self-hostable)
- Not a single-algorithm anomaly detector

---

## 2. CURRENT STATE (as of build start)

```
EXISTS:
  - anomaly.py          → IsolationForestDetector with detect()/detect_many() interface
  - Helm chart          → deployed, namespace-scoped RBAC
  - PostgreSQL          → partitioned tables set up
  - MCP servers         → configured (Prometheus, Grafana, AlertManager, Slack, Telegram,
                          Kubernetes, Docker, Vault, Helm, Trivy, Playwright, Jaeger,
                          Filesystem, GitHub, OpenTelemetry)
  - VictoriaMetrics     → identified as storage target, NOT yet integrated
  - mTLS                → implemented
  - Multi-tenancy       → implemented

DOES NOT EXIST (build targets):
  - RRCF streaming detector
  - STL decomposition preprocessing
  - LSTM autoencoder (confirmation layer)
  - 3-class root cause classifier
  - Causal sequence analyzer (Granger-style)
  - Policy engine
  - Action engine (remediation + port shifting)
  - Tiered alerting pipeline
  - LLM explain layer with ICL
  - Resource optimizer / pod profiler
  - Falco integration
  - Real data validation pipeline
```

---

## 3. FULL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KORAL ARCHITECTURE                           │
│                                                                     │
│  INGESTION                                                          │
│  VictoriaMetrics ← vmagent (push/pull) ← Prometheus scrapers       │
│  Falco ────────────────────────────────→ Falcosidekick              │
│                          │                       │                  │
│  LAYER 1 — DETECT        │                       │                  │
│  Metric stream → STL Decompose → [Trend|Season|Residual]            │
│                               → RRCF (residual, real-time)         │
│                               → IF   (residual, batch 5min)        │
│  Falco stream ────────────────────────────────────→ Process signals │
│                          │                       │                  │
│  LAYER 2 — CLASSIFY      │                       │                  │
│  [Causal Sequencer] + [Signal Aggregator] + [Time Scorer]          │
│  → 3-Class: DRIFT | OVERLOAD | ATTACK                              │
│  → Confidence score (0-1)                                          │
│  → Attack subtype: DDoS | CryptoMine | Exfil | PortScan           │
│                          │                                          │
│  LAYER 3 — DECIDE        │                                          │
│  Policy Engine: class + confidence + pod_type → response_plan       │
│  Response plan: [action, tier, requires_approval, rollback]         │
│                          │                                          │
│  LAYER 4 — ACT           │                                          │
│  Drift    → update_baseline()                                       │
│  Overload → scale_out() | recommend_limits()                       │
│  Attack   → quarantine() → confirm_3of3() → shutdown_pod()         │
│           → port_shift() [if port-targeted attack]                 │
│                          │                                          │
│  LAYER 5 — EXPLAIN       │                                          │
│  LLM (ICL, few-shot) → incident summary → Slack thread             │
│                          │                                          │
│  LAYER 6 — OPTIMIZE      │                                          │
│  Nightly: K-means pod profiling → resource recommendations          │
│                          │                                          │
│  ALERTING (runs at every layer)                                     │
│  AlertManager → Tier routing → Telegram | Slack | Email | PagerDuty│
│  PostgreSQL ← every alert logged regardless of channel              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. TECHNOLOGY STACK

```yaml
language:         Python 3.11+
package_manager:  pip (requirements.txt per module)
runtime:          Kubernetes (namespace-scoped)
deployment:       Helm chart (exists)

detection:
  rrcf:           rrcf==0.4.4
  stl:            statsmodels>=0.14.0
  isolation_forest: scikit-learn>=1.4.0  # existing
  lstm:           torch>=2.0.0 (CPU only, 16GB RAM constraint)

storage:
  timeseries:     VictoriaMetrics (remote write from Prometheus)
  relational:     PostgreSQL 15 (partitioned, exists)
  vector:         pgvector extension on existing PostgreSQL (for RAG)

security:
  runtime:        Falco (DaemonSet, eBPF mode)
  routing:        Falcosidekick → AlertManager
  admission:      OPA Gatekeeper (existing)

alerting:
  router:         AlertManager (existing MCP)
  channels:       Telegram bot, Slack webhook (existing MCP)
  email:          SMTP (configure via Vault secret)
  escalation:     PagerDuty webhook (optional, configure via env)

llm:
  primary:        Anthropic Claude claude-sonnet-4-6 via API
  fallback:       Ollama qwen2.5-coder:7b (local, air-gapped)
  method:         In-context learning (ICL) — NO fine-tuning

kubernetes_client: kubernetes>=28.0.0 (Python)
metrics_client:    prometheus-api-client>=0.5.3
http_framework:    FastAPI>=0.110.0
task_queue:        Celery + Redis (for async action execution)
config:            Pydantic Settings v2 (environment-based)
```

---

## 5. PROJECT DIRECTORY STRUCTURE

```
D:\MY_Projects\KORAL\
├── AGENTS.md                    ← THIS FILE (agent reads this first)
├── CLAUDE.md                    ← Session handoff state
├── activeContext.md             ← Current task, last action, next step
├── memory-bank/
│   ├── projectbrief.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
│
├── koral/
│   ├── __init__.py
│   ├── config.py                ← Pydantic Settings (all env vars)
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── victoria_client.py   ← VictoriaMetrics remote write + query
│   │   ├── prometheus_client.py ← PromQL query wrapper
│   │   ├── falco_consumer.py    ← Falcosidekick webhook receiver
│   │   └── metric_router.py     ← Routes metrics to correct detector type
│   │
│   ├── detection/               ← LAYER 1
│   │   ├── __init__.py
│   │   ├── base.py              ← DetectorBase ABC (detect/detect_many interface)
│   │   ├── anomaly.py           ← EXISTING IsolationForestDetector (preserve interface)
│   │   ├── rrcf_detector.py     ← NEW: RRCFStreamDetector
│   │   ├── stl_preprocessor.py  ← NEW: STLDecomposer (trend/seasonal/residual)
│   │   ├── lstm_autoencoder.py  ← NEW: LSTMAnomalyConfirmer (confirmation layer only)
│   │   └── detector_factory.py  ← NEW: Routes metric_type → correct detector
│   │
│   ├── classification/          ← LAYER 2
│   │   ├── __init__.py
│   │   ├── causal_analyzer.py   ← Granger-style causal sequence detector
│   │   ├── signal_aggregator.py ← Combines metric + process + time signals
│   │   ├── time_scorer.py       ← Time-of-day/day-of-week alignment scorer
│   │   ├── classifier.py        ← 3-class root cause classifier
│   │   └── attack_subtypes.py   ← DDoS | CryptoMine | Exfil | PortScan signatures
│   │
│   ├── policy/                  ← LAYER 3
│   │   ├── __init__.py
│   │   ├── engine.py            ← Policy Engine (class + confidence → response plan)
│   │   ├── response_plan.py     ← ResponsePlan dataclass
│   │   ├── rules.yaml           ← Declarative policy rules (editable without code change)
│   │   └── approval_gate.py     ← Human approval workflow for dangerous actions
│   │
│   ├── actions/                 ← LAYER 4
│   │   ├── __init__.py
│   │   ├── base_action.py       ← ActionBase ABC with execute/rollback/verify interface
│   │   ├── safe_actions.py      ← restart_pod, scale_out, cache_flush, config_reload
│   │   ├── quarantine.py        ← network_isolate_pod (NetworkPolicy patch)
│   │   ├── shutdown.py          ← selective_pod_shutdown (3-of-3 gated)
│   │   ├── port_shift.py        ← zero_downtime_port_shift
│   │   ├── baseline_update.py   ← update_seasonal_baseline
│   │   └── action_executor.py   ← Celery task wrapper with rollback on failure
│   │
│   ├── explain/                 ← LAYER 5
│   │   ├── __init__.py
│   │   ├── llm_client.py        ← Anthropic API + Ollama fallback
│   │   ├── icl_builder.py       ← Builds few-shot context from incident history
│   │   ├── summarizer.py        ← Generates incident summary in standard format
│   │   └── few_shot_store.py    ← PostgreSQL-backed ICL example store
│   │
│   ├── optimize/                ← LAYER 6
│   │   ├── __init__.py
│   │   ├── pod_profiler.py      ← K-means clustering on resource usage patterns
│   │   ├── resource_recommender.py ← Generates VPA/HPA recommendations
│   │   └── waste_reporter.py    ← Nightly over/under-provisioning report
│   │
│   ├── alerting/
│   │   ├── __init__.py
│   │   ├── alert_manager.py     ← AlertManager webhook sender
│   │   ├── telegram_notifier.py ← Structured Telegram messages
│   │   ├── slack_notifier.py    ← Structured Slack messages with threading
│   │   ├── alert_store.py       ← PostgreSQL alert log (every alert persisted)
│   │   ├── deduplicator.py      ← 5-minute grouping window, suppression logic
│   │   ├── escalator.py         ← WARNING→CRITICAL→EMERGENCY ladder
│   │   └── message_templates.py ← Standardized alert format per tier
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── victoria_metrics.py  ← Remote write + MetricsQL query client
│   │   ├── postgres.py          ← SQLAlchemy models + session management
│   │   ├── models.py            ← ORM: Incident, Alert, Pod, Baseline, FewShot tables
│   │   └── cardinality_guard.py ← Rejects labels exceeding cardinality bounds
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              ← FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── health.py        ← /health, /ready
│   │   │   ├── incidents.py     ← GET /incidents, GET /incidents/{id}
│   │   │   ├── pods.py          ← GET /pods, GET /pods/{name}/profile
│   │   │   ├── alerts.py        ← GET /alerts, POST /alerts/acknowledge
│   │   │   ├── approve.py       ← POST /approve/{action_id} (human approval gate)
│   │   │   └── recommendations.py ← GET /recommendations (resource optimization)
│   │   └── middleware.py        ← mTLS verification, namespace scoping
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py           ← Structured JSON logging (every component)
│       ├── metrics.py           ← KORAL self-monitoring (expose own metrics)
│       └── time_utils.py        ← Timezone-aware timestamp handling
│
├── tests/
│   ├── unit/
│   │   ├── test_rrcf_detector.py
│   │   ├── test_stl_preprocessor.py
│   │   ├── test_lstm_confirmer.py
│   │   ├── test_classifier.py
│   │   ├── test_causal_analyzer.py
│   │   ├── test_policy_engine.py
│   │   ├── test_port_shift.py
│   │   ├── test_quarantine.py
│   │   ├── test_shutdown.py
│   │   ├── test_deduplicator.py
│   │   └── test_message_templates.py
│   │
│   ├── integration/
│   │   ├── test_detection_pipeline.py    ← L1→L2 full flow
│   │   ├── test_classification_pipeline.py ← L2→L3 full flow
│   │   ├── test_action_pipeline.py       ← L3→L4 full flow
│   │   ├── test_alert_pipeline.py        ← All tiers, all channels
│   │   └── test_port_shift_e2e.py        ← Full zero-downtime shift
│   │
│   ├── scenario/                         ← 3-class scenario tests (CRITICAL)
│   │   ├── test_scenario_drift.py        ← Must NOT trigger action
│   │   ├── test_scenario_overload.py     ← Must trigger scale-out only
│   │   ├── test_scenario_ddos.py         ← Must trigger quarantine → shutdown
│   │   ├── test_scenario_cryptomining.py ← Must trigger quarantine → shutdown
│   │   ├── test_scenario_exfil.py        ← Must trigger quarantine → shutdown
│   │   └── test_scenario_false_positive.py ← Must NOT trigger any action
│   │
│   └── fixtures/
│       ├── real_cluster_metrics/        ← Populate with IISc data when available
│       ├── benchmark_datasets/          ← Google Cluster Traces, Alibaba Trace
│       ├── attack_signatures/           ← Known crypto mining, DDoS, exfil patterns
│       └── synthetic_baselines/         ← ONLY for unit tests, never for calibration
│
├── helm/                                ← Existing Helm chart
├── deploy/
│   ├── falco/
│   │   ├── falco-values.yaml            ← Falco Helm values (eBPF mode)
│   │   ├── falcosidekick-values.yaml    ← Routes to AlertManager
│   │   └── custom-rules.yaml            ← KORAL-specific Falco rules
│   ├── victoria-metrics/
│   │   └── vm-values.yaml               ← VictoriaMetrics single-node values
│   └── postgres/
│       └── migrations/                  ← Alembic migration files
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ALERT_RUNBOOK.md                 ← What each alert means + human action
│   └── API.md
│
├── requirements/
│   ├── base.txt
│   ├── detection.txt
│   ├── ml.txt
│   └── dev.txt
│
└── .env.example                         ← All required environment variables listed
```

---

## 6. ENVIRONMENT VARIABLES (complete list)

```bash
# Kubernetes
KORAL_NAMESPACE=koral-system
KORAL_TARGET_NAMESPACE=default          # namespace to monitor
KUBECONFIG=/path/to/kubeconfig

# VictoriaMetrics
VM_URL=http://victoria-metrics:8428
VM_REMOTE_WRITE_URL=http://victoria-metrics:8428/api/v1/write
VM_QUERY_URL=http://victoria-metrics:8428/api/v1/query_range

# PostgreSQL
POSTGRES_URL=postgresql://koral:password@postgres:5432/koral
PGVECTOR_ENABLED=true

# Alerting
TELEGRAM_BOT_TOKEN=<from Vault>
TELEGRAM_CHAT_ID=<from Vault>
SLACK_WEBHOOK_URL=<from Vault>
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<from Vault>
SMTP_PASSWORD=<from Vault>
ALERT_EMAIL_TO=<developer email>
PAGERDUTY_ROUTING_KEY=<from Vault>      # optional

# LLM
ANTHROPIC_API_KEY=<from Vault>
LLM_PRIMARY=anthropic
LLM_FALLBACK=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Detection thresholds (tune with real data)
RRCF_SHINGLE_SIZE=4
RRCF_TREE_SIZE=256
RRCF_NUM_TREES=40
RRCF_ANOMALY_THRESHOLD=0.65             # MUST recalibrate with real data
STL_PERIOD_HOURS=24                     # daily seasonality
STL_SEASONAL_SMOOTHING=7               # days
IF_CONTAMINATION=0.05                  # MUST recalibrate with real data
LSTM_SEQUENCE_LENGTH=60                # 60 data points lookback
LSTM_CONFIDENCE_THRESHOLD=0.75

# Classification
CLASSIFIER_ATTACK_CONFIDENCE_THRESHOLD=0.80
CLASSIFIER_OVERLOAD_CONFIDENCE_THRESHOLD=0.70
CAUSAL_LAG_WINDOW_SECONDS=120          # how far back to look for cause

# Policy
SHUTDOWN_REQUIRE_3OF3=true             # never change this to false
QUARANTINE_GRACE_PERIOD_SECONDS=30
PORT_SHIFT_GRACE_PERIOD_SECONDS=30
PORT_SHIFT_RANGE_MIN=49152
PORT_SHIFT_RANGE_MAX=65535
STATEFUL_POD_AUTO_SHUTDOWN=false       # never change this to true

# Alerting
ALERT_DEDUP_WINDOW_SECONDS=300        # 5 minutes
ALERT_ESCALATION_WARNING_SECONDS=900  # 15 min → CRITICAL
ALERT_ESCALATION_CRITICAL_SECONDS=300 # 5 min → EMERGENCY
ALERT_COOLDOWN_AFTER_ACTION_SECONDS=600 # 10 min suppress after action taken

# Cardinality guard
MAX_LABEL_CARDINALITY=1000            # reject labels exceeding this unique value count
FORBIDDEN_LABELS=request_id,trace_id,user_id,session_id

# Resource optimizer
OPTIMIZER_SCHEDULE_CRON=0 2 * * *    # 2 AM nightly
OVER_PROVISIONED_THRESHOLD=0.40      # actual/requested < 40%
UNDER_PROVISIONED_THRESHOLD=0.85     # actual/requested > 85%
```

---

## 7. LAYER 1 — DETECTION ENGINE

### 7.1 Metric Routing Logic

```python
# detector_factory.py
# Every metric is classified into one of 4 types before routing to detector

METRIC_TYPE_MAP = {
    "spiky": [
        "kube_pod_container_status_restarts_total",
        "container_oom_events_total",
        "kube_deployment_status_replicas_unavailable",
        "http_requests_error_rate",
    ],
    "seasonal": [
        "container_cpu_usage_seconds_total",
        "container_memory_usage_bytes",
        "http_requests_total",
        "nginx_ingress_controller_requests",
    ],
    "drift": [
        "container_memory_working_set_bytes",     # memory leaks
        "kube_persistentvolumeclaim_resource_requests_storage_bytes",
        "container_fs_usage_bytes",
    ],
    "multivariate": [
        # groups of metrics analyzed together by LSTM
        # triggered only when L1 spiky/seasonal fires first
        ("container_cpu_usage_seconds_total",
         "container_memory_usage_bytes",
         "container_network_transmit_bytes_total",
         "http_requests_total"),
    ]
}

def route_metric(metric_name: str) -> str:
    for metric_type, metrics in METRIC_TYPE_MAP.items():
        if any(m == metric_name or metric_name.startswith(m) for m in metrics if isinstance(m, str)):
            return metric_type
    return "seasonal"  # default: treat unknown metrics as seasonal
```

### 7.2 RRCF Streaming Detector

```python
# rrcf_detector.py — implement this exactly

class RRCFStreamDetector(DetectorBase):
    """
    Real-time streaming anomaly detection using Robust Random Cut Forest.
    
    CHARACTERISTICS:
    - Online: no training required, updates on every data point
    - O(log n) per update
    - Maintains sliding window tree forest
    - Returns anomaly score per point, not binary label
    - Score > threshold = anomaly candidate (not confirmed anomaly)
    
    USE FOR: spiky metrics (error rate, OOM, pod restarts)
    DO NOT USE FOR: seasonal metrics (use STL+IF instead)
    """
    
    def __init__(self, 
                 num_trees: int = 40,        # from env RRCF_NUM_TREES
                 tree_size: int = 256,        # from env RRCF_TREE_SIZE
                 shingle_size: int = 4,       # from env RRCF_SHINGLE_SIZE
                 threshold: float = 0.65):    # RECALIBRATE WITH REAL DATA
        pass
    
    def detect(self, value: float, timestamp: datetime) -> AnomalyResult:
        """
        Process one data point. Returns AnomalyResult immediately.
        Side effect: updates internal forest.
        Must be thread-safe (one detector instance per metric series).
        """
        pass
    
    def detect_many(self, series: pd.Series) -> list[AnomalyResult]:
        """Batch variant: processes series sequentially, returns all results."""
        pass
    
    def get_score(self) -> float:
        """Returns current anomaly score without updating tree."""
        pass

# AnomalyResult dataclass
@dataclass
class AnomalyResult:
    metric_name: str
    pod_name: str
    namespace: str
    timestamp: datetime
    value: float
    anomaly_score: float          # 0.0 = normal, 1.0 = maximum anomaly
    is_anomaly: bool              # score > threshold
    detector_type: str            # "rrcf" | "stl_if" | "lstm"
    confidence: float             # detector-specific confidence
    metadata: dict                # additional context
```

### 7.3 STL Preprocessor + IF Detector

```python
# stl_preprocessor.py

class STLDecomposer:
    """
    Decomposes time series into trend + seasonal + residual.
    Isolation Forest runs ONLY on the residual component.
    
    THIS IS THE FIX FOR FALSE POSITIVES ON SEASONAL METRICS.
    Without STL, IF flags every Monday morning traffic spike as anomalous.
    With STL, the seasonal component is stripped — IF only sees deviations
    from expected seasonal behavior.
    
    MINIMUM DATA REQUIREMENT: 2 full periods (48 hours for daily seasonality)
    Before 2 periods are available: fall back to raw IF on the full signal.
    """
    
    def __init__(self, period: int = 144, # 144 x 10min scrapes = 24 hours
                 seasonal: int = 7):       # 7-period smoothing window
        pass
    
    def decompose(self, series: pd.Series) -> STLComponents:
        """Returns namedtuple with .trend, .seasonal, .residual"""
        pass
    
    def has_sufficient_data(self, series: pd.Series) -> bool:
        """Returns True only if series spans >= 2 full periods."""
        pass

# stl_if_detector.py
class STLIFDetector(DetectorBase):
    """
    Combines STL decomposition with Isolation Forest.
    Batch detector: runs every 5 minutes on the full available window.
    
    USE FOR: seasonal metrics (CPU%, memory%, request rate, latency)
    """
    
    def __init__(self, contamination: float = 0.05): # RECALIBRATE WITH REAL DATA
        self.stl = STLDecomposer()
        self.if_detector = IsolationForest(contamination=contamination)
        self._fitted = False
    
    def detect_many(self, series: pd.Series) -> list[AnomalyResult]:
        """
        1. Decompose with STL
        2. If insufficient data: fit/predict on raw series
        3. If sufficient data: fit/predict on residual only
        4. Map residual anomaly indices back to original timestamps
        """
        pass
    
    def detect(self, value: float, timestamp: datetime) -> AnomalyResult:
        """Not the primary interface for this detector. Raise NotImplementedError."""
        raise NotImplementedError("STLIFDetector is batch-only. Use detect_many().")
```

### 7.4 LSTM Autoencoder — Confirmation Layer Only

```python
# lstm_autoencoder.py
# IMPORTANT: This is NOT a primary detector.
# It runs ONLY when Layer 1 (RRCF or STL+IF) has already flagged an anomaly.
# Purpose: multivariate cross-metric correlation confirmation.

class LSTMAnomalyConfirmer:
    """
    Multivariate LSTM Autoencoder.
    Architecture: 2-layer LSTM encoder (hidden=64) → 2-layer LSTM decoder
    Input: sequence of [cpu, memory, net_in, net_out, error_rate, request_rate]
    Output: reconstruction error per feature
    Anomaly: reconstruction error > threshold (calibrated on normal data)
    
    RAM CONSTRAINT: This model must stay under 200MB on 16GB Windows machine.
    Architecture is intentionally small.
    
    DO NOT TRAIN ON SYNTHETIC DATA.
    Model is un-trained until real cluster data is available.
    Until then: confirm() always returns confidence=0.0, confirmed=False.
    """
    
    MODEL_PATH = "models/lstm_autoencoder.pt"
    FEATURES = ["cpu_usage", "memory_usage", "net_transmit", 
                "net_receive", "error_rate", "request_rate"]
    SEQUENCE_LENGTH = 60    # 60 x 10sec scrape = 10 minutes lookback
    
    def __init__(self):
        self.model = None
        self.threshold = None
        self.scaler = None
        self._is_trained = False
    
    def is_trained(self) -> bool:
        return self._is_trained and Path(self.MODEL_PATH).exists()
    
    def confirm(self, 
                multivariate_window: pd.DataFrame,
                pod_name: str) -> ConfirmationResult:
        """
        Called by Layer 2 classifier when primary detector fires.
        Returns ConfirmationResult with:
          - confirmed: bool
          - confidence: float (0.0 if not trained)
          - per_feature_reconstruction_error: dict
          - dominant_anomalous_feature: str
        
        If not trained: return ConfirmationResult(confirmed=False, confidence=0.0)
        """
        if not self.is_trained():
            return ConfirmationResult(confirmed=False, confidence=0.0, 
                                      reason="Model not trained on real data yet")
        pass
    
    def train(self, normal_sequences: pd.DataFrame, epochs: int = 50):
        """
        Train on NORMAL sequences only (autoencoder learns normal → high error = anomalous).
        Must log training loss curve to PostgreSQL for later inspection.
        Must save model checkpoint after every 10 epochs.
        """
        pass
    
    def calibrate_threshold(self, validation_sequences: pd.DataFrame):
        """
        Sets reconstruction error threshold at 99th percentile of normal data.
        Call after train() completes.
        """
        pass
```

---

## 8. LAYER 2 — 3-CLASS CLASSIFIER

### 8.1 Signal Matrix (implements the research findings exactly)

```python
# classifier.py

class RootCauseClassifier:
    """
    Classifies every anomaly into exactly one of 3 classes.
    Uses 5 independent signals and combines them into a confidence-weighted decision.
    
    THE CLASSIFIER NEVER DEFAULTS TO "ATTACK" WITHOUT CORROBORATION.
    A wrong attack classification → wrong shutdown → financial loss.
    """
    
    CLASSES = ["SEASONAL_DRIFT", "WORKLOAD_OVERLOAD", "EXTERNAL_ATTACK"]
    
    SIGNALS = {
        "causal_sequence":  0.35,  # highest weight — causation precedes effect?
        "cpu_request_ratio": 0.25, # CPU:Request ratio stable or broken?
        "error_rate_timing": 0.15, # error rate concurrent with traffic or lagged?
        "process_signal":   0.15,  # Falco fired in same pod same window?
        "time_alignment":   0.10,  # anomaly time aligns with known calendar patterns?
    }
    
    def classify(self, 
                 pod_name: str,
                 namespace: str,
                 anomaly_results: list[AnomalyResult],
                 falco_events: list[FalcoEvent],
                 metric_history: pd.DataFrame,
                 timestamp: datetime) -> ClassificationResult:
        """
        Returns ClassificationResult:
          - root_cause: str (one of CLASSES)
          - confidence: float (0.0 - 1.0)
          - attack_subtype: str | None
          - signal_scores: dict (per-signal breakdown)
          - evidence: list[str] (human-readable evidence list for LLM layer)
        """
        pass
```

### 8.2 Causal Sequence Analyzer

```python
# causal_analyzer.py

class CausalSequenceAnalyzer:
    """
    Determines whether resource anomalies are CAUSED BY request load
    or whether resources are anomalous INDEPENDENTLY of load.
    
    OVERLOAD pattern (legitimate):
      request_rate RISES FIRST (t=0)
      cpu RISES AFTER (t=30-120s lag)
      memory RISES AFTER cpu (t=60-240s lag)
      Ratio cpu/request stays stable
    
    ATTACK pattern:
      cpu RISES with NO preceding request rate change
      OR cpu rises but cpu/request ratio is BROKEN (cpu high, requests normal/flat)
      OR egress traffic rises with NO cpu rise (data exfiltration)
    
    DRIFT pattern:
      trend component of STL is rising over days
      no sudden spike in residual
      seasonal component unchanged
    """
    
    def analyze(self,
                metric_history: pd.DataFrame,  # last 10 minutes of all metrics
                lag_window_seconds: int = 120) -> CausalResult:
        """
        Returns CausalResult:
          - cause_precedes_effect: bool
          - cpu_request_ratio_stable: bool
          - dominant_metric: str (what changed first)
          - lag_seconds: int (how many seconds between cause and effect)
          - exfil_signature: bool (egress up, cpu flat)
          - trend_drift_detected: bool (from STL trend slope)
        """
        pass
```

### 8.3 Attack Subtype Detection

```python
# attack_subtypes.py

ATTACK_SIGNATURES = {
    "CRYPTO_MINING": {
        "description": "Sustained CPU spike >85%, flat request rate, new process spawn",
        "required_signals": {
            "cpu_sustained_high": True,          # CPU >85% for >5 minutes
            "request_rate_normal": True,         # Request rate NOT elevated
            "cpu_request_ratio_broken": True,    # CPU not explained by requests
            "falco_process_spawn": True,         # Falco: new process in pod
        },
        "response": "QUARANTINE_THEN_SHUTDOWN",
        "confidence_required": 0.80,
    },
    "DDOS": {
        "description": "Ingress traffic spike, error rate rises immediately with traffic",
        "required_signals": {
            "ingress_traffic_spike": True,       # network ingress >3x baseline
            "error_rate_concurrent": True,       # error rate spikes same time as traffic
            "cpu_proportional": False,           # CPU may be high but proportional
            "request_rate_elevated": True,       # request rate elevated
        },
        "response": "PORT_SHIFT_THEN_QUARANTINE",
        "confidence_required": 0.75,
    },
    "DATA_EXFILTRATION": {
        "description": "Egress traffic spike, CPU flat, no corresponding workload",
        "required_signals": {
            "egress_traffic_spike": True,        # egress bytes >5x baseline
            "cpu_normal": True,                  # CPU NOT elevated
            "request_rate_normal": True,         # no incoming work
            "unusual_destination": True,         # Cilium Hubble: new destination IP
        },
        "response": "QUARANTINE_IMMEDIATE",
        "confidence_required": 0.85,             # highest bar — very severe
    },
    "PORT_SCAN": {
        "description": "Many connections from same source to many ports, short-lived",
        "required_signals": {
            "connection_count_spike": True,
            "connection_duration_short": True,
            "many_distinct_ports_targeted": True,
        },
        "response": "PORT_SHIFT_ONLY",
        "confidence_required": 0.70,
    },
}
```

---

## 9. LAYER 3 — POLICY ENGINE

```yaml
# rules.yaml — ALL policy decisions are declared here, not hardcoded in Python

drift:
  action: update_baseline
  alert_tier: 1
  requires_approval: false
  rollback: none

overload:
  action: scale_out
  alert_tier: 2
  requires_approval: false
  max_replicas: 10          # never exceed this autonomously
  rollback: scale_in
  verify_after_seconds: 120

attack:
  crypto_mining:
    action_sequence:
      - quarantine           # immediate, no approval
      - confirm_3of3         # collect 3 independent signals
      - shutdown_pod         # if 3of3 confirmed
    alert_tier: 4
    requires_approval_for_shutdown: false
    stateful_override: alert_only    # never shutdown stateful pods
    rollback: restore_network_policy

  ddos:
    action_sequence:
      - port_shift           # if port-targeted signature
      - quarantine           # network isolation
      - confirm_3of3
      - shutdown_pod
    alert_tier: 4
    requires_approval_for_shutdown: false
    rollback: restore_port_and_network_policy

  data_exfil:
    action_sequence:
      - quarantine           # highest priority — stop data leaving NOW
      - confirm_3of3
      - shutdown_pod
    alert_tier: 4
    requires_approval_for_shutdown: false
    rollback: restore_network_policy

  port_scan:
    action_sequence:
      - port_shift           # only action for port scan
    alert_tier: 3
    requires_approval: false
    rollback: restore_original_port

stateful_pod_policy:
  # applies to any pod with volumeMounts referencing a PVC
  auto_shutdown: NEVER
  auto_quarantine: NEVER
  action: alert_tier_4_and_wait_for_human
  message: "Stateful pod anomaly detected. MANUAL REVIEW REQUIRED. KORAL will not act."

# 3-of-3 shutdown confirmation gates (ALL must be true before shutdown)
shutdown_confirmation:
  gate_1: anomaly_score_above_threshold    # RRCF or STL+IF score > threshold
  gate_2: causal_sequence_not_overload     # Granger check: resource not explained by requests
  gate_3_options:                          # ANY ONE of these satisfies gate 3
    - falco_process_alert_in_pod
    - egress_anomaly_no_workload
    - attack_signature_pattern_matched
```

---

## 10. LAYER 4 — ACTION ENGINE

### 10.1 Port Shifting (Zero-Downtime)

```python
# port_shift.py

class ZeroDowntimePortShifter:
    """
    Shifts Kubernetes Service port without container restarts.
    Container NEVER changes its listening port.
    Only the Service port mapping and Ingress routing change.
    
    PRECONDITIONS (all must pass before execution):
      1. Pod is NOT stateful (no PVC attached)
      2. App port is configurable (not hardcoded in image)
      3. Target new port is not in use in namespace
      4. No active persistent connections (or grace period is acceptable)
      5. Attack subtype is port-targeted (DDoS or PORT_SCAN) — not crypto/exfil
    
    EXECUTION SEQUENCE (strictly ordered):
      Step 1: Validate all preconditions → abort if any fail
      Step 2: Select new port from KORAL reserved range (49152-65535)
      Step 3: Check new port not in use (scan namespace Service list)
      Step 4: Patch Service to ADD new port (Service now has BOTH old and new)
      Step 5: Update Ingress/HTTPRoute to route to new port
      Step 6: Wait grace_period_seconds (default 30)
      Step 7: Send TIER 3 alert: "Port shifted {old}→{new}. Grace period active."
      Step 8: Remove old port from Service spec
      Step 9: Verify new port receives traffic (health check)
      Step 10: Send confirmation alert: "Port shift complete. Service healthy."
      Step 11: Log full shift record to PostgreSQL
    
    ROLLBACK (if any step after Step 5 fails):
      Re-add old port, remove new port, restore Ingress, alert developer
    """
    
    def shift(self, 
              service_name: str,
              namespace: str,
              old_port: int,
              reason: str,
              grace_period_seconds: int = 30) -> PortShiftResult:
        pass
    
    def _validate_preconditions(self, service_name: str, namespace: str) -> ValidationResult:
        pass
    
    def _select_new_port(self, namespace: str) -> int:
        """Must check entire namespace for port conflicts before returning."""
        pass
    
    def _verify_new_port_healthy(self, service_name: str, new_port: int) -> bool:
        """Sends health check request to new port. Returns True if 200 received."""
        pass
```

### 10.2 Quarantine (Network Isolation)

```python
# quarantine.py

class PodQuarantiner:
    """
    Isolates a pod by patching its NetworkPolicy.
    Does NOT terminate the pod.
    
    EFFECT:
      - Pod can no longer receive new connections from outside namespace
      - Pod can no longer initiate connections (stops data exfil in progress)
      - Existing connections drain naturally
      - Pod continues running (forensic preservation, pod logs still available)
      - Replicas in same Deployment continue serving traffic normally
    
    IMPLEMENTATION:
      Create a NetworkPolicy in the pod's namespace that:
        - Denies all ingress to the pod's labels
        - Denies all egress from the pod's labels
        - Excludes KORAL's own namespace from the deny (so KORAL can still monitor)
    """
    
    def quarantine(self, pod_name: str, namespace: str, reason: str) -> QuarantineResult:
        pass
    
    def release(self, pod_name: str, namespace: str, reason: str) -> bool:
        """Removes quarantine NetworkPolicy. Used when shutdown is not confirmed."""
        pass
```

### 10.3 Selective Pod Shutdown (3-of-3 Gated)

```python
# shutdown.py

class SelectivePodShutdown:
    """
    Terminates a single compromised pod. NEVER terminates a Deployment.
    
    PRE-SHUTDOWN CHECKS (all must pass):
      1. 3-of-3 confirmation from policy engine
      2. Pod is NOT stateful (verify: no PVC volumeMount)
      3. Namespace has >1 healthy replica available to absorb traffic
      4. Replacement pod will be scheduled (resource availability check)
    
    EXECUTION SEQUENCE:
      Step 1: Drain traffic (label pod with koral.io/draining=true)
              Ingress controller reads this label and stops routing new requests
      Step 2: Wait for in-flight requests to complete (default 30s)
      Step 3: Delete pod (kubernetes_client.delete_namespaced_pod)
              Deployment controller immediately schedules replacement from clean image
      Step 4: Wait for replacement to reach Running state (timeout 120s)
      Step 5: Verify replacement pod is healthy (readiness probe)
      Step 6: Alert: "Pod {name} terminated. Replacement pod {new_name}: Running."
      Step 7: Log full record to PostgreSQL incidents table
    
    IF STEP 4 TIMES OUT:
      Alert TIER 4 immediately. Do NOT retry shutdown. Escalate to human.
    """
    
    def shutdown(self,
                 pod_name: str,
                 namespace: str,
                 confirmation_result: ConfirmationResult,
                 reason: str) -> ShutdownResult:
        pass
    
    def _is_stateful(self, pod_name: str, namespace: str) -> bool:
        """Returns True if pod has any PVC volumeMount. If True: ABORT shutdown."""
        pass
    
    def _has_healthy_replicas(self, pod_name: str, namespace: str) -> bool:
        """Returns True only if Deployment has >1 other healthy pod."""
        pass
```

---

## 11. ALERTING SYSTEM

### 11.1 Standard Alert Message Format

```python
# message_templates.py
# EVERY alert from EVERY layer uses this exact format.
# Consistency is non-negotiable. Developers read alerts at 3AM.

def format_alert(
    tier: int,
    namespace: str,
    pod_name: str,
    what: str,           # what happened (metric value, event)
    classification: str, # KORAL's classification of root cause
    cause: str,          # why KORAL thinks this happened
    action_taken: str,   # what KORAL did
    service_status: str, # UP | DEGRADED | DOWN
    next_watch: str,     # what to monitor next / when to re-alert
    confidence: float,   # classifier confidence
) -> str:
    tier_labels = {1: "INFO", 2: "WARNING", 3: "CRITICAL", 4: "EMERGENCY"}
    return f"""
[KORAL] {tier_labels[tier]} | {namespace}/{pod_name} | {datetime.utcnow().isoformat()}Z

WHAT:       {what}
CLASS:      {classification} (confidence: {confidence:.0%})
CAUSE:      {cause}
ACTION:     {action_taken}
STATUS:     {service_status}
NEXT:       {next_watch}
    """.strip()
```

### 11.2 Alert Routing Matrix

```python
TIER_ROUTING = {
    1: ["postgresql"],               # log only, no notification
    2: ["postgresql", "slack", "telegram"],
    3: ["postgresql", "slack", "telegram", "email"],
    4: ["postgresql", "slack", "telegram", "email", "pagerduty"],
}

# Deduplication: same pod + same tier within 5 minutes = one alert + update
# Suppression: after KORAL acts, suppress same-pod alerts for 10 minutes
# Escalation: WARNING unacknowledged 15min → CRITICAL; CRITICAL 5min → EMERGENCY
```

### 11.3 Alert Events Per Layer

```python
ALERT_EVENTS = {
    # Layer 1
    "metric_anomaly_detected":          {"tier": 1, "action": "log"},
    "correlated_anomaly_detected":      {"tier": 2, "action": "notify"},
    
    # Layer 2
    "classified_drift":                 {"tier": 1, "action": "log"},
    "classified_overload":              {"tier": 2, "action": "notify"},
    "classified_attack":                {"tier": 4, "action": "notify_all"},
    
    # Layer 3
    "shutdown_queued":                  {"tier": 4, "action": "notify_all"},
    "port_shift_queued":                {"tier": 3, "action": "notify"},
    
    # Layer 4
    "pod_restarted":                    {"tier": 2, "action": "notify"},
    "scale_out_executed":               {"tier": 2, "action": "notify"},
    "pod_quarantined":                  {"tier": 3, "action": "notify"},
    "pod_shutdown_executed":            {"tier": 4, "action": "notify_all"},
    "port_shift_executing":             {"tier": 3, "action": "notify"},
    "port_shift_complete":              {"tier": 3, "action": "notify"},
    "port_shift_failed":                {"tier": 4, "action": "notify_all"},
    "stateful_pod_anomaly":             {"tier": 4, "action": "notify_all"},
    "shutdown_prerequisite_failed":     {"tier": 4, "action": "notify_all"},
    
    # Layer 5
    "incident_summary_generated":       {"tier": 2, "action": "slack_thread_reply"},
    
    # Layer 6
    "nightly_resource_report":          {"tier": 1, "action": "email_and_dashboard"},
    "critical_waste_detected":          {"tier": 2, "action": "notify"},
}
```

---

## 12. LAYER 5 — LLM EXPLAIN LAYER

```python
# summarizer.py

SYSTEM_PROMPT = """
You are KORAL's incident analyst. You generate structured incident summaries 
for SRE teams. You always:
1. State what happened in plain English (no jargon unless necessary)
2. Explain KORAL's classification with the evidence that supports it
3. Describe exactly what KORAL did and why
4. State the current service health status
5. Tell the engineer what to watch next and what would trigger re-escalation

You never make up evidence not present in the incident data.
You never recommend actions beyond what KORAL's policy engine specifies.
If confidence is low, you say so explicitly.
Format: plain text, 5 sections (WHAT / WHY / ACTION / STATUS / NEXT), under 200 words.
"""

class IncidentSummarizer:
    """
    Generates incident summaries using in-context learning (ICL).
    Uses real past incidents from PostgreSQL as few-shot examples.
    
    ICL APPROACH:
    - Retrieve 3-5 similar past incidents from few_shot_store
    - Similarity: same classification class + similar metric signature
    - Include them as examples in the prompt
    - Generate summary for current incident
    
    FALLBACK:
    If Anthropic API unavailable → use Ollama (qwen2.5-coder:7b)
    If both unavailable → return templated summary (no LLM)
    Never block alerting waiting for LLM. LLM is async, alert is sync.
    """
    
    def summarize(self,
                  incident: Incident,
                  classification: ClassificationResult,
                  actions_taken: list[ActionResult]) -> str:
        few_shot_examples = self.few_shot_store.retrieve_similar(
            classification.root_cause,
            n=3
        )
        prompt = self._build_prompt(incident, classification, actions_taken, few_shot_examples)
        return self.llm_client.complete(prompt)
    
    def _build_prompt(self, incident, classification, actions, examples) -> str:
        """
        Structure:
        [SYSTEM PROMPT]
        [3 FEW-SHOT EXAMPLES from real incident history]
        [CURRENT INCIDENT DATA]
        Generate summary:
        """
        pass
```

---

## 13. LAYER 6 — RESOURCE OPTIMIZER

```python
# pod_profiler.py

class PodResourceProfiler:
    """
    Runs nightly at 2 AM. Profiles every pod's resource usage over last 7 days.
    Classifies each pod into one of 4 resource profiles using K-means clustering.
    
    FEATURES (per pod):
      - avg_cpu_utilization_ratio    (actual / requested)
      - avg_memory_utilization_ratio (actual / requested)
      - cpu_burstiness               (std_dev / mean of cpu_usage)
      - memory_predictability        (1 / cv of memory_usage)
      - p99_cpu                      (peak CPU for right-sizing)
      - p99_memory                   (peak memory for right-sizing)
    
    PROFILES:
      OVER_PROVISIONED:  avg_cpu_ratio < 0.40 AND avg_memory_ratio < 0.40
        → Recommend: reduce requests/limits to p99 * 1.2
        
      UNDER_PROVISIONED: avg_cpu_ratio > 0.85 OR avg_memory_ratio > 0.85
        → Recommend: increase limits; add HPA if burstiness > 0.3
        
      BURSTY:            burstiness > 0.5 (high std_dev relative to mean)
        → Recommend: add HPA targeting 70% CPU; remove static limits
        
      STEADY_STATE:      burstiness < 0.2, high predictability
        → Recommend: right-size with static VPA recommendation at p99 * 1.15
    
    OUTPUT:
      - Per-pod profile classification
      - Specific resource change recommendation (not vague — actual numbers)
      - Estimated savings: CPU cores + GB RAM recoverable
      - Nightly email report + dashboard widget + PostgreSQL record
    """
    
    def profile_namespace(self, namespace: str) -> list[PodProfile]:
        pass
    
    def generate_recommendations(self, profiles: list[PodProfile]) -> list[ResourceRecommendation]:
        pass
```

---

## 14. STORAGE — VICTORIAMETRICS INTEGRATION

```python
# victoria_metrics.py

class VictoriaMetricsClient:
    """
    Replaces direct Prometheus scraping for KORAL's internal storage.
    Prometheus continues to scrape pods. VM receives via remote_write.
    KORAL queries VM directly for metric history.
    
    CARDINALITY RULES (enforced before any label is written):
      FORBIDDEN labels (reject if present):
        - request_id, trace_id, user_id, session_id, transaction_id
        - Any label with cardinality > MAX_LABEL_CARDINALITY (env: 1000)
      
      REQUIRED labels for every series:
        - namespace, pod, container, node
      
    RETENTION:
      Hot:  15 days at raw resolution (10-second scrape interval default)
      Warm: 90 days at 5-minute downsampled
      Cold: 365 days at 1-hour downsampled
      (Configure via VictoriaMetrics retentionPeriod and downsampling rules)
    
    QUERY PATTERNS KORAL USES:
      1. Last N points for streaming (RRCF input)
      2. Last 24-48 hours for STL decomposition
      3. Last 7 days for resource profiler
      4. Specific time window for incident investigation
    """
    
    def query_range(self,
                    metric_query: str,
                    start: datetime,
                    end: datetime,
                    step: str = "10s") -> pd.DataFrame:
        """Returns DataFrame with timestamp index, value column."""
        pass
    
    def query_latest(self, metric_query: str, pod_name: str) -> float:
        """Returns single latest value. Used by RRCF for streaming ingestion."""
        pass
    
    def remote_write(self, metrics: list[Metric]) -> bool:
        """
        Write KORAL's own metrics (self-monitoring) to VM.
        KORAL exposes: koral_anomaly_score, koral_classification_confidence,
                       koral_actions_taken_total, koral_alerts_sent_total
        """
        pass
```

### 14.1 PostgreSQL Schema

```sql
-- Run via Alembic migrations in deploy/postgres/migrations/

CREATE TABLE incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace       VARCHAR(255) NOT NULL,
    pod_name        VARCHAR(255) NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL,
    resolved_at     TIMESTAMPTZ,
    root_cause      VARCHAR(50) NOT NULL,    -- SEASONAL_DRIFT | WORKLOAD_OVERLOAD | EXTERNAL_ATTACK
    attack_subtype  VARCHAR(50),             -- CRYPTO_MINING | DDOS | DATA_EXFIL | PORT_SCAN
    confidence      FLOAT NOT NULL,
    evidence        JSONB NOT NULL,          -- list of evidence strings from classifier
    anomaly_scores  JSONB NOT NULL,          -- per-detector scores
    actions_taken   JSONB NOT NULL,          -- list of ActionResult objects
    service_impact  VARCHAR(20) NOT NULL,    -- NONE | DEGRADED | DOWN
    created_at      TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (started_at);

CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID REFERENCES incidents(id),
    tier            INTEGER NOT NULL,
    channel         VARCHAR(50) NOT NULL,
    pod_name        VARCHAR(255) NOT NULL,
    namespace       VARCHAR(255) NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    message         TEXT NOT NULL,
    sent_at         TIMESTAMPTZ NOT NULL,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(255)
) PARTITION BY RANGE (sent_at);

CREATE TABLE pod_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace       VARCHAR(255) NOT NULL,
    pod_name        VARCHAR(255) NOT NULL,
    profiled_at     TIMESTAMPTZ NOT NULL,
    profile_class   VARCHAR(50) NOT NULL,   -- OVER_PROVISIONED | UNDER_PROVISIONED | BURSTY | STEADY_STATE
    avg_cpu_ratio   FLOAT,
    avg_mem_ratio   FLOAT,
    burstiness      FLOAT,
    recommendation  JSONB,
    estimated_savings JSONB
);

CREATE TABLE few_shot_examples (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    root_cause      VARCHAR(50) NOT NULL,
    attack_subtype  VARCHAR(50),
    metric_signature JSONB NOT NULL,         -- compact form of the anomaly signals
    incident_summary TEXT NOT NULL,          -- the LLM-generated summary that was correct
    feedback_score  INTEGER,                 -- developer rating 1-5 (for future fine-tuning)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE baselines (
    namespace       VARCHAR(255) NOT NULL,
    pod_name        VARCHAR(255) NOT NULL,
    metric_name     VARCHAR(255) NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL,
    trend_slope     FLOAT,
    seasonal_components JSONB,               -- 24-hour pattern as array
    residual_std    FLOAT,
    PRIMARY KEY (namespace, pod_name, metric_name)
);

CREATE TABLE approval_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID REFERENCES incidents(id),
    action_type     VARCHAR(100) NOT NULL,
    pod_name        VARCHAR(255) NOT NULL,
    namespace       VARCHAR(255) NOT NULL,
    requested_at    TIMESTAMPTZ NOT NULL,
    status          VARCHAR(20) DEFAULT 'PENDING',  -- PENDING | APPROVED | REJECTED
    responded_at    TIMESTAMPTZ,
    responded_by    VARCHAR(255),
    expires_at      TIMESTAMPTZ               -- auto-reject if not responded within 15min
);
```

---

## 15. FALCO INTEGRATION

```yaml
# deploy/falco/falco-values.yaml
driver:
  kind: ebpf              # NOT kernel module — safer for IISc cluster access

falcosidekick:
  enabled: true
  config:
    alertmanager:
      hostport: "http://alertmanager:9093"
      minimumpriority: "warning"
      customfields:
        source: "falco"
        cluster: "koral-monitored"
```

```yaml
# deploy/falco/custom-rules.yaml
# KORAL-specific Falco rules that feed the 3-class classifier

- rule: KORAL Crypto Mining - New Miner Process
  desc: Detects common cryptocurrency mining processes
  condition: >
    spawned_process and container and
    proc.name in (xmrig, cryptonight, minerd, ethminer, nbminer, lolminer)
  output: >
    Crypto miner detected (pod=%k8s.pod.name namespace=%k8s.ns.name 
    process=%proc.name parent=%proc.pname)
  priority: CRITICAL
  tags: [koral, crypto_mining, attack]

- rule: KORAL Crypto Mining - CPU Exhaustion Pattern
  desc: Generic process spawned with unusual resource consumption
  condition: >
    spawned_process and container and
    proc.pname in (sh, bash, python, python3) and
    not proc.name in (allowed_processes)
  output: >
    Suspicious process spawn (pod=%k8s.pod.name namespace=%k8s.ns.name
    process=%proc.name cmdline=%proc.cmdline)
  priority: WARNING
  tags: [koral, suspicious_process]

- rule: KORAL Container Escape Attempt
  desc: Attempt to access host filesystem from container
  condition: >
    open_write and container and
    fd.name startswith /proc/sys/kernel and
    not proc.name in (fluentd, node-exporter)
  output: >
    Container escape attempt (pod=%k8s.pod.name namespace=%k8s.ns.name
    file=%fd.name process=%proc.name)
  priority: CRITICAL
  tags: [koral, container_escape, attack]

- rule: KORAL Data Exfiltration - Outbound
  desc: Unusual outbound connection to external IP
  condition: >
    outbound and container and
    not fd.sip.name in (allowed_external_ips) and
    fd.sport > 1024
  output: >
    Suspicious outbound connection (pod=%k8s.pod.name namespace=%k8s.ns.name
    dest=%fd.rip:%fd.rport process=%proc.name)
  priority: WARNING
  tags: [koral, data_exfil]
```

```python
# falco_consumer.py

class FalcoEventConsumer:
    """
    Receives Falco events via Falcosidekick webhook.
    Enriches events with pod metadata and routes to Layer 2 classifier.
    
    ENDPOINT: POST /webhooks/falco
    FastAPI route receives JSON payload from Falcosidekick.
    
    ENRICHMENT:
    - Add pod name / namespace from Falco output fields
    - Look up current anomaly state for that pod (from in-memory state store)
    - If anomaly already in progress for that pod: inject as gate_3 signal
    - If no anomaly in progress: store as pending Falco event (TTL: 10 minutes)
    
    A Falco event alone does NOT trigger action.
    Falco is gate_3 of the 3-of-3 confirmation — it corroborates.
    """
    
    def receive_event(self, payload: dict) -> FalcoEvent:
        pass
    
    def get_pending_events(self, pod_name: str, namespace: str,
                           window_seconds: int = 600) -> list[FalcoEvent]:
        """Returns Falco events for this pod in the last window_seconds."""
        pass
```

---

## 16. TESTING STRATEGY

### 16.1 Unit Test Requirements

Every function in every module must have:
- Happy path test
- Edge case: empty/null input
- Edge case: minimum data (below threshold)
- Edge case: maximum load (stress boundary)

Critical tests that MUST pass before any Layer 4 code is written:

```python
# test_classifier.py — THESE TESTS ARE THE GATE

class TestClassifierScenarios:
    """
    Each scenario feeds the classifier a realistic metric snapshot.
    The classification MUST match the expected class.
    A wrong classification here means wrong action in production.
    """
    
    def test_legitimate_traffic_spike_classifies_as_overload(self):
        """
        Request rate rises first, then CPU, then memory.
        Ratio stable. No Falco events. Business hours.
        Expected: WORKLOAD_OVERLOAD, confidence > 0.70
        Must NOT classify as ATTACK.
        """
        pass
    
    def test_monday_morning_peak_classifies_as_drift(self):
        """
        CPU rises every Monday 9-10AM. Pattern repeated 3+ weeks.
        No Falco events. STL seasonal component accounts for spike.
        Expected: SEASONAL_DRIFT, confidence > 0.70
        Must NOT classify as ATTACK or OVERLOAD.
        """
        pass
    
    def test_crypto_mining_classifies_as_attack(self):
        """
        CPU >85% sustained. Request rate flat. Falco: xmrig process spawned.
        CPU:request ratio broken.
        Expected: EXTERNAL_ATTACK, subtype: CRYPTO_MINING, confidence > 0.80
        """
        pass
    
    def test_ddos_classifies_as_attack(self):
        """
        Ingress traffic spike. Error rate rises simultaneously with traffic.
        CPU proportional but error rate abnormal.
        Expected: EXTERNAL_ATTACK, subtype: DDOS, confidence > 0.75
        """
        pass
    
    def test_data_exfil_classifies_as_attack(self):
        """
        Egress bytes 10x baseline. CPU normal. Request rate normal.
        No incoming work to explain outgoing data.
        Expected: EXTERNAL_ATTACK, subtype: DATA_EXFIL, confidence > 0.85
        """
        pass
    
    def test_stateful_pod_never_shutdown_regardless_of_classification(self):
        """
        Pod has PVC attached. Crypto mining signature confirmed.
        Expected: Policy engine returns ALERT_ONLY, no quarantine, no shutdown.
        """
        pass
    
    def test_low_confidence_attack_does_not_trigger_shutdown(self):
        """
        Ambiguous signals. Classification: ATTACK, confidence=0.60 (below 0.80 threshold).
        Expected: quarantine only, shutdown NOT triggered, human approval requested.
        """
        pass
```

### 16.2 Integration Test Requirements

```python
# test_port_shift_e2e.py

class TestPortShiftEndToEnd:
    def test_full_zero_downtime_sequence(self):
        """
        Requires a real or kind cluster.
        1. Deploy test service on port 80
        2. Simulate DDoS alert triggering port shift
        3. Verify: service responds on new port
        4. Verify: old port returns connection refused (after grace period)
        5. Verify: zero connection drops during shift (test with concurrent requests)
        6. Verify: alert sent on Telegram/Slack with correct format
        7. Verify: PostgreSQL record created
        """
        pass
    
    def test_stateful_service_port_shift_aborted(self):
        """
        Service backed by StatefulSet with PVC.
        Port shift must be ABORTED. Alert must be TIER 4.
        """
        pass
    
    def test_port_shift_rollback_on_failure(self):
        """
        Simulate failure at Step 8 (old port removal fails).
        Verify: both ports still active, original routing restored, alert sent.
        """
        pass
```

### 16.3 Benchmark Datasets for Detection Validation

```
USE THESE — they are real data, not synthetic:

1. Google Cluster Traces 2019
   URL: https://github.com/google/cluster-data
   Format: CSV (task events, resource usage)
   Use for: STL+IF calibration on real CPU/memory traces

2. Alibaba Cluster Trace v2018
   URL: https://github.com/alibaba/clusterdata
   Format: CSV (machine metrics, container metrics)
   Use for: RRCF streaming validation on real time-series

3. MITRE ATT&CK for Containers case studies
   URL: https://attack.mitre.org/matrices/enterprise/containers/
   Use for: Attack scenario construction (DDoS, crypto, exfil signatures)

4. KubeHound attack graph dataset (Datadog, 2023)
   URL: https://github.com/DataDog/KubeHound
   Use for: Attack path validation for classifier

SYNTHETIC DATA RULE:
Synthetic data is ONLY permitted in:
  - Unit tests (fixtures/synthetic_baselines/)
  - LSTM training BEFORE real data arrives (must be discarded when real data available)
  - Message template formatting tests
Never use synthetic data to calibrate thresholds.
```

---

## 17. BUILD ORDER — STRICT SEQUENCE

The agent must build in this exact order. Do not skip ahead.

```
PHASE 0 — INFRASTRUCTURE (before writing any detection code)
  [ ] 0.1 Connect VictoriaMetrics remote_write from existing Prometheus
  [ ] 0.2 Verify cardinality guard works (reject forbidden labels test)
  [ ] 0.3 Run Alembic migrations (create all PostgreSQL tables)
  [ ] 0.4 Deploy Falco + Falcosidekick (DaemonSet, eBPF mode)
  [ ] 0.5 Verify Falco → Falcosidekick → AlertManager pipeline works (send test alert)
  [ ] 0.6 Set up Telegram bot and Slack webhook (send test message to both)
  GATE: Can you receive a Falco alert on Telegram? If NO: stop, fix this first.

PHASE 1 — DETECTION ENGINE (Layer 1)
  [ ] 1.1 Implement RRCFStreamDetector (preserve detect/detect_many interface)
  [ ] 1.2 Unit tests for RRCF (all 3 unit test types per function)
  [ ] 1.3 Implement STLDecomposer
  [ ] 1.4 Implement STLIFDetector (wraps existing IsolationForest)
  [ ] 1.5 Unit tests for STL+IF
  [ ] 1.6 Implement detector_factory.py (metric routing)
  [ ] 1.7 Implement metric_router.py (ingestion → factory → detector)
  [ ] 1.8 Integration test: real metric from VM → RRCF → AnomalyResult
  GATE: Does RRCF return AnomalyResult in <5ms on real VM data? If NO: debug, not proceed.

PHASE 2 — CLASSIFICATION ENGINE (Layer 2)
  [ ] 2.1 Implement CausalSequenceAnalyzer
  [ ] 2.2 Unit tests for causal analyzer (overload vs attack scenarios)
  [ ] 2.3 Implement TimeScorer
  [ ] 2.4 Implement SignalAggregator
  [ ] 2.5 Implement attack_subtypes.py signatures
  [ ] 2.6 Implement RootCauseClassifier
  [ ] 2.7 ALL scenario tests in tests/scenario/ must pass before Phase 3
  GATE: Does test_legitimate_traffic_spike_classifies_as_overload PASS?
        Does test_stateful_pod_never_shutdown PASS?
        If either FAILS: do not write a single line of Phase 3 code.

PHASE 3 — POLICY ENGINE (Layer 3)
  [ ] 3.1 Implement rules.yaml (declarative policy)
  [ ] 3.2 Implement PolicyEngine (reads rules.yaml)
  [ ] 3.3 Implement ApprovalGate (human approval for borderline actions)
  [ ] 3.4 Unit tests for policy engine
  GATE: Does policy engine correctly map ATTACK+0.60confidence → QUARANTINE_ONLY (not shutdown)?

PHASE 4 — ACTION ENGINE (Layer 4)
  [ ] 4.1 Implement safe_actions.py (restart_pod, scale_out)
  [ ] 4.2 Implement quarantine.py (NetworkPolicy patch)
  [ ] 4.3 Unit tests for quarantine (mock k8s client)
  [ ] 4.4 Implement port_shift.py (zero-downtime sequence)
  [ ] 4.5 Integration test: port_shift e2e on kind cluster
  [ ] 4.6 Implement shutdown.py (3-of-3 gated)
  [ ] 4.7 Integration test: shutdown on kind cluster with real pod
  [ ] 4.8 Implement action_executor.py (Celery async with rollback)
  GATE: Does test_full_zero_downtime_sequence PASS with zero dropped connections?
        Does stateful pod abort test PASS?

PHASE 5 — ALERTING SYSTEM
  [ ] 5.1 Implement message_templates.py (standard format)
  [ ] 5.2 Implement alert_store.py (PostgreSQL write on every alert)
  [ ] 5.3 Implement deduplicator.py (5-minute window)
  [ ] 5.4 Implement escalator.py (WARNING→CRITICAL→EMERGENCY ladder)
  [ ] 5.5 Implement telegram_notifier.py
  [ ] 5.6 Implement slack_notifier.py with thread support
  [ ] 5.7 Wire alerting into every layer
  [ ] 5.8 Test: trigger anomaly → verify Telegram message received with correct format
  GATE: Is every alert also written to PostgreSQL? If NO: not done.

PHASE 6 — LLM EXPLAIN LAYER (Layer 5)
  [ ] 6.1 Implement llm_client.py (Anthropic + Ollama fallback)
  [ ] 6.2 Implement few_shot_store.py (PostgreSQL-backed ICL examples)
  [ ] 6.3 Implement icl_builder.py (retrieves similar past incidents)
  [ ] 6.4 Implement summarizer.py (ICL prompt + generation)
  [ ] 6.5 Wire: incident complete → summarizer → Slack thread reply
  [ ] 6.6 Verify: LLM summary is ASYNC (never blocks alert delivery)
  GATE: If Anthropic API is down, does Ollama fallback work? Does system continue without LLM?

PHASE 7 — RESOURCE OPTIMIZER (Layer 6)
  [ ] 7.1 Implement pod_profiler.py (K-means on 7-day usage history)
  [ ] 7.2 Implement resource_recommender.py (specific numbers, not vague advice)
  [ ] 7.3 Implement waste_reporter.py (nightly email + PostgreSQL)
  [ ] 7.4 Schedule via Celery beat at 2 AM
  GATE: Does report generate correct profile for a known over-provisioned test pod?

PHASE 8 — LSTM CONFIRMATION LAYER
  [ ] 8.1 Implement LSTMAnomalyConfirmer (untrained state returns confidence=0.0)
  [ ] 8.2 Implement train() and calibrate_threshold()
  [ ] 8.3 Wire as confirmation layer in classifier (only if trained)
  [ ] 8.4 DO NOT TRAIN until real cluster data is available
  NOTE: LSTM is built last on purpose. The system must be fully functional without it.
        LSTM is a future accuracy improvement, not a prerequisite.

PHASE 9 — VALIDATION ON REAL DATA
  [ ] 9.1 Connect to IISc namespace (or kind cluster with real workload)
  [ ] 9.2 Run Google Cluster Traces through detection pipeline
  [ ] 9.3 Calibrate RRCF threshold on real data (not synthetic)
  [ ] 9.4 Calibrate IF contamination parameter on real data
  [ ] 9.5 Run 72-hour soak test: monitor for false positives
  [ ] 9.6 Target: <5 false positive alerts per 24 hours
  [ ] 9.7 If false positives >5/day: retune thresholds before Phase 10
  GATE: Zero false positive shutdowns or quarantines in 72-hour soak test.

PHASE 10 — PRODUCTION READINESS
  [ ] 10.1 Update Helm chart with all new components
  [ ] 10.2 KORAL self-monitoring: expose own metrics to VM
  [ ] 10.3 API documentation (FastAPI auto-docs + docs/API.md)
  [ ] 10.4 ALERT_RUNBOOK.md: what each alert means + human response steps
  [ ] 10.5 Update CLAUDE.md and activeContext.md for next session handoff
```

---

## 18. KNOWN CONSTRAINTS & NON-NEGOTIABLES

```
HARDWARE:
  16GB RAM Windows machine
  LSTM must stay under 200MB RAM
  No GPU (CPU inference only for LSTM)
  Celery + Redis adds ~200MB RAM overhead

SCOPE:
  Namespace-scoped only — never cluster-admin operations
  KORAL monitors one target namespace per deployment
  Multi-namespace requires separate KORAL deployment per namespace

NEVER DO:
  - Auto-shutdown a stateful pod (PVC attached)
  - Shift ports on a pod with active database connections
  - Run LSTM before training on real data
  - Calibrate thresholds on synthetic data
  - Use unbounded cardinality labels in Prometheus/VM
  - Block alert delivery while waiting for LLM response
  - Take 2+ actions on same pod within the same incident without re-confirmation
  - Override the 3-of-3 shutdown gate, ever

SECURITY:
  All secrets via Vault (existing MCP)
  All inter-component communication via mTLS (existing)
  KORAL's service account: read-only + specific write permissions only
    Allowed writes: NetworkPolicy (patch), Service (patch), Pod (delete specific)
    Forbidden: ClusterRole, PersistentVolume, Secret modifications

ALERTING NON-NEGOTIABLES:
  Every alert logged to PostgreSQL regardless of channel availability
  LLM failure must never block alert delivery
  Deduplication must never suppress TIER 4 EMERGENCY alerts
  Stateful pod anomaly is always TIER 4, always requires human response
```

---

## 19. ACTIVECONTEXT TEMPLATE (update at every session end)

```markdown
# KORAL activeContext.md
Last Updated: [DATE]
Last Agent Session: [DATE]

## Current Phase
Phase [X] — [Phase Name]

## Last Completed Task
[Exact task from build order, e.g., "4.2 quarantine.py implemented and unit tested"]

## Last Known State
- VictoriaMetrics: [connected | not connected]
- Falco: [deployed | not deployed]
- RRCF: [implemented | not implemented]
- STL+IF: [implemented | not implemented]
- Classifier: [implemented | not implemented | scenario tests passing]
- Port shift: [implemented | not implemented | e2e tested]
- Alerting: [wired | not wired]
- Real data: [available | not available]
- LSTM: [not started | implemented | trained]

## Blocking Issues
[Any issues found that prevent next step]

## Next Task
[Exact next task from build order]

## Do Not Touch
[Files that are complete and should not be modified without reason]
```

---

*Document ends. Agent: start with Phase 0. Read Section 18 constraints before writing any code.*