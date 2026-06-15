# AIDER.md

## Project

KORAL is a production-grade AI operations platform that combines:

* Multi-agent orchestration
* OpenClaw browser automation
* Secure sandbox execution
* PostgreSQL memory and persistence
* Telegram and Slack integrations
* Observability with Prometheus and Grafana
* Docker and Kubernetes deployment
* MCP-based tool ecosystem

This repository is evolving from a hackathon prototype into a production SaaS product.

---

# Agent Rules

## Primary Goal

Prioritize:

1. Reliability
2. Security
3. Maintainability
4. Scalability
5. Cost efficiency

Do not optimize for demos, mockups, shortcuts, or temporary hacks.

---

# Token Usage

Minimize token consumption.

Rules:

* Never rewrite entire files when only a small section changes.
* Return unified diffs whenever possible.
* Summarize findings instead of dumping logs.
* Avoid repeating repository context.
* Keep responses concise.
* Only expand when explicitly requested.

---

# Code Quality Requirements

All code must:

* Pass linting
* Pass type checking
* Pass tests
* Use environment variables for secrets
* Include structured logging
* Include error handling
* Include retry mechanisms where appropriate

Never hardcode:

* API keys
* Tokens
* Passwords
* Webhook URLs
* Database credentials

---

# Architecture Principles

## Backend

Preferred stack:

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* PgBouncer

## Frontend

Preferred stack:

* React
* TypeScript
* Vite

## Infrastructure

Preferred stack:

* Docker
* Kubernetes
* Prometheus
* Grafana
* GitHub Actions

---

# Database Rules

Use PostgreSQL only.

Requirements:

* SQLAlchemy models
* Alembic migrations
* Connection pooling via PgBouncer
* No destructive migrations without approval
* No dropping tables automatically

---

# Sandbox Rules

All code execution must occur inside the sandbox.

Requirements:

* Resource limits
* Timeout limits
* Network restrictions
* Filesystem isolation
* Audit logging

Never execute user code directly on the host.

---

# OpenClaw Rules

OpenClaw is the primary browser automation layer.

Requirements:

* Retry logic
* Timeout protection
* Structured logging
* Graceful failure handling

Never store browser credentials in source control.

---

# Observability

Every service should expose:

* Health endpoint
* Metrics endpoint
* Structured logs

Prometheus metrics required for:

* Request latency
* Error rates
* Queue sizes
* Agent execution times

---

# Security Rules

Always:

* Validate inputs
* Sanitize outputs
* Use least privilege
* Use environment variables
* Mask secrets in logs

Never:

* Commit secrets
* Commit .env files
* Disable authentication
* Disable authorization
* Bypass security checks

---

# CI/CD Rules

GitHub Actions must:

* Run tests
* Run linting
* Build Docker images
* Validate Kubernetes manifests

Fail fast on:

* Missing dependencies
* Failing tests
* Security issues

---

# MCP Usage Priority

Use MCPs only when needed.

Priority order:

1. Filesystem MCP
2. GitHub MCP
3. PostgreSQL MCP
4. Docker MCP
5. Kubernetes MCP
6. Prometheus MCP
7. Grafana MCP
8. Slack MCP
9. Telegram MCP

Avoid unnecessary MCP calls.

---

# Repository Cleanup Rules

Remove:

* Duplicate files
* Obsolete documentation
* Mock implementations
* Temporary test artifacts
* Dead code

Keep:

* README.md
* CLAUDE.md
* Architecture docs
* Deployment docs
* API documentation

---

# Decision Making

When multiple approaches exist:

1. Choose production-safe solution.
2. Choose maintainable solution.
3. Choose secure solution.
4. Choose scalable solution.
5. Explain tradeoffs briefly.

Do not choose the quickest solution if it increases technical debt.

---

# Output Format

When completing tasks:

1. Summary
2. Files changed
3. Validation performed
4. Risks
5. Recommended next step

Keep responses concise and token-efficient.
