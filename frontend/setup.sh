#!/bin/bash
# KORAL Frontend Quick Setup

set -e

echo "========================================"
echo " KORAL Frontend Setup"
echo "========================================"

# 1. Install dependencies
echo "[1/3] Installing dependencies..."
npm install

# 2. Build for production
echo "[2/3] Building production bundle..."
npm run build

# 3. Docker build (optional)
read -p "Build Docker image? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    read -p "Enter DockerHub username: " DOCKER_USER
    echo "[3/3] Building Docker image..."
    docker build -t $DOCKER_USER/koral-frontend:latest .
    
    read -p "Push to DockerHub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        docker push $DOCKER_USER/koral-frontend:latest
        echo "✓ Image pushed to DockerHub"
    fi
fi

echo ""
echo "========================================"
echo " Frontend Setup Complete ✓"
echo "========================================"
echo ""
echo "Next steps:"
echo "  - Local dev: npm start"
echo "  - Deploy: helm upgrade frontend ../charts/frontend -n koral-system"
echo "  - Access: minikube service frontend -n koral-system"
