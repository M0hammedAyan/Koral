# KORAL Production Quick Reference

## Local Development

```bash
# Start with SQLite and no auth required
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f backend
```

## Production Testing (Local)

```bash
# Full setup: PostgreSQL, Prometheus, proper secrets
docker compose -f docker-compose-prod.yml up -d

# Access services
curl http://localhost:8000/health  # Requires API key in prod
curl -H "X-API-Key: dev-api-key" http://localhost:8000/health

# Prometheus
open http://localhost:9090

# Database
psql -h localhost -U koral -d koral

# Tear down
docker compose -f docker-compose-prod.yml down -v
```

## Kubernetes Deployment

### Initial Setup
```bash
# Build images
docker build -t your-registry/koral-backend:v1 -f backend/Dockerfile .
docker build -t your-registry/koral-ai-engine:v1 -f ai_engine/Dockerfile .
docker push your-registry/koral-backend:v1
docker push your-registry/koral-ai-engine:v1

# Update image references in k8s/koral-deployment.yaml

# Deploy secrets (EDIT FIRST!)
kubectl apply -f k8s/koral-secrets.yaml

# Deploy infrastructure
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/prometheus-deployment.yaml

# Deploy services
kubectl apply -f k8s/koral-deployment.yaml
```

### Monitoring
```bash
# Check pod status
kubectl get pods -n koral-system

# Watch rollout
kubectl rollout status deployment/backend -n koral-system

# View logs
kubectl logs -f deployment/backend -n koral-system
kubectl logs -f deployment/ai-engine -n koral-system

# Port forward to test
kubectl port-forward -n koral-system svc/backend 8000:8000

# Test API
curl -H "X-API-Key: your-api-key" http://localhost:8000/health
```

### Database Operations
```bash
# Connect to database
kubectl exec -it postgres-0 -n koral-system -- psql -U koral -d koral

# Backup
kubectl exec postgres-0 -n koral-system -- pg_dump -U koral koral > backup.sql

# Restore
kubectl exec -i postgres-0 -n koral-system -- psql -U koral koral < backup.sql

# Check disk usage
kubectl exec postgres-0 -n koral-system -- du -sh /var/lib/postgresql/data
```

### Prometheus Access
```bash
# Port forward
kubectl port-forward -n koral-system svc/prometheus 9090:9090

# Query metrics
curl http://localhost:9090/api/v1/query?query=up
curl http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total

# Check scrape targets
curl http://localhost:9090/api/v1/targets
```

### Updates & Rollback
```bash
# Update backend image
kubectl set image deployment/backend \
  backend=your-registry/koral-backend:v2 \
  -n koral-system

# Check rollout status
kubectl rollout status deployment/backend -n koral-system

# View history
kubectl rollout history deployment/backend -n koral-system

# Rollback
kubectl rollout undo deployment/backend -n koral-system

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=1 -n koral-system
```

## Configuration Management

### Environment Variables

**For Docker Compose:**
```bash
# Create .env file
cp .env.example .env
# Edit .env with your values
```

**For Kubernetes:**
```bash
# Edit secrets
kubectl edit secret koral-secrets -n koral-system

# Apply changes
kubectl apply -f k8s/koral-secrets.yaml
```

### Common Configuration Changes

```bash
# Change API key
kubectl patch secret koral-secrets -n koral-system -p \
  '{"stringData":{"API_KEY":"new-api-key"}}'

# Change database password
kubectl patch secret koral-secrets -n koral-system -p \
  '{"stringData":{"DB_PASS":"new-password"}}'

# Change allowed origins
kubectl set env deployment/backend \
  ALLOWED_ORIGINS="https://new-domain.com" \
  -n koral-system
```

## Testing & Validation

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# AI Engine health
curl http://localhost:8006/health

# Correlation Engine health
curl http://localhost:8005/health

# Database connection
kubectl exec -it postgres-0 -n koral-system -- \
  psql -U koral -d koral -c "SELECT 1"
```

### API Testing

```bash
# Create anomaly report
curl -X POST http://localhost:8000/anomalies \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pod": "my-pod",
    "namespace": "koral-system",
    "metric": "cpu",
    "value": 95.5,
    "unit": "%",
    "z_score": 3.2,
    "is_anomaly": true
  }'

# Get incidents
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/incidents

# Get incident details
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/incidents/INC-ABC123
```

### Prometheus Queries

```bash
# Pod CPU usage
query=rate(container_cpu_usage_seconds_total[5m])

# Pod memory usage
query=container_memory_working_set_bytes

# Backend uptime
query=up{job="backend"}

# Error rate
query=rate(http_requests_total{status=~"5.."}[5m])
```

## Troubleshooting Commands

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n koral-system

# Check recent errors
kubectl logs <pod-name> -n koral-system | tail -100

# Check resource usage
kubectl top pods -n koral-system

# Check events
kubectl get events -n koral-system --sort-by='.lastTimestamp'

# Check persistent volumes
kubectl get pv
kubectl describe pv <pv-name>

# Check persistent volume claims
kubectl get pvc -n koral-system
kubectl describe pvc <pvc-name> -n koral-system

# Check services
kubectl get svc -n koral-system
kubectl describe svc <svc-name> -n koral-system

# Check ingress
kubectl get ingress -n koral-system
kubectl describe ingress <ingress-name> -n koral-system
```

## Cleaning Up

```bash
# Remove a deployment
kubectl delete deployment backend -n koral-system

# Remove a service
kubectl delete svc backend -n koral-system

# Remove all resources in namespace
kubectl delete namespace koral-system

# Remove all but keep data
kubectl delete deployment,svc --all -n koral-system
```

## Docker Image Management

```bash
# List local images
docker images | grep koral

# Remove image
docker rmi koral-backend:latest

# Tag for registry
docker tag koral-backend:latest your-registry/koral-backend:v1

# Push
docker push your-registry/koral-backend:v1

# Pull
docker pull your-registry/koral-backend:v1

# Build with specific tag
docker build -t your-registry/koral-backend:v1 -f backend/Dockerfile .
```

## Certificate Management (for HTTPS)

```bash
# Create TLS secret for Ingress
kubectl create secret tls koral-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n koral-system

# Update Ingress to use TLS
kubectl patch ingress koral-ingress -n koral-system --type='json' \
  -p='[{"op":"add","path":"/spec/tls","value":[{"hosts":["koral.example.com"],"secretName":"koral-tls"}]}]'
```

## Performance Tuning

```bash
# Increase backend replicas
kubectl scale deployment backend --replicas=5 -n koral-system

# Update resource limits
kubectl patch deployment backend -n koral-system --type='json' \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/cpu","value":"2000m"}]'

# Check current scaling
kubectl get hpa -n koral-system  # Horizontal Pod Autoscaler
kubectl describe hpa backend -n koral-system
```

## Getting Help

```bash
# Kubernetes API documentation
kubectl api-resources

# Explain resource fields
kubectl explain pod.spec.containers

# Get detailed kubectl help
kubectl --help
kubectl logs --help

# View kubectl context
kubectl config current-context
kubectl config get-contexts
kubectl get nodes
```

## Emergency Commands

```bash
# Delete stuck pod (force)
kubectl delete pod <pod-name> --grace-period=0 --force -n koral-system

# View all resources in namespace
kubectl get all -n koral-system

# Get resource YAML
kubectl get pod <pod-name> -n koral-system -o yaml

# Edit resource directly
kubectl edit pod <pod-name> -n koral-system

# Port forward to debug
kubectl port-forward pod/<pod-name> 8000:8000 -n koral-system

# Execute command in pod
kubectl exec <pod-name> -n koral-system -- bash
kubectl exec <pod-name> -n koral-system -- curl http://localhost:8000/health
```

---

**Pro Tips:**
- Always use `-n koral-system` to target the correct namespace
- Use `kubectl -f <file> --dry-run=client` to preview changes
- Save frequently used commands in shell aliases
- Monitor `kubectl top nodes` to prevent resource exhaustion
- Use resource quotas to prevent runaway workloads
- Keep backups of secrets outside the cluster
