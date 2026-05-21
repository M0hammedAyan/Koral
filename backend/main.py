from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.responses import JSONResponse
import signal
import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
try:
    import prometheus_client
    from prometheus_client import Counter, CONTENT_TYPE_LATEST
    PROM_AVAILABLE = True
except Exception:
    PROM_AVAILABLE = False
    class _DummyCounter:
        def __init__(self, *a, **k):
            pass
        def inc(self):
            pass
    Counter = _DummyCounter
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    class _DummyProm:
        @staticmethod
        def generate_latest():
            return b""
    prometheus_client = _DummyProm()
from contextlib import asynccontextmanager
from backend.routes.anomalies import router as anomalies_router
from backend.routes.incidents import router as incidents_router
from backend.routes.graph import router as graph_router
from backend.routes.correlations import router as correlations_router
from backend.routes.feedback import router as feedback_router
from backend.routes.ai import router as ai_router
from backend.routes.fixes import router as fixes_router
from backend.routes.remediation import router as remediation_router
from backend.websocket.manager import manager
from backend.auth import get_allowed_origins, validate_api_key
from backend.database import init_db, close_db_pool, query_one
from backend.database_remediation import init_remediation_db
import logging
import sys
import time
from collections import defaultdict
from typing import Dict, Tuple
import httpx
from backend.middleware import RequestIDMiddleware, ErrorResponseMiddleware
from backend.errors import standard_response
from backend.resilience import CircuitBreaker, call_with_circuit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

_ip_requests: Dict[Tuple[str, int], list[float]] = defaultdict(list)
_key_requests: Dict[Tuple[str, int], list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_IP = 100
RATE_LIMIT_API_KEY = 500


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KORAL Backend starting up...")
    try:
        init_db()
        logger.info("Database initialized and loaded")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
    # Non-breaking: initialize remediation tables (no effect unless remediation enabled)
    try:
        init_remediation_db()
        logger.info("Remediation tables initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize remediation tables: {e}")
    logger.info("All routes registered")
    logger.info("Backend ready to accept connections")
    yield
    await manager.close_all()
    close_db_pool()
    logger.info("KORAL Backend shutting down...")


app = FastAPI(
    title="KORAL Backend",
    # graceful shutdown handling
    shutdown_event = asyncio.Event()

    def _on_signal():
        logger.info("SIGTERM received, initiating graceful shutdown")
        shutdown_event.set()

    if hasattr(signal, "SIGTERM"):
        loop = asyncio.get_event_loop()
        try:
            loop.add_signal_handler(signal.SIGTERM, _on_signal)
        except Exception:
            # not all platforms support add_signal_handler
            pass

    try:
        yield
        # wait for external shutdown event if set (timeout window)
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=int(__import__("os").environ.get("SHUTDOWN_TIMEOUT", "30")))
        except asyncio.TimeoutError:
            pass
    finally:
        await manager.close_all()
        close_db_pool()
        logger.info("KORAL Backend shutting down...")
)

# Prometheus metrics
REQUEST_COUNT = Counter('koral_backend_requests_total', 'Total HTTP requests to KORAL backend')


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        REQUEST_COUNT.inc()
        return await call_next(request)


app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(ErrorResponseMiddleware)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path in {"/health", "/health/live", "/health/ready", "/metrics", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        now = time.time()
        window = int(now // RATE_LIMIT_WINDOW)
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")

        def _allow(bucket: Dict[Tuple[str, int], list[float]], key: str, limit: int) -> bool:
            entries = bucket[(key, window)]
            entries[:] = [ts for ts in entries if now - ts < RATE_LIMIT_WINDOW]
            if len(entries) >= limit:
                return False
            entries.append(now)
            return True

        if not _allow(_ip_requests, client_ip, RATE_LIMIT_IP):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        if api_key and not _allow(_key_requests, api_key, RATE_LIMIT_API_KEY):
            return JSONResponse({"detail": "API key rate limit exceeded"}, status_code=429)

        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    allow_credentials=True,
)

app.include_router(anomalies_router)
app.include_router(incidents_router)
app.include_router(graph_router)
app.include_router(correlations_router)
app.include_router(feedback_router)
app.include_router(ai_router)
app.include_router(fixes_router)
app.include_router(remediation_router)


@app.get("/health/live")
def health_live():
    return {"status": "ok", "live": True, "service": "koral-backend"}


@app.get("/health/ready")
async def health_ready():
    try:
        query_one("SELECT 1")
        async with httpx.AsyncClient(timeout=2) as client:
            ai_response = await client.get("http://ai-engine:8006/health")
            correlation_response = await client.get("http://correlation-engine:8005/health")
            if ai_response.status_code != 200 or correlation_response.status_code != 200:
                raise RuntimeError("downstream dependency unavailable")
        return {"status": "ok", "ready": True, "service": "koral-backend"}
    except Exception:
        return JSONResponse({"status": "degraded", "ready": False, "service": "koral-backend"}, status_code=503)


@app.get("/health")
def health():
    """Backward-compatible liveness endpoint."""
    return {"status": "ok", "version": "2.0.0", "service": "koral-backend"}


@app.get("/metrics")
def metrics():
    data = prometheus_client.generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "service": "KORAL Backend",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "anomalies": "/anomalies",
            "incidents": "/incidents",
            "graph": "/graph",
            "correlations": "/correlations",
            "fixes": "/fixes/history",
            "websocket": "/ws/live"
        }
    }


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
