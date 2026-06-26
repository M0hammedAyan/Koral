"""Add users table for user management API.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(64), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('role', sa.String(16), nullable=False, server_default='viewer'),
        sa.Column('api_key_hash', sa.String(64), nullable=False),
        sa.Column('key_expires_at', sa.String(64), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.String(64), nullable=False),
        sa.Column('updated_at', sa.String(64), nullable=False),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_api_key_hash', 'users', ['api_key_hash'])
    op.create_index('ix_users_role', 'users', ['role'])


def downgrade() -> None:
    op.drop_index('ix_users_role')
    op.drop_index('ix_users_api_key_hash')
    op.drop_index('ix_users_email')
    op.drop_index('ix_users_username')
    op.drop_table('users')
