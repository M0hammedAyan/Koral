# Kubernetes & Production Files Guide

This directory contains all Kubernetes manifests and configuration files for deploying KORAL to production.

## Files Overview

### Core Deployments

**koral-deployment.yaml** - Main KORAL services
- Backend deployment (2 replicas) with PostgreSQL connection
- AI Engine deployment (2 replicas)
- Both services with health checks, resource limits, and secret management
- Services expose ports on ClusterIP

**postgres-deployment.yaml** - Database for production
- StatefulSet for consistent database naming
- PersistentVolume for data durability
- PostgreSQL 16 Alpine (lightweight)
- Database credentials from secrets
- Health checks via pg_isready

**prometheus-deployment.yaml** - Metrics collection
- Single Prometheus instance
- ServiceAccount with RBAC permissions
- Scrapes: pods, nodes, kubelet, cAdvisor
- 30-day retention policy
- ConfigMap for scrape configuration

### Secrets

**koral-secrets.yaml** - Sensitive data storage
- API keys (OpenAI, Anthropic)
- Database credentials
- JWT secrets
- SMTP credentials
- Always encrypted at rest in Kubernetes

## Quick Start

### 1. Create Namespace & Secrets

```bash
# This creates koral-system namespace
kubectl apply -f koral-deployment.yaml

# Create secrets (EDIT FIRST with your values!)
kubectl edit -f koral-secrets.yaml
kubectl apply -f koral-secrets.yaml
```

### 2. Deploy Infrastructure

```bash
# Database
kubectl apply -f postgres-deployment.yaml

# Monitoring
kubectl apply -f prometheus-deployment.yaml
```

### 3. Deploy Services

```bash
# Backend & AI Engine
kubectl apply -f koral-deployment.yaml
```

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n koral-system

# Check services
kubectl get svc -n koral-system

# View logs
kubectl logs -f deployment/backend -n koral-system
```

## Configuration

### Secrets Template

Before deploying, edit `koral-secrets.yaml`:

```yaml
stringData:
  # Required
  OPENAI_API_KEY: "sk-your-actual-key"
  API_KEY: "your-api-key-for-accessing-koral"
  JWT_SECRET: "your-jwt-secret-for-token-signing"
  DB_USER: "koral"
  DB_PASS: "your-secure-database-password"
  
  # Optional (for alerts)
  SMTP_USER: "alerts@example.com"
  SMTP_PASS: "your-app-password"
  ANTHROPIC_API_KEY: "sk-ant-your-claude-key"
```

### Environment Variables

The deployments use these key environment variables:

**Backend:**
- `DB_TYPE=postgres` - Use PostgreSQL
- `DB_HOST=postgres` - Database host
- `ALLOWED_ORIGINS` - CORS whitelist
- `API_KEY` - From secrets
- `JWT_SECRET` - From secrets

**AI Engine:**
- `BACKEND_URL=http://backend:8000`
- `OPENAI_API_KEY` - From secrets
- `ANTHROPIC_API_KEY` - From secrets
- `ALERT_EMAIL` - For critical alerts
- `SMTP_*` - From secrets

## Troubleshooting

### Check Pod Status

```bash
kubectl describe pod <pod-name> -n koral-system
```

### View Logs

```bash
# Backend logs
kubectl logs deployment/backend -n koral-system -f

# AI Engine logs
kubectl logs deployment/ai-engine -n koral-system -f

# Database logs
kubectl logs statefulset/postgres -n koral-system -f
```

### Database Connection

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n koral-system -- \
  psql -U koral -d koral

# Backup database
kubectl exec postgres-0 -n koral-system -- \
  pg_dump -U koral koral > backup.sql

# Restore database
kubectl exec -i postgres-0 -n koral-system -- \
  psql -U koral koral < backup.sql
```

### Check Prometheus Targets

```bash
# Port forward to Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n koral-system

# Visit http://localhost:9090/targets
# Check which scrapers are up/down
```

## Production Considerations

### 1. Image Registry

Update image references in `koral-deployment.yaml`:

```yaml
image: your-registry/koral-backend:v1  # Change this
```

### 2. Persistent Storage

The database needs storage. Options:
- **Cloud Storage** - AWS EBS, GCP PD, Azure Disk
- **NFS** - Shared network storage
- **Local** - Single-node, not recommended for HA

### 3. Network Policies

Restrict traffic:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: koral-backend-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: ai-engine
```

### 4. Ingress (External Access)

Add ingress for HTTPS:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: koral-ingress
spec:
  rules:
    - host: koral.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
```

### 5. Sealed Secrets (Prod)

For production, use Sealed Secrets:
```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/sealed-secrets-v0.24.0.yaml

# Seal your secrets
kubeseal -f koral-secrets.yaml -w koral-secrets-sealed.yaml

# Deploy sealed secrets
kubectl apply -f koral-secrets-sealed.yaml
```

### 6. Resource Quotas

Set namespace quotas:
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: koral-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
```

### 7. Monitoring & Alerts

Set up alerts in Prometheus:
```yaml
groups:
  - name: koral
    rules:
      - alert: BackendDown
        expr: up{job="backend"} == 0
        for: 5m
        annotations:
          summary: "Backend is down"
      
      - alert: DatabaseDiskFull
        expr: |
          (kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes) > 0.9
        annotations:
          summary: "Database disk is 90% full"
```

## Upgrade Process

### Rolling Update Example

```bash
# Update image
kubectl set image deployment/backend \
  backend=your-registry/koral-backend:v2 \
  -n koral-system

# Monitor rollout
kubectl rollout status deployment/backend -n koral-system

# Rollback if needed
kubectl rollout undo deployment/backend -n koral-system
```

## Cleanup

```bash
# Delete all KORAL resources
kubectl delete namespace koral-system

# This also deletes:
# - All deployments
# - All services
# - All PVCs (including database!)
# - All secrets
```

## Related Documentation

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [PostgreSQL on Kubernetes](https://www.postgresql.org/docs/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Production Grade Checklist](../PRODUCTION_DEPLOYMENT.md)
