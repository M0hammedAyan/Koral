import os
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_PATH = os.getenv("APPROVAL_DB_PATH", "/data/approvals.db")

# PostgreSQL connection params (used when DB_TYPE=postgres)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "koral")
DB_USER = os.getenv("DB_USER", "koral")
DB_PASS = os.getenv("DB_PASS", "")

_CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS approvals (
        approval_id        TEXT PRIMARY KEY,
        plan_id            TEXT NOT NULL,
        incident_id        TEXT NOT NULL,
        severity           TEXT,
        root_cause         TEXT,
        recommended_action TEXT,
        confidence         REAL,
        affected_pods      TEXT,
        parameters         TEXT,
        ai_reasoning       TEXT,
        status             TEXT NOT NULL DEFAULT 'pending',
        approver           TEXT,
        approval_reason    TEXT,
        email_sent         INTEGER DEFAULT 0,
        auto_approved      INTEGER DEFAULT 0,
        created_at         TEXT NOT NULL,
        expires_at         TEXT NOT NULL,
        approved_at        TEXT,
        rejected_at        TEXT
    )
"""


def _conn_sqlite():
    import sqlite3
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _conn_pg():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASS,
        connect_timeout=int(os.getenv("DB_TIMEOUT_DB", "3")),
    )


def _conn():
    if DB_TYPE == "postgres":
        return _conn_pg()
    return _conn_sqlite()


def _ph():
    return "%s" if DB_TYPE == "postgres" else "?"


def _row_to_dict(row) -> Dict[str, Any]:
    d = dict(row)
    d["affected_pods"] = json.loads(d.get("affected_pods") or "[]")
    d["parameters"] = json.loads(d.get("parameters") or "{}")
    d["email_sent"] = bool(d.get("email_sent"))
    d["auto_approved"] = bool(d.get("auto_approved"))
    return d


def init_db() -> None:
    c = _conn()
    try:
        cur = c.cursor()
        if DB_TYPE == "postgres":
            cur.execute(_CREATE_TABLE_SQL.replace("INTEGER DEFAULT 0", "SMALLINT DEFAULT 0"))
        else:
            cur.execute(_CREATE_TABLE_SQL)
        c.commit()
    finally:
        c.close()


def insert_approval(approval_id: str, plan_id: str, incident_id: str,
                    severity: str, root_cause: str, recommended_action: str,
                    confidence: float, affected_pods: list, parameters: dict,
                    ai_reasoning: str, status: str, email_sent: bool,
                    auto_approved: bool, created_at: str, expires_at: str,
                    approver: Optional[str] = None, approved_at: Optional[str] = None) -> None:
    ph = _ph()
    sql = f"""
        INSERT INTO approvals
        (approval_id, plan_id, incident_id, severity, root_cause,
         recommended_action, confidence, affected_pods, parameters,
         ai_reasoning, status, email_sent, auto_approved,
         created_at, expires_at, approver, approved_at)
        VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})
    """
    c = _conn()
    try:
        c.cursor().execute(sql, (
            approval_id, plan_id, incident_id, severity, root_cause,
            recommended_action, confidence,
            json.dumps(affected_pods), json.dumps(parameters),
            ai_reasoning, status, int(email_sent), int(auto_approved),
            created_at, expires_at, approver, approved_at
        ))
        c.commit()
    finally:
        c.close()


def get_approval(approval_id: str) -> Optional[Dict[str, Any]]:
    ph = _ph()
    c = _conn()
    try:
        if DB_TYPE == "postgres":
            from psycopg2.extras import RealDictCursor
            cur = c.cursor(cursor_factory=RealDictCursor)
        else:
            cur = c.cursor()
        cur.execute(f"SELECT * FROM approvals WHERE approval_id={ph}", (approval_id,))
        row = cur.fetchone()
    finally:
        c.close()
    if not row:
        return None
    return _row_to_dict(row)


def update_approval(approval_id: str, status: str, approver: str,
                    reason: str, timestamp_field: str, timestamp_value: str) -> None:
    ph = _ph()
    c = _conn()
    try:
        c.cursor().execute(
            f"UPDATE approvals SET status={ph}, approver={ph}, approval_reason={ph}, {timestamp_field}={ph} WHERE approval_id={ph}",
            (status, approver, reason, timestamp_value, approval_id)
        )
        c.commit()
    finally:
        c.close()


def list_approvals(status: Optional[str] = None) -> List[Dict[str, Any]]:
    ph = _ph()
    c = _conn()
    try:
        if DB_TYPE == "postgres":
            from psycopg2.extras import RealDictCursor
            cur = c.cursor(cursor_factory=RealDictCursor)
        else:
            cur = c.cursor()
        if status:
            cur.execute(f"SELECT * FROM approvals WHERE status={ph} ORDER BY created_at DESC", (status,))
        else:
            cur.execute("SELECT * FROM approvals ORDER BY created_at DESC")
        rows = cur.fetchall()
    finally:
        c.close()
    return [_row_to_dict(row) for row in rows]
