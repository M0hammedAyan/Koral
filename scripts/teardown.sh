#!/bin/bash

HELM="${HELM_BIN:-$(which helm 2>/dev/null || echo "/mnt/c/Users/moham/AppData/Local/Microsoft/WinGet/Links/helm.exe")}"
KUBECTL="${KUBECTL_BIN:-$(which kubectl 2>/dev/null || echo "/mnt/c/Program Files/Docker/Docker/resources/bin/kubectl.exe")}"
MINIKUBE="${MINIKUBE_BIN:-$(which minikube 2>/dev/null || echo "/mnt/c/Program Files/Kubernetes/Minikube/minikube.exe")}"

echo "==> Uninstalling Helm releases..."
"$HELM" uninstall monitoring fluentd cpu memory storage logs backend frontend correlation \
  -n koral-system 2>/dev/null || true

echo "==> Deleting namespace koral-system..."
"$KUBECTL" delete namespace koral-system 2>/dev/null || true

echo "==> Stopping Minikube..."
"$MINIKUBE" stop

echo "==> Teardown complete."
