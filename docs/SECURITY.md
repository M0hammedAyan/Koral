# KORAL Security Hardening Guide

This document consolidates the security hardening guidance for KORAL (merged from Phase 2 security materials).

## Overview
Phase 2 implements comprehensive security infrastructure including secrets management, authentication hardening, TLS/mTLS, audit logging, and automated secret rotation.

## Key Controls

### Secrets Management (Sealed Secrets)
- Deploy sealed-secrets controller and use sealed secret manifests for git-friendly encrypted secrets.

### Pod Security Standards
- Enforce Restricted PSS; run workloads non-root, read-only root filesystem, drop capabilities.

### Audit Logging
- Collect Kubernetes API audit events; forward to centralized log store with retention policies.

### Enhanced Authentication
- Use `backend/auth_enhanced.py` and `backend/rate_limit.py` for stronger auth and rate-limiting.

### TLS / mTLS
- Use cert-manager for ingress TLS and implement service-to-service mTLS where required.

### Secret Rotation
- Implement CronJobs for periodic rotation of JWT, API keys, and DB credentials with graceful rollout.

## Operational Steps (summary)
1. Deploy sealed-secrets and backup keys.  
2. Label namespaces with PSS enforcement.  
3. Apply audit logging manifests and configure retention.  
4. Deploy enhanced auth middleware and enable rate limiting.  
5. Deploy cert-manager and configure TLS/mTLS manifests.  
6. Create CronJobs for secret rotation and monitor success metrics.

## Monitoring & Alerts
- Monitor authentication failures, secret-rotation jobs, certificate expiry, and audit log ingestion.

For detailed implementation steps and manifest references see the original phase materials in the repository history.
