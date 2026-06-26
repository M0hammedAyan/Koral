"""
Multi-tenancy module for KORAL.

Implements row-level tenant isolation:
  - Each user belongs to exactly one tenant
  - All data queries are automatically filtered by tenant_id
  - Tenant context is resolved from the authenticated user
  - ADMIN users with tenant_id=NULL are "super-admins" (see all tenants)

Tenant model:
  - A tenant represents a team/org that manages specific K8s namespaces
  - Namespaces are mapped to tenants (one namespace belongs to one tenant)
  - Anomalies/incidents are scoped by namespace → automatically tenant-scoped
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request

from backend.database import query_one, query_all, execute, DB_TYPE

logger = logging.getLogger(__name__)


def _ph() -> str:
    """Get SQL placeholder for current DB type."""
    return "%s" if DB_TYPE == "postgres" else "?"


class TenantContext:
    """Resolved tenant context for the current request."""

    def __init__(self, tenant_id: Optional[str], tenant_name: Optional[str], is_super_admin: bool = False):
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.is_super_admin = is_super_admin

    def can_access_tenant(self, target_tenant_id: str) -> bool:
        """Check if this context has access to a given tenant."""
        if self.is_super_admin:
            return True
        return self.tenant_id == target_tenant_id

    def get_filter_sql(self, column: str = "tenant_id") -> tuple:
        """
        Return (sql_fragment, params) to filter queries by tenant.
        Super-admins get no filter (empty string).
        """
        if self.is_super_admin:
            return ("", ())
        return (f" AND {column}={_ph()}", (self.tenant_id,))


def resolve_tenant_from_user(username: str) -> TenantContext:
    """
    Look up the tenant for a given user.
    Returns TenantContext with tenant info or super-admin flag.
    """
    if not username or username.startswith("env:"):
        # Env-var based keys are super-admins (backward compat)
        return TenantContext(tenant_id=None, tenant_name=None, is_super_admin=True)

    sql = f"SELECT tenant_id FROM users WHERE username={_ph()}"
    user = query_one(sql, (username,))

    if not user or not user.get("tenant_id"):
        # Users without tenant_id are super-admins
        return TenantContext(tenant_id=None, tenant_name=None, is_super_admin=True)

    tenant_id = user["tenant_id"]
    sql = f"SELECT name FROM tenants WHERE id={_ph()} AND is_active=1"
    tenant = query_one(sql, (tenant_id,))

    if not tenant:
        return TenantContext(tenant_id=tenant_id, tenant_name="unknown", is_super_admin=False)

    return TenantContext(tenant_id=tenant_id, tenant_name=tenant["name"], is_super_admin=False)


def get_tenant_namespaces(tenant_id: str) -> list:
    """Get all K8s namespaces assigned to a tenant."""
    sql = f"SELECT namespace FROM tenant_namespaces WHERE tenant_id={_ph()}"
    rows = query_all(sql, (tenant_id,))
    return [r["namespace"] for r in rows]
