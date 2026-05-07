# KORAL Production Deployment Checklist

## Pre-Deployment

### Code Review
- [ ] Review all authentication changes in `backend/auth.py`
- [ ] Review database abstraction in `backend/database.py`
- [ ] Verify CORS restrictions match your domain requirements
- [ ] Check API key length and complexity (min 32 chars recommended)
- [ ] Review JWT secret strength (min 32 chars recommended)

### Configuration
- [ ] Fill in all required fields in `k8s/koral-secrets.yaml`:
  - [ ] `OPENAI_API_KEY` - Valid OpenAI key
  - [ ] `ANTHROPIC_API_KEY` - Valid Anthropic key (optional)
  - [ ] `API_KEY` - Secure, random API key
  - [ ] `JWT_SECRET` - Secure, random secret
  - [ ] `DB_USER` - PostgreSQL username
  - [ ] `DB_PASS` - Secure PostgreSQL password
  - [ ] `SMTP_USER` - Email username for alerts
  - [ ] `SMTP_PASS` - Email app password
- [ ] Update `.env.example` values if using Docker Compose
- [ ] Verify `ALLOWED_ORIGINS` matches your frontend URL
- [ ] Review `PROMETHEUS_URL` points to your Prometheus instance

### Infrastructure
- [ ] Kubernetes cluster is running and accessible
- [ ] `kubectl` is configured and can access the cluster
- [ ] Persistent storage is configured (EBS, GCP PD, NFS, etc.)
- [ ] Container registry is accessible (Docker Hub, ECR, GCR, etc.)
- [ ] Network policies allow inter-pod communication

### Docker Images
- [ ] Built backend image: `docker build -t your-registry/koral-backend:v1 -f backend/Dockerfile .`
- [ ] Built AI engine image: `docker build -t your-registry/koral-ai-engine:v1 -f ai_engine/Dockerfile .`
- [ ] Pushed images to registry: `docker push your-registry/koral-backend:v1`
- [ ] Pushed images to registry: `docker push your-registry/koral-ai-engine:v1`
- [ ] Updated image references in `k8s/koral-deployment.yaml`

### Testing
- [ ] Tested locally with `docker compose -f docker-compose-prod.yml up -d`
- [ ] Verified PostgreSQL connection works
- [ ] Verified Prometheus is collecting metrics
- [ ] Tested API with API key header:
  ```bash
  curl -H "X-API-Key: test-key" http://localhost:8000/health
  ```
- [ ] Verified CORS restrictions work

---

## Deployment Steps

### Step 1: Prepare Kubernetes
```bash
# Create namespace (included in koral-deployment.yaml but verify)
kubectl create namespace koral-system

# Label nodes if needed (for storage affinity)
kubectl label nodes node-1 storage=koral --overwrite
```

**Checklist:**
- [ ] Namespace created
- [ ] Nodes labeled if required
- [ ] PersistentStorageClass configured

### Step 2: Deploy Secrets
```bash
# Apply secrets
kubectl apply -f k8s/koral-secrets.yaml

# Verify secrets are created
kubectl get secrets -n koral-system
```

**Checklist:**
- [ ] `koral-secrets` secret created
- [ ] All keys are present: `kubectl get secret koral-secrets -n koral-system -o yaml`
- [ ] Secrets are NOT empty or default values

### Step 3: Deploy Infrastructure
```bash
# Deploy PostgreSQL
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for postgres to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n koral-system --timeout=300s

# Deploy Prometheus
kubectl apply -f k8s/prometheus-deployment.yaml

# Wait for prometheus to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n koral-system --timeout=300s
```

**Checklist:**
- [ ] PostgreSQL pod is running: `kubectl get pod -l app=postgres -n koral-system`
- [ ] PostgreSQL pod is ready (1/1): `kubectl get pods -n koral-system`
- [ ] PersistentVolume is bound: `kubectl get pv`
- [ ] Prometheus pod is running: `kubectl get pod -l app=prometheus -n koral-system`
- [ ] Prometheus is healthy: `kubectl exec -it <prometheus-pod> -n koral-system -- wget -O- http://localhost:9090/-/healthy`

### Step 4: Deploy KORAL Services
```bash
# Deploy backend and AI engine
kubectl apply -f k8s/koral-deployment.yaml

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=backend -n koral-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=ai-engine -n koral-system --timeout=300s
```

**Checklist:**
- [ ] Backend pods are running: `kubectl get pods -l app=backend -n koral-system`
- [ ] AI Engine pods are running: `kubectl get pods -l app=ai-engine -n koral-system`
- [ ] Services are created: `kubectl get svc -n koral-system`
- [ ] All pods show 1/1 Ready: `kubectl get pods -n koral-system`

---

## Post-Deployment Verification

### Check All Services
```bash
# List all pods
kubectl get pods -n koral-system

# List all services
kubectl get svc -n koral-system

# Describe services
kubectl describe svc backend -n koral-system
kubectl describe svc ai-engine -n koral-system
```

**Checklist:**
- [ ] All pods show `Running` status
- [ ] All pods show `1/1` Ready
- [ ] All services show proper IP addresses
- [ ] No pods show `CrashLoopBackOff` or `Error` status

### Test Connectivity

```bash
# Test backend health
kubectl exec -it $(kubectl get pod -l app=backend -n koral-system -o jsonpath='{.items[0].metadata.name}') \
  -n koral-system -- curl http://localhost:8000/health

# Test AI engine health
kubectl exec -it $(kubectl get pod -l app=ai-engine -n koral-system -o jsonpath='{.items[0].metadata.name}') \
  -n koral-system -- curl http://localhost:8006/health

# Test database connection
kubectl exec -it postgres-0 -n koral-system -- \
  psql -U koral -d koral -c "SELECT 1"
```

**Checklist:**
- [ ] Backend health endpoint returns `{"status": "ok", ...}`
- [ ] AI Engine health endpoint returns status
- [ ] Database connection succeeds
- [ ] Logs show no errors: `kubectl logs deployment/backend -n koral-system | grep -i error`

### Test API Authentication

```bash
# Test with API key
kubectl port-forward -n koral-system svc/backend 8000:8000 &

# Should fail without API key
curl http://localhost:8000/health  # Expect 401 if auth is enabled

# Should succeed with API key
curl -H "X-API-Key: your-actual-api-key" http://localhost:8000/health  # Expect 200
```

**Checklist:**
- [ ] API requires X-API-Key header
- [ ] Invalid API key returns 403
- [ ] Valid API key returns 200
- [ ] CORS headers are correct

### Check Metrics Flow

```bash
# Access Prometheus
kubectl port-forward -n koral-system svc/prometheus 9090:9090 &

# Visit http://localhost:9090

# Check targets
curl http://localhost:9090/api/v1/targets
```

**Checklist:**
- [ ] Prometheus is accessible
- [ ] All scrape targets show `State: up`
- [ ] Pod metrics are being collected
- [ ] Query `up{job="backend"}` returns data

---

## Production Hardening

### Security Hardening
- [ ] Network policies are in place to restrict inter-pod traffic
- [ ] Pod security policies restrict privileged containers
- [ ] RBAC roles are configured (least privilege)
- [ ] Ingress is configured with HTTPS/TLS
- [ ] API Gateway or WAF is in front of services

### Observability
- [ ] Logs are being sent to centralized logging (ELK, DataDog, etc.)
- [ ] Metrics are being scraped by central Prometheus
- [ ] Alerts are configured for critical issues
- [ ] Dashboards are set up (Grafana, etc.)

### Backups & Recovery
- [ ] Database backups are automated
- [ ] Backup retention policy is set
- [ ] Restore procedure has been tested
- [ ] Disaster recovery plan is documented

### Scaling & HA
- [ ] Horizontal Pod Autoscaling is configured
- [ ] Multiple replicas are running in different nodes
- [ ] Pod Disruption Budgets are set
- [ ] Load balancing is configured for services

---

## Monitoring & Maintenance

### Daily Checks
- [ ] All pods are running and healthy
- [ ] No pods in crash loops
- [ ] Error rates are normal
- [ ] CPU/memory usage is within limits
- [ ] Disk usage is not growing unexpectedly

### Weekly Checks
- [ ] Database backups completed successfully
- [ ] No security warnings in logs
- [ ] All components updated to latest patches
- [ ] Performance metrics are acceptable

### Monthly Checks
- [ ] Disaster recovery procedure tested
- [ ] Capacity planning updated
- [ ] Cost analysis reviewed
- [ ] Security audit completed

---

## Rollback Procedure

If something goes wrong, you can rollback using Kubernetes rollout:

```bash
# Check rollout history
kubectl rollout history deployment/backend -n koral-system

# Rollback to previous version
kubectl rollout undo deployment/backend -n koral-system

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n koral-system

# Monitor rollout
kubectl rollout status deployment/backend -n koral-system
```

**Checklist:**
- [ ] Know which revision was the last stable one
- [ ] Have tested rollback procedure
- [ ] Communication plan is in place for rollbacks
- [ ] Post-rollback verification steps are documented

---

## Troubleshooting Common Issues

### Issue: Pods stuck in Pending

```bash
kubectl describe pod <pod-name> -n koral-system

# Likely causes:
# 1. PersistentVolume not available
# 2. Node selector constraints not met
# 3. Insufficient cluster resources
```

### Issue: CrashLoopBackOff

```bash
kubectl logs <pod-name> -n koral-system

# Check:
# 1. Application errors in logs
# 2. Configuration issues (env vars, secrets)
# 3. Resource limits too restrictive
```

### Issue: Database connection refused

```bash
kubectl exec -it postgres-0 -n koral-system -- psql -U koral -d koral

# Check:
# 1. PostgreSQL service DNS is resolvable
# 2. Password is correct in secrets
# 3. Database pods are running
```

### Issue: Prometheus has no data

```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Issues:
# 1. Scrape target pods are not running
# 2. Ports are incorrect
# 3. Service DNS is not resolvable
```

---

## Documentation & Handoff

- [ ] All configuration is documented
- [ ] Runbooks are created for common tasks
- [ ] On-call procedures are documented
- [ ] Escalation paths are clear
- [ ] Team is trained on operations

---

## Final Sign-Off

- [ ] QA team has verified functionality
- [ ] Security review is complete
- [ ] Performance baselines are set
- [ ] Stakeholders approve production deployment
- [ ] Deployment is scheduled
- [ ] Deployment team is prepared
- [ ] Rollback plan is tested and ready

---

**Deployed Date:** ________________
**Deployed By:** ________________
**Approved By:** ________________
**Notes:** ________________________________________________
