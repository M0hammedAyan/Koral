import asyncio
import os
import uuid
import httpx
import json
from datetime import datetime, timezone
from typing import List, Dict
from backend.database import (
    insert_anomaly, insert_incident, update_incident, get_incidents,
    execute, query_all, query_one
)

CORRELATION_URL = os.getenv("CORRELATION_ENGINE_URL", "http://localhost:8005")
AI_ENGINE_URL   = os.getenv("AI_ENGINE_URL", "http://localhost:8006")

# ── In-memory cache (fast reads) ────────────────────────────────────
anomalies: List[dict] = []
incidents: List[dict] = []
correlations: List[dict] = []
fix_history: List[dict] = []
graph_data: Dict = {"nodes": [], "edges": []}

# Load existing data from DB on startup
def _load_from_db():
    try:
        rows = get_incidents(limit=200)
        for row in reversed(rows):
            if isinstance(row, dict):
                inc = dict(row)
            else:
                inc = {
                    "incident_id": row.get("incident_id"),
                    "timestamp": row.get("timestamp"),
                    "namespace": row.get("namespace"),
                    "severity": row.get("severity"),
                    "root_cause": row.get("root_cause"),
                    "summary": row.get("summary"),
                    "affected_pods": json.loads(row.get("affected_pods") or "[]"),
                    "primary_metric": row.get("primary_metric"),
                    "confidence": row.get("confidence"),
                    "evidence_count": row.get("evidence_count"),
                    "created_at": row.get("created_at"),
                    "ai_explanation": row.get("ai_explanation"),
                    "ai_action": row.get("ai_action"),
                    "ai_model": row.get("ai_model"),
                }
            inc["affected_pods"] = json.loads(inc.get("affected_pods") or "[]") if isinstance(inc.get("affected_pods"), str) else inc.get("affected_pods", [])
            incidents.append(inc)
        print(f"[db] Loaded {len(incidents)} incidents from database")
    except Exception as e:
        print(f"[db] load error: {e}")

_load_from_db()


# ── Fix history tracking ─────────────────────────────────────────────
def store_fix_history(incident_id: str, fix_type: str, fix_description: str, 
                      applied_by: str, success: bool, kubectl_command: str = "",
                      error_message: str = ""):
    """Store a fix action in the history database"""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        sql = """
            INSERT INTO fix_history
            (incident_id, fix_type, fix_description, applied_by, success,
             error_message, kubectl_command, timestamp, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """ if os.getenv("DB_TYPE") == "postgres" else """
            INSERT INTO fix_history
            (incident_id, fix_type, fix_description, applied_by, success,
             error_message, kubectl_command, timestamp, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """
        execute(sql, (
            incident_id, fix_type, fix_description, applied_by, int(success),
            error_message, kubectl_command, int(datetime.now(timezone.utc).timestamp()),
            timestamp
        ))
        
        # Add to in-memory cache
        fix_entry = {
            "incident_id": incident_id,
            "fix_type": fix_type,
            "fix_description": fix_description,
            "applied_by": applied_by,
            "success": success,
            "error_message": error_message,
            "kubectl_command": kubectl_command,
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "created_at": timestamp
        }
        fix_history.append(fix_entry)
        print(f"[fix_history] Stored: {fix_type} by {applied_by} for {incident_id}")
    except Exception as e:
        print(f"[fix_history] Error storing fix: {e}")


# ── Main anomaly processor ───────────────────────────────────────────
async def process_anomaly(data: dict, broadcast_fn):
    anomalies.append(data)

    # Persist anomaly
    try:
        insert_anomaly(
            data.get("timestamp"), data.get("pod"), data.get("namespace", "koral-system"),
            data.get("metric"), data.get("value"), data.get("unit", ""),
            data.get("z_score"), int(data.get("is_anomaly", False)),
            data.get("window_size", 300), data.get("source", "")
        )
    except Exception as e:
        print(f"[db] anomaly insert error: {e}")

    await broadcast_fn({"type": "anomaly", "payload": data})

    if not data.get("is_anomaly"):
        return

    # Call correlation engine
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{CORRELATION_URL}/correlate", json=data)
            if r.status_code == 200:
                result = r.json()
                if "correlation" in result:
                    correlations.append(result)
                _handle_correlation_result(result)
                await broadcast_fn({"type": "incident", "payload": result})

                # Call AI engine asynchronously (don't block the response)
                asyncio.create_task(_call_ai_engine(result, data, broadcast_fn))
    except Exception as e:
        print(f"[processor] correlation engine unreachable: {e}")


async def _call_ai_engine(incident: dict, anomaly: dict, broadcast_fn):
    try:
        ai_payload = {
            "incident_id": incident.get("incident_id", ""),
            "severity":    incident.get("severity", "medium"),
            "root_cause":  incident.get("root_cause", ""),
            "summary":     incident.get("summary", ""),
            "affected_pods": incident.get("affected_pods", []),
            "primary_metric": incident.get("primary_metric", anomaly.get("metric", "")),
            "confidence":  incident.get("confidence", 0.5),
            "namespace":   incident.get("namespace", "koral-system"),
            "z_score":     anomaly.get("z_score", 0.0),
            "value":       anomaly.get("value", 0.0),
        }
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.post(f"{AI_ENGINE_URL}/analyze", json=ai_payload)
            if r.status_code == 200:
                ai_result = r.json()
                # Attach AI explanation to the incident
                incident["ai_explanation"] = ai_result.get("explanation", "")
                incident["ai_message"]     = ai_result.get("user_message", "")
                incident["ai_action"]      = ai_result.get("action_type", "")
                incident["ai_model"]       = ai_result.get("model_used", "")
                # Update DB
                _update_incident_ai(incident)
                # Broadcast updated incident with AI data
                await broadcast_fn({"type": "incident_ai", "payload": incident})
    except Exception as e:
        print(f"[processor] AI engine unreachable: {e}")


def _update_incident_ai(incident: dict):
    try:
        conn = _get_db()
        conn.execute("""
            UPDATE incidents SET
                ai_explanation=?, ai_action=?, ai_model=?
            WHERE incident_id=?
        """, (
            incident.get("ai_explanation", ""),
            incident.get("ai_action", ""),
            incident.get("ai_model", ""),
            incident.get("incident_id"),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[db] ai update error: {e}")


def _handle_correlation_result(result: dict):
    if "incident_id" not in result:
        result["incident_id"] = f"INC-{uuid.uuid4().hex[:6].upper()}"
    if "created_at" not in result:
        result["created_at"] = datetime.now(timezone.utc).isoformat()
    incidents.append(result)

    # Persist incident
    try:
        insert_incident(
            result.get("incident_id"), result.get("timestamp"),
            result.get("namespace", "koral-system"), result.get("severity", "medium"),
            result.get("root_cause", ""), result.get("summary", ""),
            result.get("affected_pods", []),
            result.get("primary_metric", ""), result.get("confidence", 0.5),
            result.get("evidence_count", 1)
        )
    except Exception as e:
        print(f"[db] incident insert error: {e}")

    # Update graph
    affected = result.get("affected_pods", [])
    root = result.get("root_cause_pod")

    for pod in affected:
        if not any(n["id"] == pod for n in graph_data["nodes"]):
            graph_data["nodes"].append({"id": pod, "label": pod, "status": "problem"})
            try:
                conn = _get_db()
                conn.execute("INSERT OR IGNORE INTO graph_nodes VALUES (?,?,?)", (pod, pod, "problem"))
                conn.commit(); conn.close()
            except Exception: pass

    if root and not any(n["id"] == root for n in graph_data["nodes"]):
        graph_data["nodes"].append({"id": root, "label": root, "status": "problem"})
        try:
            conn = _get_db()
            conn.execute("INSERT OR IGNORE INTO graph_nodes VALUES (?,?,?)", (root, root, "problem"))
            conn.commit(); conn.close()
        except Exception: pass

    for pod in affected:
        if root and pod != root:
            edge = {"source": root, "target": pod}
            if edge not in graph_data["edges"]:
                graph_data["edges"].append(edge)
                try:
                    conn = _get_db()
                    conn.execute("INSERT OR IGNORE INTO graph_edges VALUES (?,?)", (root, pod))
                    conn.commit(); conn.close()
                except Exception: pass

    if root and len(affected) == 1 and len(graph_data["nodes"]) > 1:
        for existing in graph_data["nodes"]:
            if existing["id"] != root:
                edge = {"source": root, "target": existing["id"]}
                if edge not in graph_data["edges"]:
                    graph_data["edges"].append(edge)
                    try:
                        conn = _get_db()
                        conn.execute("INSERT OR IGNORE INTO graph_edges VALUES (?,?)", (root, existing["id"]))
                        conn.commit(); conn.close()
                    except Exception: pass
                break

