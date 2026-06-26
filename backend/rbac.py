"""Role-based access control for KORAL backend."""
import os
import hmac
import hashlib
from enum import IntEnum
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Header
from typing import Optional

from backend.auth import DISABLE_AUTH, JWT_SECRET, JWT_ALGORITHM, _write_auth_audit

try:
    import jwt as _jwt
except Exception:
    _jwt = None  # type: ignore


class Role(IntEnum):
    VIEWER = 1
    OPERATOR = 2
    ADMIN = 3


_ROLE_KEYS: dict[Role, Optional[str]] = {
    Role.ADMIN:    os.getenv("API_KEY_ADMIN"),
    Role.OPERATOR: os.getenv("API_KEY_OPERATOR"),
    Role.VIEWER:   os.getenv("API_KEY_VIEWER"),
}

# Fallback: the legacy API_KEY gets operator-level access
_LEGACY_KEY = os.getenv("API_KEY")


def _resolve_role_from_api_key(api_key: str) -> Optional[Role]:
    """Check env-var keys first, then fall back to user DB lookup."""
    for role, key in _ROLE_KEYS.items():
        if key and hmac.compare_digest(api_key, key):
            return role
    if _LEGACY_KEY and hmac.compare_digest(api_key, _LEGACY_KEY):
        return Role.OPERATOR

    # Check user-managed keys in the database
    return _resolve_role_from_user_key(api_key)


def _resolve_role_from_user_key(api_key: str) -> Optional[Role]:
    """Look up a user's hashed API key in the database."""
    try:
        from backend.database import query_one, DB_TYPE
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        placeholder = "%s" if DB_TYPE == "postgres" else "?"
        sql = f"SELECT role, is_active, key_expires_at FROM users WHERE api_key_hash={placeholder}"
        user = query_one(sql, (key_hash,))
        if not user:
            return None
        if not user.get("is_active", True):
            return None
        # Check key expiry
        expires_at = user.get("key_expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at)
                if expiry < datetime.now(timezone.utc):
                    return None  # Key expired
            except (ValueError, TypeError):
                pass
        role_str = user.get("role", "viewer").upper()
        return Role[role_str]
    except Exception:
        return None


def _resolve_role_from_jwt(token: str) -> Optional[Role]:
    if _jwt is None:
        return None
    try:
        payload = _jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        role_str = payload.get("role", "viewer")
        return Role[role_str.upper()]
    except Exception:
        return None


def _get_role(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Role:
    if DISABLE_AUTH:
        return Role.ADMIN

    # Try API key first
    if api_key:
        role = _resolve_role_from_api_key(api_key)
        if role is not None:
            return role
        _write_auth_audit("auth.login_failed", "api_key", {"reason": "invalid_key"})
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Try JWT Bearer
    if authorization:
        try:
            scheme, token = authorization.split(maxsplit=1)
            if scheme.lower() == "bearer":
                role = _resolve_role_from_jwt(token)
                if role is not None:
                    return role
        except ValueError:
            pass
        _write_auth_audit("auth.login_failed", "jwt", {"reason": "invalid_token"})
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    _write_auth_audit("auth.login_failed", "anonymous", {"reason": "no_credentials"})
    raise HTTPException(status_code=401, detail="Authentication required")


def require_role(minimum: Role):
    """Dependency factory: require at least `minimum` role."""
    def _dep(role: Role = Depends(_get_role)) -> Role:
        if role < minimum:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {minimum.name.lower()} role or higher",
            )
        return role
    return _dep


# Convenience dependencies
require_viewer   = require_role(Role.VIEWER)
require_operator = require_role(Role.OPERATOR)
require_admin    = require_role(Role.ADMIN)
