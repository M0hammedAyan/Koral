#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="koral-system"
DASHBOARD_DIR="$(dirname "$0")/../infra/grafana/dashboards"
VALUES_FILE="$(dirname "$0")/../infra/monitoring/prometheus-values.yaml"

echo "==> Creating Grafana dashboard ConfigMap..."
kubectl create configmap koral-grafana-dashboards \
  --namespace "$NAMESPACE" \
  --from-file="$DASHBOARD_DIR" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Upgrading kube-prometheus-stack with Grafana enabled..."
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --values "$VALUES_FILE" \
  --wait --timeout 5m

echo "==> Grafana deployed. Access via:"
echo "    kubectl port-forward svc/monitoring-grafana $NAMESPACE 3001:3001"
echo "    Default credentials: admin / \${GRAFANA_ADMIN_PASSWORD:-koral-admin}"
