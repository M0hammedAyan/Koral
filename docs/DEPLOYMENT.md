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

---

## Merged: Deployment Checklist & Kubernetes Quick Reference

The following content was consolidated from repository root checklists and k8s quick references to centralize deployment guidance.

### Pre-Deployment Validation (merged)
- Ensure `.env` created from `.env.example` and not committed
- AI API key configured (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
- SMTP/email alert settings configured if used
- Prometheus URL configured and accessible
- Namespace: `koral-system` (or target namespace)

### Infrastructure Prerequisites
- Minikube (or cluster) available
- `kubectl` configured for target cluster
- Helm available for Helm-based deploys
- Sufficient resources (4 CPU, 8GB RAM recommended for demo/proof-of-concept)

### Quick Deploy Steps (merged)
1. Create namespace and secrets
```bash
kubectl create namespace koral-system || true
kubectl apply -f k8s/koral-secrets.yaml
```
2. Deploy core infra (Postgres, Prometheus)
```bash
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
```
3. Deploy KORAL services
```bash
kubectl apply -f k8s/koral-deployment.yaml
```
4. Verify
```bash
kubectl get pods -n koral-system
kubectl logs -f deployment/backend -n koral-system
```

### Kubernetes Quick Reference (merged)
- Use `kubectl apply -k infra/manifests/overlays/production` for kustomize-based production deploys
- Use `helm install -f infra/helm/koral/values-production.yaml koral infra/helm/koral` for Helm-based deploys
- For Minikube testing, use `minikube image load` for locally built images and `minikube service <svc> -n koral-system` to expose services

### Notes
- This file consolidates multiple checklist and quick-reference sources. Obsolete or duplicate markdown files have been removed; see `DOC_CLEANUP_REPORT.md` for details.
