"""
User Management API — KORAL

Provides:
  - User CRUD (invite, list, deactivate)
  - API key rotation (per-user key generation with expiry)
  - Per-user audit log queries
  - Role assignment

All endpoints require ADMIN role.
"""
import os
import hmac
import hashlib
import secrets
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from backend.rbac import require_admin, Role
from backend.audit import write_audit
from backend.database import execute, query_all, query_one, DB_TYPE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

# ── Constants ────────────────────────────────────────────────────────
KEY_PREFIX = "koral_"
DEFAULT_KEY_EXPIRY_DAYS = int(os.getenv("API_KEY_EXPIRY_DAYS", "90"))


# ── Pydantic Models ──────────────────────────────────────────────────

class UserInvite(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    email: str = Field(..., min_length=5, max_length=255)
    role: str = Field(default="viewer")
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v.upper() not in ("VIEWER", "OPERATOR", "ADMIN"):
            raise ValueError("role must be one of: viewer, operator, admin")
        return v.lower()


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in ("VIEWER", "OPERATOR", "ADMIN"):
            raise ValueError("role must be one of: viewer, operator, admin")
        return v.lower() if v else v


class KeyRotateRequest(BaseModel):
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)
    reason: Optional[str] = Field(default=None, max_length=255)


# ── Helpers ──────────────────────────────────────────────────────────

def _generate_api_key() -> str:
    """Generate a secure random API key with koral_ prefix."""
    raw = secrets.token_urlsafe(32)
    return f"{KEY_PREFIX}{raw}"


def _hash_key(api_key: str) -> str:
    """SHA-256 hash of the API key for storage (we never store plaintext)."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def _placeholder(n: int = 1) -> str:
    """Return SQL placeholder(s) for the configured DB type."""
    p = "%s" if DB_TYPE == "postgres" else "?"
    return ", ".join([p] * n)


# ── Routes ───────────────────────────────────────────────────────────

@router.post("/invite", dependencies=[Depends(require_admin)])
def invite_user(body: UserInvite):
    """Create a new user and generate their initial API key."""
    # Check if username already exists
    sql = f"SELECT id FROM users WHERE username={_placeholder()}"
    existing = query_one(sql, (body.username,))
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    # Check if email already exists
    sql = f"SELECT id FROM users WHERE email={_placeholder()}"
    existing = query_one(sql, (body.email,))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    now = datetime.now(timezone.utc).isoformat()
    api_key = _generate_api_key()
    key_hash = _hash_key(api_key)

    expiry_days = body.expires_in_days or DEFAULT_KEY_EXPIRY_DAYS
    expires_at = (datetime.now(timezone.utc) + timedelta(days=expiry_days)).isoformat()

    # Insert user
    sql = (
        f"INSERT INTO users (username, email, role, api_key_hash, key_expires_at, is_active, created_at, updated_at) "
        f"VALUES ({_placeholder(8)})"
    )
    execute(sql, (body.username, body.email, body.role, key_hash, expires_at, 1, now, now))

    write_audit("user.invited", "admin", body.username, {
        "email": body.email,
        "role": body.role,
        "expires_in_days": expiry_days,
    })

    logger.info(f"User invited: {body.username} ({body.role})")

    return {
        "status": "invited",
        "username": body.username,
        "role": body.role,
        "api_key": api_key,  # Only shown once at creation time
        "expires_at": expires_at,
        "message": "Store this API key securely. It cannot be retrieved again.",
    }


@router.get("/", dependencies=[Depends(require_admin)])
def list_users(
    limit: int = Query(50, ge=1, le=500),
    role: Optional[str] = None,
    active_only: bool = True,
):
    """List all users. Never returns key hashes."""
    conditions = []
    params = []

    if active_only:
        conditions.append("is_active=1")
    if role:
        conditions.append(f"role={_placeholder()}")
        params.append(role.lower())

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    sql = f"SELECT id, username, email, role, is_active, key_expires_at, tenant_id, created_at, updated_at FROM users{where} ORDER BY created_at DESC LIMIT {_placeholder()}"
    rows = query_all(sql, tuple(params))

    return {"users": rows, "count": len(rows)}


@router.get("/{username}", dependencies=[Depends(require_admin)])
def get_user(username: str):
    """Get a single user's details (excluding key hash)."""
    sql = f"SELECT id, username, email, role, is_active, key_expires_at, tenant_id, created_at, updated_at FROM users WHERE username={_placeholder()}"
    user = query_one(sql, (username,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{username}", dependencies=[Depends(require_admin)])
def update_user(username: str, body: UserUpdate):
    """Update a user's role or active status."""
    sql = f"SELECT id, role, is_active FROM users WHERE username={_placeholder()}"
    user = query_one(sql, (username,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = []
    params = []
    now = datetime.now(timezone.utc).isoformat()

    if body.role is not None:
        updates.append(f"role={_placeholder()}")
        params.append(body.role)
    if body.is_active is not None:
        updates.append(f"is_active={_placeholder()}")
        params.append(1 if body.is_active else 0)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append(f"updated_at={_placeholder()}")
    params.append(now)
    params.append(username)

    sql = f"UPDATE users SET {', '.join(updates)} WHERE username={_placeholder()}"
    execute(sql, tuple(params))

    write_audit("user.updated", "admin", username, {
        "changes": body.model_dump(exclude_none=True),
    })

    return {"status": "updated", "username": username}


@router.delete("/{username}", dependencies=[Depends(require_admin)])
def deactivate_user(username: str):
    """Deactivate a user (soft delete). Invalidates their API key."""
    sql = f"SELECT id FROM users WHERE username={_placeholder()}"
    user = query_one(sql, (username,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc).isoformat()
    sql = f"UPDATE users SET is_active=0, api_key_hash='revoked', updated_at={_placeholder()} WHERE username={_placeholder()}"
    execute(sql, (now, username))

    write_audit("user.deactivated", "admin", username, {})

    return {"status": "deactivated", "username": username}


@router.post("/{username}/rotate-key", dependencies=[Depends(require_admin)])
def rotate_key(username: str, body: KeyRotateRequest = KeyRotateRequest()):
    """Rotate a user's API key. Returns the new key (shown only once)."""
    sql = f"SELECT id, is_active FROM users WHERE username={_placeholder()}"
    user = query_one(sql, (username,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Cannot rotate key for deactivated user")

    new_key = _generate_api_key()
    key_hash = _hash_key(new_key)
    expiry_days = body.expires_in_days or DEFAULT_KEY_EXPIRY_DAYS
    expires_at = (datetime.now(timezone.utc) + timedelta(days=expiry_days)).isoformat()
    now = datetime.now(timezone.utc).isoformat()

    sql = f"UPDATE users SET api_key_hash={_placeholder()}, key_expires_at={_placeholder()}, updated_at={_placeholder()} WHERE username={_placeholder()}"
    execute(sql, (key_hash, expires_at, now, username))

    write_audit("user.key_rotated", "admin", username, {
        "reason": body.reason or "routine rotation",
        "expires_at": expires_at,
    })

    logger.info(f"Key rotated for user: {username}")

    return {
        "status": "rotated",
        "username": username,
        "api_key": new_key,
        "expires_at": expires_at,
        "message": "Store this API key securely. The previous key is now invalid.",
    }


@router.get("/{username}/audit", dependencies=[Depends(require_admin)])
def get_user_audit(
    username: str,
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = None,
):
    """Get audit log entries for a specific user (actor or target)."""
    sql = f"SELECT id FROM users WHERE username={_placeholder()}"
    user = query_one(sql, (username,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if event_type:
        sql = (
            f"SELECT * FROM audit WHERE (actor={_placeholder()} OR target={_placeholder()}) "
            f"AND event_type={_placeholder()} ORDER BY id DESC LIMIT {_placeholder()}"
        )
        rows = query_all(sql, (username, username, event_type, limit))
    else:
        sql = (
            f"SELECT * FROM audit WHERE (actor={_placeholder()} OR target={_placeholder()}) "
            f"ORDER BY id DESC LIMIT {_placeholder()}"
        )
        rows = query_all(sql, (username, username, limit))

    return {"username": username, "audit_entries": rows, "count": len(rows)}
