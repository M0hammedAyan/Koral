"""Tests for WebSocket RBAC — role-aware connection validation (Task 5)."""
import os
import tempfile
import json
import pytest
from starlette.websockets import WebSocketDisconnect
from fastapi.testclient import TestClient

_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="koral_ws_test_")
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


class TestWebSocketAuth:
    def test_no_key_rejected(self):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/live") as ws:
                ws.send_text("ping")

    def test_invalid_key_rejected(self):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/live?api_key=bad-key") as ws:
                ws.send_text("ping")

    def test_viewer_key_connects(self):
        with client.websocket_connect("/ws/live?api_key=test-viewer-key") as ws:
            ws.send_text("ping")

    def test_operator_key_connects(self):
        with client.websocket_connect("/ws/live?api_key=test-operator-key") as ws:
            ws.send_text("ping")

    def test_admin_key_connects(self):
        with client.websocket_connect("/ws/live?api_key=test-admin-key") as ws:
            ws.send_text("ping")

    def test_legacy_key_connects(self):
        with client.websocket_connect("/ws/live?api_key=test-api-key") as ws:
            ws.send_text("ping")


class TestWebSocketUserKey:
    def test_user_managed_key_connects(self):
        # Create a user first
        r = client.post("/users/invite", json={
            "username": "wsuser",
            "email": "wsuser@koral.io",
            "role": "viewer",
        }, headers=ADMIN)
        assert r.status_code == 200
        user_key = r.json()["api_key"]

        # Connect with user-managed key
        with client.websocket_connect(f"/ws/live?api_key={user_key}") as ws:
            ws.send_text("ping")

    def test_deactivated_user_key_rejected(self):
        # Create and deactivate a user
        r = client.post("/users/invite", json={
            "username": "wsdeactivated",
            "email": "wsdeact@koral.io",
            "role": "operator",
        }, headers=ADMIN)
        deact_key = r.json()["api_key"]

        # Deactivate
        r = client.delete("/users/wsdeactivated", headers=ADMIN)
        assert r.status_code == 200

        # Connection should be rejected
        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/live?api_key={deact_key}") as ws:
                ws.send_text("ping")


class TestWebSocketSubscriptions:
    def test_subscribe_to_channel(self):
        with client.websocket_connect("/ws/live?api_key=test-admin-key") as ws:
            ws.send_text(json.dumps({"type": "subscribe", "channel": "remediation"}))
            ws.send_text(json.dumps({"type": "unsubscribe", "channel": "remediation"}))
            # Non-JSON is silently ignored
            ws.send_text("not json")
