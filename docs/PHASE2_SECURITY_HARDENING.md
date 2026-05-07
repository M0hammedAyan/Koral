# KORAL Phase 2: Security Hardening - Complete Guide

## Overview
Phase 2 implements comprehensive security infrastructure including secrets management, authentication hardening, TLS/mTLS, audit logging, and automated secret rotation.

## Phase 2 Deliverables

### ✅ Secrets Management (Sealed Secrets)
**File**: `infra/manifests/security/sealed-secrets.yaml`

- **Sealed Secrets Controller** deployment with:
  - RBAC roles and bindings
  - Encrypted secret storage
  - Automatic secret decryption in pods
  - Metrics exposure for Prometheus

- **Features**:
  - At-rest encryption for Kubernetes Secrets
  - Git-friendly sealed secrets
  - Per-namespace encryption keys
  - Audit trail for all secret operations

### ✅ Pod Security Standards
**File**: `infra/manifests/security/pod-security-standards.yaml`

- **Restricted PSS** enforcement for all workloads
- **Security Context Templates** in ConfigMap for reference
- **Validation Webhook** to reject non-compliant pods at admission time
- **RBAC** for pod security policy enforcement

- **Enforced Restrictions**:
  - No privileged containers
  - Read-only root filesystem
  - Non-root users (uid 1000)
  - No capability escalation
  - No host network access
  - Restricted volume types

### ✅ Audit Logging
**File**: `infra/manifests/security/audit-logging.yaml`

- **Comprehensive audit policy** covering:
  - Pod exec/attach commands
  - Secret access and modifications
  - RBAC policy changes
  - Network policy changes
  - Authentication attempts
  - Namespace deletions

- **Fluent Bit aggregator** for log collection
- **Structured logging** with timestamps and metadata
- **Retention policy** for audit logs (90 days minimum)

### ✅ Enhanced Authentication
**Files**: 
- `backend/auth_enhanced.py` - Improved authentication middleware
- `backend/rate_limit.py` - Rate limiting middleware

**Features**:
- Account lockout (5 failed attempts → 5 min lockout)
- API key validation with constant-time comparison
- JWT token validation with expiration
- Rate limiting (token bucket + sliding window)
- Suspicious activity detection
- Client identification by IP or user ID
- Failed attempt tracking

### ✅ TLS/mTLS Configuration
**File**: `infra/manifests/security/tls-mtls.yaml`

- **Certificate Issuer** for internal CA
- **Service Certificates** for all microservices
- **Client Certificate** for service-to-service communication
- **Istio Integration** ready:
  - PeerAuthentication for strict mTLS
  - Gateway for TLS termination
  - VirtualService for routing
  - DestinationRule for mTLS traffic policy

### ✅ Secret Rotation Automation
**File**: `infra/manifests/security/secret-rotation.yaml`

- **CronJob: JWT Secret Rotation** (weekly)
  - Generates new JWT secret
  - Backs up old secret
  - Updates Kubernetes Secret
  - Cleans up old backups

- **CronJob: API Key Rotation** (weekly)
  - Generates new API key
  - Backs up old key
  - Updates secret
  - Triggers pod restart

- **CronJob: Database Password Rotation** (monthly)
  - Framework for DB credential rotation
  - Integration with external secret managers

- **Configuration Management**:
  - Rotation intervals per secret type
  - Grace periods for gradual rollout
  - Retention policies for backups
  - Event notifications

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│           External Traffic (HTTPS/TLS)              │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Ingress Controller    │ (cert-manager + Let's Encrypt)
        │  Security Headers      │ (HSTS, CSP, X-Frame-Options)
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Rate Limiting         │ (Token Bucket + Sliding Window)
        │  API Key Validation    │ (Constant-time comparison)
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────────┐
        │  Pod-to-Pod (mTLS)         │ (Istio/Linkerd)
        │  Sealed Secrets Decryption │
        │  Pod Security Standards    │
        └────────┬───────────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Application Pods      │
        │  (Non-root, Read-only) │
        └────────────────────────┘

┌──────────────────────────────────────────────────────┐
│             Security Monitoring                      │
├──────────────────────────────────────────────────────┤
│ • Audit Logging (Kubernetes API events)             │
│ • Secret Rotation Tracking (CronJob status)         │
│ • Failed Authentication Attempts (rate-limit logs)  │
│ • TLS Certificate Expiration (cert-manager metrics) │
└──────────────────────────────────────────────────────┘
```

## Implementation Workflow

### 1. Deploy Sealed Secrets
```bash
# Deploy Sealed Secrets controller
kubectl apply -f infra/manifests/security/sealed-secrets.yaml

# Wait for controller to start
kubectl -n sealed-secrets wait --for=condition=available --timeout=300s deployment/sealed-secrets-controller

# Backup encryption key (CRITICAL!)
kubectl get secret -n sealed-secrets sealing-key-* -o yaml > sealing-key-backup.yaml
```

### 2. Create Sealed Secrets
```bash
# Install kubeseal CLI
curl -L https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz | tar xz

# Create secret and seal it
echo -n 'my-secret-password' | ./kubeseal -n koral-system --format yaml > koral-secrets.sealed.yaml

# Apply sealed secret
kubectl apply -f koral-secrets.sealed.yaml
```

### 3. Enable Pod Security Standards
```bash
# Label namespace with PSS enforcement
kubectl label namespace koral-system \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

# Deploy PSS manifests
kubectl apply -f infra/manifests/security/pod-security-standards.yaml
```

### 4. Configure Audit Logging
```bash
# Apply audit logging configuration
kubectl apply -f infra/manifests/security/audit-logging.yaml

# Enable audit logging on API server (cluster-dependent)
# Update kube-apiserver with --audit-policy-file and --audit-log-path
```

### 5. Deploy TLS/mTLS
```bash
# Deploy cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Apply TLS/mTLS manifests
kubectl apply -f infra/manifests/security/tls-mtls.yaml

# Verify certificates are issued
kubectl -n koral-system get certificates
```

### 6. Configure Secret Rotation
```bash
# Deploy secret rotation CronJobs
kubectl apply -f infra/manifests/security/secret-rotation.yaml

# Verify CronJobs are created
kubectl -n koral-system get cronjobs
```

### 7. Update Backend with Enhanced Authentication
```bash
# Copy rate_limit.py and auth_enhanced.py to backend
cp backend/rate_limit.py backend/
cp backend/auth_enhanced.py backend/

# Update backend/main.py to use new middleware
# See integration section below
```

## Integration with Backend

### Update `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.rate_limit import RateLimitMiddleware, RateLimitConfig
from backend.auth_enhanced import EnhancedAuthenticator

# Initialize app
app = FastAPI(title="KORAL Backend", version="1.0.0")

# Add rate limiting middleware
rate_limit_config = RateLimitConfig(
    requests_per_minute=60,
    requests_per_hour=3600,
    burst_size=10,
)
app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

# Add CORS middleware (from env)
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use enhanced authenticator as dependency
from backend.auth_enhanced import get_authenticated_user

@app.get("/api/incidents")
async def get_incidents(user_id: str = Depends(get_authenticated_user)):
    # user_id automatically validated and rate-limited
    return {"incidents": []}
```

## Security Features Summary

### Authentication & Authorization
| Feature | Status | Implementation |
|---------|--------|-----------------|
| API Key validation | ✅ | Constant-time comparison |
| JWT token validation | ✅ | HS256 algorithm, 24h expiration |
| Account lockout | ✅ | 5 failed attempts → 5 min lockout |
| Rate limiting | ✅ | Token bucket + sliding window |
| Role-based access | ✅ | RBAC ClusterRole/Role |

### Secrets Management
| Feature | Status | Implementation |
|---------|--------|-----------------|
| At-rest encryption | ✅ | Sealed Secrets |
| Secret rotation | ✅ | Automated CronJobs |
| Backup policy | ✅ | Keep last 3 versions |
| Audit trail | ✅ | Kubernetes audit logs |

### Network Security
| Feature | Status | Implementation |
|---------|--------|-----------------|
| mTLS | ✅ | Istio/Linkerd ready |
| Ingress TLS | ✅ | cert-manager + Let's Encrypt |
| Network policies | ✅ | Deny-all default + allow rules |
| Pod security | ✅ | Restricted PSS + admission validation |

### Compliance & Auditing
| Feature | Status | Implementation |
|---------|--------|-----------------|
| Audit logging | ✅ | Kubernetes API audit |
| Event tracking | ✅ | Secret/RBAC changes |
| Log retention | ✅ | 90 days |
| Alert integration | ✅ | Slack/PagerDuty ready |

## Operational Procedures

### Rotating Secrets Manually
```bash
# Rotate JWT secret immediately
kubectl patch secret koral-secrets -n koral-system \
  -p '{"data":{"jwt-secret":"'$(echo -n 'new-secret' | base64)'}}'

# Verify rotation
kubectl get secret koral-secrets -n koral-system -o jsonpath='{.data}' | base64 -d
```

### Viewing Audit Logs
```bash
# Stream audit logs
kubectl -n koral-system logs -f deployment/audit-logger --tail=100

# Export audit logs
kubectl -n koral-system logs deployment/audit-logger > audit-logs-backup.json
```

### Checking Certificate Status
```bash
# View certificate details
kubectl -n koral-system describe certificate koral-backend-tls

# Renew certificate immediately
kubectl delete secret koral-backend-tls -n koral-system
kubectl apply -f infra/manifests/security/tls-mtls.yaml
```

### Investigating Failed Attempts
```bash
# Check rate limit status
kubectl logs -n koral-system deployment/koral-backend | grep "Rate limit"

# Check failed authentications
kubectl logs -n koral-system deployment/koral-backend | grep "Invalid"

# View lockouts
kubectl logs -n koral-system deployment/koral-backend | grep "lockout"
```

## Monitoring & Alerting

### Prometheus Metrics
```yaml
# Rate limiting metrics
rate_limit_requests_total
rate_limit_requests_rejected_total
rate_limit_lockouts_active

# Authentication metrics
auth_attempts_total
auth_failures_total
auth_lockouts_triggered_total

# Certificate metrics
cert_manager_certificate_expiration_timestamp_seconds
cert_manager_certificate_renewal_failures_total

# Secret rotation metrics
secret_rotation_duration_seconds
secret_rotation_success_total
secret_rotation_failures_total
```

### Alert Rules
```yaml
- alert: HighAuthenticationFailureRate
  expr: rate(auth_failures_total[5m]) > 0.5
  for: 5m
  annotations:
    summary: "High authentication failure rate"

- alert: AccountLockoutActive
  expr: auth_lockouts_active > 0
  for: 1m
  annotations:
    summary: "Active account lockouts detected"

- alert: CertificateExpiringSoon
  expr: (cert_manager_certificate_expiration_timestamp_seconds - time()) < 604800
  for: 1h
  annotations:
    summary: "Certificate expiring in less than 7 days"

- alert: SecretRotationFailed
  expr: increase(secret_rotation_failures_total[1h]) > 0
  for: 30m
  annotations:
    summary: "Secret rotation job failed"
```

## Production Checklist

### Pre-Deployment
- [ ] Review security policies and adjust for organization
- [ ] Generate and backup encryption keys
- [ ] Configure Slack/PagerDuty for notifications
- [ ] Plan certificate renewal process
- [ ] Communicate rotation schedule to team
- [ ] Set up audit log retention

### Deployment
- [ ] Deploy Sealed Secrets controller
- [ ] Seal production secrets
- [ ] Apply Pod Security Standards
- [ ] Configure audit logging on API server
- [ ] Deploy TLS/mTLS manifests
- [ ] Deploy secret rotation CronJobs
- [ ] Update backend with authentication middleware
- [ ] Enable rate limiting

### Post-Deployment
- [ ] Verify pods are starting without security errors
- [ ] Test rate limiting (should receive 429 on overload)
- [ ] Test authentication failure handling
- [ ] Verify audit logs are being collected
- [ ] Confirm certificates are issued
- [ ] Test secret rotation manually
- [ ] Monitor pod startup logs for PSS violations

## Next Steps: Phase 3 (Database Backup Automation)

Phase 3 will implement:
- Automated PostgreSQL backups (pgBackRest)
- WAL archiving to S3
- Point-in-time recovery (PITR)
- Backup verification
- Disaster recovery procedures
- RTO/RPO definitions

## References

- [Sealed Secrets Documentation](https://github.com/bitnami-labs/sealed-secrets)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes Audit Logging](https://kubernetes.io/docs/tasks/debug-application-cluster/audit/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Istio Security](https://istio.io/latest/docs/concepts/security/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
