# KORAL Reprioritized Roadmap

## Why Reprioritized
Priority is shifted to reliability and operability first so existing production-ready security and deployment work can be safely operated at scale.

## New Order
1. **Phase 3: Database Backup Automation** (now)
2. **Phase 4: Observability and Alerting** (immediately after Phase 3)
3. **Phase 7: Operational Readiness** (moved up before scale changes)
4. **Phase 5: Scalability and Performance**
5. **Phase 6: Testing and Quality Assurance**
6. **Phase 8: Architecture Refactor**

## Rationale
- Backups and restores are critical-path for data loss prevention.
- Observability and on-call runbooks must exist before aggressive scaling or architecture changes.
- Performance tuning without mature telemetry creates blind spots and rollback risk.
- Final architecture refactor should be done after runtime behavior is visible and validated.

## Milestone Targets
- **M1 (48 hours):** Phase 3 manifests deployed, first successful full backup and restore verification.
- **M2 (96 hours):** Phase 4 dashboards and alerts active; alert routing to Slack/PagerDuty validated.
- **M3 (1 week):** Phase 7 runbooks and DR drills complete; on-call readiness confirmed.
- **M4 (2 weeks):** Phase 5 autoscaling policies tuned under load profiles.
- **M5 (2.5 weeks):** Phase 6 E2E/load/security tests integrated into CI.
- **M6 (3 weeks):** Phase 8 refactor merged with zero regression gates.

## Exit Criteria by Phase
- **Phase 3:** Full/diff backup SLO >= 99%, restore verification daily pass.
- **Phase 4:** MTTD under 5 minutes for critical incidents.
- **Phase 7:** MTTR playbooks tested in tabletop and live drill.
- **Phase 5:** P95 API latency under 200ms at planned RPS.
- **Phase 6:** No high-severity vulnerabilities, all E2E gates green.
- **Phase 8:** Dependency map reduced and service boundaries documented.
