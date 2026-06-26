"""Add multi-tenancy tables and tenant_id column to users.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_namespaces (
            tenant_id TEXT NOT NULL REFERENCES tenants(id),
            namespace TEXT NOT NULL,
            PRIMARY KEY (tenant_id, namespace)
        );
        """)
        op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_namespaces_ns ON tenant_namespaces(namespace);")
        # Add tenant_id to users (nullable — NULL means super-admin)
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id TEXT REFERENCES tenants(id);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users(tenant_id);")
    else:
        # SQLite
        op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_namespaces (
            tenant_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            PRIMARY KEY (tenant_id, namespace),
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        );
        """)
        op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_namespaces_ns ON tenant_namespaces(namespace);")
        # SQLite doesn't support ADD COLUMN with FK, so add without
        try:
            op.execute("ALTER TABLE users ADD COLUMN tenant_id TEXT;")
        except Exception:
            pass  # Column may already exist


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS tenant_id;")
        op.execute("DROP TABLE IF EXISTS tenant_namespaces;")
        op.execute("DROP TABLE IF EXISTS tenants;")
    else:
        # SQLite doesn't support DROP COLUMN easily, skip
        op.execute("DROP TABLE IF EXISTS tenant_namespaces;")
        op.execute("DROP TABLE IF EXISTS tenants;")
