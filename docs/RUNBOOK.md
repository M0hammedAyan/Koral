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

For full runbook details see `docs/runbooks/INCIDENT_RESPONSE.md`.
