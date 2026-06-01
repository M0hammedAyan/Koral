from fastapi import APIRouter, Depends, Query
from typing import Optional
from backend.auth import validate_api_key
from backend.database import query_all, DB_TYPE

router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.get("/audit")
def get_audit_log(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = None,
    actor: Optional[str] = None,
):
    if event_type and actor:
        sql = ("SELECT * FROM audit WHERE event_type=%s AND actor=%s ORDER BY id DESC LIMIT %s"
               if DB_TYPE == "postgres" else
               "SELECT * FROM audit WHERE event_type=? AND actor=? ORDER BY id DESC LIMIT ?")
        return query_all(sql, (event_type, actor, limit))
    if event_type:
        sql = ("SELECT * FROM audit WHERE event_type=%s ORDER BY id DESC LIMIT %s"
               if DB_TYPE == "postgres" else
               "SELECT * FROM audit WHERE event_type=? ORDER BY id DESC LIMIT ?")
        return query_all(sql, (event_type, limit))
    if actor:
        sql = ("SELECT * FROM audit WHERE actor=%s ORDER BY id DESC LIMIT %s"
               if DB_TYPE == "postgres" else
               "SELECT * FROM audit WHERE actor=? ORDER BY id DESC LIMIT ?")
        return query_all(sql, (actor, limit))
    sql = ("SELECT * FROM audit ORDER BY id DESC LIMIT %s"
           if DB_TYPE == "postgres" else
           "SELECT * FROM audit ORDER BY id DESC LIMIT ?")
    return query_all(sql, (limit,))
