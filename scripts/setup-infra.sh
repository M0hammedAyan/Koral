#!/usr/bin/env bash
set -euo pipefail

# Bootstrap local infra tools for KORAL development
# Run this on developer machine (Linux/macOS) or CI stage that needs kubectl/helm

# Minikube
if ! command -v minikube >/dev/null 2>&1; then
  echo "Installing minikube..."
  curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
  chmod +x minikube
  sudo mv minikube /usr/local/bin/
fi

# kubectl
if ! command -v kubectl >/dev/null 2>&1; then
  echo "Installing kubectl..."
  curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  chmod +x kubectl
  sudo mv kubectl /usr/local/bin/
fi

# helm
if ! command -v helm >/dev/null 2>&1; then
  echo "Installing helm..."
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo "Infra tools installed or already present."
