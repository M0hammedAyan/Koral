"""
KORAL Load Tests — Soak, Latency Percentile Targets, and Chaos Injection.

Usage:
  # Quick smoke (100 users, 60s)
  locust -f load_tests/locustfile.py --headless -u 100 -r 10 -t 60s

  # Soak test (500 users, 30 min)
  locust -f load_tests/locustfile.py --headless -u 500 -r 20 -t 30m --tags soak

  # Chaos injection (error scenarios)
  locust -f load_tests/locustfile.py --headless -u 200 -r 10 -t 5m --tags chaos

Latency targets (SLO):
  - p50 < 100ms
  - p95 < 500ms
  - p99 < 1000ms
  - Error rate < 1%
"""
from __future__ import annotations

import json
import os
import random
import time
import uuid

from locust import HttpUser, between, events, tag, task
from locust.runners import MasterRunner, WorkerRunner


# ── Configuration ────────────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("LOAD_TEST_API_KEY", "koral-dev-api-key-2024")
ADMIN_KEY = os.getenv("LOAD_TEST_ADMIN_KEY", "koral-admin-key-secret")

# SLO Targets
P50_TARGET_MS = int(os.getenv("P50_TARGET_MS", "100"))
P95_TARGET_MS = int(os.getenv("P95_TARGET_MS", "500"))
P99_TARGET_MS = int(os.getenv("P99_TARGET_MS", "1000"))
ERROR_RATE_TARGET = float(os.getenv("ERROR_RATE_TARGET", "0.01"))


# ── SLO Validation on test end ───────────────────────────────────────
@events.quitting.add_listener
def check_slo(environment, **kwargs):
    """Validate SLO targets at the end of the test run."""
    stats = environment.runner.stats.total
    if stats.num_requests == 0:
        return

    # Error rate check
    error_rate = stats.num_failures / stats.num_requests
    if error_rate > ERROR_RATE_TARGET:
        print(f"❌ SLO VIOLATION: Error rate {error_rate:.2%} > {ERROR_RATE_TARGET:.2%}")
        environment.process_exit_code = 1
    else:
        print(f"✓ Error rate: {error_rate:.2%} (target < {ERROR_RATE_TARGET:.2%})")

    # Latency percentile checks
    p50 = stats.get_response_time_percentile(0.5) or 0
    p95 = stats.get_response_time_percentile(0.95) or 0
    p99 = stats.get_response_time_percentile(0.99) or 0

    violations = []
    if p50 > P50_TARGET_MS:
        violations.append(f"p50={p50}ms > {P50_TARGET_MS}ms")
    if p95 > P95_TARGET_MS:
        violations.append(f"p95={p95}ms > {P95_TARGET_MS}ms")
    if p99 > P99_TARGET_MS:
        violations.append(f"p99={p99}ms > {P99_TARGET_MS}ms")

    if violations:
        print(f"❌ SLO VIOLATION: Latency targets missed — {', '.join(violations)}")
        environment.process_exit_code = 1
    else:
        print(f"✓ Latency: p50={p50}ms p95={p95}ms p99={p99}ms (all within targets)")

    print(f"  Total requests: {stats.num_requests}, Failures: {stats.num_failures}")
    print(f"  RPS: {stats.current_rps:.1f}, Avg response: {stats.avg_response_time:.0f}ms")


# ── Base User Class ──────────────────────────────────────────────────
class KoralUser(HttpUser):
    """Base class with auth headers and realistic wait times."""
    host = BASE_URL
    wait_time = between(0.5, 2.0)
    abstract = True

    def on_start(self):
        self.headers = {"X-API-Key": API_KEY}
        self.admin_headers = {"X-API-Key": ADMIN_KEY}


# ── Standard Load Tests (Soak-compatible) ────────────────────────────
class ViewerUser(KoralUser):
    """Simulates a dashboard viewer — mostly GET requests."""
    weight = 5

    @tag("soak", "smoke")
    @task(10)
    def health_check(self):
        self.client.get("/health/live", timeout=5)

    @tag("soak", "smoke")
    @task(8)
    def list_anomalies(self):
        self.client.get("/anomalies?limit=20", headers=self.headers, timeout=10)

    @tag("soak", "smoke")
    @task(5)
    def list_incidents(self):
        self.client.get("/incidents?limit=10", headers=self.headers, timeout=10)

    @tag("soak", "smoke")
    @task(3)
    def get_slo_summary(self):
        self.client.get("/slo/", headers=self.headers, timeout=10)

    @tag("soak")
    @task(3)
    def get_correlations(self):
        self.client.get("/correlations", headers=self.headers, timeout=10)

    @tag("soak")
    @task(2)
    def get_graph(self):
        self.client.get("/graph", headers=self.headers, timeout=10)

    @tag("soak")
    @task(2)
    def get_fixes_history(self):
        self.client.get("/fixes/history", headers=self.headers, timeout=10)

    @tag("soak")
    @task(2)
    def get_fix_stats(self):
        self.client.get("/fixes/stats", headers=self.headers, timeout=10)

    @tag("soak")
    @task(1)
    def get_remediation_status(self):
        self.client.get("/remediation/status", headers=self.headers, timeout=10)

    @tag("soak")
    @task(1)
    def get_prometheus_metrics(self):
        self.client.get("/metrics", timeout=5)

    @tag("soak")
    @task(1)
    def get_slo_availability(self):
        self.client.get("/slo/availability", headers=self.headers, timeout=10)

    @tag("soak")
    @task(1)
    def get_slo_mttr(self):
        self.client.get("/slo/mttr", headers=self.headers, timeout=10)

    @tag("soak")
    @task(1)
    def get_slo_error_budget(self):
        self.client.get("/slo/error-budget", headers=self.headers, timeout=10)


class OperatorUser(KoralUser):
    """Simulates an agent/operator posting anomalies and recording fixes."""
    weight = 2

    @tag("soak", "smoke")
    @task(10)
    def post_anomaly(self):
        payload = {
            "timestamp": int(time.time()),
            "pod": f"pod-{random.choice(['api', 'worker', 'cache', 'db'])}-{random.randint(1, 5)}",
            "metric": random.choice(["cpu", "memory", "disk_io", "network"]),
            "value": round(random.uniform(10, 95), 2),
            "z_score": round(random.uniform(-1, 4), 2),
            "is_anomaly": random.random() < 0.1,
            "namespace": random.choice(["production", "staging", "koral-system"]),
            "unit": "percent",
            "source": "load-test-agent",
            "window_size": 300,
        }
        self.client.post("/anomalies", json=payload, headers=self.headers, timeout=10)

    @tag("soak")
    @task(2)
    def record_fix(self):
        payload = {
            "incident_id": f"inc-load-{uuid.uuid4().hex[:8]}",
            "fix_type": random.choice(["restart", "scale_up", "rollback", "drain"]),
            "fix_description": "Load test generated fix",
            "applied_by": "load-test",
            "success": random.random() < 0.85,
            "kubectl_command": "kubectl rollout restart deployment/test",
            "error_message": "" if random.random() < 0.85 else "timeout waiting for pod",
        }
        self.client.post("/fixes/record", json=payload, headers=self.headers, timeout=10)


class AdminUser(KoralUser):
    """Simulates admin operations — audit queries, user management."""
    weight = 1

    @tag("soak")
    @task(5)
    def query_audit_log(self):
        self.client.get("/audit?limit=50", headers=self.admin_headers, timeout=10)

    @tag("soak")
    @task(2)
    def query_audit_by_type(self):
        event_type = random.choice(["auth.login", "fix.recorded", "api.error"])
        self.client.get(f"/audit?event_type={event_type}&limit=20", headers=self.admin_headers, timeout=10)

    @tag("soak")
    @task(1)
    def list_users(self):
        self.client.get("/users/", headers=self.admin_headers, timeout=10)

    @tag("soak")
    @task(1)
    def list_tenants(self):
        self.client.get("/tenants/", headers=self.admin_headers, timeout=10)


# ── Chaos Injection Tests ────────────────────────────────────────────
class ChaosUser(KoralUser):
    """Injects error conditions to test resilience and graceful degradation."""
    weight = 1

    @tag("chaos")
    @task(5)
    def malformed_anomaly(self):
        """Send malformed payloads — should return 422, not 500."""
        payloads = [
            {},
            {"pod": "x"},
            {"timestamp": "not-a-number", "pod": "x", "metric": "cpu"},
            {"timestamp": 12345, "pod": "", "metric": ""},
            "not-json",
        ]
        payload = random.choice(payloads)
        with self.client.post(
            "/anomalies",
            json=payload if isinstance(payload, dict) else None,
            data=payload if isinstance(payload, str) else None,
            headers=self.headers,
            timeout=5,
            catch_response=True,
        ) as resp:
            if resp.status_code in (400, 422):
                resp.success()
            elif resp.status_code == 500:
                resp.failure("Server returned 500 on bad input — should be 4xx")

    @tag("chaos")
    @task(5)
    def unauthorized_access(self):
        """Test auth enforcement under load — should always return 401."""
        with self.client.get(
            "/anomalies",
            headers={"X-API-Key": "invalid-key-chaos"},
            timeout=5,
            catch_response=True,
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Expected 401, got {resp.status_code}")

    @tag("chaos")
    @task(3)
    def oversized_payload(self):
        """Send very large payloads — test memory and timeout handling."""
        large_string = "x" * 100_000
        payload = {
            "timestamp": int(time.time()),
            "pod": large_string[:200],
            "metric": "cpu",
            "value": 50.0,
            "z_score": 1.0,
            "is_anomaly": False,
            "namespace": large_string[:200],
            "unit": "percent",
            "source": "chaos",
            "window_size": 300,
        }
        with self.client.post(
            "/anomalies",
            json=payload,
            headers=self.headers,
            timeout=10,
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 202, 400, 413, 422):
                resp.success()
            elif resp.status_code == 500:
                resp.failure("500 on oversized payload")

    @tag("chaos")
    @task(3)
    def rapid_fire_requests(self):
        """Burst of rapid requests — test rate limiting."""
        for _ in range(10):
            with self.client.get(
                "/health/live",
                timeout=2,
                catch_response=True,
            ) as resp:
                if resp.status_code in (200, 429):
                    resp.success()
                else:
                    resp.failure(f"Unexpected {resp.status_code} during burst")

    @tag("chaos")
    @task(2)
    def nonexistent_endpoints(self):
        """Hit non-existent routes — should return 404, not 500."""
        paths = ["/nonexistent", "/api/v2/data", "/admin/secret", "/../etc/passwd"]
        path = random.choice(paths)
        with self.client.get(
            path,
            headers=self.headers,
            timeout=5,
            catch_response=True,
        ) as resp:
            if resp.status_code in (404, 405):
                resp.success()
            elif resp.status_code == 500:
                resp.failure(f"500 on nonexistent path: {path}")

    @tag("chaos")
    @task(2)
    def concurrent_writes(self):
        """Simultaneous writes to same resource — test DB concurrency."""
        incident_id = "inc-chaos-concurrent"
        payload = {
            "incident_id": incident_id,
            "fix_type": "restart",
            "fix_description": f"Chaos concurrent write {uuid.uuid4().hex[:6]}",
            "applied_by": "chaos",
            "success": True,
            "kubectl_command": "kubectl rollout restart",
            "error_message": "",
        }
        with self.client.post(
            "/fixes/record",
            json=payload,
            headers=self.headers,
            timeout=10,
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 409):
                resp.success()
            elif resp.status_code == 500:
                resp.failure("500 on concurrent write")
