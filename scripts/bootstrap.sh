#!/bin/bash
set -e

# Auto-detect tool paths — override with env vars if needed
MINIKUBE="${MINIKUBE_BIN:-$(which minikube 2>/dev/null || echo "/mnt/c/Program Files/Kubernetes/Minikube/minikube.exe")}"
HELM="${HELM_BIN:-$(which helm 2>/dev/null || echo "/mnt/c/Users/moham/AppData/Local/Microsoft/WinGet/Links/helm.exe")}"
KUBECTL="${KUBECTL_BIN:-$(which kubectl 2>/dev/null || echo "/mnt/c/Program Files/Docker/Docker/resources/bin/kubectl.exe")}"

echo "==> Using:"
echo "    minikube : $MINIKUBE"
echo "    helm     : $HELM"
echo "    kubectl  : $KUBECTL"

echo ""
echo "==> Starting Minikube (4 CPU, 8GB RAM)..."
"$MINIKUBE" start --cpus=4 --memory=8192

echo ""
echo "==> Applying base manifests..."
"$KUBECTL" apply -f infra/k8s/namespaces/
"$KUBECTL" apply -f infra/k8s/rbac/
"$KUBECTL" apply -f infra/k8s/networking/

echo ""
echo "==> Adding Helm repos..."
"$HELM" repo add prometheus-community https://prometheus-community.github.io/helm-charts
"$HELM" repo add fluent https://fluent.github.io/helm-charts
"$HELM" repo update

echo ""
echo "==> Installing Prometheus monitoring stack..."
"$HELM" upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n koral-system --create-namespace --wait

echo ""
echo "==> Installing Fluentd..."
"$HELM" upgrade --install fluentd fluent/fluentd \
  -n koral-system \
  -f infra/monitoring/fluentd/values.yaml --wait

echo ""
echo "==> Bootstrap complete."
"$KUBECTL" get nodes
"$KUBECTL" get pods -n koral-system
