"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-05-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Core application tables
    op.execute("""
    CREATE TABLE IF NOT EXISTS anomalies (
        id SERIAL PRIMARY KEY,
        timestamp BIGINT,
        pod TEXT,
        namespace TEXT,
        metric TEXT,
        value FLOAT,
        unit TEXT,
        z_score FLOAT,
        is_anomaly INTEGER,
        window_size INTEGER,
        source TEXT,
        created_at TEXT
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id SERIAL PRIMARY KEY,
        incident_id TEXT UNIQUE,
        timestamp BIGINT,
        namespace TEXT,
        severity TEXT,
        root_cause TEXT,
        summary TEXT,
        affected_pods TEXT,
        primary_metric TEXT,
        confidence FLOAT,
        evidence_count INTEGER,
        created_at TEXT,
        ai_explanation TEXT,
        ai_action TEXT,
        ai_model TEXT
    );
    """)

    op.execute("""
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

    op.execute("""
    CREATE TABLE IF NOT EXISTS graph_nodes (
        id TEXT PRIMARY KEY,
        label TEXT,
        status TEXT
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS graph_edges (
        source TEXT,
        target TEXT,
        PRIMARY KEY (source, target)
    );
    """)

    # Remediation extension tables
    op.execute("""
    CREATE TABLE IF NOT EXISTS remediation_plans (
        id SERIAL PRIMARY KEY,
        plan_id TEXT UNIQUE,
        incident_id TEXT NOT NULL,
        severity TEXT,
        root_cause TEXT,
        recommended_action TEXT,
        confidence FLOAT,
        affected_pods TEXT,
        parameters TEXT,
        ai_reasoning TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        expires_at TEXT,
        FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS approval_history (
        id SERIAL PRIMARY KEY,
        approval_id TEXT UNIQUE,
        plan_id TEXT NOT NULL,
        incident_id TEXT NOT NULL,
        requested_by TEXT,
        approved_by TEXT,
        approval_status TEXT,
        approval_reason TEXT,
        email_sent_at TEXT,
        email_opened_at TEXT,
        response_timestamp TEXT,
        created_at TEXT,
        FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
        FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS execution_log (
        id SERIAL PRIMARY KEY,
        execution_id TEXT UNIQUE,
        plan_id TEXT NOT NULL,
        incident_id TEXT NOT NULL,
        command TEXT,
        parameters TEXT,
        execution_status TEXT,
        start_time TEXT,
        end_time TEXT,
        duration_ms INTEGER,
        stdout TEXT,
        stderr TEXT,
        exit_code INTEGER,
        blast_radius INTEGER,
        pod_failures TEXT,
        created_at TEXT,
        FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
        FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
    );
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS verification_results (
        id SERIAL PRIMARY KEY,
        verification_id TEXT UNIQUE,
        execution_id TEXT NOT NULL,
        plan_id TEXT NOT NULL,
        incident_id TEXT NOT NULL,
        verification_status TEXT,
        pre_metrics TEXT,
        post_metrics TEXT,
        improvement_percent FLOAT,
        anomaly_resolved INTEGER,
        z_score_delta FLOAT,
        verification_details TEXT,
        duration_ms INTEGER,
        created_at TEXT,
        FOREIGN KEY (execution_id) REFERENCES execution_log(execution_id),
        FOREIGN KEY (plan_id) REFERENCES remediation_plans(plan_id),
        FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
    );
    """)


def downgrade() -> None:
    # Drop remediation tables then core tables (non-destructive in prod, use with caution)
    op.execute("""
    DROP TABLE IF EXISTS verification_results;
    DROP TABLE IF EXISTS execution_log;
    DROP TABLE IF EXISTS approval_history;
    DROP TABLE IF EXISTS remediation_plans;
    DROP TABLE IF EXISTS graph_edges;
    DROP TABLE IF EXISTS graph_nodes;
    DROP TABLE IF EXISTS fix_history;
    DROP TABLE IF EXISTS incidents;
    DROP TABLE IF EXISTS anomalies;
    """)
