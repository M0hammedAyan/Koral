# CLAUDE.md

# KORAL AI Engineering Constitution

## Mission

KORAL is a production-grade AI observability platform for Kubernetes workloads.
It detects anomalies, correlates incidents, plans and executes remediation autonomously,
and provides full audit trails, SLO tracking, and alerting.

Never optimize for demos, hackathons, temporary workarounds, mock implementations, or cosmetic improvements over core functionality.

---

# Execution Status (as of 2026-06-16)

## Completed

| Priority | Task | Status |
|---|---|---|
| P1 | Auth enforcement — all routes protected, WS auth, 401 on bad key | DONE |
| P2 | Approval engine PostgreSQL persistence | DONE |
| P3 | Verification engine uses real Prometheus metrics | DONE (was already correct) |
| P4 | Remediation planner dynamic deployment/namespace discovery | DONE (was already correct) |
| P5 | Audit logging — login, API access denied, errors, fixes, approvals, executions | DONE |
| P6 | Grafana dashboards — datasource uid wired in all 4 dashboard JSONs | DONE |
| P7 | AlertManager — Slack + Email + notifier webhook configured | DONE |
| P8 | Multi-pod correlation — /correlate-batch endpoint in correlation-engine | DONE |
| P9 | SLO platform — /slo/* endpoints (availability, MTTR, detection latency, remediation success, error budget) | DONE |
| P10 | Integration tests — tests/test_backend_integration.py (auth, anomalies, incidents, fixes, SLO, remediation) | DONE |

## Post-Priority Hardening (2026-06-16)

| # | Task | Status |
|---|---|---|
| 1 | Commit all production hardening changes | DONE |
| 2 | Alembic migrations — alembic==1.13.1 added, Dockerfile copies alembic/, 0002_add_audit_table migration | DONE |
| 3 | CI/CD — ruff lint step + alembic upgrade head before pytest in ci.yml | DONE |
| 4 | RBAC — backend/rbac.py with VIEWER/OPERATOR/ADMIN roles; all routes annotated | DONE |
| 5 | Execution/verification DB persistence — removed in-memory dicts, all data in execution_log/verification_results | DONE |
| 6 | Frontend wiring — SLO page, getSLO()/correlateBatch() in api.ts, sidebar nav item | DONE |
| 7 | Redis rate limiter — backend/rate_limit_redis.py, graceful fallback, redis:7-alpine in docker-compose | DONE |
| 8 | Secret management — .env.example updated, koral-secrets.yaml.template for K8s | DONE |

---

# Architecture

## Services

| Service | Port | Purpose |
|---|---|---|
| backend | 8000 | FastAPI core API, auth, audit, SLO |
| correlation-engine | 8005 | Z-score anomaly detection, incident correlation, batch cross-pod correlation |
| ai-engine | 8006 | GPT-4o/Claude LLM integration |
| remediation-planner | 8007 | AI-based fix recommendation, dynamic K8s discovery |
| approval-engine | 8008 | Approval workflow with SQLite/PostgreSQL persistence |
| sandbox-executor | 8009 | Safe command execution |
| verification-engine | 8010 | Prometheus-based pre/post metrics comparison |
| notifier | 8011 | Slack/Telegram/Email notifications |
| prometheus | 9090 | Metrics collection |
| grafana | 3001 | Dashboards (4 provisioned) |
| alertmanager | 9093 | Alert routing (Slack + Email + webhook) |
| postgres | 5432 | Primary database |
| pgbouncer | 6432 | Connection pooling |

## Backend Route Map

| Prefix | Auth | Description |
|---|---|---|
| /anomalies | API Key | Ingest and list anomalies |
| /incidents | API Key | List incidents |
| /correlations | API Key | List correlations |
| /graph | API Key | Graph data |
| /fixes | API Key | Fix history, stats, recording |
| /feedback | API Key | Feedback loop |
| /ai | API Key | AI engine proxy |
| /audit | API Key | Audit log query |
| /remediation | API Key | Full remediation workflow |
| /slo | API Key | SLO metrics (availability, MTTR, error budget) |
| /health | None | Liveness/readiness probes |
| /metrics | None | Prometheus metrics |
| /ws/live | API Key (query param or header) | WebSocket real-time events |

## Auth

- All API routes require `X-API-Key` header.
- WebSocket `/ws/live` requires `api_key` query param or `X-API-Key` header.
- Invalid/missing key returns `401`.
- Auth events written to audit log.
- `DISABLE_AUTH=true` bypasses all auth (dev only).

## Database

- SQLite for development (`DB_TYPE=sqlite`).
- PostgreSQL via PgBouncer for production (`DB_TYPE=postgres`).
- Tables: anomalies, incidents, remediation_plans, approval_history, execution_log, verification_results, fix_history, audit.
- Approval engine supports both SQLite and PostgreSQL via `DB_TYPE` env var.

## Audit Events

| Event | Trigger |
|---|---|
| auth.login | Successful API key validation |
| auth.login_failed | Missing or invalid API key |
| api.access_denied | 401/403 response on any route |
| api.error | 4xx/5xx response on any route |
| fix.recorded | POST /fixes/record |
| remediation.approval_requested | POST /remediation/approve/{plan_id} |
| remediation.executed | POST /remediation/execute/{plan_id} |
| remediation.verified | POST /remediation/verify/{execution_id} |
| remediation.approved | PATCH /remediation/approvals/{id}/approve |
| remediation.rejected | PATCH /remediation/approvals/{id}/reject |

---

# Core Principles

Priority Order:

1. Security
2. Reliability
3. Correctness
4. Maintainability
5. Scalability
6. Performance
7. Developer Experience
8. Cost Optimization
9. UI Polish

When tradeoffs exist, always choose the higher-priority item.

---

# Scope Control

Never modify more than 10 files in a single task unless explicitly requested.

Prefer incremental changes.

Before performing large refactors:

* Explain purpose
* List affected files
* Explain risks
* Wait for approval

Never perform repository-wide rewrites.

---

# Token Efficiency

Minimize token consumption.

Rules:

* Never rewrite full files unnecessarily
* Prefer diffs
* Prefer targeted edits
* Summarize logs
* Avoid repeating repository context
* Avoid verbose explanations
* Return concise findings

Default response limit:

* Summary: <= 5 bullets
* Risks: <= 3 bullets
* Next Task: exactly 1

---

# Repository Scan Limits

Never scan:

* node_modules
* .git
* .venv
* dist
* build
* coverage
* logs
* __pycache__
* generated files
* compiled assets

Inspect only files relevant to the task.

---

# Code Quality Standards

All code must:

* Pass linting
* Pass tests
* Pass type checks
* Include error handling
* Include logging
* Include retry logic where appropriate
* Include input validation

Avoid:

* Dead code
* Duplicate code
* Commented-out code
* Placeholder implementations

---

# Security Requirements

Always:

* Validate inputs
* Sanitize outputs
* Use least privilege
* Store secrets in environment variables
* Mask secrets in logs
* Use secure defaults

Never:

* Commit secrets
* Commit tokens
* Commit passwords
* Commit API keys
* Commit .env files
* Disable security checks

Security takes precedence over convenience.

---

# Authentication Rules

Authentication is mandatory.

Requirements:

* API Key (X-API-Key header) on all routes
* JWT support available (validate_jwt dependency)
* WebSocket auth via query param or header
* Auth events written to audit log
* 401 on missing or invalid credentials (never 403 for auth failures)

Never bypass authentication.

Never add temporary auth exemptions.

---

# Database Rules

Database:

* PostgreSQL for production
* SQLite for development/testing

Requirements:

* PgBouncer for connection pooling
* Indexed queries
* Transaction safety
* DB_TYPE env var controls which backend is used

Never:

* Drop tables automatically
* Run destructive migrations without approval
* Store secrets in database records

---

# Sandbox Rules

All code execution must run inside sandbox environments.

Requirements:

* CPU limits
* Memory limits
* Timeout limits
* Filesystem isolation
* Network restrictions
* Audit logs

Never execute user code on host infrastructure.

---

# Observability

Every service must expose:

* /health endpoint
* /metrics endpoint (Prometheus)
* Structured logs

Backend metrics:

* koral_backend_requests_total
* koral_backend_errors_total
* koral_backend_request_latency_seconds
* koral_backend_websocket_clients
* koral_db_query_duration_seconds

Grafana dashboards (auto-provisioned):

* koral-dashboard — Agent metrics overview
* koral-ops-overview — Operations overview
* koral-incident-analysis — Incident and anomaly analysis
* koral-autonomous-remediation — Remediation pipeline status

All dashboards use datasource uid "prometheus".

---

# CI/CD Requirements

GitHub Actions must:

* Run tests
* Run linting
* Run type checking
* Build Docker images
* Validate Kubernetes manifests

Fail immediately on:

* Test failures
* Security failures
* Missing dependencies

---

# Infrastructure Standards

Preferred Stack:

Backend:

* Python
* FastAPI
* PostgreSQL
* PgBouncer

Frontend:

* React
* TypeScript
* Vite

Infrastructure:

* Docker Compose (development)
* Kubernetes (production)
* Prometheus + Grafana + AlertManager

Avoid introducing new frameworks unless justified.

---

# Output Format

After every task return only:

Summary:

* bullet points

Files Changed:

* file list

Validation:

* PASS or FAIL

Risks:

* up to 3 bullets

Next Task:

* exactly one highest-priority task

No additional commentary. No large logs. No unnecessary explanations.

---

# Decision Rule

When uncertain:

Choose the solution that would be acceptable in a production SaaS serving paying customers.

Never choose the fastest solution if it increases long-term technical debt.
