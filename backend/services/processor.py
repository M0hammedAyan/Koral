import os
import uuid
import httpx
from datetime import datetime, timezone
from typing import List, Dict

CORRELATION_URL = os.getenv("CORRELATION_ENGINE_URL", "http://correlation-engine:8005")

# In-memory stores
anomalies: List[dict] = []
incidents: List[dict] = []
correlations: List[dict] = []
graph_data: Dict = {"nodes": [], "edges": []}


async def process_anomaly(data: dict, broadcast_fn):
    anomalies.append(data)

    await broadcast_fn({"type": "anomaly", "data": data})

    if not data.get("is_anomaly"):
        return

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{CORRELATION_URL}/correlate", json=data)
            if r.status_code == 200:
                result = r.json()
                # Store raw correlation if present
                if "correlation" in result:
                    correlations.append(result)
                _handle_correlation_result(result)
                await broadcast_fn({"type": "incident_update", "data": result})
    except Exception as e:
        print(f"[processor] correlation engine unreachable: {e}")


def _handle_correlation_result(result: dict):
    if "incident_id" not in result:
        result["incident_id"] = f"INC-{uuid.uuid4().hex[:6].upper()}"
    if "created_at" not in result:
        result["created_at"] = datetime.now(timezone.utc).isoformat()
    incidents.append(result)

    for pod in result.get("affected_pods", []):
        if not any(n["id"] == pod for n in graph_data["nodes"]):
            graph_data["nodes"].append({"id": pod, "label": pod})

    root = result.get("root_cause_pod")
    for pod in result.get("affected_pods", []):
        if root and pod != root:
            edge = {"source": root, "target": pod}
            if edge not in graph_data["edges"]:
                graph_data["edges"].append(edge)
