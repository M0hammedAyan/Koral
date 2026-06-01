from fastapi import APIRouter, Depends
from backend.services.processor import graph_data
from backend.auth import validate_api_key

router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.get("/graph")
def get_graph():
    return graph_data
