from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.processor import correlations

router = APIRouter()


@router.get("/correlations")
def list_correlations(limit: int = 100):
    return correlations[-limit:]
