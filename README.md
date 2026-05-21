# KORAL — Kubernetes Observability with Real-time AI Logic

> **Production-Ready AI-Powered Kubernetes Observability System**
> 
> Real-time anomaly detection → Root cause analysis → AI explanations → Automated incident response

[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen)](docs/DEPLOYMENT.md)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](README.md)

---

## What is KORAL?

KORAL is a real-time AI-powered Kubernetes observability system that doesn't just detect failures — it explains why they happen in plain English.

**Key Features:**
- 🔍 **Real-time Anomaly Detection** — Z-score based detection across CPU, memory, storage, and logs
- 🧠 **AI Root Cause Analysis** — GPT-4o/Claude powered explanations in plain English
- ⚡ **Sub-20 Second Response** — From issue detection to dashboard notification
- 📧 **Smart Alerting** — Auto-fixes minor issues, alerts developers for critical ones
- 📊 **Live Dashboard** — WebSocket-powered real-time updates, no polling
- 🔗 **Dependency Mapping** — Automatic pod correlation and impact analysis

```
Real Pods → Prometheus → Agents → Backend → Correlation Engine → AI Engine → Dashboard
                                      ↓
                                  Database
                                      ↓
                                  WebSocket
                                      ↓
                              Real-time Updates
```

---

## Prerequisites

| Tool       | Version  | Install |
|------------|----------|---------|
| Minikube   | ≥ 1.32   | [minikube.sigs.k8s.io](https://minikube.sigs.k8s.io/docs/start/) |
| kubectl    | ≥ 1.28   | [kubernetes.io/docs](https://kubernetes.io/docs/tasks/tools/) |
| Helm       | ≥ 3.12   | [helm.sh/docs](https://helm.sh/docs/intro/install/) |
| Docker     | ≥ 24.0   | [docs.docker.com](https://docs.docker.com/get-docker/) |

**System Requirements:**
- 4 CPU cores minimum
- 8GB RAM minimum
- 20GB disk space

---

## Quick Start

### 1. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your API key
nano .env
```

**Required:** Set at least one AI API key:
- `OPENAI_API_KEY=sk-...` (OpenAI or OpenRouter)
- OR `ANTHROPIC_API_KEY=sk-ant-...` (Claude)

**Optional:** Configure email alerts:
- `ALERT_EMAIL=your-email@example.com`
- `SMTP_USER=your-gmail@gmail.com`
- `SMTP_PASS=your-app-password`

### 2. Validate Production Readiness
```bash
chmod +x scripts/*.sh
./scripts/validate-production.sh
```

### 3. Bootstrap Cluster
```bash
# Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192

# Install monitoring stack (Prometheus + Fluentd)
./scripts/bootstrap.sh
```

### 4. Deploy KORAL
```bash
# Deploy all 7 services
./scripts/deploy-all.sh

# Verify deployment
./scripts/health-check.sh
```

### 5. Access Dashboard
```bash
minikube service frontend -n koral-system
```

---

## Demo simulators

Demo/simulation pods and synthetic anomaly injectors were removed in this cleanup pass. Use real Prometheus metrics or the historical simulation scripts in `system-intelligence-evaluation` if needed for legacy testing.

---

## Architecture

### Service Architecture
```
┌─────────────────────────────────────────────────────┐
│                  koral-system (namespace)            │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │cpu-agent │  │mem-agent │  │sto-agent │  ...      │
│  │  :8001   │  │  :8002   │  │  :8003   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       └─────────────┴─────────────┘                 │
│                      │ POST /anomaly                 │
│               ┌──────▼──────┐                       │
│               │   backend   │ :8000 (ClusterIP)     │
│               └──────┬──────┘                       │
│                      │                              │
│          ┌───────────┴───────────┐                  │
│          │  correlation-engine   │ :8005             │
│          └───────────┬───────────┘                  │
│                      │                              │
│               ┌──────▼──────┐                       │
│               │  ai-engine  │ :8006                 │
│               └──────┬──────┘                       │
│                      │ WebSocket                    │
│               ┌──────▼──────┐                       │
│               │  frontend   │ :3000 → NodePort 30080│
│               └─────────────┘                       │
│                                                     │
│  ┌──────────────────────────────────────┐           │
│  │  Prometheus :9090  │  Fluentd :24224 │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

### Data Flow
1. **Agents** poll Prometheus every 10s for metrics
2. **Z-score calculation** detects anomalies (threshold: 2.5)
3. **Backend** receives anomalies, persists to SQLite
4. **Correlation Engine** analyzes patterns, identifies root cause
5. **AI Engine** generates plain-English explanation
6. **WebSocket** broadcasts updates to dashboard in real-time
7. **Email alerts** sent for critical incidents

---

## Service Port Map

| Service            | Type      | Port | Access          |
|--------------------|-----------|------|-----------------|
| backend            | ClusterIP | 8000 | internal only   |
| cpu-agent          | ClusterIP | 8001 | internal only   |
| memory-agent       | ClusterIP | 8002 | internal only   |
| storage-agent      | ClusterIP | 8003 | internal only   |
| log-agent          | ClusterIP | 8004 | internal only   |
| correlation-engine | ClusterIP | 8005 | internal only   |
| ai-engine          | ClusterIP | 8006 | internal only   |
| frontend           | NodePort  | 3000 | **30080**       |
| Prometheus         | ClusterIP | 9090 | internal only   |
| Fluentd            | ClusterIP | 24224| internal only   |

---

## Monitoring Stack

### Prometheus
- Installed via `kube-prometheus-stack` Helm chart
- Collects CPU, memory, network metrics via cAdvisor
- Node-level metrics via node_exporter
- Internal URL: `http://monitoring-kube-prometheus-prometheus.koral-system:9090`

### Fluentd
- Deployed as DaemonSet
- Tails `/var/log/containers/*.log`
- Enriches logs with namespace and pod metadata
- Accessible to log-agent for error detection

---

## Production Features

### ✅ Security
- RBAC with least privilege (read-only for agents)
- Network policies (intra-namespace only)
- Secrets via environment variables
- No hardcoded credentials

### ✅ Reliability
- Health checks on all services
- Automatic WebSocket reconnection
- Database persistence (SQLite)
- Graceful error handling

### ✅ Observability
- Structured logging on all services
- Request/response logging
- Error tracking with stack traces
- Performance metrics

### ✅ Scalability
- Horizontal pod autoscaling ready
- Resource limits configured
- Database auto-cleanup (30-day retention)
- Efficient WebSocket broadcasting

---

## Troubleshooting

### Check Service Health
```bash
./scripts/health-check.sh
```

### View Logs
```bash
# Backend
kubectl logs -f deployment/backend -n koral-system

# Agents
kubectl logs -f deployment/cpu-agent -n koral-system

# Correlation Engine
kubectl logs -f deployment/correlation-engine -n koral-system

# AI Engine
kubectl logs -f deployment/ai-engine -n koral-system
```

### Common Issues

**No incidents appearing:**
- Check agents are running: `kubectl get pods -n koral-system`
- Verify Prometheus accessible: `kubectl get svc -n koral-system | grep prometheus`
- Check agent logs for connection errors

**AI explanations missing:**
- Verify API key in .env
- Check AI engine logs: `kubectl logs deployment/ai-engine -n koral-system`
- Test health: `kubectl exec deployment/backend -n koral-system -- curl http://ai-engine:8006/health`

**Email alerts not sending:**
- Use Gmail App Password (not regular password)
- Check SMTP configuration in .env
- Review AI engine logs for email errors

---

## Teardown

```bash
# Remove all KORAL resources
./scripts/teardown.sh

# Stop Minikube
minikube stop

# Delete cluster (optional)
minikube delete
```

---

## Documentation

- [Deployment Guide & Checklist](docs/DEPLOYMENT.md)
- [Production Readiness](docs/PRODUCTION_READINESS.md)
- [Architecture Details](docs/ARCHITECTURE.md)

---

## Production Readiness

✅ All mock data removed  
✅ Production logging implemented  
✅ Comprehensive error handling  
✅ Input validation on all endpoints  
✅ Health checks configured  
✅ Resource limits set  
✅ RBAC least privilege  
✅ Network policies enforced  
✅ Secrets management via .env  
✅ Database persistence  
✅ WebSocket reconnection  
✅ AI fallback to rule-based  
✅ Email alerts for critical incidents  

**Status:** ✅ PRODUCTION READY  
**Version:** 2.0.0

---

## Support

For issues:
1. Run `./scripts/health-check.sh`
2. Check logs: `kubectl logs -f deployment/<service> -n koral-system`
3. Review [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
4. Check GitHub Issues
