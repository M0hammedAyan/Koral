# KORAL Incident Response Runbook

Consolidated runbook for common KORAL incidents.

*Source: `docs/runbooks/INCIDENT_RESPONSE.md`*

## Overview
This runbook provides step-by-step procedures for responding to common KORAL incidents.

### Backend Service Down
- Check pod status: `kubectl get pods -n koral-system -l app=backend`
- Check logs: `kubectl logs -n koral-system -l app=backend --tail=100`
- Restart deployment if needed: `kubectl rollout restart deployment/backend -n koral-system`

### Database Connection Issues
- Check PostgreSQL status and logs
- Verify secrets: `kubectl get secret koral-secrets -n koral-system -o yaml`

### AI Engine Unresponsive
- Check AI engine pod and API keys in secrets

### High CPU/Memory Usage
- Identify offending pod: `kubectl top pods -n koral-system`
- Scale or check HPA as necessary

### Additional: Local Run & Troubleshooting (merged)

Build and load images (Minikube):
```bash
docker build -t koral:v1 .
minikube image load koral:v1
```

Apply Kubernetes manifests:
```bash
kubectl apply -f k8s/koral-deployment.yaml
kubectl apply -f k8s/koral-service.yaml
```

Access the service:
```bash
# Option A: use kubectl to get NodePort and minikube IP
kubectl get svc koral
minikube ip

# Option B: minikube service helper
minikube service koral --url
```

Troubleshooting quick checks:
- ImagePullBackOff: `kubectl describe pod <pod>` and `kubectl get events` (ensure image loaded into minikube or imagePullPolicy set)
- CrashLoopBackOff: `kubectl logs <pod>` and `kubectl describe pod <pod>`
- Port not accessible: confirm container port and service mapping; use `minikube service` as above

For the consolidated runbook and incident response procedures, see this file.
