#!/bin/bash
# KORAL System Health Check
# Run after deploy-all.sh to validate the full system

KUBECTL="${KUBECTL:-kubectl}"
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
    "\"$KUBECTL\" get pods -n $NS -l app=$svc --field-selector=status.phase=Running | grep -q Running"
done

echo ""
echo "--- Monitoring ---"
check "Prometheus pod running" \
  "\"$KUBECTL\" get pods -n $NS | grep -q 'monitoring-kube-prometheus-prometheus'"
check "Fluentd pod running" \
  "\"$KUBECTL\" get pods -n $NS | grep -q 'fluentd'"

echo ""
echo "--- Services Exist ---"
for svc in cpu memory storage logs backend frontend correlation; do
  check "Service: $svc" \
    "\"$KUBECTL\" get svc $svc -n $NS"
done

echo ""
echo "--- Restart Count Check ---"
RESTARTS=$("$KUBECTL" get pods -n $NS --no-headers 2>/dev/null | awk '{print $4}' | grep -v '^0$' | wc -l)
if [ "$RESTARTS" -eq 0 ]; then
  echo "  [PASS] No pod restarts detected"
  PASS=$((PASS+1))
else
  echo "  [WARN] $RESTARTS pod(s) have restarted — check logs"
  FAIL=$((FAIL+1))
fi

echo ""
echo "--- RBAC ---"
check "ServiceAccount koral-agent exists" \
  "\"$KUBECTL\" get serviceaccount koral-agent -n $NS"
check "ClusterRoleBinding exists" \
  "\"$KUBECTL\" get clusterrolebinding koral-agent-binding"

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
