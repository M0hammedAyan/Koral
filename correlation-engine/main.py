import uuid
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="KORAL Correlation Engine (stub)", version="1.0.0")


class AnomalyIn(BaseModel):
    timestamp: int
    pod: str
    metric: str
    value: float
    z_score: float
    is_anomaly: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/correlate")
def correlate(anomaly: AnomalyIn):
    """
    Stub correlation engine.
    Returns a minimal valid incident so the full pipeline works end-to-end.
    Member 1 replaces this with real Pearson correlation + rule-based root cause.
    """
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    return {
        "incident_id": incident_id,
        "root_cause": f"{anomaly.metric} anomaly detected on {anomaly.pod} (z={anomaly.z_score})",
        "root_cause_pod": anomaly.pod,
        "confidence": round(min(abs(anomaly.z_score) / 5.0, 1.0), 2),
        "affected_pods": [anomaly.pod],
        "correlation": anomaly.z_score,
        "pod_A": anomaly.pod,
        "pod_B": anomaly.pod,
        "metric": anomaly.metric,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
