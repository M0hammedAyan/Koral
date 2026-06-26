"""
Shared SQLAlchemy connection pools for KORAL.

Supports:
  - Primary (read-write) pool: used for INSERT/UPDATE/DELETE
  - Read replica pool: used for SELECT queries (optional, falls back to primary)

Configuration:
  - DATABASE_URL / DB_* vars: primary connection
  - DATABASE_READ_URL / DB_READ_HOST: read replica connection (optional)

When DB_READ_HOST or DATABASE_READ_URL is set, read queries are automatically
routed to the replica. Otherwise, all queries go to the primary.
"""

from __future__ import annotations

import os
import logging
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


def _build_url(host_env: str = "DB_HOST", port_env: str = "DB_PORT", url_env: str = "DATABASE_URL") -> str:
    """Build a PostgreSQL connection URL from environment variables."""
    database_url = os.getenv(url_env, "").strip()

    # Sanitize
    if database_url and "#" in database_url and "%23" not in database_url:
        database_url = ""

    if not database_url:
        db_host = os.getenv(host_env, "localhost")
        db_port = int(os.getenv(port_env, "5432"))
        db_name = os.getenv("DB_NAME", "koral")
        db_user = os.getenv("DB_USER", "koral")
        db_pass = os.getenv("DB_PASS", "")
        database_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return database_url


def _create_pool(url: str, pool_size: int = 20, max_overflow: int = 10, label: str = "primary") -> Engine:
    """Create a SQLAlchemy engine with connection pooling."""
    engine = create_engine(
        url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_timeout=30,
        future=True,
    )
    logger.info(f"[db] {label} pool created: size={pool_size}, overflow={max_overflow}")
    return engine


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Get the primary (read-write) engine."""
    url = _build_url(host_env="DB_HOST", port_env="DB_PORT", url_env="DATABASE_URL")
    return _create_pool(url, pool_size=20, max_overflow=10, label="primary")


@lru_cache(maxsize=1)
def get_read_engine() -> Engine:
    """
    Get the read replica engine.

    Falls back to the primary engine if no read replica is configured.
    Configure via DB_READ_HOST or DATABASE_READ_URL.
    """
    read_url_env = os.getenv("DATABASE_READ_URL", "").strip()
    read_host = os.getenv("DB_READ_HOST", "").strip()

    if not read_url_env and not read_host:
        # No replica configured — use primary for reads
        logger.info("[db] No read replica configured, using primary for reads")
        return get_engine()

    if read_url_env:
        url = read_url_env
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        db_port = int(os.getenv("DB_READ_PORT", os.getenv("DB_PORT", "5432")))
        db_name = os.getenv("DB_NAME", "koral")
        db_user = os.getenv("DB_USER", "koral")
        db_pass = os.getenv("DB_PASS", "")
        url = f"postgresql+psycopg2://{db_user}:{db_pass}@{read_host}:{db_port}/{db_name}"

    return _create_pool(url, pool_size=30, max_overflow=15, label="read-replica")


def get_pool_status() -> dict[str, float | int]:
    """Get connection pool statistics for the primary engine."""
    engine = get_engine()
    pool = engine.pool
    checked_out = int(getattr(pool, "checkedout", lambda: 0)())
    checked_in = int(getattr(pool, "checkedin", lambda: 0)())
    pool_size = int(getattr(pool, "size", lambda: 0)())
    overflow = int(getattr(pool, "overflow", lambda: 0)())
    utilization = (checked_out / pool_size) if pool_size else 0.0

    status = {
        "active_connections": checked_out,
        "checked_in": checked_in,
        "pool_size": pool_size,
        "overflow": overflow,
        "pool_utilization": utilization,
    }

    # Add read replica stats if it's a separate pool
    try:
        read_engine = get_read_engine()
        if read_engine is not engine:
            read_pool = read_engine.pool
            status["read_active_connections"] = int(getattr(read_pool, "checkedout", lambda: 0)())
            status["read_pool_size"] = int(getattr(read_pool, "size", lambda: 0)())
            status["read_pool_utilization"] = (
                status["read_active_connections"] / status["read_pool_size"]
                if status["read_pool_size"] else 0.0
            )
    except Exception:
        pass

    return status


def install_psycopg2_pool() -> None:
    """No-op: pool is managed via SQLAlchemy engine in get_engine().
    Direct psycopg2.connect calls should bypass the pool."""
    pass


def close_pool() -> None:
    """Dispose both primary and read replica pools."""
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    if get_read_engine.cache_info().currsize:
        read_eng = get_read_engine()
        if read_eng is not get_engine():
            read_eng.dispose()
