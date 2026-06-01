from fastapi import APIRouter, HTTPException, Depends
from backend.services.processor import incidents
from backend.auth import validate_api_key
from backend.audit import write_audit
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.get("/incidents")
def list_incidents(limit: int = 50):
    """Get recent incidents"""
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit must be positive")
    if limit > 500:
        limit = 500  # Cap at 500 for performance
    
    result = incidents[-limit:]
    logger.info(f"Returning {len(result)} incidents (limit={limit})")
    return result
