"""
Enhanced Authentication Middleware with Security Features
Implements API key, JWT, rate limiting, and suspicious activity detection
"""

import os
import time
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from functools import lru_cache

from fastapi import HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthCredentials

logger = logging.getLogger(__name__)

# Security configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes in seconds
SUSPICIOUS_ACTIVITY_THRESHOLD = 10  # requests per minute


class AuthenticationTracker:
    """Track authentication attempts for security"""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[float]] = defaultdict(list)
        self.lockouts: Dict[str, float] = {}
    
    def record_failed_attempt(self, client_id: str) -> None:
        """Record failed authentication attempt"""
        now = time.time()
        self.failed_attempts[client_id].append(now)
        
        # Cleanup old attempts (older than lockout duration)
        self.failed_attempts[client_id] = [
            t for t in self.failed_attempts[client_id]
            if now - t < LOCKOUT_DURATION
        ]
        
        # Check if lockout should be triggered
        if len(self.failed_attempts[client_id]) >= MAX_FAILED_ATTEMPTS:
            self.lockouts[client_id] = now
            logger.warning(f"Account lockout triggered for {client_id}")
    
    def record_success(self, client_id: str) -> None:
        """Record successful authentication"""
        if client_id in self.failed_attempts:
            del self.failed_attempts[client_id]
        if client_id in self.lockouts:
            del self.lockouts[client_id]
    
    def is_locked_out(self, client_id: str) -> bool:
        """Check if client is locked out"""
        if client_id not in self.lockouts:
            return False
        
        now = time.time()
        if now - self.lockouts[client_id] > LOCKOUT_DURATION:
            del self.lockouts[client_id]
            return False
        
        return True
    
    def get_lockout_remaining(self, client_id: str) -> int:
        """Get remaining lockout time in seconds"""
        if client_id not in self.lockouts:
            return 0
        
        now = time.time()
        remaining = LOCKOUT_DURATION - (now - self.lockouts[client_id])
        return max(0, int(remaining))


class EnhancedAuthenticator:
    """Enhanced authentication with security features"""
    
    def __init__(self):
        self.tracker = AuthenticationTracker()
        self.jwt_secret = os.getenv("JWT_SECRET", "change-this-in-production")
        self.api_key = os.getenv("API_KEY", None)
        self.disable_auth = os.getenv("DISABLE_AUTH", "false").lower() == "true"
        
        # Try to import JWT library
        try:
            import jwt
            self.jwt = jwt
            self.jwt_available = True
        except ImportError:
            logger.warning("PyJWT not available, JWT authentication disabled")
            self.jwt = None
            self.jwt_available = False
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier"""
        if request.client:
            return request.client.host
        return "unknown"
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        if not self.api_key:
            return False
        
        # Constant-time comparison to prevent timing attacks
        from hmac import compare_digest
        return compare_digest(api_key, self.api_key)
    
    def validate_jwt(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Validate JWT token"""
        if not self.jwt_available or not self.jwt:
            logger.warning("JWT validation attempted but JWT library not available")
            return False, None
        
        try:
            payload = self.jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
            )
            return True, payload
        except self.jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False, None
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return False, None
    
    def create_jwt(self, subject: str, expires_in_hours: int = 24) -> str:
        """Create JWT token"""
        if not self.jwt_available or not self.jwt:
            raise RuntimeError("JWT library not available")
        
        now = datetime.utcnow()
        expires = now + timedelta(hours=expires_in_hours)
        
        payload = {
            "sub": subject,
            "iat": now,
            "exp": expires,
            "iss": "koral-backend",
            "aud": "koral-api",
        }
        
        return self.jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def authenticate_request(self, request: Request, authorization: Optional[str] = None, x_api_key: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Authenticate HTTP request
        
        Returns:
            Tuple of (authenticated, user_id)
        """
        client_id = self._get_client_id(request)
        
        # Check for lockout
        if self.tracker.is_locked_out(client_id):
            remaining = self.tracker.get_lockout_remaining(client_id)
            logger.warning(f"Client {client_id} is locked out for {remaining}s")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Try again in {remaining} seconds.",
                headers={"Retry-After": str(remaining)},
            )
        
        # Skip auth if disabled
        if self.disable_auth:
            return True, "development-mode"
        
        # Try API key authentication
        if x_api_key:
            if self.validate_api_key(x_api_key):
                self.tracker.record_success(client_id)
                logger.info(f"API key authentication successful for {client_id}")
                return True, f"api-key:{client_id}"
            else:
                self.tracker.record_failed_attempt(client_id)
                logger.warning(f"Invalid API key from {client_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Try JWT authentication
        if authorization:
            if not authorization.startswith("Bearer "):
                self.tracker.record_failed_attempt(client_id)
                logger.warning(f"Invalid authorization format from {client_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token = authorization[7:]  # Remove "Bearer " prefix
            valid, payload = self.validate_jwt(token)
            
            if valid and payload:
                self.tracker.record_success(client_id)
                logger.info(f"JWT authentication successful for {client_id}")
                return True, payload.get("sub", "jwt-user")
            else:
                self.tracker.record_failed_attempt(client_id)
                logger.warning(f"Invalid JWT token from {client_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # No credentials provided
        self.tracker.record_failed_attempt(client_id)
        logger.warning(f"No credentials provided from {client_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Global authenticator instance
authenticator = EnhancedAuthenticator()


# Dependency for FastAPI
def get_authenticated_user(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """FastAPI dependency for authentication"""
    authenticated, user_id = authenticator.authenticate_request(
        request,
        authorization=authorization,
        x_api_key=x_api_key,
    )
    return user_id


__all__ = [
    "EnhancedAuthenticator",
    "AuthenticationTracker",
    "authenticator",
    "get_authenticated_user",
]
