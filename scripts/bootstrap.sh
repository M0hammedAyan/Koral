#!/bin/bash
set -e

MINIKUBE="${MINIKUBE:-minikube}"
HELM="${HELM:-helm}"
KUBECTL="${KUBECTL:-kubectl}"

echo "==> Starting Minikube (4 CPU, 8GB RAM)..."
"$MINIKUBE" start --cpus=4 --memory=8192

echo "==> Applying base manifests..."
"$KUBECTL" apply -f infra/k8s/namespaces/
"$KUBECTL" apply -f infra/k8s/rbac/
"$KUBECTL" apply -f infra/k8s/networking/

echo "==> Adding Helm repos..."
"$HELM" repo add prometheus-community https://prometheus-community.github.io/helm-charts
"$HELM" repo add fluent https://fluent.github.io/helm-charts
"$HELM" repo update

echo "==> Installing monitoring stack..."
"$HELM" upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n koral-system --create-namespace --wait

echo "==> Installing Fluentd..."
"$HELM" upgrade --install fluentd fluent/fluentd \
  -n koral-system \
  -f infra/monitoring/fluentd/values.yaml

echo "==> Done."
"$KUBECTL" get nodes
"$KUBECTL" get pods -n koral-system
