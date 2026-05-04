from fastapi import APIRouter
from backend.services.processor import incidents

router = APIRouter()


@router.get("/incidents")
def list_incidents(limit: int = 50):
    return incidents[-limit:]
