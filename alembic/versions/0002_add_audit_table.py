"""add_audit_table

Revision ID: 0002_add_audit_table
Revises: 0001_initial_schema
Create Date: 2026-06-16 00:00:00.000000
"""
from alembic import op

revision = '0002_add_audit_table'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS audit (
        id         SERIAL PRIMARY KEY,
        event_type TEXT NOT NULL,
        actor      TEXT,
        target     TEXT,
        payload    TEXT,
        created_at TEXT NOT NULL
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit (event_type);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit (actor);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit (created_at);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit;")
