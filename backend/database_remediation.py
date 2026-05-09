"""
Remediation Database Extension - Adds tables for autonomous remediation system
Non-breaking addition to existing database schema
"""
import os
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

DB_TYPE = os.getenv("DB_TYPE", "sqlite")

def _json_dumps_safe(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        # If it's already a string, keep as-is (caller may already JSON-encode).
        return value
    return json.dumps(value)


def _json_loads_safe(value: Any, default: Any):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def init_remediation_db():
    """Initialize remediation-specific database tables"""
    if DB_TYPE == "sqlite":
        import sqlite3
        DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "koral.db"))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS remediation_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT UNIQUE,
                incident_id TEXT NOT NULL,
                severity TEXT,
                root_cause TEXT,
                recommended_action TEXT,
                confidence REAL,
                affected_pods TEXT,
                parameters TEXT,
                ai_reasoning TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                expires_at TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
            
            CREATE TABLE IF NOT EXISTS approval_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                approval_id TEXT UNIQUE,
                plan_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                requested_by TEXT,
                approved_by TEXT,
                approval_status TEXT,
                approval_reason TEXT,
                email_sent_at TEXT,
                email_opened_at TEXT,
                response_timestamp TEXT,
                created_at TEXT,
                FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
            
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE,
                plan_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                command TEXT,
                parameters TEXT,
                execution_status TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_ms INTEGER,
                stdout TEXT,
                stderr TEXT,
                exit_code INTEGER,
                blast_radius INTEGER,
                pod_failures TEXT,
                created_at TEXT,
                FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
            
            CREATE TABLE IF NOT EXISTS verification_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_id TEXT UNIQUE,
                execution_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                verification_status TEXT,
                pre_metrics TEXT,
                post_metrics TEXT,
                improvement_percent REAL,
                anomaly_resolved INTEGER,
                z_score_delta REAL,
                verification_details TEXT,
                duration_ms INTEGER,
                created_at TEXT,
                FOREIGN KEY (execution_id) REFERENCES execution_log(execution_id),
                FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
        """)
        conn.commit()
        conn.close()
    
    else:  # PostgreSQL
        import psycopg2
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", "5432"))
        DB_NAME = os.getenv("DB_NAME", "koral")
        DB_USER = os.getenv("DB_USER", "koral")
        DB_PASS = os.getenv("DB_PASS", "")
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS remediation_plans (
                id SERIAL PRIMARY KEY,
                plan_id TEXT UNIQUE,
                incident_id TEXT NOT NULL,
                severity TEXT,
                root_cause TEXT,
                recommended_action TEXT,
                confidence FLOAT,
                affected_pods TEXT,
                parameters TEXT,
                ai_reasoning TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                expires_at TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_history (
                id SERIAL PRIMARY KEY,
                approval_id TEXT UNIQUE,
                plan_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                requested_by TEXT,
                approved_by TEXT,
                approval_status TEXT,
                approval_reason TEXT,
                email_sent_at TEXT,
                email_opened_at TEXT,
                response_timestamp TEXT,
                created_at TEXT,
                FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                id SERIAL PRIMARY KEY,
                execution_id TEXT UNIQUE,
                plan_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                command TEXT,
                parameters TEXT,
                execution_status TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_ms INTEGER,
                stdout TEXT,
                stderr TEXT,
                exit_code INTEGER,
                blast_radius INTEGER,
                pod_failures TEXT,
                created_at TEXT,
                FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_results (
                id SERIAL PRIMARY KEY,
                verification_id TEXT UNIQUE,
                execution_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                verification_status TEXT,
                pre_metrics TEXT,
                post_metrics TEXT,
                improvement_percent FLOAT,
                anomaly_resolved INTEGER,
                z_score_delta FLOAT,
                verification_details TEXT,
                duration_ms INTEGER,
                created_at TEXT,
                FOREIGN KEY (execution_id) REFERENCES execution_log(execution_id),
                FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
        """)
        
        conn.commit()
        conn.close()


def add_remediation_plan(plan_id, incident_id, severity, root_cause, recommended_action, 
                         confidence, affected_pods, parameters, ai_reasoning):
    """Add new remediation plan"""
    affected_pods = _json_dumps_safe(affected_pods)
    parameters = _json_dumps_safe(parameters)
    if DB_TYPE == "sqlite":
        import sqlite3
        DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "koral.db"))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO remediation_plans 
            (plan_id, incident_id, severity, root_cause, recommended_action, confidence, 
             affected_pods, parameters, ai_reasoning, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (plan_id, incident_id, severity, root_cause, recommended_action, confidence,
              affected_pods, parameters, ai_reasoning, now))
        conn.commit()
        conn.close()
    else:
        import psycopg2
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", "5432"))
        DB_NAME = os.getenv("DB_NAME", "koral")
        DB_USER = os.getenv("DB_USER", "koral")
        DB_PASS = os.getenv("DB_PASS", "")
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO remediation_plans 
            (plan_id, incident_id, severity, root_cause, recommended_action, confidence, 
             affected_pods, parameters, ai_reasoning, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
        """, (plan_id, incident_id, severity, root_cause, recommended_action, confidence,
              affected_pods, parameters, ai_reasoning, now))
        conn.commit()
        conn.close()


def get_remediation_plan(plan_id):
    """Get remediation plan by ID"""
    if DB_TYPE == "sqlite":
        import sqlite3
        DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "koral.db"))
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM remediation_plans WHERE plan_id=?", (plan_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        d["affected_pods"] = _json_loads_safe(d.get("affected_pods"), [])
        d["parameters"] = _json_loads_safe(d.get("parameters"), {})
        return d
    else:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", "5432"))
        DB_NAME = os.getenv("DB_NAME", "koral")
        DB_USER = os.getenv("DB_USER", "koral")
        DB_PASS = os.getenv("DB_PASS", "")
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM remediation_plans WHERE plan_id=%s", (plan_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        row["affected_pods"] = _json_loads_safe(row.get("affected_pods"), [])
        row["parameters"] = _json_loads_safe(row.get("parameters"), {})
        return row


def list_remediation_plans(limit: int = 100) -> List[Dict[str, Any]]:
    """List remediation plans (most recent first)."""
    limit = max(1, min(int(limit), 500))
    if DB_TYPE == "sqlite":
        import sqlite3
        DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "koral.db"))
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM remediation_plans ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            d["affected_pods"] = _json_loads_safe(d.get("affected_pods"), [])
            d["parameters"] = _json_loads_safe(d.get("parameters"), {})
            result.append(d)
        return result
    else:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", "5432"))
        DB_NAME = os.getenv("DB_NAME", "koral")
        DB_USER = os.getenv("DB_USER", "koral")
        DB_PASS = os.getenv("DB_PASS", "")
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM remediation_plans ORDER BY id DESC LIMIT %s", (limit,))
        rows = cursor.fetchall()
        conn.close()
        for d in rows:
            d["affected_pods"] = _json_loads_safe(d.get("affected_pods"), [])
            d["parameters"] = _json_loads_safe(d.get("parameters"), {})
        return rows


def count_remediation_plans() -> int:
    """Return total count of remediation plans."""
    if DB_TYPE == "sqlite":
        import sqlite3
        DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "koral.db"))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM remediation_plans")
        (n,) = cursor.fetchone()
        conn.close()
        return int(n or 0)
    else:
        import psycopg2
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = int(os.getenv("DB_PORT", "5432"))
        DB_NAME = os.getenv("DB_NAME", "koral")
        DB_USER = os.getenv("DB_USER", "koral")
        DB_PASS = os.getenv("DB_PASS", "")
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM remediation_plans")
        (n,) = cursor.fetchone()
        conn.close()
        return int(n or 0)
