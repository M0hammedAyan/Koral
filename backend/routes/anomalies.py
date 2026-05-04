from fastapi import APIRouter
from pydantic import BaseModel
from backend.websocket.manager import manager
from backend.services.processor import process_anomaly, anomalies

router = APIRouter()


class AnomalyPayload(BaseModel):
    timestamp: int
    pod: str
    metric: str
    value: float
    z_score: float
    is_anomaly: bool


@router.post("/anomalies", status_code=202)
async def receive_anomaly(payload: AnomalyPayload):
    await process_anomaly(payload.model_dump(), manager.broadcast)
    return {"status": "accepted"}


@router.get("/anomalies")
def list_anomalies(limit: int = 100):
    return anomalies[-limit:]
