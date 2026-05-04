#!/bin/bash

HELM="/mnt/c/Users/moham/AppData/Local/Microsoft/WinGet/Links/helm.exe"
KUBECTL="/mnt/c/Program Files/Docker/Docker/resources/bin/kubectl.exe"
MINIKUBE="/mnt/c/Program Files/Kubernetes/Minikube/minikube.exe"

"$HELM" uninstall monitoring fluentd cpu memory storage logs backend frontend correlation \
  -n koral-system 2>/dev/null || true

"$KUBECTL" delete namespace koral-system 2>/dev/null || true

echo "==> Teardown complete."
"$MINIKUBE" stop
