#!/bin/bash
# Member 5 Quick Start — Run all tests and validations

set -e

echo "========================================"
echo " KORAL Member 5 — Quick Start"
echo "========================================"

# 1. Install dependencies
echo "[1/4] Installing dependencies..."
pip install -q -r requirements.txt

# 2. Run integration tests
echo "[2/4] Running integration tests..."
python evaluation/integration_test.py

# 3. Run full test suite
echo "[3/4] Running complete test suite..."
python run_tests.py

# 4. Validate demo scenarios
echo "[4/4] Validating demo scenarios..."
python demo_validator.py --scenario io_storm

echo ""
echo "========================================"
echo " Member 5 Setup Complete ✓"
echo "========================================"
echo ""
echo "Next steps:"
echo "  - Build simulation image: docker build -t <your-dockerhub>/koral-simulation:latest ."
echo "  - Push to registry: docker push <your-dockerhub>/koral-simulation:latest"
echo "  - Deploy simulation: kubectl apply -f simulation/k8s-io-storm.yaml"
echo "  - Monitor results: python demo_validator.py"
