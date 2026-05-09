#!/bin/bash
# KORAL System Health Verification
# Comprehensive check of all current systems before evolution
# Run: bash scripts/verify-current-health.sh

set -e

echo "============================================================"
echo "KORAL CURRENT SYSTEM HEALTH VERIFICATION"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

health_ok=true

# Function to check endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK (HTTP $response)${NC}"
    else
        echo -e "${RED}✗ FAILED (Expected $expected_status, got $response)${NC}"
        health_ok=false
    fi
}

# Function to check docker service
check_docker_service() {
    local service=$1
    
    echo -n "Checking Docker service: $service... "
    
    if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${RED}✗ NOT Running${NC}"
        health_ok=false
    fi
}

# ========== SECTION: DOCKER COMPOSE SERVICES ==========
echo ""
echo -e "${YELLOW}[SECTION] DOCKER COMPOSE SERVICES${NC}"
echo "========================================"

for service in koral-backend koral-ai-engine koral-correlation-engine koral-cpu-agent koral-memory-agent koral-storage-agent koral-log-agent koral-postgres koral-prometheus frontend; do
    check_docker_service "$service"
done

# ========== SECTION: BACKEND API ==========
echo ""
echo -e "${YELLOW}[SECTION] BACKEND API ENDPOINTS${NC}"
echo "========================================"

check_endpoint "Backend Health" "http://localhost:8000/health" "200"
check_endpoint "GET /incidents" "http://localhost:8000/incidents" "200"
check_endpoint "GET /anomalies" "http://localhost:8000/anomalies" "200"
check_endpoint "GET /correlations" "http://localhost:8000/correlations" "200"
check_endpoint "GET /graph" "http://localhost:8000/graph" "200"

# ========== SECTION: AI ENGINE ==========
echo ""
echo -e "${YELLOW}[SECTION] AI ENGINE${NC}"
echo "========================================"

check_endpoint "AI Engine Health" "http://localhost:8006/health" "200"

# ========== SECTION: CORRELATION ENGINE ==========
echo ""
echo -e "${YELLOW}[SECTION] CORRELATION ENGINE${NC}"
echo "========================================"

check_endpoint "Correlation Engine Health" "http://localhost:8005/health" "200"

# ========== SECTION: AGENTS ==========
echo ""
echo -e "${YELLOW}[SECTION] MONITORING AGENTS${NC}"
echo "========================================"

check_endpoint "CPU Agent Health" "http://localhost:8001/health" "200"
check_endpoint "Memory Agent Health" "http://localhost:8002/health" "200"
check_endpoint "Storage Agent Health" "http://localhost:8003/health" "200"
check_endpoint "Log Agent Health" "http://localhost:8004/health" "200"

# ========== SECTION: PROMETHEUS ==========
echo ""
echo -e "${YELLOW}[SECTION] PROMETHEUS MONITORING${NC}"
echo "========================================"

check_endpoint "Prometheus Query API" "http://localhost:9090/api/v1/query?query=up" "200"

# Check if targets are scraped
echo -n "Verifying Prometheus targets... "
targets=$(curl -s "http://localhost:9090/api/v1/targets" 2>/dev/null || echo "")

if echo "$targets" | grep -q "koral-backend"; then
    echo -e "${GREEN}✓ Targets found${NC}"
else
    echo -e "${YELLOW}⚠ Limited targets detected${NC}"
fi

# ========== SECTION: METRICS COLLECTION ==========
echo ""
echo -e "${YELLOW}[SECTION] METRICS COLLECTION${NC}"
echo "========================================"

echo -n "Checking if metrics are flowing... "

incidents=$(curl -s "http://localhost:8000/incidents" | grep -o "incident_id" | wc -l 2>/dev/null || echo "0")
anomalies=$(curl -s "http://localhost:8000/anomalies" | grep -o "pod" | wc -l 2>/dev/null || echo "0")

if [ "$incidents" -gt "0" ] || [ "$anomalies" -gt "0" ]; then
    echo -e "${GREEN}✓ Data flowing (incidents: $incidents, anomalies: $anomalies)${NC}"
else
    echo -e "${YELLOW}⚠ No recent data (may be normal in clean environment)${NC}"
fi

# ========== SECTION: FRONTEND ==========
echo ""
echo -e "${YELLOW}[SECTION] FRONTEND APPLICATION${NC}"
echo "========================================"

check_endpoint "Frontend (React)" "http://localhost:3000" "200"

# ========== SECTION: DATABASE ==========
echo ""
echo -e "${YELLOW}[SECTION] DATABASE (POSTGRESQL)${NC}"
echo "========================================"

echo -n "Checking PostgreSQL connectivity... "

if docker exec koral-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL responding${NC}"
    
    # Check if KORAL database exists
    echo -n "Verifying KORAL database... "
    if docker exec koral-postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -q "koral"; then
        echo -e "${GREEN}✓ Database exists${NC}"
        
        # Check table count
        echo -n "Counting database tables... "
        table_count=$(docker exec koral-postgres psql -U postgres -d koral -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")
        echo -e "${GREEN}✓ Found $table_count tables${NC}"
    else
        echo -e "${RED}✗ KORAL database not found${NC}"
        health_ok=false
    fi
else
    echo -e "${RED}✗ PostgreSQL not responding${NC}"
    health_ok=false
fi

# ========== SECTION: WEBSOCKET ==========
echo ""
echo -e "${YELLOW}[SECTION] WEBSOCKET REAL-TIME UPDATES${NC}"
echo "========================================"

echo -n "Checking WebSocket availability... "

ws_test=$(curl -s -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
    http://localhost:8000/ws 2>/dev/null | grep -i "upgrade" | wc -l)

if [ "$ws_test" -gt "0" ]; then
    echo -e "${GREEN}✓ WebSocket endpoint responsive${NC}"
else
    echo -e "${YELLOW}⚠ WebSocket check inconclusive (may be normal)${NC}"
fi

# ========== SECTION: ENVIRONMENT CONFIGURATION ==========
echo ""
echo -e "${YELLOW}[SECTION] ENVIRONMENT CONFIGURATION${NC}"
echo "========================================"

echo -n "Checking for .env file... "
if [ -f .env ]; then
    echo -e "${GREEN}✓ Found${NC}"
    
    echo -n "  - OPENAI_API_KEY configured: "
    if grep -q "OPENAI_API_KEY=" .env && [ ! "$(grep 'OPENAI_API_KEY=' .env | cut -d'=' -f2)" = "" ]; then
        echo -e "${GREEN}✓ Yes${NC}"
    else
        echo -e "${YELLOW}⚠ Not set (AI features may not work)${NC}"
    fi
    
    echo -n "  - Database type: "
    db_type=$(grep 'DB_TYPE=' .env | cut -d'=' -f2)
    echo -e "${GREEN}$db_type${NC}"
else
    echo -e "${YELLOW}⚠ .env not found${NC}"
fi

# ========== SECTION: DOCKER COMPOSE ==========
echo ""
echo -e "${YELLOW}[SECTION] DOCKER COMPOSE STATUS${NC}"
echo "========================================"

echo "Current Docker Compose state:"
docker compose ps 2>/dev/null | head -20 || echo "Error: docker compose may not be running"

# ========== SECTION: KUBERNETES (if configured) ==========
echo ""
echo -e "${YELLOW}[SECTION] KUBERNETES READINESS (Optional)${NC}"
echo "========================================"

echo -n "Checking Kubernetes availability... "

if command -v kubectl &> /dev/null; then
    if kubectl cluster-info > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Kubernetes available${NC}"
        
        echo -n "  - koral-system namespace: "
        if kubectl get namespace koral-system > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Exists${NC}"
            kubectl get pods -n koral-system 2>/dev/null || echo "    (No pods deployed)"
        else
            echo -e "${YELLOW}⚠ Not deployed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Kubernetes not available${NC}"
    fi
else
    echo -e "${YELLOW}⚠ kubectl not installed${NC}"
fi

# ========== SECTION: LOG INSPECTION ==========
echo ""
echo -e "${YELLOW}[SECTION] RECENT ERROR LOGS${NC}"
echo "========================================"

echo "Backend logs (last 5 lines):"
docker logs koral-backend 2>/dev/null | tail -5 || echo "  (Unable to retrieve)"

# ========== SUMMARY ==========
echo ""
echo "============================================================"

if [ "$health_ok" = true ]; then
    echo -e "${GREEN}✓ HEALTH CHECK PASSED${NC}"
    echo "System is healthy and ready for extension."
    exit 0
else
    echo -e "${RED}✗ HEALTH CHECK FAILED${NC}"
    echo "Some services may not be running properly."
    echo "Recommendations:"
    echo "  1. Run: docker compose up -d"
    echo "  2. Wait 30 seconds for services to start"
    echo "  3. Run this script again"
    exit 1
fi
