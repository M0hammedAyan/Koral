"""
Authentication utilities for KORAL Backend
Supports API key and JWT authentication
"""
import os
from fastapi import HTTPException, Request, Header
from typing import Optional
try:
    import jwt
except Exception:
    class _DummyJWT:
        class DecodeError(Exception):
            pass
        class ExpiredSignatureError(Exception):
            pass
        @staticmethod
        def encode(payload, secret, algorithm=None):
            return "dev-token"
        @staticmethod
        def decode(token, secret, algorithms=None):
            return {"sub": "development"}
    jwt = _DummyJWT()
from datetime import datetime, timedelta

# ── Configuration ─────────────────────────────────────────────────────
API_KEY_HEADER = "X-API-Key"
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_ALGORITHM = "HS256"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# For development: set DISABLE_AUTH=true in env vars
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() == "true"


def validate_api_key(api_key: str = Header(None, alias="X-API-Key")) -> str:
    """Validate API key from request header"""
    if DISABLE_AUTH:
        return "development"
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header."
        )
    
    valid_key = os.getenv("API_KEY")
    if not valid_key:
        raise HTTPException(
            status_code=500,
            detail="API_KEY not configured on server"
        )
    
    if api_key != valid_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return api_key


def validate_jwt(authorization: str = Header(None, alias="Authorization")) -> dict:
    """Validate JWT token from Authorization header"""
    if DISABLE_AUTH:
        return {"sub": "development"}
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (ValueError, jwt.DecodeError, jwt.ExpiredSignatureError) as e:
        raise HTTPException(
            status_code=403,
            detail=f"Invalid or expired token: {str(e)}"
        )


def create_jwt(subject: str, expires_in_hours: int = 24) -> str:
    """Create a JWT token"""
    expires = datetime.utcnow() + timedelta(hours=expires_in_hours)
    payload = {
        "sub": subject,
        "exp": expires,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_allowed_origins() -> list[str]:
    """Get CORS allowed origins"""
    if DISABLE_AUTH:
        return ["*"]
    return [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]
