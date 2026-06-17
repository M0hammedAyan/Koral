# KORAL

Self-hosted AIOps and observability platform for Kubernetes — detects anomalies, correlates incidents, plans and executes remediation autonomously, and maintains a full audit trail.

---

## What KORAL does

KORAL closes the full incident-response loop without leaving the cluster:

```
Detect → Correlate → Plan → Approve → Execute → Verify → Audit
```

1. **Detect** — agents continuously poll Prometheus for CPU, memory, storage, and log metrics. Readings above the configured Z-score threshold are flagged as anomalies.
2. **Correlate** — the correlation engine groups anomalies across pods and namespaces into incidents, identifying shared root causes.
3. **Plan** — an LLM (GPT-4o or Claude) analyses the incident and generates a ranked remediation plan with an explanation and confidence score.
4. **Approve** — the plan is routed through the approval engine. An operator reviews and approves or rejects it via the API or frontend. Approval state is persisted in PostgreSQL.
5. **Execute** — the sandbox executor runs the approved kubectl command inside an isolated environment with CPU, memory, and timeout limits.
6. **Verify** — the verification engine fetches pre- and post-execution Prometheus metrics and calculates whether the anomaly was resolved and by how much.
7. **Audit** — every auth event, API access, approval decision, execution, and verification is written to a tamper-evident audit table.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Agents (CPU / Memory / Storage / Log)                       │
│  Poll Prometheus every POLL_INTERVAL seconds                 │
└────────────────────┬─────────────────────────────────────────┘
                     │ POST /anomalies
┌────────────────────▼─────────────────────────────────────────┐
│  Backend  :8000                                              │
│  FastAPI · RBAC · Auth · Audit · SLO · WebSocket             │
│       │              │              │                         │
│  Correlation    Remediation    Approval                      │
│  Engine :8005   Planner :8007  Engine :8008                  │
│                      │                                        │
│               Sandbox Executor :8009                         │
│               Verification Engine :8010                      │
│               Notifier :8011                                 │
└──────────────────────────────────────────────────────────────┘
         │                    │
   PostgreSQL :5432      Prometheus :9090
   (via PgBouncer :6432) Grafana :3001
                          AlertManager :9093
         │
   React Frontend :3000
```

### Services

| Service | Port | Purpose |
|---|---|---|
| backend | 8000 | Core API — auth, RBAC, anomalies, incidents, SLO, audit, WebSocket |
| correlation-engine | 8005 | Z-score anomaly detection, incident grouping, cross-pod batch correlation |
| ai-engine | 8006 | LLM proxy — GPT-4o / Claude integration |
| remediation-planner | 8007 | AI-driven fix recommendation, dynamic K8s discovery |
| approval-engine | 8008 | Approval workflow with PostgreSQL persistence |
| sandbox-executor | 8009 | Isolated kubectl execution with resource limits |
| verification-engine | 8010 | Pre/post Prometheus metrics comparison |
| notifier | 8011 | Slack, Telegram, Email notifications |
| prometheus | 9090 | Metrics collection |
| grafana | 3001 | Dashboards (4 auto-provisioned) |
| alertmanager | 9093 | Alert routing — Slack, Email, webhook |
| postgres | 5432 | Primary database |
| pgbouncer | 6432 | Connection pooling |
| redis | 6379 | Distributed rate limiting |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| Frontend | React, TypeScript, Vite |
| Database | PostgreSQL (prod), SQLite (dev), PgBouncer |
| Monitoring | Prometheus, Grafana, AlertManager |
| AI | OpenAI GPT-4o, Anthropic Claude (configurable) |
| Auth | API keys (role-scoped) + JWT |
| Tracing | OpenTelemetry (OTLP exporter) |
| Rate limiting | Redis (in-memory fallback) |
| Container | Docker Compose (dev), Kubernetes (prod) |

---

## Features

- **RBAC** — three roles (VIEWER / OPERATOR / ADMIN) enforced on every route via dependency injection
- **API key + JWT auth** — all routes protected, WebSocket auth via query param or header, 401 on bad credentials
- **Anomaly detection** — Z-score per pod per metric, configurable threshold
- **Incident correlation** — single-pod and batch cross-pod correlation in one API call
- **LLM remediation planning** — GPT-4o or Claude generates fix plans with confidence scores and reasoning
- **Approval workflow** — plans require explicit approval before execution; full approve/reject history persisted
- **Sandboxed execution** — commands run with CPU, memory, timeout, and filesystem limits
- **Prometheus verification** — pre/post metrics comparison with improvement percentage
- **SLO tracking** — availability, MTTR, detection latency, remediation success rate, error budget
- **Audit log** — every auth event, fix, approval, execution, and verification is persisted and queryable
- **4 Grafana dashboards** — agent metrics, ops overview, incident analysis, remediation pipeline
- **AlertManager routing** — Slack, Email, and webhook receivers configured
- **Redis rate limiting** — per-IP and per-key limits with graceful in-memory fallback
- **WebSocket** — `/ws/live` for real-time event streaming to the frontend
- **OpenTelemetry** — trace instrumentation wired, OTLP exporter configurable
- **Alembic migrations** — versioned schema migrations with CI enforcement
- **K8s manifests** — HPA, PDB, network policies, secrets template, ingress

---

## Prerequisites

- Docker and Docker Compose v2
- An OpenAI or Anthropic API key (for remediation planning)
- 4 GB RAM minimum for the full stack

---

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/M0hammedAyan/KORAL.git
cd KORAL

# 2. Create your environment file
cp .env.example .env
# Edit .env — at minimum set API_KEY, API_KEY_ADMIN, API_KEY_OPERATOR,
# API_KEY_VIEWER, JWT_SECRET, and OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Start the stack
docker compose up -d

# 4. Check service health
docker compose ps
curl -H "X-API-Key: <your-API_KEY_VIEWER>" http://localhost:8000/health/live
```

The React frontend is at `http://localhost:3000`.
Grafana is at `http://localhost:3001` (default: admin / admin).
Interactive API docs are at `http://localhost:8000/docs`.

### Local development without Docker

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DB_TYPE=sqlite
export API_KEY=dev-key
export API_KEY_ADMIN=dev-admin
export API_KEY_OPERATOR=dev-operator
export API_KEY_VIEWER=dev-viewer
export JWT_SECRET=dev-secret

uvicorn backend.main:app --reload
```

### Run tests

```bash
pytest tests/ -v
```

---

## Environment Variables

Copy `.env.example` to `.env`. Every key is documented with a comment in that file. Key groups:

| Group | Variables |
|---|---|
| Database | `DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`, `DATABASE_URL` |
| Auth | `API_KEY`, `API_KEY_ADMIN`, `API_KEY_OPERATOR`, `API_KEY_VIEWER`, `JWT_SECRET`, `DISABLE_AUTH` |
| AI / LLM | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` |
| Alerting | `ALERT_EMAIL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `ALERT_WEBHOOK_URL` |
| Services | `BACKEND_URL`, `CORRELATION_ENGINE_URL`, `AI_ENGINE_URL`, `PROMETHEUS_URL`, `REDIS_URL` |
| Tuning | `LOG_LEVEL`, `Z_THRESHOLD`, `POLL_INTERVAL` |

---

## API Overview

All routes except `/health/*` and `/metrics` require an `X-API-Key` header.

| Prefix | Minimum Role | Description |
|---|---|---|
| `GET /anomalies` | VIEWER | List detected anomalies |
| `POST /anomalies` | OPERATOR | Ingest a new anomaly reading |
| `GET /incidents` | VIEWER | List correlated incidents |
| `GET /correlations` | VIEWER | List correlation results |
| `GET /graph` | VIEWER | Dependency graph data |
| `GET /fixes/history` | VIEWER | Fix history |
| `POST /fixes/record` | OPERATOR | Record a fix |
| `GET /fixes/stats` | VIEWER | Fix success rate stats |
| `GET /remediation/status` | VIEWER | Remediation system status |
| `GET /remediation/plans` | VIEWER | List remediation plans |
| `POST /remediation/plans` | OPERATOR | Create a remediation plan |
| `POST /remediation/approve/:id` | OPERATOR | Submit plan for approval |
| `POST /remediation/execute/:id` | ADMIN | Execute an approved plan |
| `GET /remediation/executions` | VIEWER | List execution records |
| `GET /slo/` | VIEWER | Full SLO summary |
| `GET /slo/availability` | VIEWER | Availability percentage |
| `GET /slo/mttr` | VIEWER | Mean time to recovery |
| `GET /slo/error-budget` | VIEWER | Error budget remaining |
| `GET /audit` | ADMIN | Query the audit log |
| `GET /ai/health` | VIEWER | AI engine connectivity status |
| `WS /ws/live` | API key | Real-time event stream |
| `GET /health/live` | None | Liveness probe |
| `GET /metrics` | None | Prometheus scrape endpoint |

---

## Project Structure

```
KORAL/
├── backend/                    Core FastAPI application
│   ├── routes/                 One module per API route group
│   ├── auth.py                 API key validation and auth audit events
│   ├── rbac.py                 Role resolution and FastAPI dependency factories
│   ├── audit.py                Audit log writer
│   ├── database.py             SQLite / PostgreSQL abstraction layer
│   ├── database_remediation.py Remediation-specific DB helpers
│   ├── middleware.py           Request ID, error shaping, audit middleware
│   ├── rate_limit_redis.py     Redis rate limiter with in-memory fallback
│   └── resilience.py           Circuit breaker helper
├── correlation-engine/         Z-score detection and incident correlation service
├── ai-engine/                  LLM proxy (GPT-4o / Claude)
├── remediation-planner/        AI fix recommendations and K8s discovery
├── approval-engine/            Approval workflow with DB persistence
├── sandbox-executor/           Isolated kubectl execution
├── verification-engine/        Pre/post Prometheus metrics comparison
├── notifier/                   Slack / Telegram / Email alert delivery
├── agents/                     Per-metric Kubernetes polling agents
│   ├── cpu-agent/
│   ├── memory-agent/
│   ├── storage-agent/
│   └── log-agent/
├── frontend/                   React + TypeScript UI (Vite)
│   └── src/pages/              Dashboard, Incidents, Remediation, SLO, Settings
├── infra/
│   ├── grafana/                Provisioned dashboards and datasource config
│   └── monitoring/             AlertManager configuration
├── k8s/                        Kubernetes manifests (HPA, PDB, ingress, secrets)
├── alembic/                    Database migration scripts
├── tests/                      Integration test suite (40 tests)
├── load_tests/                 Locust load test definitions
├── docker-compose.yml          Development stack
├── docker-compose-prod.yml     Production stack
├── .env.example                Documented environment variable template
└── requirements.txt            Python dependencies
```

---

## Current Limitations

- **Anomaly detection is Z-score only.** No trained model, no seasonal baselines, no forecasting. High false-positive rate on bursty workloads.
- **Single cluster.** No multi-cluster federation. Each deployment watches one cluster.
- **No user management UI.** API keys are configured via environment variables. There is no interface for key rotation or user provisioning.
- **WebSocket auth uses legacy key only.** The `/ws/live` endpoint validates `API_KEY` but is not role-aware.
- **AI dependency.** Remediation planning requires a live OpenAI or Anthropic API key. No local or offline model fallback.
- **No Helm chart.** Kubernetes deployment uses raw manifests. No single-command install.
- **No mTLS.** Inter-service communication inside the cluster is plaintext HTTP.

---

## Roadmap

- Helm chart for one-command cluster install
- WebSocket RBAC (role-aware connection validation)
- Multi-cluster federation
- User management API and frontend (key rotation, role assignment)
- Improved anomaly detection (LSTM or seasonal decomposition)
- mTLS between services via cert-manager
- Runbooks-as-code (versioned YAML playbooks alongside LLM-generated plans)
- PagerDuty / OpsGenie integration
- Fine-tuned self-hosted model to remove the OpenAI/Anthropic API dependency
- Compliance reports auto-generated from the audit log (SOC2 / ISO27001 evidence)

---

## License

MIT
