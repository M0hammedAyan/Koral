"""Tests for the User Management API (Task 4)."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="koral_users_test_")
os.close(_db_fd)

os.environ["API_KEY"] = "test-api-key"
os.environ["API_KEY_ADMIN"] = "test-admin-key"
os.environ["API_KEY_OPERATOR"] = "test-operator-key"
os.environ["API_KEY_VIEWER"] = "test-viewer-key"
os.environ["JWT_SECRET"] = "test-jwt-secret"
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_PATH"] = _db_path
os.environ["DISABLE_AUTH"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["REMEDIATION_ENABLED"] = "true"

from backend.database import init_db as _init_db
_init_db()

from backend.main import app

client = TestClient(app, raise_server_exceptions=False)
ADMIN = {"X-API-Key": "test-admin-key"}
VIEWER = {"X-API-Key": "test-viewer-key"}


class TestUserAccess:
    def test_viewer_cannot_access_users(self):
        r = client.get("/users/", headers=VIEWER)
        assert r.status_code == 403

    def test_admin_can_list_users_empty(self):
        r = client.get("/users/", headers=ADMIN)
        assert r.status_code == 200
        assert "users" in r.json()
        assert "count" in r.json()


class TestUserInvite:
    def test_invite_user(self):
        r = client.post("/users/invite", json={
            "username": "alice",
            "email": "alice@koral.io",
            "role": "operator",
        }, headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "alice"
        assert data["api_key"].startswith("koral_")
        assert data["role"] == "operator"

    def test_duplicate_username_rejected(self):
        r = client.post("/users/invite", json={
            "username": "alice",
            "email": "alice2@koral.io",
            "role": "viewer",
        }, headers=ADMIN)
        assert r.status_code == 409

    def test_duplicate_email_rejected(self):
        r = client.post("/users/invite", json={
            "username": "alice2",
            "email": "alice@koral.io",
            "role": "viewer",
        }, headers=ADMIN)
        assert r.status_code == 409

    def test_invalid_role_rejected(self):
        r = client.post("/users/invite", json={
            "username": "baduser",
            "email": "bad@koral.io",
            "role": "superadmin",
        }, headers=ADMIN)
        assert r.status_code == 422


class TestUserKeyAuth:
    def test_user_key_authenticates(self):
        # Invite bob as viewer
        r = client.post("/users/invite", json={
            "username": "bob",
            "email": "bob@koral.io",
            "role": "viewer",
        }, headers=ADMIN)
        assert r.status_code == 200
        bob_key = r.json()["api_key"]

        # Bob can read anomalies (viewer)
        r = client.get("/anomalies", headers={"X-API-Key": bob_key})
        assert r.status_code == 200

    def test_user_key_respects_role(self):
        # Invite carol as viewer
        r = client.post("/users/invite", json={
            "username": "carol",
            "email": "carol@koral.io",
            "role": "viewer",
        }, headers=ADMIN)
        carol_key = r.json()["api_key"]

        # Carol cannot post anomalies (requires operator)
        payload = {
            "timestamp": 1700000099, "pod": "p", "metric": "cpu",
            "value": 50.0, "z_score": 1.0, "is_anomaly": False,
            "namespace": "ns", "unit": "%", "source": "test", "window_size": 300,
        }
        r = client.post("/anomalies", json=payload, headers={"X-API-Key": carol_key})
        assert r.status_code == 403


class TestKeyRotation:
    def test_rotate_key(self):
        # Invite dave
        r = client.post("/users/invite", json={
            "username": "dave",
            "email": "dave@koral.io",
            "role": "operator",
        }, headers=ADMIN)
        old_key = r.json()["api_key"]

        # Rotate
        r = client.post("/users/dave/rotate-key", json={"reason": "test"}, headers=ADMIN)
        assert r.status_code == 200
        new_key = r.json()["api_key"]
        assert new_key != old_key

        # Old key rejected
        r = client.get("/anomalies", headers={"X-API-Key": old_key})
        assert r.status_code == 401

        # New key works
        r = client.get("/anomalies", headers={"X-API-Key": new_key})
        assert r.status_code == 200

    def test_rotate_nonexistent_user(self):
        r = client.post("/users/nobody/rotate-key", json={}, headers=ADMIN)
        assert r.status_code == 404


class TestUserDeactivation:
    def test_deactivate_user(self):
        # Invite eve
        r = client.post("/users/invite", json={
            "username": "eve",
            "email": "eve@koral.io",
            "role": "operator",
        }, headers=ADMIN)
        eve_key = r.json()["api_key"]

        # Deactivate
        r = client.delete("/users/eve", headers=ADMIN)
        assert r.status_code == 200

        # Key no longer works
        r = client.get("/anomalies", headers={"X-API-Key": eve_key})
        assert r.status_code == 401

    def test_cannot_rotate_deactivated_user(self):
        r = client.post("/users/eve/rotate-key", json={}, headers=ADMIN)
        assert r.status_code == 400


class TestPerUserAudit:
    def test_user_audit_log(self):
        r = client.get("/users/alice/audit", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "alice"
        assert data["count"] > 0
        # Should have at least the invite event
        events = [e["event_type"] for e in data["audit_entries"]]
        assert "user.invited" in events

    def test_audit_filter_by_event_type(self):
        r = client.get("/users/alice/audit?event_type=user.invited", headers=ADMIN)
        assert r.status_code == 200
        for entry in r.json()["audit_entries"]:
            assert entry["event_type"] == "user.invited"

    def test_nonexistent_user_audit_404(self):
        r = client.get("/users/nobody/audit", headers=ADMIN)
        assert r.status_code == 404


class TestUserUpdate:
    def test_update_role(self):
        r = client.patch("/users/bob", json={"role": "operator"}, headers=ADMIN)
        assert r.status_code == 200

        r = client.get("/users/bob", headers=ADMIN)
        assert r.json()["role"] == "operator"

    def test_update_nonexistent(self):
        r = client.patch("/users/nobody", json={"role": "admin"}, headers=ADMIN)
        assert r.status_code == 404
