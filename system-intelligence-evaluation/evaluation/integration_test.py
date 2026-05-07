"""Integration Test — validates full system flow: simulation → agent → backend → correlation → incident."""
import os
import time
import requests
from typing import Dict

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend.koral-system:8000")
TIMEOUT = 60

def test_anomaly_detection() -> bool:
    """Verify agents are sending anomalies to backend."""
    try:
        r = requests.get(f"{BACKEND_URL}/anomalies", timeout=5)
        anomalies = r.json()
        return len(anomalies) > 0
    except:
        return False

def test_correlation_engine() -> bool:
    """Verify correlation engine is generating correlations."""
    try:
        r = requests.get(f"{BACKEND_URL}/correlations", timeout=5)
        correlations = r.json()
        return len(correlations) > 0
    except:
        return False

def test_incident_generation() -> bool:
    """Verify incidents are being created with root causes."""
    try:
        r = requests.get(f"{BACKEND_URL}/incidents", timeout=5)
        incidents = r.json()
        if not incidents:
            return False
        # Check incident has required fields
        inc = incidents[0]
        return all(k in inc for k in ["incident_id", "root_cause", "affected_pods"])
    except:
        return False

def test_graph_endpoint() -> bool:
    """Verify dependency graph is accessible."""
    try:
        r = requests.get(f"{BACKEND_URL}/graph", timeout=5)
        graph = r.json()
        return "nodes" in graph and "edges" in graph
    except:
        return False

def run_integration_tests() -> Dict[str, bool]:
    """Run all integration tests and return results."""
    print("\n" + "="*50)
    print(" KORAL Integration Test Suite")
    print("="*50)
    
    tests = {
        "Anomaly Detection": test_anomaly_detection,
        "Correlation Engine": test_correlation_engine,
        "Incident Generation": test_incident_generation,
        "Graph Endpoint": test_graph_endpoint,
    }
    
    results = {}
    for name, test_fn in tests.items():
        print(f"\nRunning: {name}...", end=" ")
        passed = test_fn()
        results[name] = passed
        status = "\033[92mPASS\033[0m" if passed else "\033[91mFAIL\033[0m"
        print(status)
    
    passed_count = sum(results.values())
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f" Results: {passed_count}/{total} tests passed")
    print("="*50)
    
    return results

if __name__ == "__main__":
    results = run_integration_tests()
    exit(0 if all(results.values()) else 1)
