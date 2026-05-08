#!/usr/bin/env bash
# Start KORAL platform in demo mode (quiet logs, demo sims disabled)
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Building images (if needed)..."
docker compose -f docker-compose-prod.yml build

echo "Starting stack (prod + demo override)..."
docker compose -f docker-compose-prod.yml -f docker-compose.demo.yml up -d

echo "Waiting 10s for healthchecks..."
sleep 10

echo "Services (short):"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "Prometheus: http://localhost:9090"
echo "Frontend: http://localhost:3000"

echo "Demo stack started. Use scripts/generate_incidents.sh to trigger synthetic incidents." 
