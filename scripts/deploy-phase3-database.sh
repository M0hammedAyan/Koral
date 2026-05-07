#!/bin/bash
# KORAL Phase 3 Deployment Script
# Database backup automation, restore verification, and PgBouncer.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="koral-system"
IMAGE_TAG="v1.0.0"
BACKUP_IMAGE="ghcr.io/m0hammedayan/koral/koral-postgres-backup:${IMAGE_TAG}"

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_err() { echo -e "${RED}[ERR]${NC} $*"; }

check_prerequisites() {
  log_info "Checking prerequisites"

  command -v kubectl >/dev/null 2>&1 || { log_err "kubectl is required"; exit 1; }
  kubectl cluster-info >/dev/null 2>&1 || { log_err "Cannot reach Kubernetes cluster"; exit 1; }
  log_ok "kubectl and cluster connectivity verified"

  if ! command -v docker >/dev/null 2>&1; then
    log_warn "docker not found. You must provide backup image ${BACKUP_IMAGE} from CI/CD"
  else
    log_ok "docker found"
  fi
}

build_and_push_backup_image() {
  if ! command -v docker >/dev/null 2>&1; then
    return 0
  fi

  log_info "Building local backup image"
  docker build -t "${BACKUP_IMAGE}" -f infra/images/postgres-backup/Dockerfile .
  log_ok "Built ${BACKUP_IMAGE}"

  log_warn "Push skipped by default. Push manually if your cluster cannot pull local images:"
  echo "  docker push ${BACKUP_IMAGE}"
}

apply_phase3_manifests() {
  log_info "Applying Phase 3 manifests"

  kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

  kubectl apply -k infra/manifests/database
  kubectl apply -f infra/monitoring/alerts/backup-alert-rules.yaml || \
    log_warn "PrometheusRule apply failed (Prometheus Operator CRD may be missing)"

  log_ok "Phase 3 manifests applied"
}

verify_phase3() {
  log_info "Verifying Phase 3 components"

  kubectl -n "${NAMESPACE}" get configmap pgbackrest-config >/dev/null
  log_ok "pgBackRest config present"

  kubectl -n "${NAMESPACE}" get cronjob pgbackrest-full-backup >/dev/null
  kubectl -n "${NAMESPACE}" get cronjob pgbackrest-diff-backup >/dev/null
  kubectl -n "${NAMESPACE}" get cronjob pgbackrest-restore-verify >/dev/null
  log_ok "Backup and restore verification CronJobs present"

  kubectl -n "${NAMESPACE}" rollout status deployment/pgbouncer --timeout=180s
  log_ok "PgBouncer deployment ready"

  kubectl -n "${NAMESPACE}" get svc pgbouncer >/dev/null
  log_ok "PgBouncer service present"

  log_info "Current cronjobs:"
  kubectl -n "${NAMESPACE}" get cronjobs
}

show_next_steps() {
  cat <<EOF

Phase 3 deploy completed.

Next steps:
1) Replace placeholders in infra/manifests/database/pgbackrest-config.yaml
2) Ensure postgres PVC claimName in cronjobs matches your cluster (postgres-pvc)
3) Set DB clients to use pgbouncer.koral-system.svc.cluster.local:6432
4) Apply S3 lifecycle policy from infra/aws/s3-backup-lifecycle-policy.json
5) Trigger a manual backup test:
   kubectl -n ${NAMESPACE} create job --from=cronjob/pgbackrest-full-backup pgbackrest-full-backup-manual

EOF
}

main() {
  check_prerequisites
  build_and_push_backup_image
  apply_phase3_manifests
  verify_phase3
  show_next_steps
}

main "$@"
