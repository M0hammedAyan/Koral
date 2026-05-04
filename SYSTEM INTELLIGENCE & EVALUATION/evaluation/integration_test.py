"""
Integration Test Runner
Validates: Simulation → Agent → Backend → Correlation → Incident

Usage:
    BACKEND_URL=http://localhost:8000 python evaluation/integration_test.py
"""
import os
import time
import json
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend.koral-system:8000")
POLL_INTERVAL = 5   # seconds between checks
MAX_WAIT = 120      # seconds before timeout

SCENARIOS = [
    {"pod": "cpu-spike-sim",       "metric": "cpu"},
    {"pod": "memory-pressure-sim", "metric": "memory"},
    {"pod": "io-storm-sim",        "metric": "storage"},
    {"pod": "log-error-gen-sim",   "metric": "log"},
]


def _get(path: str) -> dict | list | None:
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [WARN] GET {path} failed: {e}")
        return None


def wait_for_anomaly(pod: str, metric: str) -> bool:
    """Poll /anomalies until the expected pod+metric anomaly appears."""
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        data = _get("/anomalies") or []
        for a in data:
            if a.get("pod") == pod and a.get("metric") == metric and a.get("is_anomaly"):
                return True
        time.sleep(POLL_INTERVAL)
    return False


def wait_for_incident(pod: str) -> dict | None:
    """Poll /incidents until an incident referencing the pod appears."""
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        data = _get("/incidents") or []
        for inc in data:
            if pod in inc.get("affected_pods", []):
                return inc
        time.sleep(POLL_INTERVAL)
    return None


def run():
    results = []
    for s in SCENARIOS:
        pod, metric = s["pod"], s["metric"]
        print(f"\n[TEST] {metric.upper()} — pod: {pod}")

        anomaly_ok = wait_for_anomaly(pod, metric)
        print(f"  Anomaly detected : {'PASS' if anomaly_ok else 'FAIL'}")

        incident = wait_for_incident(pod) if anomaly_ok else None
        incident_ok = incident is not None
        print(f"  Incident created : {'PASS' if incident_ok else 'FAIL'}")
        if incident:
            print(f"  Root cause       : {incident.get('root_cause')}")
            print(f"  Confidence       : {incident.get('confidence')}")

        results.append({
            "scenario": metric,
            "pod": pod,
            "anomaly_detected": anomaly_ok,
            "incident_created": incident_ok,
            "incident": incident,
        })

    passed = sum(1 for r in results if r["anomaly_detected"] and r["incident_created"])
    print(f"\n{'='*40}")
    print(f" Integration Results: {passed}/{len(results)} passed")
    print(f"{'='*40}")

    with open("integration_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return passed == len(results)


if __name__ == "__main__":
    ok = run()
    raise SystemExit(0 if ok else 1)
