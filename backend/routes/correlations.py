from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.services.processor import correlations
from backend.rbac import require_viewer

router = APIRouter()


@router.get("/correlations", dependencies=[Depends(require_viewer)])
def list_correlations(limit: int = 100):
    return correlations[-limit:]
