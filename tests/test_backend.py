from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app

client = TestClient(app)

SAMPLE_ANOMALY = {
    "timestamp": 1710000000,
    "pod": "pod-A",
    "metric": "cpu",
    "value": 85.2,
    "z_score": 3.1,
    "is_anomaly": True,
}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@patch("backend.routes.anomalies.process_anomaly", new_callable=AsyncMock)
def test_post_anomaly(mock_process):
    mock_process.return_value = None
    r = client.post("/anomalies", json=SAMPLE_ANOMALY)
    assert r.status_code == 202
    assert r.json()["status"] == "accepted"
    mock_process.assert_called_once()


def test_get_anomalies_empty():
    r = client.get("/anomalies")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_incidents_empty():
    r = client.get("/incidents")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_graph_structure():
    r = client.get("/graph")
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body
    assert "edges" in body


def test_get_correlations_empty():
    r = client.get("/correlations")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_post_feedback_valid():
    r = client.post("/feedback", json={
        "incident_id": "INC-TEST",
        "metric": "cpu",
        "is_correct": False
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("applied", "feedback_loop_unavailable")


def test_post_anomaly_invalid_payload():
    r = client.post("/anomalies", json={"bad": "data"})
    assert r.status_code == 422
