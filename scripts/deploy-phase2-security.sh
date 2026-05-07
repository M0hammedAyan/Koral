#!/bin/bash
# KORAL Phase 2 Deployment Script
# Security Hardening Installation and Verification

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="koral-system"
SEALED_SECRETS_NAMESPACE="sealed-secrets"

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC}  $*"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $*"
}

log_error() {
    echo -e "${RED}✗${NC}  $*"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    log_success "kubectl found"
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    log_success "Connected to Kubernetes cluster"
    
    # Check helm (optional)
    if command -v helm &> /dev/null; then
        log_success "helm found (optional)"
    else
        log_warning "helm not found (optional)"
    fi
}

install_sealed_secrets() {
    log_info "Installing Sealed Secrets..."
    
    # Create namespace
    kubectl create namespace $SEALED_SECRETS_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    log_success "Created sealed-secrets namespace"
    
    # Apply Sealed Secrets manifests
    kubectl apply -f infra/manifests/security/sealed-secrets.yaml
    log_success "Applied Sealed Secrets manifests"
    
    # Wait for deployment
    kubectl -n $SEALED_SECRETS_NAMESPACE wait --for=condition=available --timeout=300s \
        deployment/sealed-secrets-controller
    log_success "Sealed Secrets controller ready"
    
    # Verify controller
    if kubectl -n $SEALED_SECRETS_NAMESPACE get deployment sealed-secrets-controller &> /dev/null; then
        log_success "Sealed Secrets controller verified"
    else
        log_error "Sealed Secrets controller verification failed"
        return 1
    fi
}

install_pod_security_standards() {
    log_info "Installing Pod Security Standards..."
    
    # Apply PSS manifests
    kubectl apply -f infra/manifests/security/pod-security-standards.yaml
    log_success "Applied Pod Security Standards manifests"
    
    # Label namespace
    kubectl label namespace $NAMESPACE \
        pod-security.kubernetes.io/enforce=restricted \
        pod-security.kubernetes.io/audit=restricted \
        pod-security.kubernetes.io/warn=restricted \
        --overwrite || true
    log_success "Labeled namespace with PSS enforcement"
}

install_audit_logging() {
    log_info "Installing Audit Logging..."
    
    # Apply audit logging manifests
    kubectl apply -f infra/manifests/security/audit-logging.yaml
    log_success "Applied audit logging manifests"
    
    # Wait for deployment
    kubectl -n $NAMESPACE wait --for=condition=available --timeout=300s \
        deployment/audit-logger || log_warning "Audit logger not ready (this is optional)"
    
    log_success "Audit logging configured"
}

install_tls_mtls() {
    log_info "Installing TLS/mTLS..."
    
    # Check if cert-manager is installed
    if ! kubectl get crd certificates.cert-manager.io &> /dev/null; then
        log_warning "cert-manager not found, installing..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
        
        # Wait for cert-manager
        kubectl -n cert-manager wait --for=condition=available --timeout=300s \
            deployment/cert-manager deployment/cert-manager-webhook deployment/cert-manager-cainjector
        log_success "cert-manager installed and ready"
    else
        log_success "cert-manager already installed"
    fi
    
    # Apply TLS/mTLS manifests
    kubectl apply -f infra/manifests/security/tls-mtls.yaml
    log_success "Applied TLS/mTLS manifests"
    
    # Wait for certificates to be issued
    log_info "Waiting for certificates to be issued..."
    sleep 5
    kubectl -n $NAMESPACE wait --for=condition=Ready=true \
        certificate/koral-backend-tls \
        certificate/koral-ai-engine-tls \
        certificate/koral-correlation-engine-tls \
        --timeout=300s || log_warning "Certificates may still be issuing"
    
    log_success "TLS/mTLS configured"
}

install_secret_rotation() {
    log_info "Installing Secret Rotation Automation..."
    
    # Apply secret rotation manifests
    kubectl apply -f infra/manifests/security/secret-rotation.yaml
    log_success "Applied secret rotation manifests"
    
    # Verify CronJobs
    sleep 2
    CRONJOBS=$(kubectl -n $NAMESPACE get cronjobs -o jsonpath='{.items[*].metadata.name}')
    log_success "Created CronJobs: $CRONJOBS"
}

verify_security_deployment() {
    log_info "Verifying security deployment..."
    
    # Check Sealed Secrets
    log_info "Checking Sealed Secrets..."
    if kubectl -n $SEALED_SECRETS_NAMESPACE get deployment sealed-secrets-controller &> /dev/null; then
        REPLICAS=$(kubectl -n $SEALED_SECRETS_NAMESPACE get deployment sealed-secrets-controller \
            -o jsonpath='{.status.readyReplicas}')
        if [[ $REPLICAS -ge 1 ]]; then
            log_success "Sealed Secrets: operational ($REPLICAS replicas)"
        else
            log_warning "Sealed Secrets: not ready"
        fi
    fi
    
    # Check PSS labels
    log_info "Checking Pod Security Standards..."
    PSS_LABELS=$(kubectl get namespace $NAMESPACE \
        -o jsonpath='{.metadata.labels.pod-security\.kubernetes\.io/enforce}')
    if [[ "$PSS_LABELS" == "restricted" ]]; then
        log_success "Pod Security Standards: enforced (restricted)"
    else
        log_warning "Pod Security Standards: not properly labeled"
    fi
    
    # Check audit logger
    log_info "Checking Audit Logging..."
    if kubectl -n $NAMESPACE get deployment audit-logger &> /dev/null; then
        log_success "Audit Logging: deployed"
    else
        log_warning "Audit Logging: not deployed"
    fi
    
    # Check certificates
    log_info "Checking TLS Certificates..."
    CERTS=$(kubectl -n $NAMESPACE get certificates -o jsonpath='{.items[*].metadata.name}')
    if [[ -n "$CERTS" ]]; then
        log_success "Certificates found: $CERTS"
        
        # Check certificate status
        READY=$(kubectl -n $NAMESPACE get certificates \
            -o jsonpath='{.items[?(@.status.conditions[0].type=="Ready")].status.conditions[0].status}' 2>/dev/null || echo "Unknown")
        if [[ "$READY" == "True" ]]; then
            log_success "Certificates: ready"
        else
            log_warning "Certificates: still issuing"
        fi
    else
        log_warning "No certificates found"
    fi
    
    # Check CronJobs
    log_info "Checking Secret Rotation..."
    CRONJOB_COUNT=$(kubectl -n $NAMESPACE get cronjobs --no-headers 2>/dev/null | wc -l)
    if [[ $CRONJOB_COUNT -ge 2 ]]; then
        log_success "Secret Rotation: $CRONJOB_COUNT CronJobs configured"
    else
        log_warning "Secret Rotation: fewer than 2 CronJobs found"
    fi
}

test_rate_limiting() {
    log_info "Testing rate limiting (if backend running)..."
    
    # Check if backend is accessible
    if kubectl -n $NAMESPACE port-forward svc/koral-backend 8000:8000 &> /dev/null &
    then
        FORWARD_PID=$!
        sleep 2
        
        # Test rate limiting
        RATE_LIMIT_COUNT=0
        for i in {1..150}; do
            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
            if [[ "$RESPONSE" == "429" ]]; then
                RATE_LIMIT_COUNT=$((RATE_LIMIT_COUNT + 1))
            fi
        done
        
        kill $FORWARD_PID 2>/dev/null || true
        
        if [[ $RATE_LIMIT_COUNT -gt 0 ]]; then
            log_success "Rate limiting: working ($RATE_LIMIT_COUNT requests limited)"
        else
            log_warning "Rate limiting: not triggered (backend may need update)"
        fi
    else
        log_warning "Rate limiting: cannot test (backend service not accessible)"
    fi
}

show_next_steps() {
    log_info "Phase 2 Deployment Complete!"
    
    cat << EOF

${GREEN}Security Features Deployed:${NC}
  ✓ Sealed Secrets (secrets encryption at rest)
  ✓ Pod Security Standards (restricted profile)
  ✓ Audit Logging (API event tracking)
  ✓ TLS/mTLS (certificate management)
  ✓ Secret Rotation (automated CronJobs)

${YELLOW}Next Steps:${NC}

1. Create Sealed Secrets with your credentials:
   kubeseal -n $NAMESPACE --format yaml < secrets.yaml > secrets-sealed.yaml
   kubectl apply -f secrets-sealed.yaml

2. Update backend deployment with new authentication middleware:
   - Copy backend/rate_limit.py and backend/auth_enhanced.py
   - Update backend/main.py to include new middleware
   - Rebuild Docker image and redeploy

3. Monitor security:
   kubectl -n $NAMESPACE logs -f deployment/audit-logger
   kubectl -n $NAMESPACE get cronjobs

4. Test authentication:
   curl -H "X-API-Key: <key>" http://api.koral.ai/health

${BLUE}Documentation:${NC}
  See docs/PHASE2_SECURITY_HARDENING.md for complete guide

${YELLOW}Important:${NC}
  - Backup Sealed Secrets encryption key (sealing-key-*)
  - Configure Slack/PagerDuty for alerts
  - Review and adjust RBAC policies
  - Test certificate renewal before expiration

EOF
}

# Main execution
main() {
    log_info "KORAL Phase 2: Security Hardening Deployment"
    echo ""
    
    check_prerequisites
    echo ""
    
    install_sealed_secrets
    echo ""
    
    install_pod_security_standards
    echo ""
    
    install_audit_logging
    echo ""
    
    install_tls_mtls
    echo ""
    
    install_secret_rotation
    echo ""
    
    verify_security_deployment
    echo ""
    
    test_rate_limiting
    echo ""
    
    show_next_steps
}

# Run main
main "$@"
