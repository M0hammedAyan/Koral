"""Add federated_clusters table for multi-cluster federation.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS federated_clusters (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        api_endpoint TEXT NOT NULL,
        region TEXT DEFAULT '',
        provider TEXT DEFAULT '',
        cluster_token TEXT NOT NULL,
        tenant_id TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        status TEXT DEFAULT 'registered',
        node_count INTEGER DEFAULT 0,
        pod_count INTEGER DEFAULT 0,
        anomaly_count_24h INTEGER DEFAULT 0,
        incident_count_24h INTEGER DEFAULT 0,
        last_heartbeat TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_federated_clusters_name ON federated_clusters(name);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_federated_clusters_tenant ON federated_clusters(tenant_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS federated_clusters;")
