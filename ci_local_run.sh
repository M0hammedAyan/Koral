#!/bin/bash
set -euo pipefail

echo "=== CI LOCAL RUN: start postgres, install deps, run tests, build images ==="

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI not found in PATH. Aborting." >&2
  exit 2
fi

# Cleanup previous container
docker rm -f ci-postgres 2>/dev/null || true

echo "Starting ci-postgres container..."
docker run -d --name ci-postgres -e POSTGRES_DB=koral -e POSTGRES_USER=koral -e POSTGRES_PASSWORD=koralpass -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 postgres:15

echo "Waiting for Postgres to be ready (max 30s)..."
for i in $(seq 1 30); do
  if docker exec ci-postgres pg_isready -U koral >/dev/null 2>&1; then
    echo "Postgres ready"
    break
  fi
  sleep 1
done

if ! docker exec ci-postgres pg_isready -U koral >/dev/null 2>&1; then
  echo "Postgres did not become ready within timeout. Showing logs:" >&2
  docker logs ci-postgres || true
  docker rm -f ci-postgres || true
  exit 3
fi

# Install Python deps
python -m pip install --upgrade pip

pip install -r backend/requirements.txt || { echo 'Failed to install backend requirements'; exit 4; }

REQS=(agents/requirements.txt agents/cpu-agent/requirements.txt agents/memory-agent/requirements.txt agents/storage-agent/requirements.txt agents/log-agent/requirements.txt correlation-engine/requirements.txt ai_engine/requirements.txt tests/requirements.txt)
for r in "${REQS[@]}"; do
  if [ -f "$r" ]; then
    echo "Installing $r"
    pip install -r "$r" || { echo "Failed to install $r"; exit 5; }
  fi
done

# Export environment for tests
export DB_TYPE=postgres
export DB_HOST=127.0.0.1
export DB_PORT=5432
export DB_NAME=koral
export DB_USER=koral
export DB_PASS=koralpass
export API_KEY=testapikey
export JWT_SECRET=testjwtsecret
export OPENAI_API_KEY=testopenai
export ANTHROPIC_API_KEY=testanthropic
export SMTP_USER=test@test.com
export SMTP_PASS=testpass
export ALLOWED_ORIGINS=http://localhost:3000
export BACKEND_URL=http://localhost:8000
export PROMETHEUS_URL=http://localhost:9090
export Z_THRESHOLD=2.5
export POLL_INTERVAL=10
export PYTHONPATH="$(pwd):$(pwd)/agents"

# Run tests
echo "Running pytest..."
python -m pytest tests/ -v --tb=short

# Build Docker images
echo "Building Docker images..."

docker build -t koral:ci .
docker build -t koral-ai-engine:ci -f ai_engine/Dockerfile ai_engine
docker build -t koral-correlation-engine:ci -f correlation-engine/Dockerfile correlation-engine
docker build -t koral-frontend:ci -f frontend/Dockerfile frontend

# Cleanup
echo "Cleaning up ci-postgres container..."
docker rm -f ci-postgres || true

echo "=== CI LOCAL RUN COMPLETE ==="
