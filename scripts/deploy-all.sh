#!/bin/bash
set -e

HELM="${HELM_BIN:-$(which helm 2>/dev/null || echo "/mnt/c/Users/moham/AppData/Local/Microsoft/WinGet/Links/helm.exe")}"
KUBECTL="${KUBECTL_BIN:-$(which kubectl 2>/dev/null || echo "/mnt/c/Program Files/Docker/Docker/resources/bin/kubectl.exe")}"
NS=koral-system

echo "==> Deploying all KORAL services to namespace: $NS"

"$HELM" upgrade --install cpu         charts/cpu-agent          -n $NS --create-namespace --wait
"$HELM" upgrade --install memory      charts/memory-agent       -n $NS --create-namespace --wait
"$HELM" upgrade --install storage     charts/storage-agent      -n $NS --create-namespace --wait
"$HELM" upgrade --install logs        charts/log-agent          -n $NS --create-namespace --wait
"$HELM" upgrade --install backend     charts/backend            -n $NS --create-namespace --wait
"$HELM" upgrade --install frontend    charts/frontend           -n $NS --create-namespace --wait
"$HELM" upgrade --install correlation charts/correlation-engine -n $NS --create-namespace --wait

echo ""
echo "==> All services deployed. Pod status:"
"$KUBECTL" get pods -n $NS
