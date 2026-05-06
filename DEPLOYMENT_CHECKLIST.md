# KORAL Production Deployment Checklist

## Pre-Deployment Validation

### 1. Environment Setup
- [ ] `.env` file created from `.env.example`
- [ ] At least one AI API key configured (OpenAI or Anthropic)
- [ ] Email alerts configured (optional but recommended)
- [ ] SMTP credentials set for Gmail (if using email alerts)
- [ ] Prometheus URL configured correctly
- [ ] Namespace set to `koral-system` or your target namespace

### 2. Infrastructure Prerequisites
- [ ] Minikube installed (≥ 1.32)
- [ ] kubectl installed (≥ 1.28)
- [ ] Helm installed (≥ 3.12)
- [ ] Docker installed (≥ 24.0)
- [ ] Sufficient resources: 4 CPUs, 8GB RAM minimum

### 3. Code Validation
- [ ] Run `./scripts/validate-production.sh` - all checks pass
- [ ] No mock data files present (create_incident.py, simulate.py, etc.)
- [ ] All Dockerfiles present and valid
- [ ] All Helm charts complete
- [ ] All agent implementations complete

### 4. Security Checklist
- [ ] API keys stored in `.env`, not committed to git
- [ ] `.env` file in `.gitignore`
- [ ] RBAC configured with least privilege
- [ ] Network policies in place
- [ ] No hardcoded credentials in code

## Deployment Steps

### Step 1: Start Minikube
```bash
minikube start --cpus=4 --memory=8192
```

### Step 2: Bootstrap Monitoring Stack
```bash
./scripts/bootstrap.sh
```

Expected output:
- Namespace `koral-system` created
- Prometheus stack installed
- Fluentd DaemonSet deployed
- RBAC configured

### Step 3: Deploy KORAL Services
```bash
./scripts/deploy-all.sh
```

Expected output:
- 7 Helm releases installed
- All pods starting

### Step 4: Verify Deployment
```bash
./scripts/health-check.sh
```

Expected output:
- All pods Running
- No restarts
- All services exist
- System ready for demo

### Step 5: Access Dashboard
```bash
minikube service frontend -n koral-system
```

## Post-Deployment Validation

### 1. Check All Services Running
```bash
kubectl get pods -n koral-system
```

Expected: 7+ pods in Running state

### 2. Check Logs for Errors
```bash
# Backend
kubectl logs -f deployment/backend -n koral-system

# Agents
kubectl logs -f deployment/cpu-agent -n koral-system
kubectl logs -f deployment/memory-agent -n koral-system

# Correlation Engine
kubectl logs -f deployment/correlation-engine -n koral-system

# AI Engine
kubectl logs -f deployment/ai-engine -n koral-system
```

Expected: No error messages, agents polling successfully

### 3. Verify WebSocket Connection
- Open browser console (F12)
- Look for: `[KORAL] WS connected to ws://...`
- Status indicator should show "LIVE"

### 4. Test with Simulation Pods
```bash
# Deploy CPU spike simulation
kubectl apply -f infra/k8s/simulation/cpu-spike.yaml

# Wait 30-60 seconds

# Check dashboard for:
# - Anomaly banner appears
# - Incident card created
# - AI explanation generated
```

### 5. Verify AI Integration
- Check incident has AI explanation
- Verify model used (GPT-4o or Claude)
- For critical incidents, check email was sent (if configured)

## Production Monitoring

### Key Metrics to Watch

1. **Agent Health**
   - Agents polling every 10 seconds
   - No connection errors to Prometheus
   - Anomalies being detected when thresholds breached

2. **Backend Health**
   - WebSocket connections stable
   - Database writes successful
   - No memory leaks

3. **AI Engine Health**
   - API calls succeeding
   - Response times < 5 seconds
   - Email alerts sending (if configured)

### Troubleshooting Commands

```bash
# Check all resources
kubectl get all -n koral-system

# Check events
kubectl get events -n koral-system --sort-by=.lastTimestamp

# Check specific pod
kubectl describe pod <pod-name> -n koral-system

# Check logs with timestamps
kubectl logs <pod-name> -n koral-system --timestamps

# Check resource usage
kubectl top pods -n koral-system
kubectl top nodes

# Restart a service
kubectl rollout restart deployment/<service> -n koral-system
```

## Performance Benchmarks

### Expected Performance
- **Anomaly Detection Latency**: < 10 seconds from metric change to detection
- **Incident Creation**: < 2 seconds from anomaly to incident
- **AI Analysis**: < 5 seconds for explanation generation
- **Dashboard Update**: Real-time via WebSocket (< 1 second)
- **End-to-End**: < 20 seconds from issue to dashboard notification

### Resource Usage (per service)
- **Agents**: 50-100 MB RAM, 0.1 CPU
- **Backend**: 200-300 MB RAM, 0.2 CPU
- **Correlation Engine**: 150-250 MB RAM, 0.15 CPU
- **AI Engine**: 200-400 MB RAM, 0.2 CPU
- **Frontend**: 100-150 MB RAM, 0.1 CPU

## Scaling Considerations

### Horizontal Scaling
```bash
# Scale agents for high-traffic clusters
kubectl scale deployment cpu-agent --replicas=3 -n koral-system

# Scale backend for more concurrent users
kubectl scale deployment backend --replicas=2 -n koral-system
```

### Vertical Scaling
Edit Helm values.yaml:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Backup and Recovery

### Backup Database
```bash
kubectl exec deployment/backend -n koral-system -- cat /data/koral.db > backup-$(date +%Y%m%d).db
```

### Restore Database
```bash
kubectl cp backup-20240101.db backend-pod:/data/koral.db -n koral-system
kubectl rollout restart deployment/backend -n koral-system
```

## Maintenance

### Update KORAL
```bash
# Pull latest code
git pull origin main

# Rebuild images
docker compose build

# Redeploy
./scripts/deploy-all.sh
```

### Clean Old Data
```bash
# Database auto-manages size
# To manually clean old incidents (>30 days):
kubectl exec -it deployment/backend -n koral-system -- python3 -c "
import sqlite3
conn = sqlite3.connect('/data/koral.db')
conn.execute('DELETE FROM incidents WHERE created_at < datetime(\"now\", \"-30 days\")')
conn.execute('DELETE FROM anomalies WHERE created_at < datetime(\"now\", \"-7 days\")')
conn.commit()
"
```

## Production Readiness Certification

- [x] All mock data removed
- [x] Production logging implemented
- [x] Error handling comprehensive
- [x] Input validation on all endpoints
- [x] Health checks configured
- [x] Resource limits set
- [x] RBAC least privilege
- [x] Network policies enforced
- [x] Secrets management via .env
- [x] Database persistence configured
- [x] WebSocket reconnection logic
- [x] AI fallback to rule-based engine
- [x] Email alerts for critical incidents
- [x] Comprehensive documentation

## Support

For production issues:
1. Check logs: `kubectl logs -f deployment/<service> -n koral-system`
2. Run health check: `./scripts/health-check.sh`
3. Review PRODUCTION_GUIDE.md
4. Check GitHub Issues

---

**Status**: ✅ PRODUCTION READY

**Last Validated**: $(date)

**Version**: 2.0.0
