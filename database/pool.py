"""Shared SQLAlchemy pool for PostgreSQL-backed KORAL services."""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool


@lru_cache(maxsize=1)
def get_engine():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url and "#" in database_url and "%23" not in database_url:
        database_url = ""
    if not database_url:
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_name = os.getenv("DB_NAME", "koral")
        db_user = os.getenv("DB_USER", "koral")
        db_pass = os.getenv("DB_PASS", "")
        database_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        future=True,
    )


def get_pool_status() -> dict[str, float | int]:
    engine = get_engine()
    pool = engine.pool
    checked_out = int(getattr(pool, "checkedout", lambda: 0)())
    checked_in = int(getattr(pool, "checkedin", lambda: 0)())
    pool_size = int(getattr(pool, "size", lambda: 0)())
    overflow = int(getattr(pool, "overflow", lambda: 0)())
    utilization = (checked_out / pool_size) if pool_size else 0.0
    return {
        "active_connections": checked_out,
        "checked_in": checked_in,
        "pool_size": pool_size,
        "overflow": overflow,
        "pool_utilization": utilization,
    }


def install_psycopg2_pool() -> None:
    import psycopg2

    if getattr(psycopg2, "_koral_pool_installed", False):
        return

    def pooled_connect(*args, **kwargs):
        return get_engine().raw_connection()

    psycopg2.connect = pooled_connect
    psycopg2._koral_pool_installed = True


def close_pool() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()