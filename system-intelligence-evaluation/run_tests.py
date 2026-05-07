#!/usr/bin/env python3
"""Master Test Runner — executes all Member 5 tests and generates report."""
import sys
import json
from evaluation.integration_test import run_integration_tests
from evaluation.metrics import evaluate

def run_all_tests():
    print("\n" + "="*60)
    print(" KORAL MEMBER 5 — COMPLETE TEST SUITE")
    print("="*60)
    
    all_results = {}
    
    # 1. Integration Tests
    print("\n[1/2] Running Integration Tests...")
    integration_results = run_integration_tests()
    all_results["integration"] = integration_results
    
    # 2. Evaluation Metrics (mock data for demo)
    print("\n[2/2] Running Evaluation Metrics...")
    ground_truth = [
        {"pod": "io-storm-sim", "metric": "storage", "timestamp": 1710000000},
        {"pod": "cpu-spike-sim", "metric": "cpu", "timestamp": 1710000010},
    ]
    detected = [
        {"pod": "io-storm-sim", "metric": "storage", "timestamp": 1710000001, "is_anomaly": True},
        {"pod": "cpu-spike-sim", "metric": "cpu", "timestamp": 1710000012, "is_anomaly": True},
        {"pod": "false-pod", "metric": "memory", "timestamp": 1710000020, "is_anomaly": True},
    ]
    
    metrics = evaluate(ground_truth, detected)
    all_results["metrics"] = metrics
    
    print(f"\n  Precision: {metrics['precision']}")
    print(f"  Recall: {metrics['recall']}")
    print(f"  False Positive Rate: {metrics['false_positive_rate']}")
    print(f"  Avg Detection Latency: {metrics['latency_ms']}ms")
    
    # Final Summary
    integration_passed = sum(integration_results.values())
    integration_total = len(integration_results)
    
    print(f"\n{'='*60}")
    print(f" SUMMARY")
    print(f"{'='*60}")
    print(f"  Integration Tests: {integration_passed}/{integration_total} passed")
    print(f"  Precision: {metrics['precision']} | Recall: {metrics['recall']}")
    
    all_passed = integration_passed == integration_total and metrics['precision'] >= 0.6
    
    if all_passed:
        print(f"\n  STATUS: \033[92mSYSTEM READY ✓\033[0m")
    else:
        print(f"\n  STATUS: \033[91mSYSTEM NOT READY ✗\033[0m")
    
    print("="*60)
    
    # Save results
    with open("test_output.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
