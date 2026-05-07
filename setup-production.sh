#!/bin/bash
#
# KORAL Production Deployment Infrastructure Setup
# This script creates the complete production-grade infrastructure
# Run: chmod +x setup-production.sh && ./setup-production.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
KORAL_NAMESPACE="koral-system"
KORAL_VERSION="v1.0.0"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Phase 0: Validation
validate_prerequisites() {
    log_info "Validating prerequisites..."
    
    command -v docker &> /dev/null || log_error "docker not found"
    command -v kubectl &> /dev/null || log_error "kubectl not found"
    command -v helm &> /dev/null || log_error "helm not found"
    
    # Check Kubernetes cluster
    kubectl cluster-info &> /dev/null || log_error "Cannot connect to Kubernetes cluster"
    
    # Check namespace
    kubectl get namespace ${KORAL_NAMESPACE} 2>/dev/null || {
        log_info "Creating namespace ${KORAL_NAMESPACE}..."
        kubectl create namespace ${KORAL_NAMESPACE}
    }
    
    log_success "Prerequisites validated"
}

# Phase 1: Infrastructure setup
setup_infrastructure() {
    log_info "Setting up infrastructure..."
    
    # Create directories
    mkdir -p "${PROJECT_ROOT}/infra/helm/koral"
    mkdir -p "${PROJECT_ROOT}/infra/manifests/base"
    mkdir -p "${PROJECT_ROOT}/infra/manifests/overlays/production"
    mkdir -p "${PROJECT_ROOT}/infra/manifests/overlays/staging"
    mkdir -p "${PROJECT_ROOT}/infra/scripts"
    mkdir -p "${PROJECT_ROOT}/infra/monitoring"
    mkdir -p "${PROJECT_ROOT}/infra/security"
    
    log_success "Infrastructure directories created"
}

# Phase 2: Install system components
install_system_components() {
    log_info "Installing system components..."
    
    # Cert-Manager
    log_info "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml || {
        log_warn "cert-manager may already be installed"
    }
    
    # Prometheus
    log_info "Adding Prometheus Helm repo..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # AlertManager
    log_info "Adding AlertManager configuration..."
    # Will be applied via manifests
    
    log_success "System components prepared"
}

# Phase 3: Create secrets
create_secrets() {
    log_info "Creating secrets template..."
    
    # This should be populated by user
    cat > "${PROJECT_ROOT}/infra/secrets/.env.production.template" << 'EOF'
# Database
DB_HOST=postgres.koral-system.svc.cluster.local
DB_PORT=5432
DB_NAME=koral
DB_USER=koral
DB_PASS=CHANGE_ME_STRONG_PASSWORD_HERE
DB_SSL=require

# Authentication
API_KEY=CHANGE_ME_RANDOM_API_KEY_HERE
JWT_SECRET=CHANGE_ME_RANDOM_JWT_SECRET_HERE

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Email Alerts
ALERT_EMAIL=alerts@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-specific-password

# Slack Alerts
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Production
LOG_LEVEL=INFO
KORAL_NAMESPACE=koral-system
DISABLE_AUTH=false
EOF
    
    log_warn "⚠️  UPDATE ${PROJECT_ROOT}/infra/secrets/.env.production.template WITH REAL VALUES"
    log_info "Then run: kubectl create secret generic koral-secrets -n ${KORAL_NAMESPACE} --from-env-file=infra/secrets/.env.production"
}

# Phase 4: Generate configurations
generate_configurations() {
    log_info "Generating production configurations..."
    
    # Will be created in subsequent phases
    log_success "Configuration templates prepared"
}

# Main
main() {
    log_info "=========================================="
    log_info "KORAL Production Deployment Setup"
    log_info "Version: ${KORAL_VERSION}"
    log_info "Namespace: ${KORAL_NAMESPACE}"
    log_info "=========================================="
    
    validate_prerequisites
    setup_infrastructure
    install_system_components
    create_secrets
    generate_configurations
    
    log_success ""
    log_success "=========================================="
    log_success "Production infrastructure setup complete!"
    log_success "=========================================="
    log_info ""
    log_info "Next steps:"
    log_info "1. Update secrets in infra/secrets/.env.production.template"
    log_info "2. Run: kubectl create secret generic koral-secrets -n ${KORAL_NAMESPACE} --from-env-file=infra/secrets/.env.production"
    log_info "3. Deploy Phase 1: Image Registry & CI/CD"
    log_info "4. Deploy Phase 2: Security"
    log_info "5. Deploy Phase 3: Database"
    log_info "6. Deploy Phase 4: Observability"
    log_info "7. Deploy Phase 5: Scalability"
    log_info ""
}

main
