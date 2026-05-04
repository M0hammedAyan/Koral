<<<<<<< HEAD
# Korel
a correlation engine that doesn’t just detect failures, but explains why they happen in real time.
=======
# KORAL — Kubernetes Observability with Real-time ArtificialIntelligence Logic

> **Member 2 — Infrastructure & DevOps**
> This repository owns the entire Kubernetes infrastructure, monitoring stack, Helm deployments, CI/CD pipeline, RBAC, networking, and simulation environment for KORAL.

---

## What is KORAL?

KORAL is a real-time AI-powered Kubernetes observability system. It detects anomalies across CPU, memory, storage, and logs — then correlates them to identify root causes and explain incidents in plain English.

```
Metrics → Agents → Backend → Correlation Engine → Incident → WebSocket → Dashboard
```

---

## Prerequisites

| Tool       | Version  | Install |
|------------|----------|---------|
| Minikube   | ≥ 1.32   | [minikube.sigs.k8s.io](https://minikube.sigs.k8s.io/docs/start/) |
| kubectl    | ≥ 1.28   | [kubernetes.io/docs](https://kubernetes.io/docs/tasks/tools/) |
| Helm       | ≥ 3.12   | [helm.sh/docs](https://helm.sh/docs/intro/install/) |
| Docker     | ≥ 24.0   | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Git Bash   | any      | Included with Git for Windows |

> **Windows users:** All scripts use absolute paths to `minikube.exe`, `helm.exe`, and `kubectl.exe`. Update the path variables at the top of each script in `scripts/` if your install locations differ.

---

## Quick Start

```bash
# 1. Make scripts executable
chmod +x scripts/*.sh

# 2. Bootstrap cluster + monitoring (one-time)
./scripts/bootstrap.sh

# 3. Deploy all 7 KORAL services
./scripts/deploy-all.sh

# 4. Validate everything is healthy
./scripts/health-check.sh

# 5. Open the dashboard
minikube service frontend -n koral-system
```

---

## Demo Flow

Trigger simulations to generate real anomalies:

```bash
# I/O storm — primary demo scenario (triggers cross-pod correlation)
kubectl apply -f infra/k8s/simulation/io-storm.yaml

# CPU spike
kubectl apply -f infra/k8s/simulation/cpu-spike.yaml

# Memory pressure
kubectl apply -f infra/k8s/simulation/memory-pressure.yaml

# Log error generator
kubectl apply -f infra/k8s/simulation/log-error-gen.yaml
```

Expected demo timeline:
1. Simulation pods start generating load
2. Agents detect anomalies (z-score threshold breach)
3. Correlation engine links affected pods
4. Root cause identified and incident created
5. Dashboard updates in real-time via WebSocket
6. Plain-English explanation visible in UI

> Full flow visible in under 60 seconds.

---

## Teardown

```bash
./scripts/teardown.sh
```

Removes all Helm releases, deletes the `koral-system` namespace, and stops Minikube.

---

## Directory Structure

```
KORAL/
├── .github/
│   └── workflows/
│       └── ci-cd.yaml              # GitHub Actions — build, push, deploy
│
├── agents/                         # Stub Dockerfiles (Member 3 fills in)
│   ├── cpu-agent/Dockerfile
│   ├── memory-agent/Dockerfile
│   ├── storage-agent/Dockerfile
│   └── log-agent/Dockerfile
│
├── backend/Dockerfile              # Stub (Member 3 fills in)
├── frontend/Dockerfile             # Stub (Member 4 fills in)
├── correlation-engine/Dockerfile   # Stub (Member 1 fills in)
│
├── charts/                         # Helm charts — one per service
│   ├── cpu-agent/
│   ├── memory-agent/
│   ├── storage-agent/
│   ├── log-agent/
│   ├── backend/
│   ├── frontend/
│   └── correlation-engine/
│
├── infra/
│   ├── k8s/
│   │   ├── namespaces/
│   │   │   └── namespace.yaml      # koral-system namespace
│   │   ├── rbac/
│   │   │   └── rbac.yaml           # ServiceAccount + ClusterRole + Binding
│   │   ├── networking/
│   │   │   └── network-policy.yaml # Intra-namespace allow, external block
│   │   └── simulation/
│   │       ├── cpu-spike.yaml
│   │       ├── io-storm.yaml       # PVC + busybox I/O loop
│   │       ├── memory-pressure.yaml
│   │       └── log-error-gen.yaml  # Structured JSON error log emitter
│   └── monitoring/
│       └── fluentd/
│           └── values.yaml         # Fluentd DaemonSet Helm values
│
├── scripts/
│   ├── bootstrap.sh                # Cluster init + monitoring install
│   ├── deploy-all.sh               # Deploy all 7 Helm charts
│   ├── health-check.sh             # Pre-demo validation
│   └── teardown.sh                 # Full cleanup
│
├── README.md
└── requirements.txt                # Infrastructure tool version requirements
```

---

## Service Architecture

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

---

## Service Port Map

| Service            | Kubernetes Type | Internal Port | External Access |
|--------------------|-----------------|---------------|-----------------|
| backend            | ClusterIP       | 8000          | internal only   |
| cpu-agent          | ClusterIP       | 8001          | internal only   |
| memory-agent       | ClusterIP       | 8002          | internal only   |
| storage-agent      | ClusterIP       | 8003          | internal only   |
| log-agent          | ClusterIP       | 8004          | internal only   |
| correlation-engine | ClusterIP       | 8005          | internal only   |
| frontend           | NodePort        | 3000          | **30080**       |
| Prometheus         | ClusterIP       | 9090          | internal only   |
| Fluentd            | ClusterIP       | 24224         | internal only   |

---

## Monitoring Stack

### Prometheus + cAdvisor + node_exporter
Installed via `kube-prometheus-stack` Helm chart. Provides:
- Container CPU, memory, network metrics (cAdvisor)
- Node-level metrics (node_exporter)
- Metrics API for agents to query

Prometheus internal URL (used by agents):
```
http://monitoring-kube-prometheus-prometheus.koral-system:9090
```

### Fluentd
Deployed as a DaemonSet. Tails `/var/log/containers/*.log` from all pods, tags logs as `koral.*`, enriches with `namespace` and `pod` metadata, and outputs to stdout (accessible to log-agent).

---

## RBAC

All agent pods run under the `koral-agent` ServiceAccount which has a ClusterRole granting:

```yaml
resources: ["pods", "nodes", "namespaces", "events", "persistentvolumeclaims"]
verbs:     ["get", "list", "watch"]

resources: ["pods", "nodes"]   # metrics.k8s.io
verbs:     ["get", "list"]
```

No write permissions. Principle of least privilege.

---

## Helm Charts

Each chart follows the same structure:

```
charts/<service>/
├── Chart.yaml          # name, version, description
├── values.yaml         # image, port, resources, env vars
└── templates/
    ├── deployment.yaml # Deployment with env injection + resource limits
    └── service.yaml    # ClusterIP or NodePort
```

To override image for a specific service during deploy:
```bash
helm upgrade --install cpu charts/cpu-agent \
  -n koral-system \
  --set image.repository=yourdockerhub/cpu-agent \
  --set image.tag=latest
```

---

## CI/CD Pipeline

File: `.github/workflows/ci-cd.yaml`

**On push to `main`:**
1. Matrix-builds all 7 Docker images in parallel
2. Pushes to DockerHub tagged with both `latest` and the commit SHA
3. Deploys all charts via Helm using the SHA tag (ensures fresh image pull)

**Required GitHub Secrets:**

| Secret              | Description                              |
|---------------------|------------------------------------------|
| `DOCKERHUB_USERNAME`| Your DockerHub username                  |
| `DOCKERHUB_TOKEN`   | DockerHub access token (not password)    |
| `KUBECONFIG`        | `base64 -w0 ~/.kube/config` output       |

To encode your kubeconfig:
```bash
base64 -w0 ~/.kube/config
```

---

## Health Check

Run before every demo:

```bash
./scripts/health-check.sh
```

Checks:
- Cluster node is Ready
- `koral-system` namespace exists
- All 7 service pods are Running
- Prometheus and Fluentd are running
- All 7 Kubernetes Services exist
- Zero pod restarts
- RBAC ServiceAccount and ClusterRoleBinding exist

Output:
```
==============================
 KORAL Health Check
==============================
  [PASS] Node is Ready
  [PASS] koral-system namespace exists
  [PASS] Pod: cpu
  ...
  [PASS] No pod restarts detected
==============================
 Results: 18 passed, 0 failed
 STATUS: SYSTEM READY FOR DEMO
==============================
```

---

## Simulation Pods

| Pod                  | What it does                                      | Triggers         |
|----------------------|---------------------------------------------------|------------------|
| `cpu-spike-sim`      | Runs `dd` in a tight loop to max CPU              | CPU Agent        |
| `memory-pressure-sim`| Allocates 512MB RAM via `stress`                  | Memory Agent     |
| `io-storm-sim`       | Writes to a PVC continuously via `dd`             | Storage Agent    |
| `log-error-gen-sim`  | Emits structured JSON ERROR/WARN logs every 2s    | Log Agent        |

---

## Teammate Integration Guide

When a teammate delivers their code:

```bash
# 1. Drop their code into the correct directory
#    e.g. agents/cpu-agent/main.py + requirements.txt

# 2. Build and push their image
docker build -t yourdockerhub/cpu-agent:latest ./agents/cpu-agent
docker push yourdockerhub/cpu-agent:latest

# 3. Update the chart and redeploy
helm upgrade cpu charts/cpu-agent \
  -n koral-system \
  --set image.repository=yourdockerhub/cpu-agent \
  --set image.tag=latest
```

| Member | Directory               | Port |
|--------|-------------------------|------|
| M3     | `agents/cpu-agent/`     | 8001 |
| M3     | `agents/memory-agent/`  | 8002 |
| M3     | `agents/storage-agent/` | 8003 |
| M3     | `agents/log-agent/`     | 8004 |
| M3     | `backend/`              | 8000 |
| M1     | `correlation-engine/`   | 8005 |
| M4     | `frontend/`             | 3000 |

---

## Troubleshooting

**Pods stuck in `Pending`**
```bash
kubectl describe pod <pod-name> -n koral-system
# Usually: insufficient resources → increase Minikube memory
minikube stop && minikube start --cpus=4 --memory=8192
```

**ImagePullBackOff**
```bash
# Image not pushed to DockerHub yet — use local image
eval $(minikube docker-env)
docker build -t cpu-agent:latest ./agents/cpu-agent
helm upgrade cpu charts/cpu-agent -n koral-system --set image.pullPolicy=Never
```

**Agents can't reach Prometheus**
```bash
kubectl get svc -n koral-system | grep prometheus
# Verify the service name matches PROMETHEUS_URL in values.yaml
```


**Permission denied errors in agent logs**
```bash
kubectl get clusterrolebinding koral-agent-binding
kubectl auth can-i list pods --as=system:serviceaccount:koral-system:koral-agent
```

**Frontend not accessible**
```bash
minikube service frontend -n koral-system
# Or get the URL manually:
minikube service frontend -n koral-system --url
```
>>>>>>> MohammedAyan
