#!/usr/bin/env python3
"""
Demo Scenario Validator
Drives the full KORAL demo flow and prints a structured pass/fail report.

Usage:
    BACKEND_URL=http://localhost:8000 python demo_validator.py [--scenario io_storm]

Scenarios: io_storm (default), cpu_spike, memory_leak, log_error
"""
import os
import sys
import time
import json
import argparse
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend.koral-system:8000")
POLL_INTERVAL = 5
MAX_WAIT = 90

SCENARIO_MAP = {
    "io_storm":    {"pod": "io-storm-sim",        "metric": "storage"},
    "cpu_spike":   {"pod": "cpu-spike-sim",        "metric": "cpu"},
    "memory_leak": {"pod": "memory-pressure-sim",  "metric": "memory"},
    "log_error":   {"pod": "log-error-gen-sim",    "metric": "log"},
}

_PASS = "\033[92m[PASS]\033[0m"
_FAIL = "\033[91m[FAIL]\033[0m"


def _get(path):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _poll(check_fn, label):
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        result = check_fn()
        if result:
            print(f"  {_PASS} {label}")
            return result
        time.sleep(POLL_INTERVAL)
    print(f"  {_FAIL} {label} (timeout {MAX_WAIT}s)")
    return None


def validate_scenario(name: str) -> dict:
    cfg = SCENARIO_MAP[name]
    pod, metric = cfg["pod"], cfg["metric"]

    print(f"\n{'='*50}")
    print(f" Scenario: {name.upper().replace('_', ' ')} - pod: {pod}")
    print(f"{'='*50}")

    checks = {}

    # 1. Anomaly detected
    anomaly = _poll(
        lambda: next(
            (a for a in (_get("/anomalies") or [])
             if a.get("pod") == pod and a.get("metric") == metric and a.get("is_anomaly")),
            None
        ),
        "Anomaly detected by agent"
    )
    checks["anomaly_detected"] = anomaly is not None

    # 2. Correlation references this pod
    correlation = _poll(
        lambda: next(
            (c for c in (_get("/correlations") or [])
             if pod in (c.get("pod_A"), c.get("pod_B"))),
            None
        ),
        "Correlation identifies affected pod"
    ) if checks["anomaly_detected"] else None
    checks["correlation_found"] = correlation is not None

    # 3. Incident with root cause generated
    incident = _poll(
        lambda: next(
            (i for i in (_get("/incidents") or [])
             if pod in i.get("affected_pods", [])),
            None
        ),
        "Root cause incident generated"
    ) if checks["anomaly_detected"] else None
    checks["incident_created"] = incident is not None

    if incident:
        print(f"  Root cause  : {incident.get('root_cause', 'N/A')}")
        print(f"  Confidence  : {incident.get('confidence', 'N/A')}")
        print(f"  Incident ID : {incident.get('incident_id', 'N/A')}")

    # 4. Incident visible via /incidents (dashboard feed)
    checks["dashboard_feed_ok"] = checks["incident_created"]
    status = _PASS if checks["dashboard_feed_ok"] else _FAIL
    print(f"  {status} Incident visible in dashboard feed")

    passed = sum(checks.values())
    total = len(checks)
    print(f"\n  Result: {passed}/{total} checks passed")
    return {"scenario": name, "checks": checks, "passed": passed, "total": total}


def run(scenarios: list[str]):
    print("\n" + "="*50)
    print(" KORAL Demo Scenario Validator")
    print("="*50)

    all_results = [validate_scenario(s) for s in scenarios]

    grand_pass = sum(r["passed"] for r in all_results)
    grand_total = sum(r["total"] for r in all_results)

    print(f"\n{'='*50}")
    print(f" FINAL: {grand_pass}/{grand_total} checks passed")
    if grand_pass == grand_total:
        print(" STATUS: \033[92mSYSTEM DEMO-READY ✓\033[0m")
    else:
        print(" STATUS: \033[91mSYSTEM NOT READY ✗\033[0m")
    print("="*50)

    with open("demo_validation_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    return grand_pass == grand_total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIO_MAP.keys()) + ["all"],
        default="io_storm",
        help="Which scenario to validate (default: io_storm)"
    )
    args = parser.parse_args()

    scenarios = list(SCENARIO_MAP.keys()) if args.scenario == "all" else [args.scenario]
    ok = run(scenarios)
    sys.exit(0 if ok else 1)
