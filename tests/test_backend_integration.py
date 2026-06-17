"""Integration tests for KORAL backend routes."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Use a real temp file so all sqlite3.connect() calls share one DB.
# :memory: opens a fresh empty database per connection, breaking init_db().
_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="koral_test_")
os.close(_db_fd)

os.environ["API_KEY"]          = "test-api-key"
os.environ["API_KEY_ADMIN"]    = "test-admin-key"
os.environ["API_KEY_OPERATOR"] = "test-operator-key"
os.environ["API_KEY_VIEWER"]   = "test-viewer-key"
os.environ["JWT_SECRET"]       = "test-jwt-secret"
os.environ["DB_TYPE"]          = "sqlite"
os.environ["DB_PATH"]          = _db_path
os.environ["DISABLE_AUTH"]     = "false"
os.environ["REMEDIATION_ENABLED"] = "true"

# Explicitly init schema — TestClient doesn't guarantee lifespan fires before first test
from backend.database import init_db as _init_db
_init_db()

from backend.main import app

client = TestClient(app, raise_server_exceptions=False)
ADMIN    = {"X-API-Key": "test-admin-key"}
OPERATOR = {"X-API-Key": "test-operator-key"}
VIEWER   = {"X-API-Key": "test-viewer-key"}
BAD_AUTH = {"X-API-Key": "wrong-key"}
# Legacy key gets operator-level access
AUTH     = {"X-API-Key": "test-api-key"}


# ── Auth ──────────────────────────────────────────────────────────

def test_missing_api_key_returns_401():
    r = client.get("/anomalies")
    assert r.status_code == 401


def test_invalid_api_key_returns_401():
    r = client.get("/anomalies", headers=BAD_AUTH)
    assert r.status_code == 401


def test_valid_api_key_returns_200():
    r = client.get("/anomalies", headers=VIEWER)
    assert r.status_code == 200


def test_health_requires_no_auth():
    r = client.get("/health/live")
    assert r.status_code == 200


def test_metrics_requires_no_auth():
    r = client.get("/metrics")
    assert r.status_code == 200


# ── RBAC ──────────────────────────────────────────────────────────

def test_viewer_cannot_post_anomaly():
    payload = {
        "timestamp": 1700000001, "pod": "x", "metric": "cpu",
        "value": 1.0, "z_score": 1.0, "is_anomaly": False,
        "namespace": "koral-system", "unit": "percent",
        "source": "test", "window_size": 300,
    }
    r = client.post("/anomalies", json=payload, headers=VIEWER)
    assert r.status_code == 403


def test_operator_can_post_anomaly():
    payload = {
        "timestamp": 1700000002, "pod": "op-pod", "metric": "cpu",
        "value": 50.0, "z_score": 2.0, "is_anomaly": True,
        "namespace": "koral-system", "unit": "percent",
        "source": "test", "window_size": 300,
    }
    r = client.post("/anomalies", json=payload, headers=OPERATOR)
    assert r.status_code == 202


def test_viewer_cannot_access_audit():
    r = client.get("/audit", headers=VIEWER)
    assert r.status_code == 403


def test_operator_cannot_access_audit():
    r = client.get("/audit", headers=OPERATOR)
    assert r.status_code == 403


def test_admin_can_access_audit():
    r = client.get("/audit", headers=ADMIN)
    assert r.status_code == 200


def test_viewer_cannot_execute_remediation():
    r = client.post("/remediation/execute/some-plan", headers=VIEWER, params={"approval_id": "x"})
    assert r.status_code == 403


def test_operator_cannot_execute_remediation():
    r = client.post("/remediation/execute/some-plan", headers=OPERATOR, params={"approval_id": "x"})
    assert r.status_code == 403


def test_viewer_can_read_remediation_status():
    r = client.get("/remediation/status", headers=VIEWER)
    assert r.status_code == 200


# ── Anomalies ─────────────────────────────────────────────────────

def test_post_anomaly_valid():
    payload = {
        "timestamp": 1700000000,
        "pod": "test-pod-abc",
        "metric": "cpu",
        "value": 85.5,
        "z_score": 3.2,
        "is_anomaly": True,
        "namespace": "koral-system",
        "unit": "percent",
        "source": "cpu-agent",
        "window_size": 300,
    }
    r = client.post("/anomalies", json=payload, headers=AUTH)
    assert r.status_code == 202
    assert r.json()["status"] == "accepted"


def test_post_anomaly_missing_field_returns_422():
    r = client.post("/anomalies", json={"pod": "x"}, headers=AUTH)
    assert r.status_code == 422


def test_list_anomalies_limit_cap():
    r = client.get("/anomalies?limit=9999", headers=AUTH)
    assert r.status_code == 200


def test_list_anomalies_invalid_limit():
    r = client.get("/anomalies?limit=0", headers=AUTH)
    assert r.status_code == 400


# ── Incidents ─────────────────────────────────────────────────────

def test_list_incidents():
    r = client.get("/incidents", headers=AUTH)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_incidents_invalid_limit():
    r = client.get("/incidents?limit=-1", headers=AUTH)
    assert r.status_code == 400


# ── Audit ─────────────────────────────────────────────────────────

def test_audit_log_accessible():
    r = client.get("/audit", headers=ADMIN)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_audit_filter_by_event_type():
    r = client.get("/audit?event_type=auth.login", headers=ADMIN)
    assert r.status_code == 200


# ── Fixes ─────────────────────────────────────────────────────────

def test_record_fix():
    payload = {
        "incident_id": "inc-test-001",
        "fix_type": "restart",
        "fix_description": "Restarted pod",
        "applied_by": "AI",
        "success": True,
        "kubectl_command": "kubectl rollout restart deployment/test",
        "error_message": "",
    }
    r = client.post("/fixes/record", json=payload, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["status"] == "recorded"


def test_fix_history_returns_list():
    r = client.get("/fixes/history", headers=AUTH)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_fix_stats_structure():
    r = client.get("/fixes/stats", headers=AUTH)
    assert r.status_code == 200
    data = r.json()
    assert "total_fixes" in data
    assert "success_rate" in data


def test_fix_by_incident():
    r = client.get("/fixes/by-incident/inc-test-001", headers=AUTH)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Correlations / Graph ──────────────────────────────────────────

def test_correlations_returns_list():
    r = client.get("/correlations", headers=AUTH)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_graph_returns_dict():
    r = client.get("/graph", headers=AUTH)
    assert r.status_code == 200


# ── SLO ──────────────────────────────────────────────────────────

def test_slo_summary():
    r = client.get("/slo/", headers=AUTH)
    assert r.status_code == 200
    data = r.json()
    assert "availability_percent" in data
    assert "error_budget" in data


def test_slo_availability():
    r = client.get("/slo/availability", headers=AUTH)
    assert r.status_code == 200
    assert "availability_percent" in r.json()


def test_slo_mttr():
    r = client.get("/slo/mttr", headers=AUTH)
    assert r.status_code == 200
    assert "mttr_seconds" in r.json()


def test_slo_remediation_success():
    r = client.get("/slo/remediation-success", headers=AUTH)
    assert r.status_code == 200
    assert "remediation_success_rate" in r.json()


def test_slo_error_budget():
    r = client.get("/slo/error-budget", headers=AUTH)
    assert r.status_code == 200
    assert "error_budget_remaining_percent" in r.json()


# ── Remediation ───────────────────────────────────────────────────

def test_remediation_status():
    r = client.get("/remediation/status", headers=AUTH)
    assert r.status_code == 200
    data = r.json()
    assert "enabled" in data
    assert "plan_count" in data


def test_remediation_list_plans_empty():
    r = client.get("/remediation/plans", headers=AUTH)
    assert r.status_code == 200
    assert "plans" in r.json()


def test_remediation_plan_not_found():
    r = client.get("/remediation/plans/nonexistent-plan-id", headers=AUTH)
    assert r.status_code == 404


def test_remediation_approve_not_found():
    r = client.post("/remediation/approve/nonexistent-plan-id", headers=AUTH)
    assert r.status_code == 404


def test_remediation_executions_empty():
    r = client.get("/remediation/executions", headers=AUTH)
    assert r.status_code == 200
    assert "executions" in r.json()


def test_remediation_approvals_list():
    r = client.get("/remediation/approvals", headers=AUTH)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── AI endpoints ──────────────────────────────────────────────────

def test_ai_health_graceful():
    r = client.get("/ai/health", headers=AUTH)
    assert r.status_code == 200


def test_ai_activity_graceful():
    r = client.get("/ai/activity", headers=AUTH)
    assert r.status_code == 200
