# KORAL Production Deployment Guide

## ⚠️ IMPORTANT: Mock Data Removed

All mock incident creation scripts have been removed. KORAL now operates in **production mode only**.

## Quick Start

### 1. Prerequisites Check
```bash
# Verify all tools are installed
minikube version    # Should be ≥ 1.32
kubectl version     # Should be ≥ 1.28
helm version        # Should be ≥ 3.12
docker version      # Should be ≥ 24.0
```

### 2. Configure Environment
```bash
# Copy and edit .env file
cp .env.example .env
nano .env

# Required: Set at least one AI API key
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Configure email alerts
ALERT_EMAIL=your-email@example.com
SMTP_USER=your-gmail@gmail.com
SMTP_PASS=your-16-char-app-password
```

### 3. Bootstrap Cluster
```bash
# Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192

# Bootstrap monitoring stack
./scripts/bootstrap.sh
```

### 4. Deploy KORAL
```bash
# Deploy all services
./scripts/deploy-all.sh

# Verify deployment
./scripts/health-check.sh
```

### 5. Access Dashboard
```bash
# Open frontend
minikube service frontend -n koral-system

# Or get URL
minikube service frontend -n koral-system --url
```

## Testing with Real Workloads

### Option 1: Use Simulation Pods (Recommended for Demo)
```bash
# CPU spike simulation
kubectl apply -f infra/k8s/simulation/cpu-spike.yaml

# Memory pressure simulation
kubectl apply -f infra/k8s/simulation/memory-pressure.yaml

# I/O storm simulation
kubectl apply -f infra/k8s/simulation/io-storm.yaml

# Log error generator
kubectl apply -f infra/k8s/simulation/log-error-gen.yaml
```

### Option 2: Monitor Real Applications
```bash
# Deploy your application to koral-system namespace
kubectl apply -f your-app.yaml -n koral-system

# KORAL will automatically monitor all pods in the namespace
```

## Expected Behavior

1. **Agents** poll Prometheus every 10 seconds
2. **Anomalies** are detected when z-score > 2.5
3. **Correlation Engine** analyzes anomalies and identifies root cause
4. **AI Engine** generates plain-English explanations
5. **Dashboard** updates in real-time via WebSocket
6. **Email alerts** sent for critical incidents (if configured)

## Monitoring

### Check Agent Logs
```bash
kubectl logs -f deployment/cpu-agent -n koral-system
kubectl logs -f deployment/memory-agent -n koral-system
kubectl logs -f deployment/storage-agent -n koral-system
kubectl logs -f deployment/log-agent -n koral-system
```

### Check Backend Logs
```bash
kubectl logs -f deployment/backend -n koral-system
```

### Check Correlation Engine Logs
```bash
kubectl logs -f deployment/correlation-engine -n koral-system
```

### Check AI Engine Logs
```bash
kubectl logs -f deployment/ai-engine -n koral-system
```

## Troubleshooting

### No Incidents Appearing
1. Check agents are running: `kubectl get pods -n koral-system`
2. Check Prometheus is accessible: `kubectl get svc -n koral-system | grep prometheus`
3. Verify agents can reach backend: `kubectl logs deployment/cpu-agent -n koral-system`
4. Check backend logs for errors: `kubectl logs deployment/backend -n koral-system`

### AI Explanations Not Showing
1. Verify API key is set: `kubectl get deployment ai-engine -n koral-system -o yaml | grep OPENAI_API_KEY`
2. Check AI engine logs: `kubectl logs deployment/ai-engine -n koral-system`
3. Test AI engine health: `kubectl exec -it deployment/backend -n koral-system -- curl http://ai-engine:8006/health`

### Email Alerts Not Sending
1. Verify SMTP credentials in .env
2. Use Gmail App Password (not regular password)
3. Check AI engine logs for email errors

## Production Checklist

- [ ] AI API key configured (OpenAI or Anthropic)
- [ ] Email alerts configured (optional but recommended)
- [ ] Prometheus accessible from agents
- [ ] All 7 services running (4 agents + backend + correlation + frontend)
- [ ] Health check passes: `./scripts/health-check.sh`
- [ ] WebSocket connection established (check browser console)
- [ ] Test incident created via simulation pods

## Cleanup

```bash
# Remove all KORAL resources
./scripts/teardown.sh

# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
```

## Architecture Flow

```
Real Pods → Prometheus → Agents → Backend → Correlation Engine → AI Engine
                                      ↓
                                  Database
                                      ↓
                                  WebSocket
                                      ↓
                                  Dashboard
```

## Support

For issues or questions:
1. Check logs using commands above
2. Run health check: `./scripts/health-check.sh`
3. Review README.md for detailed architecture
4. Check GitHub Issues

---

**Note**: This is a production-ready deployment. All mock data and test scripts have been removed.
