# KORAL Production Deployment Guide

This file consolidates production deployment instructions for KORAL.

*Original source: `PRODUCTION_DEPLOYMENT.md`*

---

 (See full deployment guide in repository root `PRODUCTION_DEPLOYMENT.md`.)

## Quick actions

1. Create secrets: `kubectl apply -f k8s/koral-secrets.yaml`
2. Deploy Postgres & Prometheus: `kubectl apply -f k8s/postgres-deployment.yaml` and `kubectl apply -f k8s/prometheus-deployment.yaml`
3. Deploy KORAL services: `kubectl apply -f k8s/koral-deployment.yaml`
4. Verify: `kubectl get pods -n koral-system` and `kubectl logs -f deployment/backend -n koral-system`

For the full, detailed production deployment guide keep `PRODUCTION_DEPLOYMENT.md` at the repository root until final cleanup.
