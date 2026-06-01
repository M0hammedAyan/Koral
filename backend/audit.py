"""Audit logging — writes to the audit table for key system events."""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from backend.database import execute, DB_TYPE

logger = logging.getLogger(__name__)

_SQL = {
    "sqlite":   "INSERT INTO audit (event_type, actor, target, payload, created_at) VALUES (?,?,?,?,?)",
    "postgres": "INSERT INTO audit (event_type, actor, target, payload, created_at) VALUES (%s,%s,%s,%s,%s)",
}


def write_audit(event_type: str, actor: str, target: str, payload: Optional[Any] = None) -> None:
    """Fire-and-forget audit write. Never raises — logs on failure."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload) if payload is not None else "{}"
        sql = _SQL.get(DB_TYPE, _SQL["sqlite"])
        execute(sql, (event_type, actor, target, payload_str, now))
    except Exception as e:
        logger.warning(f"[audit] write failed ({event_type}): {e}")
