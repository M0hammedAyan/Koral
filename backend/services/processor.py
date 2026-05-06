import asyncio
import os
import uuid
import httpx
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict

CORRELATION_URL = os.getenv("CORRELATION_ENGINE_URL", "http://localhost:8005")
AI_ENGINE_URL   = os.getenv("AI_ENGINE_URL", "http://localhost:8006")
DB_PATH         = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "koral.db"))

# ── SQLite persistence ───────────────────────────────────────────────
def _get_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER, pod TEXT, namespace TEXT,
            metric TEXT, value REAL, unit TEXT,
            z_score REAL, is_anomaly INTEGER,
            window_size INTEGER, source TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE,
            timestamp INTEGER, namespace TEXT,
            severity TEXT, root_cause TEXT,
            summary TEXT, affected_pods TEXT,
            primary_metric TEXT, confidence REAL,
            evidence_count INTEGER, created_at TEXT,
            ai_explanation TEXT, ai_action TEXT,
            ai_model TEXT
        );
        CREATE TABLE IF NOT EXISTS fix_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT,
            fix_type TEXT,
            fix_description TEXT,
            applied_by TEXT,
            success INTEGER,
            error_message TEXT,
            kubectl_command TEXT,
            timestamp TEXT,
            created_at TEXT,
            FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
        );
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id TEXT PRIMARY KEY, label TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS graph_edges (
            source TEXT, target TEXT,
            PRIMARY KEY (source, target)
        );
    """)
    conn.commit()
    conn.close()

_init_db()

# ── In-memory cache (fast reads) ────────────────────────────────────
anomalies: List[dict] = []
incidents: List[dict] = []
correlations: List[dict] = []
fix_history: List[dict] = []
graph_data: Dict = {"nodes": [], "edges": []}

# Load existing data from DB on startup
def _load_from_db():
    try:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM anomalies ORDER BY id DESC LIMIT 500").fetchall()
        anomalies.extend([dict(r) for r in reversed(rows)])
        rows = conn.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT 200").fetchall()
        for r in reversed(rows):
            inc = dict(r)
            inc["affected_pods"] = json.loads(inc.get("affected_pods") or "[]")
            incidents.append(inc)
        rows = conn.execute("SELECT * FROM fix_history ORDER BY id DESC LIMIT 200").fetchall()
        fix_history.extend([dict(r) for r in reversed(rows)])
        nodes = conn.execute("SELECT * FROM graph_nodes").fetchall()
        graph_data["nodes"] = [dict(n) for n in nodes]
        edges = conn.execute("SELECT * FROM graph_edges").fetchall()
        graph_data["edges"] = [dict(e) for e in edges]
        conn.close()
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
        conn = _get_db()
        conn.execute("""
            INSERT INTO fix_history
            (incident_id, fix_type, fix_description, applied_by, success,
             error_message, kubectl_command, timestamp, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            incident_id, fix_type, fix_description, applied_by, int(success),
            error_message, kubectl_command, int(datetime.now(timezone.utc).timestamp()),
            timestamp
        ))
        conn.commit()
        conn.close()
        
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
        conn = _get_db()
        conn.execute("""
            INSERT INTO anomalies
            (timestamp, pod, namespace, metric, value, unit, z_score,
             is_anomaly, window_size, source, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("timestamp"), data.get("pod"), data.get("namespace", "koral-system"),
            data.get("metric"), data.get("value"), data.get("unit", ""),
            data.get("z_score"), int(data.get("is_anomaly", False)),
            data.get("window_size", 300), data.get("source", ""),
            datetime.now(timezone.utc).isoformat(),
        ))
        conn.commit()
        conn.close()
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
        conn = _get_db()
        conn.execute("""
            INSERT OR IGNORE INTO incidents
            (incident_id, timestamp, namespace, severity, root_cause,
             summary, affected_pods, primary_metric, confidence,
             evidence_count, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            result.get("incident_id"), result.get("timestamp"),
            result.get("namespace", "koral-system"), result.get("severity", "medium"),
            result.get("root_cause", ""), result.get("summary", ""),
            json.dumps(result.get("affected_pods", [])),
            result.get("primary_metric", ""), result.get("confidence", 0.5),
            result.get("evidence_count", 1), result.get("created_at"),
        ))
        conn.commit()
        conn.close()
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

