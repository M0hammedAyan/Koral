# KORAL Production Deployment Guide

This guide covers all 6 production-readiness fixes that have been implemented.

## 1. ✅ Fixed CORS (Wildcard Origins → Restricted)

**Before:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dangerous!
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**After:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),  # From auth.py, env-controlled
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    allow_credentials=True,
)
```

**How to set allowed origins in production:**
```bash
export ALLOWED_ORIGINS="https://your-frontend.com,https://app.example.com"
```

---

## 2. ✅ Implemented API Key & JWT Authentication

**New file: `backend/auth.py`**
- `validate_api_key()` - Validates X-API-Key header
- `validate_jwt()` - Validates Bearer token
- `create_jwt()` - Issues new JWT tokens
- `get_allowed_origins()` - Returns CORS allowed origins

**Usage:**
All protected endpoints should use:
```python
@router.post("/incidents")
async def create_incident(data: dict, api_key: str = Depends(validate_api_key)):
    # Protected endpoint
    return process_incident(data)
```

**Configuration (via Kubernetes Secrets):**
```yaml
stringData:
  API_KEY: "your-secure-api-key-here"
  JWT_SECRET: "your-jwt-secret-here"
```

**How to call the API in production:**
```bash
# Using API Key
curl -X POST http://backend:8000/anomalies \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"pod": "..."}'

# Using JWT
curl -X POST http://backend:8000/anomalies \
  -H "Authorization: Bearer your.jwt.token" \
  -H "Content-Type: application/json" \
  -d '{"pod": "..."}'
```

---

## 3. ✅ Switched from SQLite to PostgreSQL

**New file: `backend/database.py`**
- Abstracts database operations
- Supports both SQLite (dev) and PostgreSQL (prod)
- Uses `DB_TYPE` env var to switch

**How to use PostgreSQL:**
```bash
export DB_TYPE=postgres
export DB_HOST=postgres.default.svc.cluster.local
export DB_PORT=5432
export DB_NAME=koral
export DB_USER=koral
export DB_PASS=your-secure-password
```

**SQLite (development only):**
```bash
export DB_TYPE=sqlite
export DB_PATH=/data/koral.db
```

**Benefits of PostgreSQL:**
- ✅ Supports concurrent connections
- ✅ Safe for pod restarts (no data loss)
- ✅ Replication & backup support
- ✅ Better performance at scale
- ✅ ACID transactions

---

## 4. ✅ Implemented Kubernetes Secrets

**New file: `k8s/koral-secrets.yaml`**

Create secrets:
```bash
kubectl apply -f k8s/koral-secrets.yaml
```

Edit secrets:
```bash
kubectl edit secret koral-secrets -n koral-system
```

Reference in deployments:
```yaml
env:
  - name: API_KEY
    valueFrom:
      secretKeyRef:
        name: koral-secrets
        key: API_KEY
```

**All sensitive data is now stored in:**
- ✅ OpenAI/Anthropic API keys
- ✅ SMTP credentials for alerts
- ✅ Database passwords
- ✅ JWT secret
- ✅ API keys

**NO MORE** plain environment variables for secrets!

---

## 5. ✅ Deployed AI Engine to Kubernetes

**New in `k8s/koral-deployment.yaml`:**
```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-engine
  namespace: koral-system
spec:
  replicas: 2  # High availability
  # Uses secrets for OPENAI_API_KEY, ANTHROPIC_API_KEY
  # Uses secrets for authentication
```

**Deploy with:**
```bash
kubectl apply -f k8s/koral-secrets.yaml
kubectl apply -f k8s/koral-deployment.yaml
```

**Verify AI Engine is running:**
```bash
kubectl get pods -n koral-system | grep ai-engine
kubectl logs -f deployment/ai-engine -n koral-system
```

**Now incidents WILL get AI explanations** because the AI Engine is deployed and reachable.

---

## 6. ✅ Deployed Prometheus to Kubernetes

**New file: `k8s/prometheus-deployment.yaml`**

Prometheus is now running in the cluster with:
- ✅ Pod metrics (cAdvisor)
- ✅ Node metrics
- ✅ Kubelet metrics
- ✅ Container metrics

**Deploy Prometheus:**
```bash
kubectl apply -f k8s/prometheus-deployment.yaml
```

**Access Prometheus:**
```bash
kubectl port-forward -n koral-system svc/prometheus 9090:9090
# Open http://localhost:9090
```

**Verify data is flowing:**
```bash
curl http://prometheus:9090/api/v1/query?query=container_cpu_usage_seconds_total
```

**Now agents get real metrics** instead of all zeros!

---

## Production Database Setup

**New file: `k8s/postgres-deployment.yaml`**

Deploys PostgreSQL with:
- ✅ StatefulSet (consistent naming)
- ✅ PersistentVolume (data survives pod restarts)
- ✅ Proper health checks
- ✅ Resource limits

**Deploy PostgreSQL:**
```bash
kubectl apply -f k8s/postgres-deployment.yaml
```

**Backup the database:**
```bash
kubectl exec -n koral-system postgres-0 -- \
  pg_dump -U koral koral > backup.sql
```

---

## Docker Compose (Local Production Testing)

**New file: `docker-compose-prod.yml`**

This includes everything needed to test production setup locally:
```bash
# Start all services with PostgreSQL & Prometheus
docker compose -f docker-compose-prod.yml up -d

# Verify all services are healthy
docker compose -f docker-compose-prod.yml ps

# Check logs
docker compose -f docker-compose-prod.yml logs -f backend

# Tear down
docker compose -f docker-compose-prod.yml down -v
```

---

## Kubernetes Full Deployment (Production)

**Step 1: Create secrets**
```bash
# Edit k8s/koral-secrets.yaml with your actual values
kubectl apply -f k8s/koral-secrets.yaml
```

**Step 2: Deploy database & monitoring**
```bash
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
```

**Step 3: Deploy KORAL services**
```bash
kubectl apply -f k8s/koral-deployment.yaml
```

**Step 4: Verify everything is running**
```bash
# Check all pods are running
kubectl get pods -n koral-system

# Check services are accessible
kubectl get svc -n koral-system

# View logs
kubectl logs -f deployment/backend -n koral-system
kubectl logs -f deployment/ai-engine -n koral-system
```

**Step 5: Test the API**
```bash
# Get a pod IP or use the service
curl -H "X-API-Key: your-api-key" \
  http://backend:8000/health
```

---

## Environment Variables Checklist

**Required secrets (in `koral-secrets.yaml`):**
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude (optional fallback)
- `API_KEY` - Your KORAL API key (set this to something secure)
- `JWT_SECRET` - Secret key for JWT signing
- `DB_USER` - PostgreSQL username
- `DB_PASS` - PostgreSQL password
- `SMTP_USER` - Gmail or SMTP username for alerts
- `SMTP_PASS` - Gmail app-specific password or SMTP password

**Service configuration (in deployment env):**
- `DB_TYPE=postgres` - Use PostgreSQL (not SQLite)
- `DB_HOST=postgres` - PostgreSQL service hostname
- `ALLOWED_ORIGINS=https://your-frontend.com` - Restrict CORS
- `DISABLE_AUTH=false` - Enforce authentication (default)

---

## Migration from Development to Production

**1. Export your development database:**
```bash
# If using SQLite
sqlite3 data/koral.db ".dump" > dump.sql
```

**2. Create PostgreSQL and load data:**
```bash
kubectl exec -n koral-system postgres-0 -- \
  psql -U koral -d koral < dump.sql
```

**3. Update environment variables:**
- Change `DB_TYPE` from `sqlite` to `postgres`
- Set `ALLOWED_ORIGINS` to your domain
- Set real API keys in secrets
- Set `DISABLE_AUTH=false`

**4. Restart services:**
```bash
kubectl rollout restart deployment/backend -n koral-system
kubectl rollout restart deployment/ai-engine -n koral-system
```

---

## Security Checklist

- ✅ CORS is restricted to allowed domains only
- ✅ All API calls require X-API-Key or Bearer JWT token
- ✅ All secrets stored in Kubernetes Secrets (not env vars)
- ✅ Database passwords are encrypted at rest (use Sealed Secrets in production)
- ✅ API endpoints use HTTPS in production (configure with Ingress)
- ✅ SQLite replaced with PostgreSQL for data safety
- ✅ AI Engine deployed for incident explanations
- ✅ Prometheus collecting real metrics from pods

---

## Troubleshooting

**Q: Backend can't connect to PostgreSQL**
```bash
# Check if postgres pod is running
kubectl get pods -n koral-system | grep postgres

# Check connection from backend pod
kubectl exec -n koral-system deployment/backend -- \
  python -c "import psycopg2; print(psycopg2.connect('host=postgres user=koral'))"
```

**Q: AI Engine not analyzing incidents**
```bash
# Check AI Engine is running
kubectl logs -f deployment/ai-engine -n koral-system

# Verify it can reach backend
kubectl exec -n koral-system deployment/ai-engine -- \
  curl http://backend:8000/health
```

**Q: Prometheus has no data**
```bash
# Check Prometheus is scraping targets
kubectl port-forward -n koral-system svc/prometheus 9090:9090
# Visit http://localhost:9090/targets
```

**Q: Getting 401 Unauthorized**
```bash
# Check your API key header
curl -v -H "X-API-Key: your-actual-key" http://backend:8000/health

# Or check secret is set
kubectl get secret koral-secrets -n koral-system -o yaml | grep API_KEY
```

---

## Next Steps

1. **Helm Charts** - Convert deployments to Helm for easier management
2. **Ingress** - Set up ingress for external access with HTTPS
3. **Network Policies** - Restrict traffic between pods
4. **Pod Security Policies** - Enforce security standards
5. **Monitoring Dashboard** - Set up Grafana to visualize Prometheus metrics
6. **Backup Strategy** - Automated PostgreSQL backups to S3
7. **Disaster Recovery** - Multi-region deployment

---

## Support

For issues or questions about production deployment, refer to:
- Kubernetes docs: https://kubernetes.io/docs/
- PostgreSQL docs: https://www.postgresql.org/docs/
- Prometheus docs: https://prometheus.io/docs/
