#!/usr/bin/env python3
"""
KORAL Remediation System - Simplified Demo
Tests just the remediation workflow (planner → approval → execute → verify)
"""
import os
import requests
import json
import time
import uuid
from datetime import datetime, timezone

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PLANNER_URL = os.getenv("REMEDIATION_PLANNER_URL", "http://localhost:8007")
APPROVAL_URL = os.getenv("APPROVAL_ENGINE_URL", "http://localhost:8008")
EXECUTOR_URL = os.getenv("SANDBOX_EXECUTOR_URL", "http://localhost:8009")
VERIFICATION_URL = os.getenv("VERIFICATION_ENGINE_URL", "http://localhost:8010")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://localhost:8011")

def test_remediation_workflow():
    """Test the remediation workflow"""
    print("\n" + "="*70)
    print("  KORAL Remediation System - Simplified Workflow Demo")
    print("="*70 + "\n")
    
    # Step 1: Check backend status
    print("[1/5] Checking backend remediation status...")
    try:
        resp = requests.get(f"{BACKEND_URL}/remediation/status", timeout=5)
        status = resp.json()
        print(f"✓ Status: {status['status']}")
        print(f"✓ Enabled: {status['enabled']}")
        print(f"✓ Plans: {status['plan_count']}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Step 2: Create remediation plan
    print("\n[2/5] Creating remediation plan...")
    plan_request = {
        "incident_id": str(uuid.uuid4()),
        "severity": "high",
        "root_cause": "cpu_saturation",
        "affected_pods": ["pod-cpu-1", "pod-cpu-2"],
        "primary_metric": "cpu_usage",
        "z_score": 3.2
    }
    
    try:
        resp = requests.post(f"{PLANNER_URL}/create-plan", json=plan_request, timeout=15)
        if resp.status_code != 200:
            print(f"✗ Status: {resp.status_code}")
            print(f"✗ Response: {resp.text}")
            return False
        
        plan = resp.json()
        plan_id = plan.get("plan_id")
        print(f"✓ Plan created: {plan_id}")
        print(f"✓ Action: {plan.get('recommended_action')}")
        print(f"✓ Confidence: {plan.get('confidence', 0):.1%}")
        print(f"✓ Reasoning: {plan.get('ai_reasoning', 'N/A')[:80]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Step 3: Request approval
    print("\n[3/5] Requesting approval...")
    approval_request = {
        "plan_id": plan.get("plan_id"),
        "incident_id": plan.get("incident_id"),
        "severity": plan.get("severity"),
        "root_cause": plan.get("root_cause"),
        "recommended_action": plan.get("recommended_action"),
        "confidence": plan.get("confidence"),
        "affected_pods": plan.get("affected_pods"),
        "parameters": plan.get("parameters", {}),
        "ai_reasoning": plan.get("ai_reasoning", "")
    }
    
    try:
        resp = requests.post(f"{APPROVAL_URL}/request-approval", json=approval_request, timeout=15)
        if resp.status_code != 200:
            print(f"✗ Status: {resp.status_code}")
            return False
        
        approval = resp.json()
        approval_id = approval.get("approval_id")
        print(f"✓ Approval requested: {approval_id}")
        print(f"✓ Status: {approval.get('status')}")
        
        if approval.get('auto_approved'):
            print(f"✓ Auto-approved (minor severity)")
        else:
            # Manually approve
            print(f"  Approving plan...")
            approve_resp = requests.post(
                f"{APPROVAL_URL}/approve",
                params={
                    "approval_id": approval_id,
                    "approver_email": "demo@example.com",
                    "reason": "Demo approval"
                },
                timeout=10
            )
            if approve_resp.status_code == 200:
                print(f"✓ Plan approved")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Step 4: Execute remediation
    print("\n[4/5] Executing remediation...")
    execution_request = {
        "approval_id": approval_id,
        "plan_id": plan.get("plan_id"),
        "incident_id": plan.get("incident_id"),
        "command": plan.get("recommended_action"),
        "parameters": plan.get("parameters", {}),
        "affected_pods": plan.get("affected_pods", [])
    }
    
    try:
        resp = requests.post(f"{EXECUTOR_URL}/execute", json=execution_request, timeout=30)
        if resp.status_code != 200:
            print(f"✗ Status: {resp.status_code}")
            print(f"✗ Response: {resp.text}")
            return False
        
        execution = resp.json()
        execution_id = execution.get("execution_id")
        print(f"✓ Execution completed: {execution_id}")
        print(f"✓ Command: {execution.get('command')}")
        print(f"✓ Status: {execution.get('status')}")
        print(f"✓ Exit code: {execution.get('exit_code')}")
        print(f"✓ Duration: {execution.get('duration_ms')}ms")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Step 5: Verify remediation
    print("\n[5/5] Verifying remediation...")
    time.sleep(2)
    
    verification_request = {
        "execution_id": execution_id,
        "plan_id": plan.get("plan_id"),
        "incident_id": plan.get("incident_id"),
        "affected_pods": plan.get("affected_pods", []),
        "primary_metric": "cpu_usage",
        "pre_metrics": {
            "mean": 85.5,
            "stdev": 5.2,
            "min": 78.0,
            "max": 92.1
        }
    }
    
    try:
        resp = requests.post(f"{VERIFICATION_URL}/verify", json=verification_request, timeout=120)
        if resp.status_code != 200:
            print(f"✗ Status: {resp.status_code}")
            return False
        
        verification = resp.json()
        print(f"✓ Verification complete: {verification.get('verification_id')}")
        print(f"✓ Status: {verification.get('verification_status')}")
        print(f"✓ Improvement: {verification.get('improvement_percent', 0):.1f}%")
        print(f"✓ Anomaly resolved: {verification.get('anomaly_resolved')}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Summary
    print("\n" + "="*70)
    print("  ✓ WORKFLOW COMPLETE - ALL STEPS SUCCESSFUL")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    import sys
    success = test_remediation_workflow()
    sys.exit(0 if success else 1)
