"""
Database module for KORAL - supports SQLite (dev) and PostgreSQL (prod)
"""
import os
import json
import time
from contextlib import nullcontext
from typing import List, Dict, Optional
from datetime import datetime, timezone
from database.pool import close_pool, install_psycopg2_pool, get_pool_status

try:
    from prometheus_client import Histogram, Gauge
except Exception:
    Histogram = Gauge = None

try:
    from opentelemetry import trace
    TRACER = trace.get_tracer(__name__)
except Exception:
    TRACER = None

DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # "sqlite" or "postgres"

if Histogram is not None:
    DB_QUERY_DURATION = Histogram(
        "koral_db_query_duration_seconds",
        "Database query duration by operation",
        ["operation"],
    )
    DB_ACTIVE_CONNECTIONS = Gauge(
        "koral_db_active_connections",
        "Active database connections in the shared pool",
    )
    DB_POOL_UTILIZATION = Gauge(
        "koral_db_pool_utilization",
        "Database pool utilization ratio",
    )
else:
    DB_QUERY_DURATION = None
    DB_ACTIVE_CONNECTIONS = None
    DB_POOL_UTILIZATION = None


def _observe_pool_metrics() -> None:
    if DB_ACTIVE_CONNECTIONS is None or DB_POOL_UTILIZATION is None:
        return
    try:
        status = get_pool_status()
        DB_ACTIVE_CONNECTIONS.set(status["active_connections"])
        DB_POOL_UTILIZATION.set(status["pool_utilization"])
    except Exception:
        pass

# ── SQLite Setup ───────────────────────────────────────────────────
if DB_TYPE == "sqlite":
    import sqlite3
    
    DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "koral.db"))
    
    def _get_db():
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

# ── PostgreSQL Setup ───────────────────────────────────────────────
else:
    install_psycopg2_pool()
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "koral")
    DB_USER = os.getenv("DB_USER", "koral")
    DB_PASS = os.getenv("DB_PASS", "")
    
    def _get_db():
        # respect DB connect timeout env var
        connect_timeout = int(os.getenv("DB_TIMEOUT_DB", "3"))
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=connect_timeout,
        )
        return conn


# ── Initialize Database Schema ─────────────────────────────────────
def init_db():
    """Initialize database schema"""
    conn = _get_db()
    try:
        cursor = conn.cursor()
        if DB_TYPE == "sqlite":
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT, pod TEXT, namespace TEXT, metric TEXT,
                    value REAL, unit TEXT, z_score REAL, is_anomaly INTEGER,
                    window_size INTEGER, source TEXT, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE, timestamp TEXT, namespace TEXT,
                    severity TEXT, root_cause TEXT, summary TEXT,
                    affected_pods TEXT, primary_metric TEXT, confidence REAL,
                    evidence_count INTEGER, ai_explanation TEXT, ai_action TEXT,
                    ai_model TEXT, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS remediation_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT UNIQUE, incident_id TEXT NOT NULL,
                    severity TEXT, root_cause TEXT, recommended_action TEXT,
                    confidence REAL, affected_pods TEXT, parameters TEXT,
                    ai_reasoning TEXT, status TEXT DEFAULT 'pending',
                    created_at TEXT, expires_at TEXT
                );
                CREATE TABLE IF NOT EXISTS approval_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_id TEXT UNIQUE, plan_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL, requested_by TEXT, approved_by TEXT,
                    approval_status TEXT, approval_reason TEXT, email_sent_at TEXT,
                    email_opened_at TEXT, response_timestamp TEXT, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT UNIQUE, plan_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL, command TEXT, parameters TEXT,
                    execution_status TEXT, start_time TEXT, end_time TEXT,
                    duration_ms INTEGER, stdout TEXT, stderr TEXT,
                    exit_code INTEGER, blast_radius INTEGER, pod_failures TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS verification_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    verification_id TEXT UNIQUE, execution_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL, incident_id TEXT NOT NULL,
                    verification_status TEXT, pre_metrics TEXT, post_metrics TEXT,
                    improvement_percent REAL, anomaly_resolved INTEGER,
                    z_score_delta REAL, verification_details TEXT,
                    duration_ms INTEGER, created_at TEXT
                );
            """)
        else:
            cursor.execute("SELECT 1")
    finally:
        conn.commit()
        conn.close()


def close_db_pool():
    """Dispose the shared PostgreSQL pool on shutdown."""
    close_pool()


# ── Query Helpers ──────────────────────────────────────────────────
def query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    """Execute query and return first row as dict"""
    started = time.perf_counter()
    conn = _get_db()
    try:
        span_ctx = TRACER.start_as_current_span("db.query_one") if TRACER else nullcontext()
        with span_ctx as span:
            if span is not None:
                span.set_attribute("db.operation", "query_one")
            if DB_TYPE == "sqlite":
                cursor = conn.cursor()
                cursor.execute(sql, params)
                row = cursor.fetchone()
                return dict(row) if row else None
            else:  # PostgreSQL
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(sql, params)
                return cursor.fetchone()
    finally:
        if DB_QUERY_DURATION is not None:
            DB_QUERY_DURATION.labels(operation="query_one").observe(time.perf_counter() - started)
        _observe_pool_metrics()
        conn.close()


def query_all(sql: str, params: tuple = ()) -> List[dict]:
    """Execute query and return all rows as list of dicts"""
    started = time.perf_counter()
    conn = _get_db()
    try:
        span_ctx = TRACER.start_as_current_span("db.query_all") if TRACER else nullcontext()
        with span_ctx as span:
            if span is not None:
                span.set_attribute("db.operation", "query_all")
            if DB_TYPE == "sqlite":
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:  # PostgreSQL
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(sql, params)
                return cursor.fetchall()
    finally:
        if DB_QUERY_DURATION is not None:
            DB_QUERY_DURATION.labels(operation="query_all").observe(time.perf_counter() - started)
        _observe_pool_metrics()
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """Execute INSERT/UPDATE/DELETE and return last insert id or rows affected"""
    started = time.perf_counter()
    conn = _get_db()
    try:
        span_ctx = TRACER.start_as_current_span("db.execute") if TRACER else nullcontext()
        with span_ctx as span:
            if span is not None:
                span.set_attribute("db.operation", "execute")
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()

            if DB_TYPE == "sqlite":
                return cursor.lastrowid
            else:  # PostgreSQL
                return cursor.rowcount
    finally:
        if DB_QUERY_DURATION is not None:
            DB_QUERY_DURATION.labels(operation="execute").observe(time.perf_counter() - started)
        _observe_pool_metrics()
        conn.close()


def execute_many(sql: str, params_list: List[tuple]) -> int:
    """Execute multiple INSERT/UPDATE/DELETE"""
    started = time.perf_counter()
    conn = _get_db()
    try:
        span_ctx = TRACER.start_as_current_span("db.execute_many") if TRACER else nullcontext()
        with span_ctx as span:
            if span is not None:
                span.set_attribute("db.operation", "execute_many")
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()

            if DB_TYPE == "sqlite":
                return cursor.lastrowid
            else:  # PostgreSQL
                return cursor.rowcount
    finally:
        if DB_QUERY_DURATION is not None:
            DB_QUERY_DURATION.labels(operation="execute_many").observe(time.perf_counter() - started)
        _observe_pool_metrics()
        conn.close()


# ── Convenience functions ──────────────────────────────────────────
def insert_anomaly(timestamp, pod, namespace, metric, value, unit, z_score, is_anomaly, window_size, source):
    """Insert an anomaly record"""
    now = datetime.now(timezone.utc).isoformat()
    sql = """
        INSERT INTO anomalies 
        (timestamp, pod, namespace, metric, value, unit, z_score, is_anomaly, window_size, source, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """ if DB_TYPE == "postgres" else """
        INSERT INTO anomalies 
        (timestamp, pod, namespace, metric, value, unit, z_score, is_anomaly, window_size, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    return execute(sql, (timestamp, pod, namespace, metric, value, unit, z_score, is_anomaly, window_size, source, now))


def insert_incident(incident_id, timestamp, namespace, severity, root_cause, summary, affected_pods, primary_metric, confidence, evidence_count):
    """Insert an incident record"""
    now = datetime.now(timezone.utc).isoformat()
    pods_str = json.dumps(affected_pods) if isinstance(affected_pods, list) else affected_pods
    sql = """
        INSERT INTO incidents 
        (incident_id, timestamp, namespace, severity, root_cause, summary, affected_pods, primary_metric, confidence, evidence_count, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """ if DB_TYPE == "postgres" else """
        INSERT INTO incidents 
        (incident_id, timestamp, namespace, severity, root_cause, summary, affected_pods, primary_metric, confidence, evidence_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    return execute(sql, (incident_id, timestamp, namespace, severity, root_cause, summary, pods_str, primary_metric, confidence, evidence_count, now))


def update_incident(incident_id, ai_explanation, ai_action, ai_model):
    """Update incident with AI analysis"""
    sql = """
        UPDATE incidents SET ai_explanation=%s, ai_action=%s, ai_model=%s WHERE incident_id=%s
    """ if DB_TYPE == "postgres" else """
        UPDATE incidents SET ai_explanation=?, ai_action=?, ai_model=? WHERE incident_id=?
    """
    return execute(sql, (ai_explanation, ai_action, ai_model, incident_id))


def get_incidents(limit=100):
    """Get recent incidents"""
    sql = "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT %s" if DB_TYPE == "postgres" else "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?"
    return query_all(sql, (limit,))


def get_incident(incident_id):
    """Get specific incident"""
    sql = "SELECT * FROM incidents WHERE incident_id=%s" if DB_TYPE == "postgres" else "SELECT * FROM incidents WHERE incident_id=?"
    return query_one(sql, (incident_id,))


# Note: init_db() is now called from main.py lifespan handler
# to ensure database is ready before initialization
