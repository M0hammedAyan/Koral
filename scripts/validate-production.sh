#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
#  KORAL Production Validation Script
#  Verifies the system is production-ready before deployment
# ═══════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  KORAL Production Validation"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── Helper functions ─────────────────────────────────────────────
pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASS++))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAIL++))
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARN++))
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ── 1. Check for mock/test files ────────────────────────────────
echo "1. Checking for mock/test files..."

if [ -f "create_incident.py" ]; then
    fail "Mock file 'create_incident.py' still exists"
else
    pass "No create_incident.py found"
fi

if [ -f "clear_old_incidents.py" ]; then
    fail "Mock file 'clear_old_incidents.py' still exists"
else
    pass "No clear_old_incidents.py found"
fi

if [ -f "simulate.py" ]; then
    fail "Mock file 'simulate.py' still exists"
else
    pass "No simulate.py found"
fi

if [ -f "inject_anomaly.py" ]; then
    fail "Mock file 'inject_anomaly.py' still exists"
else
    pass "No inject_anomaly.py found"
fi

if [ -f "AIML/Member1_work/data/dummy_events.json" ]; then
    fail "Dummy data file still exists"
else
    pass "No dummy_events.json found"
fi

echo ""

# ── 2. Check environment configuration ──────────────────────────
echo "2. Checking environment configuration..."

if [ ! -f ".env" ]; then
    fail ".env file not found"
    info "Run: cp .env.example .env"
else
    pass ".env file exists"
    
    # Check for API keys
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        pass "OpenAI API key configured"
    elif grep -q "ANTHROPIC_API_KEY=sk-ant-" .env 2>/dev/null; then
        pass "Anthropic API key configured"
    else
        fail "No AI API key configured"
        info "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env"
    fi
    
    # Check for email config
    if grep -q "ALERT_EMAIL=.*@" .env 2>/dev/null; then
        pass "Alert email configured"
    else
        warn "Alert email not configured (optional)"
    fi
fi

echo ""

# ── 3. Check Docker images ──────────────────────────────────────
echo "3. Checking Docker configuration..."

if [ -f "docker-compose.yml" ]; then
    pass "docker-compose.yml exists"
else
    fail "docker-compose.yml not found"
fi

if [ -f "backend/Dockerfile" ]; then
    pass "Backend Dockerfile exists"
else
    fail "Backend Dockerfile not found"
fi

if [ -f "frontend/Dockerfile" ]; then
    pass "Frontend Dockerfile exists"
else
    fail "Frontend Dockerfile not found"
fi

if [ -f "correlation-engine/Dockerfile" ]; then
    pass "Correlation Engine Dockerfile exists"
else
    fail "Correlation Engine Dockerfile not found"
fi

if [ -f "ai_engine/Dockerfile" ]; then
    pass "AI Engine Dockerfile exists"
else
    fail "AI Engine Dockerfile not found"
fi

echo ""

# ── 4. Check Helm charts ────────────────────────────────────────
echo "4. Checking Helm charts..."

CHARTS=("backend" "frontend" "correlation-engine" "cpu-agent" "memory-agent" "storage-agent" "log-agent")

for chart in "${CHARTS[@]}"; do
    if [ -f "charts/$chart/Chart.yaml" ] && [ -f "charts/$chart/values.yaml" ]; then
        pass "Chart: $chart"
    else
        fail "Chart incomplete: $chart"
    fi
done

echo ""

# ── 5. Check Kubernetes manifests ──────────────────────────────
echo "5. Checking Kubernetes manifests..."

if [ -f "infra/k8s/namespaces/namespace.yaml" ]; then
    pass "Namespace manifest exists"
else
    fail "Namespace manifest not found"
fi

if [ -f "infra/k8s/rbac/rbac.yaml" ]; then
    pass "RBAC manifest exists"
else
    fail "RBAC manifest not found"
fi

if [ -f "infra/k8s/networking/network-policy.yaml" ]; then
    pass "Network policy exists"
else
    fail "Network policy not found"
fi

echo ""

# ── 6. Demo simulators ─────────────────────────────────────────
echo "6. Demo simulators: removed in cleanup pass (optional)"
echo ""

# ── 7. Check scripts ────────────────────────────────────────────
echo "7. Checking deployment scripts..."

SCRIPTS=("bootstrap.sh" "deploy-all.sh" "health-check.sh" "teardown.sh")

for script in "${SCRIPTS[@]}"; do
    if [ -f "scripts/$script" ]; then
        pass "Script: $script"
    else
        fail "Script missing: $script"
    fi
done

echo ""

# ── 8. Check agent code ─────────────────────────────────────────
echo "8. Checking agent implementations..."

AGENTS=("cpu-agent" "memory-agent" "storage-agent" "log-agent")

for agent in "${AGENTS[@]}"; do
    if [ -f "agents/$agent/main.py" ] && [ -f "agents/$agent/requirements.txt" ]; then
        pass "Agent: $agent"
    else
        fail "Agent incomplete: $agent"
    fi
done

if [ -f "agents/base_agent.py" ]; then
    pass "Base agent class exists"
else
    fail "Base agent class not found"
fi

echo ""

# ── 9. Check correlation engine ────────────────────────────────
echo "9. Checking correlation engine..."

if [ -f "correlation-engine/main.py" ]; then
    pass "Correlation engine main.py exists"
else
    fail "Correlation engine main.py not found"
fi

if [ -d "correlation-engine/ai_core" ]; then
    pass "AI core modules exist"
else
    fail "AI core modules not found"
fi

echo ""

# ── 10. Check AI engine ─────────────────────────────────────────
echo "10. Checking AI engine..."

if [ -f "ai_engine/main.py" ]; then
    pass "AI engine main.py exists"
else
    fail "AI engine main.py not found"
fi

echo ""

# ── 11. Check frontend ──────────────────────────────────────────
echo "11. Checking frontend..."

if [ -f "frontend/package.json" ]; then
    pass "Frontend package.json exists"
else
    fail "Frontend package.json not found"
fi

if [ -f "frontend/src/App.tsx" ]; then
    pass "Frontend App.tsx exists"
else
    fail "Frontend App.tsx not found"
fi

if [ -f "frontend/src/services/api.ts" ]; then
    pass "Frontend API service exists"
else
    fail "Frontend API service not found"
fi

echo ""

# ── 12. Check documentation ─────────────────────────────────────
echo "12. Checking documentation..."

if [ -f "README.md" ]; then
    pass "README.md exists"
else
    fail "README.md not found"
fi

if [ -f "PRODUCTION_GUIDE.md" ]; then
    pass "PRODUCTION_GUIDE.md exists"
else
    warn "PRODUCTION_GUIDE.md not found (recommended)"
fi

echo ""

# ── Summary ─────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo "  Validation Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}PASS:${NC} $PASS"
echo -e "${YELLOW}WARN:${NC} $WARN"
echo -e "${RED}FAIL:${NC} $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ System is PRODUCTION READY${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review .env configuration"
    echo "  2. Run: ./scripts/bootstrap.sh"
    echo "  3. Run: ./scripts/deploy-all.sh"
    echo "  4. Run: ./scripts/health-check.sh"
    echo "  5. Access dashboard: minikube service frontend -n koral-system"
    echo ""
    exit 0
else
    echo -e "${RED}✗ System has $FAIL critical issues${NC}"
    echo ""
    echo "Fix the issues above before deploying to production."
    echo ""
    exit 1
fi
