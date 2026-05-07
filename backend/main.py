from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routes.anomalies import router as anomalies_router
from backend.routes.incidents import router as incidents_router
from backend.routes.graph import router as graph_router
from backend.routes.correlations import router as correlations_router
from backend.routes.feedback import router as feedback_router
from backend.routes.ai import router as ai_router
from backend.routes.fixes import router as fixes_router
from backend.websocket.manager import manager
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KORAL Backend starting up...")
    logger.info("Database initialized and loaded")
    logger.info("All routes registered")
    logger.info("Backend ready to accept connections")
    yield
    logger.info("KORAL Backend shutting down...")


app = FastAPI(
    title="KORAL Backend",
    version="2.0.0",
    description="Kubernetes Observability with Real-time AI Logic - Backend API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(anomalies_router)
app.include_router(incidents_router)
app.include_router(graph_router)
app.include_router(correlations_router)
app.include_router(feedback_router)
app.include_router(ai_router)
app.include_router(fixes_router)


@app.get("/health")
def health():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "service": "koral-backend"
    }


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
