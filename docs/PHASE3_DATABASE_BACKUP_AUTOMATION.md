# KORAL Phase 3: Database Backup Automation

## Overview
Phase 3 implements backup automation, restore verification, and connection pooling to improve data durability and operational resilience.

## Deliverables
- `infra/manifests/database/pgbackrest-config.yaml`
- `infra/manifests/database/pgbackrest-backup-cronjobs.yaml`
- `infra/manifests/database/pgbackrest-restore-verify.yaml`
- `infra/manifests/database/pgbouncer.yaml`
- `infra/manifests/database/kustomization.yaml`
- `infra/monitoring/alerts/backup-alert-rules.yaml`
- `infra/aws/s3-backup-lifecycle-policy.json`
- `infra/images/postgres-backup/Dockerfile`
- `scripts/deploy-phase3-database.sh`

## Backup Policy
- Full backup: daily at `02:00` UTC
- Differential backup: every 2 hours
- Restore verification: daily at `03:30` UTC
- Backup metadata/info export: every 4 hours

## Retention and Storage
- S3 repository path prefix: `koral-backups/`
- Full backup retention: 14
- Differential backup retention: 7
- S3 transitions:
  - Day 30 -> STANDARD_IA
  - Day 90 -> GLACIER
  - Day 365 -> object expiration

## PgBouncer Policy
- Pool mode: `transaction`
- Max client connections: `500`
- Default pool size: `25`
- Reserve pool size: `5`

## Kubernetes Deployment Instructions (Current State)

1. Ensure the cluster context is correct:
```bash
kubectl cluster-info
kubectl config current-context
```

2. Deploy base platform (Phase 1):
```bash
kubectl apply -k infra/manifests/base
kubectl apply -k infra/manifests/overlays/production
```

3. Deploy security (Phase 2):
```bash
bash scripts/deploy-phase2-security.sh
```

4. Deploy database resilience (Phase 3):
```bash
bash scripts/deploy-phase3-database.sh
```

5. Apply backup alert rules:
```bash
kubectl apply -f infra/monitoring/alerts/backup-alert-rules.yaml
```

6. Verify health and backup resources:
```bash
kubectl -n koral-system get deploy,svc,cronjob,pods
kubectl -n koral-system get cronjobs | grep pgbackrest
kubectl -n koral-system get deployment pgbouncer
```

7. Trigger manual full backup test:
```bash
kubectl -n koral-system create job --from=cronjob/pgbackrest-full-backup pgbackrest-full-backup-manual
kubectl -n koral-system logs -f job/pgbackrest-full-backup-manual
```

8. Trigger manual restore verification test:
```bash
kubectl -n koral-system create job --from=cronjob/pgbackrest-restore-verify pgbackrest-restore-verify-manual
kubectl -n koral-system logs -f job/pgbackrest-restore-verify-manual
```

## Required Placeholder Updates Before Production
1. Update `pgbackrest-s3-credentials` in `infra/manifests/database/pgbackrest-config.yaml`
2. Replace `repo1-s3-bucket` with your backup bucket name
3. Ensure `postgres-pvc` matches your actual database PVC claim
4. Replace `REPLACE_WITH_MD5_HASH` in `infra/manifests/database/pgbouncer.yaml`
5. Build and publish backup image from `infra/images/postgres-backup/Dockerfile`

## Rollback
```bash
kubectl delete -k infra/manifests/database
kubectl delete -f infra/monitoring/alerts/backup-alert-rules.yaml
```

## Success Criteria
- Full and differential backup jobs succeed repeatedly.
- Restore verification job succeeds daily.
- PgBouncer deployment has 2/2 ready replicas.
- Backup alert rules are loaded in Prometheus.

