"""
Rate Limiting Middleware for KORAL Backend
Implements token bucket and sliding window rate limiting
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 3600,
        burst_size: int = 10,
        enable_by_ip: bool = True,
        enable_by_user: bool = True,
        exempt_paths: Optional[list] = None,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.enable_by_ip = enable_by_ip
        self.enable_by_user = enable_by_user
        self.exempt_paths = exempt_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        
        Returns:
            True if successful, False if rate limited
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_remaining(self) -> float:
        """Get remaining tokens"""
        self._refill()
        return self.tokens


class SlidingWindowCounter:
    """Sliding window counter for rate limiting"""
    
    def __init__(self, window_size: int):
        """
        Args:
            window_size: Time window in seconds
        """
        self.window_size = window_size
        self.requests: deque = deque()
    
    def _cleanup(self) -> None:
        """Remove old requests outside the window"""
        cutoff = time.time() - self.window_size
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def add_request(self) -> None:
        """Add current request to window"""
        self.requests.append(time.time())
    
    def get_count(self) -> int:
        """Get request count in current window"""
        self._cleanup()
        return len(self.requests)


class RateLimiter:
    """Main rate limiter using token bucket and sliding window"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
    
    def _get_client_id(self, request: Request) -> Optional[str]:
        """Extract client identifier (IP or user)"""
        client_ip = request.client.host if request.client else "unknown"
        user = None
        
        # Try to get user from headers
        if self.config.enable_by_user:
            auth_header = request.headers.get("X-User-ID")
            if auth_header:
                user = auth_header
        
        if user:
            return f"user:{user}"
        elif self.config.enable_by_ip:
            return f"ip:{client_ip}"
        else:
            return None
    
    def _get_bucket(self, client_id: str) -> TokenBucket:
        """Get or create token bucket for client"""
        if client_id not in self.token_buckets:
            # Refill rate: requests_per_minute / 60
            refill_rate = self.config.requests_per_minute / 60
            self.token_buckets[client_id] = TokenBucket(
                capacity=self.config.burst_size,
                refill_rate=refill_rate,
            )
        return self.token_buckets[client_id]
    
    def _get_window(self, client_id: str) -> SlidingWindowCounter:
        """Get or create sliding window counter for client"""
        if client_id not in self.sliding_windows:
            self.sliding_windows[client_id] = SlidingWindowCounter(window_size=3600)
        return self.sliding_windows[client_id]
    
    def is_allowed(self, client_id: str) -> Tuple[bool, Dict]:
        """
        Check if request is allowed
        
        Returns:
            Tuple of (allowed, headers_dict)
        """
        bucket = self._get_bucket(client_id)
        window = self._get_window(client_id)
        
        # Check minute limit
        if not bucket.consume():
            return False, {
                "X-RateLimit-Limit": str(self.config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 60),
            }
        
        # Check hourly limit
        window.add_request()
        if window.get_count() > self.config.requests_per_hour:
            return False, {
                "X-RateLimit-Limit": str(self.config.requests_per_hour),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 3600),
            }
        
        return True, {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(int(bucket.get_remaining())),
            "X-RateLimit-Reset": str(int(time.time()) + 60),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.rate_limiter = RateLimiter(self.config)
    
    async def dispatch(self, request: Request, call_next):
        # Skip exempt paths
        if request.url.path in self.config.exempt_paths:
            response = await call_next(request)
            return response
        
        # Get client identifier
        client_id = self.rate_limiter._get_client_id(request)
        if not client_id:
            response = await call_next(request)
            return response
        
        # Check rate limit
        allowed, headers = self.rate_limiter.is_allowed(client_id)
        
        # Log rate limit check
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id}")
        
        # Add rate limit headers
        response = await call_next(request) if allowed else JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "client_id": client_id,
                "retry_after": 60,
            },
        )
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# Export for use in main.py
__all__ = ["RateLimitMiddleware", "RateLimitConfig", "RateLimiter"]
