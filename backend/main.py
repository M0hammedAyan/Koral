from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.routes.anomalies import router as anomalies_router
from backend.routes.incidents import router as incidents_router
from backend.routes.graph import router as graph_router
from backend.routes.correlations import router as correlations_router
from backend.routes.feedback import router as feedback_router
from backend.websocket.manager import manager

app = FastAPI(title="KORAL Backend", version="1.0.0")

app.include_router(anomalies_router)
app.include_router(incidents_router)
app.include_router(graph_router)
app.include_router(correlations_router)
app.include_router(feedback_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
