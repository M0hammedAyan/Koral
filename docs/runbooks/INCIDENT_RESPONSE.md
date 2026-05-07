# KORAL Incident Response Runbook

## Overview
This runbook provides step-by-step procedures for responding to common KORAL incidents.

## 1. Backend Service Down

### Symptoms
- Dashboard shows connection errors
- API calls return 503 errors
- Health check fails

### Steps
1. Check pod status: `kubectl get pods -n koral-system -l app=backend`
2. Check logs: `kubectl logs -n koral-system -l app=backend --tail=100`
3. Check for crash loops: `kubectl describe pod -n koral-system -l app=backend`
4. Restart deployment if needed: `kubectl rollout restart deployment/backend -n koral-system`

## 2. Database Connection Issues

### Symptoms
- "Connection refused" in backend logs
- Incidents not being stored
- Slow response times

### Steps
1. Check PostgreSQL status: `kubectl get pods -n koral-system -l app=postgres`
2. Check PostgreSQL logs: `kubectl logs -n koral-system -l app=postgres`
3. Verify secrets: `kubectl get secret koral-secrets -n koral-system -o yaml`
4. Check connection pooling metrics

## 3. AI Engine Unresponsive

### Symptoms
- No AI explanations for incidents
- GPT/Claude API errors in logs

### Steps
1. Check AI engine pod: `kubectl get pods -n koral-system -l app=ai-engine`
2. Verify API keys: Check OPENAI_API_KEY and ANTHROPIC_API_KEY secrets
3. Test API connectivity: `kubectl exec -n koral-system -it deploy/backend -- curl http://ai-engine:8006/health`
4. Check rate limits on OpenAI/Claude accounts

## 4. High CPU/Memory Usage

### Symptoms
- Alert manager notifications
- Pod evictions
- Slow response times

### Steps
1. Identify offending pod: `kubectl top pods -n koral-system`
2. Check for runaway processes: `kubectl exec -n koral-system <pod> -- ps aux`
3. Scale up if needed: `kubectl scale deployment/<name> -n koral-system --replicas=3`
4. Check HPA status: `kubectl get hpa -n koral-system`

## 5. Alert Storm

### Symptoms
- Too many email/slack alerts
- 100+ incidents in short time

### Steps
1. Check for cluster-wide issues: `kubectl get nodes`
2. Temporarily increase z-score threshold: `Z_THRESHOLD=3.5`
3. Review monitoring: Check Prometheus for false positives
4. Notify team and pause non-critical alerts

## Escalation Contacts
- Primary On-Call: DevOps Team
- Secondary: ML/AI Team (for AI engine issues)
- Database: DBA Team (for PostgreSQL issues)

