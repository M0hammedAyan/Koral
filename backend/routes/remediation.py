"""
KORAL Backend - Remediation Routes
Orchestrates the remediation workflow across all services
"""
import os
import uuid
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

from backend.database_remediation import (
    add_remediation_plan,
    get_remediation_plan as db_get_remediation_plan,
    list_remediation_plans as db_list_remediation_plans,
    count_remediation_plans as db_count_remediation_plans,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/remediation", tags=["remediation"])

# ── Configuration ──────────────────────────────────────────────────
REMEDIATION_PLANNER_URL = os.getenv("REMEDIATION_PLANNER_URL", "http://remediation-planner:8007")
APPROVAL_ENGINE_URL = os.getenv("APPROVAL_ENGINE_URL", "http://approval-engine:8008")
SANDBOX_EXECUTOR_URL = os.getenv("SANDBOX_EXECUTOR_URL", "http://sandbox-executor:8009")
VERIFICATION_ENGINE_URL = os.getenv("VERIFICATION_ENGINE_URL", "http://verification-engine:8010")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://notifier:8011")
REMEDIATION_ENABLED = os.getenv("REMEDIATION_ENABLED", "false").lower() == "true"

# ── Models ─────────────────────────────────────────────────────────
class RemediationPlanCreate(BaseModel):
    incident_id: str
    severity: str
    root_cause: str
    affected_pods: list
    primary_metric: str
    z_score: float

class RemediationStatus(BaseModel):
    status: str
    enabled: bool
    plan_count: int
    execution_count: int

# NOTE: workflow durability
# Plans are persisted in DB via backend.database_remediation.
# Executions/verifications are still in-memory (Phase 3/4 will persist these too).
remediation_executions = {}
remediation_verifications = {}

# ── Health Check ──────────────────────────────────────────────────
@router.get("/status")
async def remediation_status() -> RemediationStatus:
    """Get remediation system status"""
    return RemediationStatus(
        status="operational" if REMEDIATION_ENABLED else "disabled",
        enabled=REMEDIATION_ENABLED,
        plan_count=db_count_remediation_plans(),
        execution_count=len(remediation_executions)
    )

# ── Create Remediation Plan ──────────────────────────────────────
@router.post("/plans")
async def create_remediation_plan(incident: RemediationPlanCreate):
    """Create remediation plan via AI analysis"""
    
    if not REMEDIATION_ENABLED:
        raise HTTPException(status_code=503, detail="Remediation system not enabled")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{REMEDIATION_PLANNER_URL}/create-plan",
                json=incident.dict()
            )
            
            if response.status_code == 200:
                plan = response.json()
                try:
                    add_remediation_plan(
                        plan_id=plan["plan_id"],
                        incident_id=plan["incident_id"],
                        severity=plan.get("severity"),
                        root_cause=plan.get("root_cause"),
                        recommended_action=plan.get("recommended_action"),
                        confidence=plan.get("confidence"),
                        affected_pods=plan.get("affected_pods", []),
                        parameters=plan.get("parameters", {}),
                        ai_reasoning=plan.get("ai_reasoning", ""),
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist plan {plan.get('plan_id')}: {e}")
                logger.info(f"Created remediation plan: {plan['plan_id']}")
                return plan
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to create plan")
    
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Get Remediation Plan ──────────────────────────────────────────
@router.get("/plans/{plan_id}")
async def get_remediation_plan(plan_id: str):
    """Get remediation plan details"""
    plan = db_get_remediation_plan(plan_id)
    if plan:
        return plan
    raise HTTPException(status_code=404, detail="Plan not found")

# ── Request Approval ──────────────────────────────────────────────
@router.post("/approve/{plan_id}")
async def request_approval(plan_id: str):
    """Request approval for remediation plan"""
    
    plan = db_get_remediation_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{APPROVAL_ENGINE_URL}/request-approval",
                json={
                    "plan_id": plan["plan_id"],
                    "incident_id": plan["incident_id"],
                    "severity": plan["severity"],
                    "root_cause": plan["root_cause"],
                    "recommended_action": plan["recommended_action"],
                    "confidence": plan["confidence"],
                    "affected_pods": plan["affected_pods"],
                    "parameters": plan["parameters"],
                    "ai_reasoning": plan["ai_reasoning"]
                }
            )
            
            if response.status_code == 200:
                approval = response.json()
                logger.info(f"Approval requested: {approval['approval_id']}")
                return approval
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to request approval")
    
    except Exception as e:
        logger.error(f"Error requesting approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Execute Remediation ──────────────────────────────────────────
@router.post("/execute/{plan_id}")
async def execute_remediation(plan_id: str, approval_id: str):
    """Execute approved remediation plan"""
    
    plan = db_get_remediation_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            # Check approval status
            approval_check = await client.get(
                f"{APPROVAL_ENGINE_URL}/status/{approval_id}"
            )
            
            if approval_check.status_code != 200 or approval_check.json().get("status") != "approved":
                raise HTTPException(status_code=403, detail="Plan not approved")
            
            # Execute command
            response = await client.post(
                f"{SANDBOX_EXECUTOR_URL}/execute",
                json={
                    "approval_id": approval_id,
                    "plan_id": plan["plan_id"],
                    "incident_id": plan["incident_id"],
                    "command": plan["recommended_action"],
                    "parameters": plan["parameters"],
                    "affected_pods": plan["affected_pods"]
                }
            )
            
            if response.status_code == 200:
                execution = response.json()
                remediation_executions[execution["execution_id"]] = execution
                logger.info(f"Executed remediation: {execution['execution_id']}")
                return execution
            else:
                raise HTTPException(status_code=response.status_code, detail="Execution failed")
    
    except Exception as e:
        logger.error(f"Error executing remediation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Verify Remediation ──────────────────────────────────────────
@router.post("/verify/{execution_id}")
async def verify_remediation(execution_id: str, plan_id: str, primary_metric: str):
    """Verify remediation effectiveness"""
    
    if execution_id not in remediation_executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    execution = remediation_executions[execution_id]
    plan = db_get_remediation_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{VERIFICATION_ENGINE_URL}/verify",
                json={
                    "execution_id": execution_id,
                    "plan_id": plan_id,
                    "incident_id": plan["incident_id"],
                    "affected_pods": plan["affected_pods"],
                    "primary_metric": primary_metric,
                    "pre_metrics": {"mean": 0.0, "stdev": 1.0}  # Placeholder
                }
            )
            
            if response.status_code == 200:
                verification = response.json()
                remediation_verifications[verification["verification_id"]] = verification
                logger.info(f"Verification complete: {verification['verification_id']}")
                return verification
            else:
                raise HTTPException(status_code=response.status_code, detail="Verification failed")
    
    except Exception as e:
        logger.error(f"Error verifying remediation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Send Notification ──────────────────────────────────────────
@router.post("/notify/{incident_id}")
async def send_remediation_notification(incident_id: str, severity: str, root_cause: str, 
                                       status: str, message: str, affected_pods: list,
                                       plan_id: Optional[str] = None,
                                       execution_id: Optional[str] = None):
    """Send remediation notification"""
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{NOTIFIER_URL}/notify",
                json={
                    "incident_id": incident_id,
                    "severity": severity,
                    "root_cause": root_cause,
                    "status": status,
                    "message": message,
                    "affected_pods": affected_pods,
                    "remediation_plan_id": plan_id,
                    "execution_id": execution_id
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Notification sent for {incident_id}")
                return response.json()
            else:
                logger.warning(f"Notification failed: {response.status_code}")
                return {}
    
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return {}

# ── List Plans ──────────────────────────────────────────────────
@router.get("/plans")
async def list_remediation_plans(limit: int = 100):
    """List all remediation plans"""
    plans_list = db_list_remediation_plans(limit=limit)
    return {
        "count": len(plans_list),
        "plans": plans_list
    }

# ── List Executions ────────────────────────────────────────────
@router.get("/executions")
async def list_executions(limit: int = 100):
    """List all execution records"""
    executions_list = list(remediation_executions.values())[:limit]
    return {
        "count": len(executions_list),
        "executions": executions_list
    }
