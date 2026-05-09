# CURRENT HEALTH REPORT (PHASE 1)
Generated: May 9, 2026  
Scope: Establish a production-safe baseline before evolving KORAL into autonomous remediation.

## Executive summary

KORAL’s **core observability pipeline is structurally sound** and implements the critical contracts needed for near-production operations:

- **Metrics + anomaly surfacing**: Prometheus scrape targets defined; backend exposes `/metrics`.
- **Correlation + AI explanation**: correlation-engine + ai-engine are wired into backend orchestration.
- **Real-time updates**: backend WebSocket (`/ws/live`) drives live dashboards and AI activity.
- **Deployment hygiene**: health endpoints exist; K8s probes use `/health`; backend image includes a healthcheck.

Phase 2 remediation foundations exist but include **safety gaps that must be closed before enabling remediation** (see “Stability findings”).

---

## CURRENT ARCHITECTURE

```
KORAL Observability Pipeline (Current)
======================================

Monitoring Agents (CPU/Memory/Storage/Logs)
    ↓ Z-score anomaly detection
Prometheus (metric collection, 15s scrape)
    ↓ Agent polls + sends anomalies
Backend API (port 8000)
    ├─ Receive anomaly: POST /anomalies
    ├─ Store in-memory + PostgreSQL
    ├─ Send to Correlation Engine
    └─ Broadcast via WebSocket
        ↓
Correlation Engine (port 8005)
    ├─ Event schema validation
    ├─ Root cause analysis (9 categories)
    ├─ Severity determination
    └─ Return incident
        ↓
AI Engine (port 8006)
    ├─ GPT-4o/Claude explanations
    ├─ Severity-based routing
    ├─ Email alerts for critical
    └─ Activity logging
        ↓
Database (PostgreSQL)
    ├─ incidents table
    ├─ anomalies table
    ├─ fix_history table
    └─ Persistence for replay
        ↓
Frontend Dashboard (port 3000)
    ├─ WebSocket listener
    ├─ Real-time incident list
    ├─ Interactive charts
    └─ Incident drill-down

Total E2E Latency: ~1 second
```

---

## Phase 1 verification (static + contract-level)

### Important constraint

This report is based on **code and configuration verification** (contracts, wiring, and safety posture).  
Runtime verification should be executed using the procedures below (see “Runtime verification steps”).

### Core service contracts (must remain stable)

- **Backend** (`backend/main.py`)
  - Health: `GET /health`
  - Metrics: `GET /metrics` (Prometheus exposition)
  - WebSocket: `ws://<host>/ws/live`
  - Routes: anomalies, incidents, graph, correlations, feedback, ai, fixes, **remediation** (new; feature-flagged)
- **Prometheus** (`prometheus.yml`)
  - Scrapes: backend, ai-engine, correlation-engine, cpu-agent, memory-agent, storage-agent, log-agent
- **Frontend** (`frontend/src/pages/Dashboard.tsx`, `frontend/src/components/AIAssistant.tsx`)
  - Live charts and incident list update via WebSocket messages (`anomaly`, `incident`, `incident_ai`)
  - AI assistant calls ai-engine directly in dev (port 3000) and listens for `incident_ai`

### Remediation feature-flag posture (baseline safety)

- Backend remediation orchestration is gated by `REMEDIATION_ENABLED` (default false).
- Compose defaults keep remediation services present but safe:
  - `REMEDIATION_ENABLED=false`
  - `DRY_RUN=true`
  - `DISABLE_EMAIL=true`, `DISABLE_TELEGRAM=true`, `DISABLE_SLACK=true`

---

## Runtime verification steps (Phase 1)

### Docker runtime

1. Create `.env` from `.env.example`.
2. Start:
   - `docker compose up -d --build`
3. Validate health endpoints:
   - Backend: `GET http://localhost:8000/health`
   - Correlation: `GET http://localhost:8005/health`
   - AI engine: `GET http://localhost:8006/health`
   - Prometheus: `GET http://localhost:9090/-/healthy`
   - Frontend: `GET http://localhost:3000/`
4. Validate Prometheus targets:
   - Open `http://localhost:9090/targets` and confirm all KORAL jobs are UP.
5. Validate WebSocket:
   - Open dashboard and confirm WS indicator is LIVE.
6. Validate data flow:
   - Trigger anomaly generation via manifests/scripts under `infra/k8s/simulation/*` or `system-intelligence-evaluation/simulation/*`.
   - Confirm anomaly charts update and incidents appear; confirm `incident_ai` appears when ai-engine is enabled.

### Kubernetes runtime

1. Apply `k8s/` manifests (namespace + secrets + core deployments).
2. Confirm probes:
   - Backend and AI engine readiness/liveness are `/health`.
3. Port-forward Prometheus and check `/targets`.

---

## Stability findings (what’s safe vs what must be fixed)

### Demo-safe behavior (acceptable if feature-flagged)

- Email/Telegram/Slack are disabled by default for demo reliability.

### Hardcoded / placeholder logic (must be addressed before production enablement)

- **Backend remediation workflow state is in-memory** (`backend/routes/remediation.py`).
- **Verification orchestration uses placeholder pre-metrics** in backend orchestration; must be replaced with real baselines.

### Safety issue (must fix before enabling remediation)

- **Sandbox executor execution model**: currently uses `subprocess.run(..., shell=True)` after formatting a command string.
  - Required: move to argv-based invocation without shell, strict parameter validation, least privilege, and auditable execution logs.

---

## STABILITY CRITERIA

Before proceeding with remediation layer:

✓ All health checks pass  
✓ No critical errors in logs  
✓ Metrics flowing correctly  
✓ WebSocket connected  
✓ Database responding  
✓ AI engine initialized  

---

## NEXT STEPS

Proceed to Phase 2 only when:

1. Docker and/or Kubernetes runtime verification steps pass
2. Prometheus targets are UP
3. WebSocket live updates work in dashboard
4. Incidents flow: anomaly → correlation → incident persisted/broadcast
5. AI pipeline degrades gracefully when LLM keys/SMTP are absent

---

## NOTES

- For hackathon demo stability, keep `REMEDIATION_ENABLED=false` until Phase 2 safety fixes are completed.
- Any remediation enablement must be guarded by:
  - feature flags + dry-run mode
  - allowlisted commands only
  - persistent audit logs + rollback strategy

---

See: PHASE1_HEALTH_CHECK_PROCEDURES.md for detailed testing steps
