#!/usr/bin/env bash
# Generate synthetic incidents for demo recording
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting CPU simulator (koral-sim-cpu)..."
docker compose -f docker-compose-prod.yml -f docker-compose.demo.yml up -d sim-cpu || true
sleep 2

echo "Starting memory simulator (koral-sim-memory)..."
docker compose -f docker-compose-prod.yml -f docker-compose.demo.yml up -d sim-memory || true
sleep 2

echo "Starting storage fill simulator (koral-sim-storage)..."
docker compose -f docker-compose-prod.yml -f docker-compose.demo.yml up -d sim-storage-fill || true

echo "Simulators started. Leave them running for demo; to stop them:"
echo "  docker rm -f koral-sim-cpu koral-sim-memory koral-sim-storage || true"
