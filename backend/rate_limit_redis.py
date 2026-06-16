"""Redis-backed rate limiter with in-memory fallback."""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


async def check_rate_limit(
    redis_client,
    key: str,
    limit: int,
    window: int,
) -> bool:
    """
    Fixed-window rate limit check using Redis INCR + EXPIRE.
    Returns True if the request is allowed, False if limit exceeded.
    Falls back to True (allow) on any Redis error.
    """
    if redis_client is None:
        return True
    try:
        bucket = int(time.time() // window)
        redis_key = f"rl:{key}:{bucket}"
        count = await redis_client.incr(redis_key)
        if count == 1:
            await redis_client.expire(redis_key, window)
        return count <= limit
    except Exception as e:
        logger.warning(f"[rate_limit] Redis error, allowing request: {e}")
        return True


async def connect_redis(url: str):
    """
    Connect to Redis and return the async client, or None if unavailable.
    """
    if not url:
        return None
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(url, socket_connect_timeout=2, socket_timeout=1)
        await client.ping()
        logger.info(f"Redis rate limiter connected: {url}")
        return client
    except Exception as e:
        logger.warning(f"Redis unavailable ({url}), using in-memory rate limiter: {e}")
        return None
