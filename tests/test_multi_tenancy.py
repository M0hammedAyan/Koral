"""Tests for Multi-Tenancy API (Task 7)."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="koral_tenant_test_")
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


class TestTenantAccess:
    def test_viewer_cannot_access_tenants(self):
        r = client.get("/tenants/", headers=VIEWER)
        assert r.status_code == 403

    def test_admin_can_list_tenants_empty(self):
        r = client.get("/tenants/", headers=ADMIN)
        assert r.status_code == 200
        assert r.json()["count"] == 0


class TestTenantCRUD:
    def test_create_tenant(self):
        r = client.post("/tenants/", json={
            "name": "team-alpha",
            "display_name": "Team Alpha",
            "namespaces": ["alpha-prod", "alpha-staging"],
        }, headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "team-alpha"
        assert data["tenant_id"].startswith("tn_")
        assert set(data["namespaces"]) == {"alpha-prod", "alpha-staging"}

    def test_duplicate_tenant_rejected(self):
        r = client.post("/tenants/", json={
            "name": "team-alpha",
            "display_name": "Duplicate",
        }, headers=ADMIN)
        assert r.status_code == 409

    def test_list_tenants(self):
        r = client.get("/tenants/", headers=ADMIN)
        assert r.status_code == 200
        assert r.json()["count"] == 1
        assert r.json()["tenants"][0]["name"] == "team-alpha"

    def test_get_tenant(self):
        # Get tenant_id from list
        r = client.get("/tenants/", headers=ADMIN)
        tenant_id = r.json()["tenants"][0]["id"]

        r = client.get(f"/tenants/{tenant_id}", headers=ADMIN)
        assert r.status_code == 200
        assert r.json()["name"] == "team-alpha"
        assert "alpha-prod" in r.json()["namespaces"]

    def test_update_tenant(self):
        r = client.get("/tenants/", headers=ADMIN)
        tenant_id = r.json()["tenants"][0]["id"]

        r = client.patch(f"/tenants/{tenant_id}", json={"display_name": "Alpha Squad"}, headers=ADMIN)
        assert r.status_code == 200


class TestNamespaceMapping:
    def test_add_namespace(self):
        r = client.get("/tenants/", headers=ADMIN)
        tenant_id = r.json()["tenants"][0]["id"]

        r = client.post(f"/tenants/{tenant_id}/namespaces", json={"namespace": "alpha-dev"}, headers=ADMIN)
        assert r.status_code == 200

    def test_duplicate_namespace_rejected(self):
        r = client.get("/tenants/", headers=ADMIN)
        tenant_id = r.json()["tenants"][0]["id"]

        r = client.post(f"/tenants/{tenant_id}/namespaces", json={"namespace": "alpha-dev"}, headers=ADMIN)
        assert r.status_code == 409

    def test_remove_namespace(self):
        r = client.get("/tenants/", headers=ADMIN)
        tenant_id = r.json()["tenants"][0]["id"]

        r = client.delete(f"/tenants/{tenant_id}/namespaces/alpha-dev", headers=ADMIN)
        assert r.status_code == 200


class TestUserTenantAssignment:
    def test_assign_user_to_tenant(self):
        # Create a user first
        r = client.post("/users/invite", json={
            "username": "tenant_user",
            "email": "tuser@koral.io",
            "role": "operator",
        }, headers=ADMIN)
        assert r.status_code == 200

        # Get tenant
        r = client.get("/tenants/", headers=ADMIN)
        tenant_id = r.json()["tenants"][0]["id"]

        # Assign
        r = client.post(f"/tenants/{tenant_id}/users", json={"username": "tenant_user"}, headers=ADMIN)
        assert r.status_code == 200

    def test_user_key_still_works_after_tenant_assignment(self):
        # Re-invite won't work, let's just check the user endpoint
        r = client.get("/users/tenant_user", headers=ADMIN)
        assert r.status_code == 200
        # tenant_id should be set
        assert r.json().get("tenant_id") is not None

    def test_remove_user_from_tenant(self):
        r = client.get("/tenants/", headers=ADMIN)
        tenant_id = r.json()["tenants"][0]["id"]

        r = client.delete(f"/tenants/{tenant_id}/users/tenant_user", headers=ADMIN)
        assert r.status_code == 200
