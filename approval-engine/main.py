"""
KORAL Approval Engine - Email-based remediation approval workflow
Manages plan review and approval by authorized users
"""
import os
import json
import uuid
import smtplib
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KORAL Approval Engine",
    version="1.0.0",
    description="Email-based approval workflow for remediation plans"
)

# ── Configuration ──────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
APPROVAL_EMAIL = os.getenv("APPROVAL_EMAIL", "remediation@koral.local")
APPROVAL_RECIPIENTS = os.getenv("APPROVAL_RECIPIENTS", "admin@example.com").split(",")
APPROVAL_TIMEOUT_MINUTES = int(os.getenv("APPROVAL_TIMEOUT_MINUTES", "30"))
AUTO_APPROVE_MINOR = os.getenv("AUTO_APPROVE_MINOR", "false").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
DISABLE_EMAIL = os.getenv("DISABLE_EMAIL", "true").lower() == "true"

# ── Models ─────────────────────────────────────────────────────────
class ApprovalRequest(BaseModel):
    plan_id: str
    incident_id: str
    severity: str
    root_cause: str
    recommended_action: str
    confidence: float
    affected_pods: list
    parameters: Dict
    ai_reasoning: str

class ApprovalDecision(BaseModel):
    approval_id: str
    plan_id: str
    approved: bool
    approver_email: str
    reason: Optional[str] = None

# ── In-Memory Store (for demo) ─────────────────────────────────────
approval_store = {}

# ── Health Check ──────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "approval-engine",
        "version": "1.0.0",
        "auto_approve_enabled": AUTO_APPROVE_MINOR
    }

# ── Send Approval Email ──────────────────────────────────────────
def send_approval_email(approval_id: str, plan_id: str, severity: str, 
                        root_cause: str, action: str, affected_pods: list):
    """Send approval request email"""
    if DISABLE_EMAIL:
        logger.info(f"[EMAIL DISABLED] Would send approval email to {APPROVAL_RECIPIENTS}")
        return True
    
    try:
        # Build email
        subject = f"[KORAL] Remediation Approval Required - {severity.upper()} - {root_cause}"
        
        approval_link = f"http://koral-dashboard/approval?id={approval_id}"
        
        html_body = f"""
        <html>
        <body>
        <h2>KORAL Remediation Approval Required</h2>
        <p><strong>Severity:</strong> {severity.upper()}</p>
        <p><strong>Root Cause:</strong> {root_cause}</p>
        <p><strong>Recommended Action:</strong> {action}</p>
        <p><strong>Affected Pods:</strong> {', '.join(affected_pods[:5])}{' and more...' if len(affected_pods) > 5 else ''}</p>
        
        <h3>Approval Link</h3>
        <p><a href="{approval_link}">Review and Approve</a></p>
        
        <p><small>Plan ID: {plan_id}</small></p>
        <p><small>Approval ID: {approval_id}</small></p>
        <p><small>Approval expires in {APPROVAL_TIMEOUT_MINUTES} minutes</small></p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = APPROVAL_EMAIL
        msg["To"] = ", ".join(APPROVAL_RECIPIENTS)
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(APPROVAL_EMAIL, APPROVAL_RECIPIENTS, msg.as_string())
        
        logger.info(f"Sent approval email for {plan_id} to {APPROVAL_RECIPIENTS}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send approval email: {e}")
        return False

# ── Request Approval ──────────────────────────────────────────────
@app.post("/request-approval")
async def request_approval(request: ApprovalRequest):
    """Request approval for remediation plan"""
    
    approval_id = str(uuid.uuid4())
    
    # Auto-approve for minor severity if enabled
    if AUTO_APPROVE_MINOR and request.severity in ["low", "medium"]:
        logger.info(f"Auto-approving plan {request.plan_id} (minor severity)")
        approval_store[approval_id] = {
            "status": "approved",
            "approver": "auto-system",
            "approved_at": datetime.now(timezone.utc).isoformat()
        }
        return {
            "approval_id": approval_id,
            "status": "approved",
            "auto_approved": True,
            "reason": "Auto-approved for minor severity"
        }
    
    # Send approval email
    email_sent = send_approval_email(
        approval_id, request.plan_id, request.severity,
        request.root_cause, request.recommended_action, request.affected_pods
    )
    
    # Store approval request
    approval_store[approval_id] = {
        "plan_id": request.plan_id,
        "incident_id": request.incident_id,
        "status": "pending",
        "severity": request.severity,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=APPROVAL_TIMEOUT_MINUTES)).isoformat(),
        "email_sent": email_sent
    }
    
    logger.info(f"Created approval request {approval_id} for plan {request.plan_id}")
    
    return {
        "approval_id": approval_id,
        "status": "pending",
        "email_sent": email_sent,
        "expires_in_minutes": APPROVAL_TIMEOUT_MINUTES
    }

# ── Approve Plan ──────────────────────────────────────────────────
@app.post("/approve")
async def approve_plan(approval_id: str, approver_email: str, reason: Optional[str] = None):
    """Approve remediation plan"""
    
    if approval_id not in approval_store:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = approval_store[approval_id]
    
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already {approval['status']}")
    
    # Check expiration
    if datetime.fromisoformat(approval["expires_at"]) < datetime.now(timezone.utc):
        approval["status"] = "expired"
        raise HTTPException(status_code=400, detail="Approval request expired")
    
    # Mark as approved
    approval["status"] = "approved"
    approval["approver"] = approver_email
    approval["approved_at"] = datetime.now(timezone.utc).isoformat()
    approval["approval_reason"] = reason or "Approved"
    
    logger.info(f"Approved plan {approval['plan_id']} (approval: {approval_id})")
    
    return {
        "approval_id": approval_id,
        "status": "approved",
        "approved_by": approver_email,
        "approved_at": approval["approved_at"]
    }

# ── Reject Plan ──────────────────────────────────────────────────
@app.post("/reject")
async def reject_plan(approval_id: str, approver_email: str, reason: str):
    """Reject remediation plan"""
    
    if approval_id not in approval_store:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = approval_store[approval_id]
    
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already {approval['status']}")
    
    # Mark as rejected
    approval["status"] = "rejected"
    approval["approver"] = approver_email
    approval["rejected_at"] = datetime.now(timezone.utc).isoformat()
    approval["rejection_reason"] = reason
    
    logger.info(f"Rejected plan {approval['plan_id']} (approval: {approval_id}): {reason}")
    
    return {
        "approval_id": approval_id,
        "status": "rejected",
        "rejected_by": approver_email,
        "reason": reason
    }

# ── Check Approval Status ──────────────────────────────────────────
@app.get("/status/{approval_id}")
async def check_status(approval_id: str):
    """Check approval status"""
    
    if approval_id not in approval_store:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = approval_store[approval_id]
    
    return {
        "approval_id": approval_id,
        "status": approval.get("status"),
        "created_at": approval.get("created_at"),
        "expires_at": approval.get("expires_at"),
        "approver": approval.get("approver")
    }

# ── Metrics ──────────────────────────────────────────────────────
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008, workers=2)
