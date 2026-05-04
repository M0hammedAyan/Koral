#!/bin/bash
# KORAL System Health Check — run after deploy-all.sh

KUBECTL="${KUBECTL_BIN:-$(which kubectl 2>/dev/null || echo "/mnt/c/Program Files/Docker/Docker/resources/bin/kubectl.exe")}"
MINIKUBE="${MINIKUBE_BIN:-$(which minikube 2>/dev/null || echo "/mnt/c/Program Files/Kubernetes/Minikube/minikube.exe")}"
NS=koral-system
PASS=0
FAIL=0

check() {
  local label=$1
  local cmd=$2
  if eval "$cmd" &>/dev/null; then
    echo "  [PASS] $label"
    PASS=$((PASS+1))
  else
    echo "  [FAIL] $label"
    FAIL=$((FAIL+1))
  fi
}

echo ""
echo "=============================="
echo " KORAL Health Check"
echo "=============================="

echo ""
echo "--- Cluster ---"
check "Node is Ready" \
  "\"$KUBECTL\" get nodes | grep -q ' Ready'"

echo ""
echo "--- Namespace ---"
check "koral-system namespace exists" \
  "\"$KUBECTL\" get namespace koral-system"

echo ""
echo "--- Core Pods Running ---"
for svc in cpu memory storage logs backend frontend correlation; do
  check "Pod: $svc" \
    "\"$KUBECTL\" get pods -n $NS --no-headers | grep '^$svc' | grep -q 'Running'"
done

echo ""
echo "--- Monitoring ---"
check "Prometheus pod running" \
  "\"$KUBECTL\" get pods -n $NS --no-headers | grep -q 'prometheus.*Running'"
check "Fluentd pod running" \
  "\"$KUBECTL\" get pods -n $NS --no-headers | grep -q 'fluentd.*Running'"

echo ""
echo "--- Services Exist ---"
for svc in cpu memory storage logs backend frontend correlation; do
  check "Service: $svc" \
    "\"$KUBECTL\" get svc $svc -n $NS"
done

echo ""
echo "--- Restart Count Check ---"
RESTARTS=$("$KUBECTL" get pods -n $NS --no-headers 2>/dev/null | awk '{print $4}' | grep -v '^0$' | wc -l | tr -d ' ')
if [ "$RESTARTS" -eq 0 ]; then
  echo "  [PASS] No pod restarts detected"
  PASS=$((PASS+1))
else
  echo "  [WARN] $RESTARTS pod(s) have restarted - check logs"
  FAIL=$((FAIL+1))
fi

echo ""
echo "--- RBAC ---"
check "ServiceAccount koral-agent exists" \
  "\"$KUBECTL\" get serviceaccount koral-agent -n $NS"
check "ClusterRoleBinding exists" \
  "\"$KUBECTL\" get clusterrolebinding koral-agent-binding"

echo ""
echo "--- Backend API ---"
BACKEND_URL=$("$MINIKUBE" service backend -n $NS --url 2>/dev/null || echo "")
if [ -n "$BACKEND_URL" ]; then
  check "Backend /health responds" \
    "curl -sf $BACKEND_URL/health"
else
  echo "  [SKIP] Backend URL unavailable - run: minikube service backend -n $NS --url"
fi

echo ""
echo "=============================="
echo " Results: $PASS passed, $FAIL failed"
echo "=============================="

if [ "$FAIL" -eq 0 ]; then
  echo " STATUS: SYSTEM READY FOR DEMO"
else
  echo " STATUS: $FAIL issue(s) need attention"
  exit 1
fi
