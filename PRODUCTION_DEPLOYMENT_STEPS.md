Production deployment checklist — KORAL

1. Configure secrets
   - Create Kubernetes Secret `koral-secrets` with `DB_PASS`, `API_KEY`, `JWT_SECRET`, `SMTP_PASS`, etc.
   - Locally, copy `.env.example` to `.env` and set values.

2. Database
   - Use Postgres (StatefulSet) in k8s or managed Postgres in production.
   - Ensure PVCs and backups are configured.

3. Build images
   - From project root run:
     docker compose -f docker-compose-prod.yml build --no-cache

4. Start services (local)
   - docker compose -f docker-compose-prod.yml up -d
   - Verify with `docker compose -f docker-compose-prod.yml ps` and logs.

5. Monitoring
   - Prometheus is included in `docker-compose-prod.yml` and `prometheus.yml`.
   - Ensure services expose `/metrics` (backend, ai-engine, correlation-engine).

6. Security
   - Do NOT use `ALLOWED_ORIGINS="*"` in production.
   - Use secure `JWT_SECRET` and rotate keys regularly.
   - Move secrets to K8s Secrets when deploying to cluster.

7. Tests & Smoke checks
   - Run `python -m pytest -q` locally before deploying.
   - Check AI engine connectivity (POST /analyze) and backend DB writes.

8. K8s deployment
   - Apply manifests in `k8s/` after updating image tags and secrets.
   - Run `kubectl rollout status` on deployments and check readiness/liveness.

9. Post-deploy
   - Verify Prometheus targets and alerting rules.
   - Configure log aggregation and alert channels (Slack/email).

10. Rollback plan
   - Keep previous image tags and DB backups available.
