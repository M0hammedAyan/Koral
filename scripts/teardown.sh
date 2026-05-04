#!/bin/bash

HELM="${HELM:-helm}"
KUBECTL="${KUBECTL:-kubectl}"
MINIKUBE="${MINIKUBE:-minikube}"

"$HELM" uninstall monitoring fluentd cpu memory storage logs backend frontend correlation \
  -n koral-system 2>/dev/null || true

"$KUBECTL" delete namespace koral-system 2>/dev/null || true

echo "==> Teardown complete."
"$MINIKUBE" stop
