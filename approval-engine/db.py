import os
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

DB_PATH = os.getenv("APPROVAL_DB_PATH", "/data/approvals.db")


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id   TEXT PRIMARY KEY,
                plan_id       TEXT NOT NULL,
                incident_id   TEXT NOT NULL,
                severity      TEXT,
                root_cause    TEXT,
                recommended_action TEXT,
                confidence    REAL,
                affected_pods TEXT,
                parameters    TEXT,
                ai_reasoning  TEXT,
                status        TEXT NOT NULL DEFAULT 'pending',
                approver      TEXT,
                approval_reason TEXT,
                email_sent    INTEGER DEFAULT 0,
                auto_approved INTEGER DEFAULT 0,
                created_at    TEXT NOT NULL,
                expires_at    TEXT NOT NULL,
                approved_at   TEXT,
                rejected_at   TEXT
            )
        """)
        c.commit()


def insert_approval(approval_id: str, plan_id: str, incident_id: str,
                    severity: str, root_cause: str, recommended_action: str,
                    confidence: float, affected_pods: list, parameters: dict,
                    ai_reasoning: str, status: str, email_sent: bool,
                    auto_approved: bool, created_at: str, expires_at: str,
                    approver: Optional[str] = None, approved_at: Optional[str] = None) -> None:
    with _conn() as c:
        c.execute("""
            INSERT INTO approvals
            (approval_id, plan_id, incident_id, severity, root_cause,
             recommended_action, confidence, affected_pods, parameters,
             ai_reasoning, status, email_sent, auto_approved,
             created_at, expires_at, approver, approved_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            approval_id, plan_id, incident_id, severity, root_cause,
            recommended_action, confidence,
            json.dumps(affected_pods), json.dumps(parameters),
            ai_reasoning, status, int(email_sent), int(auto_approved),
            created_at, expires_at, approver, approved_at
        ))
        c.commit()


def get_approval(approval_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["affected_pods"] = json.loads(d.get("affected_pods") or "[]")
    d["parameters"] = json.loads(d.get("parameters") or "{}")
    d["email_sent"] = bool(d["email_sent"])
    d["auto_approved"] = bool(d["auto_approved"])
    return d


def update_approval(approval_id: str, status: str, approver: str,
                    reason: str, timestamp_field: str, timestamp_value: str) -> None:
    with _conn() as c:
        c.execute(f"""
            UPDATE approvals
            SET status=?, approver=?, approval_reason=?, {timestamp_field}=?
            WHERE approval_id=?
        """, (status, approver, reason, timestamp_value, approval_id))
        c.commit()


def list_approvals(status: Optional[str] = None) -> list:
    with _conn() as c:
        if status:
            rows = c.execute("SELECT * FROM approvals WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
        else:
            rows = c.execute("SELECT * FROM approvals ORDER BY created_at DESC").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["affected_pods"] = json.loads(d.get("affected_pods") or "[]")
        d["parameters"] = json.loads(d.get("parameters") or "{}")
        result.append(d)
    return result
