from fastapi import APIRouter, Depends
from backend.services.processor import graph_data
from backend.rbac import require_viewer

router = APIRouter()


@router.get("/graph", dependencies=[Depends(require_viewer)])
def get_graph():
    return graph_data
