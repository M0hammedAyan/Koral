# KORAL activeContext.md
Last Updated: 2026-06-30
Last Agent Session: 2026-06-30

## Current Phase
Phase 1 — DETECTION ENGINE

## Last Completed Task
1.2 RRCF unit tests passing (12/12 tests, including <5ms performance gate)

## Completed in This Session
- 0.1 VictoriaMetrics client created (`koral/ingestion/victoria_client.py`)
- 0.2 Cardinality guard created and tested (11 tests passing)
- 0.3 Alembic migrations run on koral-postgres (6 new tables created)
- 0.4 Falco deployment config created (`deploy/falco/falco-values.yaml`)
- 1.1 RRCF Streaming Detector implemented (`koral/detection/rrcf_detector.py`)
- 1.2 RRCF unit tests written and passing (12 tests)

## Last Known State
- VictoriaMetrics: client implemented, NOT yet deployed/connected
- Falco: config written, NOT yet deployed on minikube
- RRCF: ✅ IMPLEMENTED, 12 tests passing, <5ms per detection
- STL+IF: NOT implemented (Phase 1.3-1.5 next)
- Classifier: NOT implemented (Phase 2)
- Port shift: NOT implemented (Phase 4)
- Alerting: NOT wired (Phase 5)
- Real data: NOT available
- LSTM: NOT started (Phase 8)

## Blocking Issues
- Phase 0.1 needs a running K8s cluster or Docker Compose with VictoriaMetrics to validate remote_write connection
- Phase 0.4 needs a cluster to deploy Falco DaemonSet
- Phase 0.5 needs Falco deployed to test the Falcosidekick → AlertManager pipeline

## Next Task
1.3 Implement STLDecomposer (stl_preprocessor.py)
1.4 Implement STLIFDetector (stl_if_detector.py — wraps existing IsolationForest)
1.5 Unit tests for STL+IF

## Do Not Touch
- `correlation-engine/ai_core/anomaly.py` — existing IsolationForest, working
- `backend/` — existing API, 84 tests passing
- `helm/koral/` — existing Helm chart, lint passing
- `tests/test_backend_integration.py` — existing integration tests
