import os
import httpx
from fastapi import APIRouter, Depends
from backend.rbac import require_viewer, require_operator

router = APIRouter()
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8006")


@router.get("/ai/activity", dependencies=[Depends(require_viewer)])
async def get_ai_activity(limit: int = 50):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{AI_ENGINE_URL}/activity?limit={limit}")
            return r.json()
    except Exception:
        return []


@router.post("/ai/chat", dependencies=[Depends(require_operator)])
async def ai_chat(body: dict):
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.post(f"{AI_ENGINE_URL}/chat", json=body)
            return r.json()
    except Exception as e:
        return {"response": f"AI engine unavailable: {e}", "model": "none"}


@router.get("/ai/health", dependencies=[Depends(require_viewer)])
async def ai_health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{AI_ENGINE_URL}/health")
            return r.json()
    except Exception:
        return {"status": "unreachable"}
