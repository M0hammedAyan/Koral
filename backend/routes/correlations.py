from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.services.processor import correlations
from backend.auth import validate_api_key

router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.get("/correlations")
def list_correlations(limit: int = 100):
    return correlations[-limit:]
