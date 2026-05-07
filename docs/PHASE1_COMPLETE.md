# KORAL Production Deployment Guide - Phase 1 Complete

## Overview
Phase 1 of the enterprise production transformation establishes image registry, versioning, and CI/CD infrastructure. This guide documents the complete Phase 1 implementation.

## Phase 1: Image Registry & Versioning - Complete Artifacts

### ✅ Artifacts Generated

#### 1. GitHub Actions Workflows
- **`.github/workflows/release-images.yml`**: Production image build, scan, sign, push pipeline
- **`.github/workflows/semantic-versioning.yml`**: Semantic version management with conventional commits

#### 2. Helm Charts
- **`infra/helm/koral/Chart.yaml`**: Helm chart metadata and dependencies
- **`infra/helm/koral/values.yaml`**: Production-grade Helm values with HPA, PDB, resource limits

#### 3. Kubernetes Manifests (Base)
- **`infra/manifests/base/rbac.yaml`**: ServiceAccounts, Roles, RoleBindings
- **`infra/manifests/base/network-policies.yaml`**: Strict ingress/egress NetworkPolicies
- **`infra/manifests/base/ingress.yaml`**: Ingress with TLS, cert-manager, security headers
- **`infra/manifests/base/backend-deployment.yaml`**: Production backend deployment with HPA, PDB, probes
- **`infra/manifests/base/ai-engine-deployment.yaml`**: Production AI engine deployment
- **`infra/manifests/base/correlation-engine-deployment.yaml`**: Production correlation engine deployment
- **`infra/manifests/base/frontend-deployment.yaml`**: Production frontend deployment with Nginx
- **`infra/manifests/base/kustomization.yaml`**: Kustomization base configuration

#### 4. Kubernetes Overlays (Production)
- **`infra/manifests/overlays/production/kustomization.yaml`**: Production overlay with image versioning
- **`infra/manifests/overlays/production/namespace-config.yaml`**: Production namespace, quotas, PSP, ServiceMonitor

#### 5. Dockerfiles (Hardened)
- **`backend/Dockerfile`**: Multi-stage, non-root user, read-only filesystem
- **`ai_engine/Dockerfile`**: Multi-stage, security hardening
- **`correlation-engine/Dockerfile`**: Multi-stage, security hardening
- **`frontend/Dockerfile`**: Multi-stage Node→Nginx, security hardening

#### 6. Versioning & Scripts
- **`docs/VERSIONING_STRATEGY.md`**: Comprehensive semantic versioning documentation
- **`scripts/version-bump.sh`**: Bash script for local version management
- **`VERSION`**: Version file (current: 1.0.0)

#### 7. Secrets Management
- **`.env.production.template`**: Production secrets template with comprehensive variable documentation

### ✅ Key Features Implemented

#### Semantic Versioning
- ✓ Conventional commits integration
- ✓ Automated version bumping (major/minor/patch)
- ✓ Pre-release versions (rc, beta, alpha)
- ✓ Git tag creation and release notes
- ✓ Docker image tag strategy (semver, latest, sha)

#### Security Hardening
- ✓ Multi-stage Dockerfiles for smaller images
- ✓ Non-root user containers
- ✓ Read-only root filesystem preparation
- ✓ Capability dropping (CAP_DROP: ALL)
- ✓ Network policies: Deny by default, allow specific flows
- ✓ RBAC: Minimal permissions per service
- ✓ Ingress security headers (HSTS, CSP, X-Frame-Options)
- ✓ Pod security policies

#### High Availability
- ✓ Horizontal Pod Autoscaling (HPA) for all services
- ✓ Pod Disruption Budgets (PDB) ensuring minimum replicas
- ✓ Pod anti-affinity for node distribution
- ✓ Health probes: liveness, readiness, startup
- ✓ Rolling update strategy

#### Observability
- ✓ Prometheus service monitors
- ✓ Metrics endpoints on all services
- ✓ Structured logging
- ✓ Resource quotas per namespace
- ✓ Pod annotations for Prometheus scraping

#### Production Configuration
- ✓ Resource requests and limits
- ✓ Node selectors for workload distribution
- ✓ Init containers for dependency checks
- ✓ ConfigMaps for configuration
- ✓ Secrets for sensitive data
- ✓ EmptyDir volumes for temporary storage
- ✓ Volume mounts with proper permissions

### ✅ Image Registry Strategy

#### Container Registry
- **Primary**: GitHub Container Registry (ghcr.io)
- **Fallback**: Docker Hub (docker.io)
- **Feature**: Public image pulls with rate limiting awareness

#### Image Tagging Strategy
| Tag Type | Purpose | Example |
|----------|---------|---------|
| semver | Release version | `v1.0.0` |
| major.minor | Track latest patch | `v1.0` |
| sha | Build identifier | `abc123def...` |
| latest | Latest release | `latest` |
| prerelease | RC/Beta/Alpha | `v1.0.0-rc.1` |

#### Multi-Architecture Builds
- ✓ linux/amd64 (x86-64)
- ✓ linux/arm64 (ARM 64-bit for Apple Silicon, Graviton)
- ✓ BuildX cache optimization

#### Image Security
- ✓ Trivy vulnerability scanning
- ✓ SBOM generation (SPDX format)
- ✓ Image signing (Cosign ready)
- ✓ Fail on CRITICAL/HIGH vulnerabilities
- ✓ GitHub Security tab integration

### Deployment Workflow

#### GitHub Actions Triggers
1. **Release Workflow** (`release-images.yml`)
   - Triggered: Git tag `v*.*.*`
   - Actions: Validate version → Build multi-arch → Scan → Push → Create release

2. **Semantic Versioning** (`semantic-versioning.yml`)
   - Triggered: PR merge to main, workflow dispatch
   - Actions: Analyze commits → Validate conventional commits → Bump version → Create release

#### Version Lifecycle
```
Development Branch
       ↓
   Pull Request (conventional commits)
       ↓
   Merge to Main (triggers version bump)
       ↓
   Git Tag Creation (v1.0.0)
       ↓
   GitHub Actions: Build & Push
       ↓
   Multi-arch images pushed to ghcr.io
       ↓
   Security scanning results published
       ↓
   Release published on GitHub
```

### Kubernetes Deployment

#### Deployment with Kustomize
```bash
# Development
kubectl apply -k infra/manifests/overlays/development

# Staging
kubectl apply -k infra/manifests/overlays/staging

# Production
kubectl apply -k infra/manifests/overlays/production
```

#### Deployment with Helm
```bash
# Add Helm repo
helm repo add koral https://charts.koral.ai

# Install
helm install koral koral/koral -f values-production.yaml

# Upgrade
helm upgrade koral koral/koral -f values-production.yaml
```

### Production Checklist

#### Pre-Deployment
- [ ] GitHub Actions workflows tested and enabled
- [ ] VERSION file initialized
- [ ] Helm charts validated: `helm lint infra/helm/koral`
- [ ] Kubernetes manifests validated: `kubectl apply --dry-run=client -f infra/manifests/`
- [ ] Secrets configured in GitHub Actions or external secret manager
- [ ] Container registry credentials configured
- [ ] TLS certificates ready (Let's Encrypt via cert-manager)
- [ ] Database credentials generated and stored securely
- [ ] API keys and JWT secrets generated

#### Deployment
- [ ] Create namespace: `kubectl create namespace koral-system`
- [ ] Apply base manifests: `kubectl apply -k infra/manifests/base`
- [ ] Apply production overlay: `kubectl apply -k infra/manifests/overlays/production`
- [ ] Verify pod startup: `kubectl -n koral-system get pods`
- [ ] Check pod health: `kubectl -n koral-system get pods -w`
- [ ] Verify Ingress: `kubectl -n koral-system get ingress`
- [ ] Test TLS: `curl -I https://api.koral.ai`
- [ ] Verify metrics: `curl http://backend:8000/metrics`

#### Post-Deployment
- [ ] Health checks passing
- [ ] All pods running and ready
- [ ] Ingress routes working
- [ ] Metrics flowing to Prometheus
- [ ] Logs aggregating correctly
- [ ] Alerts configured and tested
- [ ] Backup jobs scheduled
- [ ] Disaster recovery tested

### Next Steps: Phase 2 (Security Hardening)

Phase 2 will implement:
- ✓ Secrets management (Vault/Sealed Secrets)
- ✓ Pod Security Standards enforcement
- ✓ API rate limiting and authentication
- ✓ TLS mutual authentication
- ✓ Audit logging
- ✓ RBAC policy refinement
- ✓ Network policy refinement
- ✓ Secret rotation automation

### Key Commands

#### Version Management
```bash
# Show current version
./scripts/version-bump.sh show

# Bump patch version (local)
./scripts/version-bump.sh patch --dry-run

# Bump minor version
./scripts/version-bump.sh minor

# Create pre-release
./scripts/version-bump.sh prerelease --prerelease-type beta
```

#### Docker Operations
```bash
# Build backend image
docker build -f backend/Dockerfile -t ghcr.io/m0hammedayan/koral/koral-backend:v1.0.0 .

# Scan image for vulnerabilities
trivy image ghcr.io/m0hammedayan/koral/koral-backend:v1.0.0

# Push to registry
docker push ghcr.io/m0hammedayan/koral/koral-backend:v1.0.0
```

#### Kubernetes Operations
```bash
# Deploy with Kustomize (production)
kubectl apply -k infra/manifests/overlays/production

# Watch pod startup
kubectl -n koral-system get pods -w

# View pod logs
kubectl -n koral-system logs -f deployment/koral-backend

# Port forward for debugging
kubectl -n koral-system port-forward svc/koral-backend 8000:8000

# Get events
kubectl -n koral-system get events --sort-by='.lastTimestamp'

# Scale replicas
kubectl -n koral-system scale deployment koral-backend --replicas=5
```

#### Monitoring
```bash
# View Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Query metrics
curl 'http://prometheus:9090/api/v1/query?query=koral_backend_requests_total'

# Port forward to Prometheus
kubectl -n koral-system port-forward svc/prometheus 9090:9090
```

### Troubleshooting

#### Pods not starting
```bash
# Check pod status
kubectl -n koral-system describe pod <pod-name>

# View pod logs
kubectl -n koral-system logs <pod-name>

# Check events
kubectl -n koral-system get events
```

#### Image pull failures
```bash
# Verify image exists
docker pull ghcr.io/m0hammedayan/koral/koral-backend:v1.0.0

# Check image pull secrets
kubectl -n koral-system get secret
kubectl -n koral-system get serviceaccount koral-backend -o yaml
```

#### Network connectivity
```bash
# Test connectivity between pods
kubectl -n koral-system exec <pod> -- curl http://backend:8000/health

# View network policies
kubectl -n koral-system get networkpolicies

# Check endpoints
kubectl -n koral-system get endpoints
```

### References

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/best-practices/)
- [OWASP Container Security](https://owasp.org/www-project-container-security/)
- [Helm Documentation](https://helm.sh/docs/)
- [Kustomize Documentation](https://kustomize.io/)
