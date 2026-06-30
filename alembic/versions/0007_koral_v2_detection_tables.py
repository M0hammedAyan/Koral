"""Add KORAL v2 detection engine tables.

Creates:
  - incidents_v2 (partitioned, UUID-based, JSONB evidence)
  - alerts_v2 (partitioned, tier-based routing)
  - pod_profiles (resource optimizer output)
  - few_shot_examples (LLM ICL store)
  - baselines (STL seasonal baselines per metric)
  - approval_requests_v2 (action approval gate)

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        # Enable uuid-ossp for gen_random_uuid
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

        # Incidents v2 — partitioned by started_at
        op.execute("""
        CREATE TABLE IF NOT EXISTS incidents_v2 (
            id UUID DEFAULT gen_random_uuid(),
            namespace VARCHAR(255) NOT NULL,
            pod_name VARCHAR(255) NOT NULL,
            started_at TIMESTAMPTZ NOT NULL,
            resolved_at TIMESTAMPTZ,
            root_cause VARCHAR(50) NOT NULL,
            attack_subtype VARCHAR(50),
            confidence FLOAT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '[]',
            anomaly_scores JSONB NOT NULL DEFAULT '{}',
            actions_taken JSONB NOT NULL DEFAULT '[]',
            service_impact VARCHAR(20) NOT NULL DEFAULT 'NONE',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (id, started_at)
        ) PARTITION BY RANGE (started_at);
        """)

        # Create monthly partitions for incidents_v2 (current + next 3 months)
        op.execute("""
        CREATE TABLE IF NOT EXISTS incidents_v2_default PARTITION OF incidents_v2 DEFAULT;
        """)

        # Alerts v2 — partitioned by sent_at
        op.execute("""
        CREATE TABLE IF NOT EXISTS alerts_v2 (
            id UUID DEFAULT gen_random_uuid(),
            incident_id UUID,
            tier INTEGER NOT NULL,
            channel VARCHAR(50) NOT NULL,
            pod_name VARCHAR(255) NOT NULL,
            namespace VARCHAR(255) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMPTZ NOT NULL,
            acknowledged_at TIMESTAMPTZ,
            acknowledged_by VARCHAR(255),
            PRIMARY KEY (id, sent_at)
        ) PARTITION BY RANGE (sent_at);
        """)

        op.execute("""
        CREATE TABLE IF NOT EXISTS alerts_v2_default PARTITION OF alerts_v2 DEFAULT;
        """)

        # Pod Profiles (resource optimizer)
        op.execute("""
        CREATE TABLE IF NOT EXISTS pod_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            namespace VARCHAR(255) NOT NULL,
            pod_name VARCHAR(255) NOT NULL,
            profiled_at TIMESTAMPTZ NOT NULL,
            profile_class VARCHAR(50) NOT NULL,
            avg_cpu_ratio FLOAT,
            avg_mem_ratio FLOAT,
            burstiness FLOAT,
            recommendation JSONB,
            estimated_savings JSONB
        );
        """)

        # Few-shot examples (LLM ICL store)
        op.execute("""
        CREATE TABLE IF NOT EXISTS few_shot_examples (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            root_cause VARCHAR(50) NOT NULL,
            attack_subtype VARCHAR(50),
            metric_signature JSONB NOT NULL,
            incident_summary TEXT NOT NULL,
            feedback_score INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

        # Baselines (STL seasonal components per metric)
        op.execute("""
        CREATE TABLE IF NOT EXISTS baselines (
            namespace VARCHAR(255) NOT NULL,
            pod_name VARCHAR(255) NOT NULL,
            metric_name VARCHAR(255) NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            trend_slope FLOAT,
            seasonal_components JSONB,
            residual_std FLOAT,
            PRIMARY KEY (namespace, pod_name, metric_name)
        );
        """)

        # Approval requests v2
        op.execute("""
        CREATE TABLE IF NOT EXISTS approval_requests_v2 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            incident_id UUID,
            action_type VARCHAR(100) NOT NULL,
            pod_name VARCHAR(255) NOT NULL,
            namespace VARCHAR(255) NOT NULL,
            requested_at TIMESTAMPTZ NOT NULL,
            status VARCHAR(20) DEFAULT 'PENDING',
            responded_at TIMESTAMPTZ,
            responded_by VARCHAR(255),
            expires_at TIMESTAMPTZ
        );
        """)

        # Indexes
        op.execute("CREATE INDEX IF NOT EXISTS ix_incidents_v2_namespace ON incidents_v2 (namespace);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_incidents_v2_root_cause ON incidents_v2 (root_cause);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_incidents_v2_pod ON incidents_v2 (pod_name);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_v2_tier ON alerts_v2 (tier);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_v2_namespace ON alerts_v2 (namespace);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_pod_profiles_namespace ON pod_profiles (namespace, pod_name);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_few_shot_root_cause ON few_shot_examples (root_cause);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_baselines_namespace ON baselines (namespace);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_approval_v2_status ON approval_requests_v2 (status);")

    else:
        # SQLite — same structure without partitioning or UUID extensions
        op.execute("""
        CREATE TABLE IF NOT EXISTS incidents_v2 (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            pod_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            resolved_at TEXT,
            root_cause TEXT NOT NULL,
            attack_subtype TEXT,
            confidence REAL NOT NULL,
            evidence TEXT NOT NULL DEFAULT '[]',
            anomaly_scores TEXT NOT NULL DEFAULT '{}',
            actions_taken TEXT NOT NULL DEFAULT '[]',
            service_impact TEXT NOT NULL DEFAULT 'NONE',
            created_at TEXT
        );
        """)

        op.execute("""
        CREATE TABLE IF NOT EXISTS alerts_v2 (
            id TEXT PRIMARY KEY,
            incident_id TEXT,
            tier INTEGER NOT NULL,
            channel TEXT NOT NULL,
            pod_name TEXT NOT NULL,
            namespace TEXT NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            acknowledged_at TEXT,
            acknowledged_by TEXT
        );
        """)

        op.execute("""
        CREATE TABLE IF NOT EXISTS pod_profiles (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            pod_name TEXT NOT NULL,
            profiled_at TEXT NOT NULL,
            profile_class TEXT NOT NULL,
            avg_cpu_ratio REAL,
            avg_mem_ratio REAL,
            burstiness REAL,
            recommendation TEXT,
            estimated_savings TEXT
        );
        """)

        op.execute("""
        CREATE TABLE IF NOT EXISTS few_shot_examples (
            id TEXT PRIMARY KEY,
            root_cause TEXT NOT NULL,
            attack_subtype TEXT,
            metric_signature TEXT NOT NULL,
            incident_summary TEXT NOT NULL,
            feedback_score INTEGER,
            created_at TEXT
        );
        """)

        op.execute("""
        CREATE TABLE IF NOT EXISTS baselines (
            namespace TEXT NOT NULL,
            pod_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            trend_slope REAL,
            seasonal_components TEXT,
            residual_std REAL,
            PRIMARY KEY (namespace, pod_name, metric_name)
        );
        """)

        op.execute("""
        CREATE TABLE IF NOT EXISTS approval_requests_v2 (
            id TEXT PRIMARY KEY,
            incident_id TEXT,
            action_type TEXT NOT NULL,
            pod_name TEXT NOT NULL,
            namespace TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            responded_at TEXT,
            responded_by TEXT,
            expires_at TEXT
        );
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS approval_requests_v2;")
    op.execute("DROP TABLE IF EXISTS baselines;")
    op.execute("DROP TABLE IF EXISTS few_shot_examples;")
    op.execute("DROP TABLE IF EXISTS pod_profiles;")
    op.execute("DROP TABLE IF EXISTS alerts_v2;")
    op.execute("DROP TABLE IF EXISTS incidents_v2;")
