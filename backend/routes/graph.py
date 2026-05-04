from fastapi import APIRouter
from backend.services.processor import graph_data

router = APIRouter()


@router.get("/graph")
def get_graph():
    return graph_data
