"""
KORAL Remediation System - End-to-End Integration Test
Demonstrates the complete remediation workflow
"""
import os
import sys
import json
import time
import uuid
import requests
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PLANNER_URL = os.getenv("REMEDIATION_PLANNER_URL", "http://localhost:8007")
APPROVAL_URL = os.getenv("APPROVAL_ENGINE_URL", "http://localhost:8008")
EXECUTOR_URL = os.getenv("SANDBOX_EXECUTOR_URL", "http://localhost:8009")
VERIFICATION_URL = os.getenv("VERIFICATION_ENGINE_URL", "http://localhost:8010")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://localhost:8011")

# ─────────────────────────────────────────────────────────────────
# Test Utilities
# ─────────────────────────────────────────────────────────────────

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_step(step: int, text: str):
    """Print step message"""
    print(f"\n{Colors.YELLOW}Step {step}: {text}{Colors.END}")

def pretty_json(obj: Dict) -> str:
    """Pretty print JSON"""
    return json.dumps(obj, indent=2)

# ─────────────────────────────────────────────────────────────────
# Service Health Checks
# ─────────────────────────────────────────────────────────────────

def check_service_health(url: str, service_name: str, timeout: int = 5) -> bool:
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            print_success(f"{service_name} ({url})")
            return True
        else:
            print_error(f"{service_name} returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{service_name}: {e}")
        return False

def verify_all_services() -> bool:
    """Verify all services are running"""
    print_header("Verifying Service Health")
    
    services = [
        (BACKEND_URL, "Backend"),
        (PLANNER_URL, "Remediation Planner"),
        (APPROVAL_URL, "Approval Engine"),
        (EXECUTOR_URL, "Sandbox Executor"),
        (VERIFICATION_URL, "Verification Engine"),
        (NOTIFIER_URL, "Notifier"),
    ]
    
    results = []
    for url, name in services:
        results.append(check_service_health(url, name))
    
    if all(results):
        print_success(f"All {len(services)} services healthy")
        return True
    else:
        print_error(f"Some services not healthy")
        return False

# ─────────────────────────────────────────────────────────────────
# Demo Workflow
# ─────────────────────────────────────────────────────────────────

def demo_create_incident() -> Dict:
    """Step 1: Create a simulated incident in the backend"""
    print_step(1, "Create Incident")
    
    incident = {
        "name": f"CPU Spike - {datetime.now(timezone.utc).isoformat()}",
        "severity": "high",
        "source": "demo",
        "description": "Simulated CPU saturation incident"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/incidents",
            json=incident,
            timeout=5
        )
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            print_success(f"Incident created")
            print_info(f"Response: {pretty_json(data)}")
            return data
        else:
            print_error(f"Failed to create incident: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

def demo_create_anomaly(incident_id: Optional[str] = None) -> Dict:
    """Step 2: Create a simulated anomaly"""
    print_step(2, "Create Anomaly Detection")
    
    anomaly = {
        "source": "cpu-agent",
        "metric": "cpu",
        "value": 85.5,
        "threshold": 75.0,
        "z_score": 3.2,
        "is_anomaly": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/anomalies",
            json=anomaly,
            timeout=5
        )
        
        if response.status_code in [200, 201, 202]:
            print_success(f"Anomaly recorded")
            print_info(f"CPU: {anomaly['value']}%, Z-Score: {anomaly['z_score']}")
            return anomaly
        else:
            print_error(f"Failed to record anomaly: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

def demo_request_remediation_plan() -> Dict:
    """Step 3: Request remediation plan from planner"""
    print_step(3, "Request Remediation Plan")
    
    plan_request = {
        "incident_id": str(uuid.uuid4()),
        "severity": "high",
        "root_cause": "cpu_saturation",
        "affected_pods": ["pod-cpu-heavy-1", "pod-cpu-heavy-2"],
        "primary_metric": "cpu_usage",
        "z_score": 3.2
    }
    
    try:
        response = requests.post(
            f"{PLANNER_URL}/create-plan",
            json=plan_request,
            timeout=10
        )
        
        if response.status_code == 200:
            plan = response.json()
            print_success(f"Plan created: {plan.get('plan_id')}")
            print_info(f"Recommended action: {plan.get('recommended_action')}")
            print_info(f"Confidence: {plan.get('confidence', 0):.1%}")
            print_info(f"Reasoning: {plan.get('ai_reasoning', 'N/A')[:100]}...")
            return plan
        else:
            print_error(f"Failed to create plan: {response.status_code}")
            if response.text:
                print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

def demo_request_approval(plan: Dict) -> Optional[str]:
    """Step 4: Request approval from approval engine"""
    print_step(4, "Request Approval")
    
    approval_request = {
        "plan_id": plan.get("plan_id"),
        "incident_id": plan.get("incident_id"),
        "severity": plan.get("severity"),
        "root_cause": plan.get("root_cause"),
        "recommended_action": plan.get("recommended_action"),
        "confidence": plan.get("confidence"),
        "affected_pods": plan.get("affected_pods"),
        "parameters": plan.get("parameters"),
        "ai_reasoning": plan.get("ai_reasoning")
    }
    
    try:
        response = requests.post(
            f"{APPROVAL_URL}/request-approval",
            json=approval_request,
            timeout=10
        )
        
        if response.status_code == 200:
            approval = response.json()
            approval_id = approval.get("approval_id")
            print_success(f"Approval request created: {approval_id}")
            print_info(f"Status: {approval.get('status')}")
            
            # Auto-approval message
            if approval.get('auto_approved'):
                print_success("✓ Auto-approved (minor severity)")
            
            return approval_id
        else:
            print_error(f"Failed to request approval: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

def demo_approve_plan(approval_id: str) -> bool:
    """Step 5: Manually approve the plan"""
    print_step(5, "Approve Plan")
    
    try:
        response = requests.post(
            f"{APPROVAL_URL}/approve",
            params={
                "approval_id": approval_id,
                "approver_email": "demo@example.com",
                "reason": "Approved by integration test"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            approval_result = response.json()
            print_success(f"Plan approved")
            print_info(f"Approver: {approval_result.get('approved_by')}")
            return True
        else:
            print_error(f"Failed to approve: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def demo_execute_remediation(plan: Dict, approval_id: str) -> Optional[str]:
    """Step 6: Execute the remediation command"""
    print_step(6, "Execute Remediation")
    
    execution_request = {
        "approval_id": approval_id,
        "plan_id": plan.get("plan_id"),
        "incident_id": plan.get("incident_id"),
        "command": plan.get("recommended_action"),
        "parameters": plan.get("parameters"),
        "affected_pods": plan.get("affected_pods")
    }
    
    try:
        response = requests.post(
            f"{EXECUTOR_URL}/execute",
            json=execution_request,
            timeout=30
        )
        
        if response.status_code == 200:
            execution = response.json()
            execution_id = execution.get("execution_id")
            print_success(f"Execution completed: {execution_id}")
            print_info(f"Command: {execution.get('command')}")
            print_info(f"Status: {execution.get('status')}")
            print_info(f"Exit code: {execution.get('exit_code')}")
            print_info(f"Duration: {execution.get('duration_ms')}ms")
            
            if execution.get('status') == 'success':
                print_success("✓ Command executed successfully (dry-run mode)")
            
            return execution_id
        else:
            print_error(f"Failed to execute: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

def demo_verify_remediation(execution_id: str, plan: Dict) -> Dict:
    """Step 7: Verify remediation effectiveness"""
    print_step(7, "Verify Remediation")
    
    # Wait for metrics to stabilize
    print_info("Waiting for metrics to stabilize...")
    time.sleep(2)
    
    verification_request = {
        "execution_id": execution_id,
        "plan_id": plan.get("plan_id"),
        "incident_id": plan.get("incident_id"),
        "affected_pods": plan.get("affected_pods"),
        "primary_metric": "cpu_usage",
        "pre_metrics": {
            "mean": 85.5,
            "stdev": 5.2,
            "min": 78.0,
            "max": 92.1
        }
    }
    
    try:
        response = requests.post(
            f"{VERIFICATION_URL}/verify",
            json=verification_request,
            timeout=120
        )
        
        if response.status_code == 200:
            verification = response.json()
            print_success(f"Verification complete: {verification.get('verification_id')}")
            print_info(f"Status: {verification.get('verification_status')}")
            print_info(f"Improvement: {verification.get('improvement_percent', 0):.1f}%")
            print_info(f"Z-score delta: {verification.get('z_score_delta', 0):.2f}")
            
            if verification.get('anomaly_resolved'):
                print_success("✓ Anomaly resolved")
            else:
                print_info("Anomaly still present - may require manual intervention")
            
            return verification
        else:
            print_error(f"Failed to verify: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

def demo_send_notification(plan: Dict, execution_id: str) -> bool:
    """Step 8: Send notification"""
    print_step(8, "Send Notification")
    
    notification = {
        "incident_id": plan.get("incident_id"),
        "severity": plan.get("severity"),
        "root_cause": plan.get("root_cause"),
        "status": "resolved",
        "message": f"Remediation {execution_id} completed successfully",
        "affected_pods": plan.get("affected_pods"),
        "remediation_plan_id": plan.get("plan_id"),
        "execution_id": execution_id
    }
    
    try:
        response = requests.post(
            f"{NOTIFIER_URL}/notify",
            json=notification,
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("Notification sent")
            result = response.json()
            print_info(f"Email: {result.get('email', 'disabled')}")
            print_info(f"Telegram: {result.get('telegram', 'disabled')}")
            print_info(f"Slack: {result.get('slack', 'disabled')}")
            return True
        else:
            print_error(f"Failed to send notification: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

def demo_query_status() -> bool:
    """Step 9: Query remediation status"""
    print_step(9, "Query System Status")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/remediation/status",
            timeout=10
        )
        
        if response.status_code == 200:
            status = response.json()
            print_success("Remediation system status retrieved")
            print_info(f"Status: {status.get('status')}")
            print_info(f"Enabled: {status.get('enabled')}")
            print_info(f"Plans created: {status.get('plan_count')}")
            print_info(f"Executions: {status.get('execution_count')}")
            return True
        else:
            print_error(f"Failed to query status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

# ─────────────────────────────────────────────────────────────────
# Main Test Suite
# ─────────────────────────────────────────────────────────────────

def run_full_workflow():
    """Run the complete remediation workflow"""
    print_header("KORAL Remediation System - Integration Test")
    print_info(f"Backend: {BACKEND_URL}")
    print_info(f"Planner: {PLANNER_URL}")
    print_info(f"Approval: {APPROVAL_URL}")
    print_info(f"Executor: {EXECUTOR_URL}")
    print_info(f"Verification: {VERIFICATION_URL}")
    print_info(f"Notifier: {NOTIFIER_URL}")
    
    # Verify services
    if not verify_all_services():
        print_error("Not all services are healthy. Aborting.")
        return False
    
    # Run workflow
    try:
        # Step 1-2: Create incident and anomaly
        incident = demo_create_incident()
        anomaly = demo_create_anomaly()
        
        # Step 3: Request plan
        plan = demo_request_remediation_plan()
        if not plan:
            print_error("Failed to create plan. Aborting workflow.")
            return False
        
        # Step 4: Request approval
        approval_id = demo_request_approval(plan)
        if not approval_id:
            print_error("Failed to request approval. Aborting workflow.")
            return False
        
        # Step 5: Approve plan
        if not demo_approve_plan(approval_id):
            print_error("Failed to approve plan. Aborting workflow.")
            return False
        
        # Step 6: Execute
        execution_id = demo_execute_remediation(plan, approval_id)
        if not execution_id:
            print_error("Failed to execute remediation. Aborting workflow.")
            return False
        
        # Step 7: Verify
        verification = demo_verify_remediation(execution_id, plan)
        if not verification:
            print_error("Failed to verify. Aborting workflow.")
            return False
        
        # Step 8: Notify
        demo_send_notification(plan, execution_id)
        
        # Step 9: Query status
        demo_query_status()
        
        # Success summary
        print_header("Integration Test Complete")
        print_success("All workflow steps executed successfully")
        print_info(f"Plan ID: {plan.get('plan_id')}")
        print_info(f"Execution ID: {execution_id}")
        print_info(f"Verification ID: {verification.get('verification_id')}")
        
        return True
        
    except Exception as e:
        print_error(f"Workflow failed: {e}")
        return False

if __name__ == "__main__":
    success = run_full_workflow()
    sys.exit(0 if success else 1)
