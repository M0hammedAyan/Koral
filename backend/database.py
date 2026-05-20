"""
Database module for KORAL - supports SQLite (dev) and PostgreSQL (prod)
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone
from database.pool import close_pool, install_psycopg2_pool

DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # "sqlite" or "postgres"

# ── SQLite Setup ───────────────────────────────────────────────────
if DB_TYPE == "sqlite":
    import sqlite3
    
    DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "koral.db"))
    
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
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn


# ── Initialize Database Schema ─────────────────────────────────────
def init_db():
    """Initialize database schema"""
    conn = _get_db()
    
    if DB_TYPE == "sqlite":
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER, pod TEXT, namespace TEXT,
                metric TEXT, value REAL, unit TEXT,
                z_score REAL, is_anomaly INTEGER,
                window_size INTEGER, source TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT UNIQUE,
                timestamp INTEGER, namespace TEXT,
                severity TEXT, root_cause TEXT,
                summary TEXT, affected_pods TEXT,
                primary_metric TEXT, confidence REAL,
                evidence_count INTEGER, created_at TEXT,
                ai_explanation TEXT, ai_action TEXT,
                ai_model TEXT
            );
            CREATE TABLE IF NOT EXISTS fix_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT,
                fix_type TEXT,
                fix_description TEXT,
                applied_by TEXT,
                success INTEGER,
                error_message TEXT,
                kubectl_command TEXT,
                timestamp TEXT,
                created_at TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY, label TEXT, status TEXT
            );
            CREATE TABLE IF NOT EXISTS graph_edges (
                source TEXT, target TEXT,
                PRIMARY KEY (source, target)
            );
        """)
    else:  # PostgreSQL
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id SERIAL PRIMARY KEY,
                timestamp BIGINT, pod TEXT, namespace TEXT,
                metric TEXT, value FLOAT, unit TEXT,
                z_score FLOAT, is_anomaly INTEGER,
                window_size INTEGER, source TEXT,
                created_at TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id SERIAL PRIMARY KEY,
                incident_id TEXT UNIQUE,
                timestamp BIGINT, namespace TEXT,
                severity TEXT, root_cause TEXT,
                summary TEXT, affected_pods TEXT,
                primary_metric TEXT, confidence FLOAT,
                evidence_count INTEGER, created_at TEXT,
                ai_explanation TEXT, ai_action TEXT,
                ai_model TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fix_history (
                id SERIAL PRIMARY KEY,
                incident_id TEXT,
                fix_type TEXT,
                fix_description TEXT,
                applied_by TEXT,
                success INTEGER,
                error_message TEXT,
                kubectl_command TEXT,
                timestamp TEXT,
                created_at TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY, label TEXT, status TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_edges (
                source TEXT, target TEXT,
                PRIMARY KEY (source, target)
            );
        """)
        conn.commit()
    
    conn.commit()
    conn.close()


def close_db_pool():
    """Dispose the shared PostgreSQL pool on shutdown."""
    close_pool()


# ── Query Helpers ──────────────────────────────────────────────────
def query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    """Execute query and return first row as dict"""
    conn = _get_db()
    try:
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
        conn.close()


def query_all(sql: str, params: tuple = ()) -> List[dict]:
    """Execute query and return all rows as list of dicts"""
    conn = _get_db()
    try:
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
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """Execute INSERT/UPDATE/DELETE and return last insert id or rows affected"""
    conn = _get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        
        if DB_TYPE == "sqlite":
            return cursor.lastrowid
        else:  # PostgreSQL
            return cursor.rowcount
    finally:
        conn.close()


def execute_many(sql: str, params_list: List[tuple]) -> int:
    """Execute multiple INSERT/UPDATE/DELETE"""
    conn = _get_db()
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        conn.commit()
        
        if DB_TYPE == "sqlite":
            return cursor.lastrowid
        else:  # PostgreSQL
            return cursor.rowcount
    finally:
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
