#!/bin/bash
set -e

HELM="/mnt/c/Users/moham/AppData/Local/Microsoft/WinGet/Links/helm.exe"
KUBECTL="/mnt/c/Program Files/Docker/Docker/resources/bin/kubectl.exe"
NS=koral-system

"$HELM" upgrade --install cpu         charts/cpu-agent          -n $NS
"$HELM" upgrade --install memory      charts/memory-agent       -n $NS
"$HELM" upgrade --install storage     charts/storage-agent      -n $NS
"$HELM" upgrade --install logs        charts/log-agent          -n $NS
"$HELM" upgrade --install backend     charts/backend            -n $NS
"$HELM" upgrade --install frontend    charts/frontend           -n $NS
"$HELM" upgrade --install correlation charts/correlation-engine -n $NS

echo "==> All deployed. Checking pods..."
"$KUBECTL" get pods -n $NS
