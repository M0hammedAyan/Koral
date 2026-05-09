# KORAL Remediation System - Example API Calls
# Copy and paste these commands into PowerShell to test the system

Write-Host "
╔════════════════════════════════════════════════════════════════════╗
║     KORAL Remediation System - API Examples                        ║
║                                                                    ║
║  This script demonstrates all key remediation endpoints           ║
║  Make sure all services are running before starting               ║
╚════════════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────

$BACKEND = "http://localhost:8000"
$PLANNER = "http://localhost:8007"
$APPROVAL = "http://localhost:8008"
$EXECUTOR = "http://localhost:8009"
$VERIFICATION = "http://localhost:8010"
$NOTIFIER = "http://localhost:8011"

# ─────────────────────────────────────────────────────────────────
# 1. HEALTH CHECKS - Verify all services are up
# ─────────────────────────────────────────────────────────────────

function Test-Services {
    Write-Host "`n=== SERVICE HEALTH CHECKS ===" -ForegroundColor Yellow
    
    $services = @(
        @{Name="Backend"; Port=8000},
        @{Name="Planner"; Port=8007},
        @{Name="Approval"; Port=8008},
        @{Name="Executor"; Port=8009},
        @{Name="Verification"; Port=8010},
        @{Name="Notifier"; Port=8011}
    )
    
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" `
                -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            Write-Host "✓ $($service.Name)" -ForegroundColor Green
        } catch {
            Write-Host "✗ $($service.Name) - Not responding" -ForegroundColor Red
        }
    }
}

# ─────────────────────────────────────────────────────────────────
# 2. CREATE ANOMALY - Simulate a CPU spike
# ─────────────────────────────────────────────────────────────────

function Create-Anomaly {
    Write-Host "`n=== CREATE ANOMALY ===" -ForegroundColor Yellow
    
    $anomaly = @{
        source = "cpu-agent"
        metric = "cpu"
        value = 85.5
        threshold = 75.0
        z_score = 3.2
        is_anomaly = $true
        timestamp = (Get-Date).ToUniversalTime().ToString("o")
    } | ConvertTo-Json
    
    Write-Host "POST $BACKEND/anomalies"
    Write-Host "Payload: $anomaly"
    
    $response = Invoke-WebRequest -Uri "$BACKEND/anomalies" `
        -Method Post `
        -ContentType "application/json" `
        -Body $anomaly `
        -UseBasicParsing
    
    Write-Host "Response: $($response.Content)" -ForegroundColor Green
    return $response.Content | ConvertFrom-Json
}

# ─────────────────────────────────────────────────────────────────
# 3. CREATE REMEDIATION PLAN
# ─────────────────────────────────────────────────────────────────

function Create-RemediationPlan {
    Write-Host "`n=== CREATE REMEDIATION PLAN ===" -ForegroundColor Yellow
    
    $planRequest = @{
        incident_id = [guid]::NewGuid().ToString()
        severity = "high"
        root_cause = "cpu_saturation"
        affected_pods = @("pod-cpu-1", "pod-cpu-2", "pod-cpu-3")
        primary_metric = "cpu_usage"
        z_score = 3.2
    } | ConvertTo-Json
    
    Write-Host "POST $PLANNER/create-plan"
    Write-Host "Payload: $planRequest"
    
    try {
        $response = Invoke-WebRequest -Uri "$PLANNER/create-plan" `
            -Method Post `
            -ContentType "application/json" `
            -Body $planRequest `
            -UseBasicParsing
        
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        $plan = $response.Content | ConvertFrom-Json
        Write-Host "Plan ID: $($plan.plan_id)" -ForegroundColor Cyan
        Write-Host "Action: $($plan.recommended_action)" -ForegroundColor Cyan
        Write-Host "Confidence: $($plan.confidence)" -ForegroundColor Cyan
        
        return $plan
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────
# 4. REQUEST APPROVAL
# ─────────────────────────────────────────────────────────────────

function Request-Approval {
    param([Parameter(Mandatory=$true)]$Plan)
    
    Write-Host "`n=== REQUEST APPROVAL ===" -ForegroundColor Yellow
    
    $approvalRequest = @{
        plan_id = $Plan.plan_id
        incident_id = $Plan.incident_id
        severity = $Plan.severity
        root_cause = $Plan.root_cause
        recommended_action = $Plan.recommended_action
        confidence = $Plan.confidence
        affected_pods = $Plan.affected_pods
        parameters = $Plan.parameters
        ai_reasoning = $Plan.ai_reasoning
    } | ConvertTo-Json
    
    Write-Host "POST $APPROVAL/request-approval"
    
    try {
        $response = Invoke-WebRequest -Uri "$APPROVAL/request-approval" `
            -Method Post `
            -ContentType "application/json" `
            -Body $approvalRequest `
            -UseBasicParsing
        
        $approval = $response.Content | ConvertFrom-Json
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        Write-Host "Approval ID: $($approval.approval_id)" -ForegroundColor Cyan
        Write-Host "Status: $($approval.status)" -ForegroundColor Cyan
        
        return $approval
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────
# 5. APPROVE PLAN
# ─────────────────────────────────────────────────────────────────

function Approve-Plan {
    param([Parameter(Mandatory=$true)]$ApprovalId)
    
    Write-Host "`n=== APPROVE PLAN ===" -ForegroundColor Yellow
    
    $uri = "$APPROVAL/approve?approval_id=$ApprovalId&approver_email=demo@example.com&reason=Test%20Approval"
    
    Write-Host "POST $uri"
    
    try {
        $response = Invoke-WebRequest -Uri $uri `
            -Method Post `
            -UseBasicParsing
        
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        $result = $response.Content | ConvertFrom-Json
        Write-Host "Approved: $($result.status)" -ForegroundColor Cyan
        
        return $result
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────
# 6. EXECUTE REMEDIATION
# ─────────────────────────────────────────────────────────────────

function Execute-Remediation {
    param(
        [Parameter(Mandatory=$true)]$Plan,
        [Parameter(Mandatory=$true)]$ApprovalId
    )
    
    Write-Host "`n=== EXECUTE REMEDIATION ===" -ForegroundColor Yellow
    
    $executionRequest = @{
        approval_id = $ApprovalId
        plan_id = $Plan.plan_id
        incident_id = $Plan.incident_id
        command = $Plan.recommended_action
        parameters = $Plan.parameters
        affected_pods = $Plan.affected_pods
    } | ConvertTo-Json
    
    Write-Host "POST $EXECUTOR/execute"
    
    try {
        $response = Invoke-WebRequest -Uri "$EXECUTOR/execute" `
            -Method Post `
            -ContentType "application/json" `
            -Body $executionRequest `
            -UseBasicParsing -TimeoutSec 30
        
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        $execution = $response.Content | ConvertFrom-Json
        Write-Host "Execution ID: $($execution.execution_id)" -ForegroundColor Cyan
        Write-Host "Status: $($execution.status)" -ForegroundColor Cyan
        Write-Host "Duration: $($execution.duration_ms)ms" -ForegroundColor Cyan
        
        return $execution
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────
# 7. VERIFY REMEDIATION
# ─────────────────────────────────────────────────────────────────

function Verify-Remediation {
    param(
        [Parameter(Mandatory=$true)]$ExecutionId,
        [Parameter(Mandatory=$true)]$Plan
    )
    
    Write-Host "`n=== VERIFY REMEDIATION ===" -ForegroundColor Yellow
    Write-Host "Waiting for metrics to stabilize..."
    Start-Sleep -Seconds 3
    
    $verificationRequest = @{
        execution_id = $ExecutionId
        plan_id = $Plan.plan_id
        incident_id = $Plan.incident_id
        affected_pods = $Plan.affected_pods
        primary_metric = "cpu_usage"
        pre_metrics = @{
            mean = 85.5
            stdev = 5.2
            min = 78.0
            max = 92.1
        }
    } | ConvertTo-Json
    
    Write-Host "POST $VERIFICATION/verify"
    
    try {
        $response = Invoke-WebRequest -Uri "$VERIFICATION/verify" `
            -Method Post `
            -ContentType "application/json" `
            -Body $verificationRequest `
            -UseBasicParsing -TimeoutSec 120
        
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        $verification = $response.Content | ConvertFrom-Json
        Write-Host "Verification ID: $($verification.verification_id)" -ForegroundColor Cyan
        Write-Host "Status: $($verification.verification_status)" -ForegroundColor Cyan
        Write-Host "Improvement: $($verification.improvement_percent)%" -ForegroundColor Cyan
        
        return $verification
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────
# 8. SEND NOTIFICATION
# ─────────────────────────────────────────────────────────────────

function Send-Notification {
    param(
        [Parameter(Mandatory=$true)]$Plan,
        [Parameter(Mandatory=$true)]$ExecutionId
    )
    
    Write-Host "`n=== SEND NOTIFICATION ===" -ForegroundColor Yellow
    
    $notification = @{
        incident_id = $Plan.incident_id
        severity = $Plan.severity
        root_cause = $Plan.root_cause
        status = "resolved"
        message = "Remediation completed successfully"
        affected_pods = $Plan.affected_pods
        remediation_plan_id = $Plan.plan_id
        execution_id = $ExecutionId
    } | ConvertTo-Json
    
    Write-Host "POST $NOTIFIER/notify"
    
    try {
        $response = Invoke-WebRequest -Uri "$NOTIFIER/notify" `
            -Method Post `
            -ContentType "application/json" `
            -Body $notification `
            -UseBasicParsing
        
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        return $response.Content | ConvertFrom-Json
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────
# 9. QUERY REMEDIATION STATUS
# ─────────────────────────────────────────────────────────────────

function Get-RemediationStatus {
    Write-Host "`n=== REMEDIATION STATUS ===" -ForegroundColor Yellow
    
    Write-Host "GET $BACKEND/remediation/status"
    
    try {
        $response = Invoke-WebRequest -Uri "$BACKEND/remediation/status" `
            -UseBasicParsing
        
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        $status = $response.Content | ConvertFrom-Json
        Write-Host "Status: $($status.status)" -ForegroundColor Cyan
        Write-Host "Enabled: $($status.enabled)" -ForegroundColor Cyan
        Write-Host "Plans: $($status.plan_count)" -ForegroundColor Cyan
        Write-Host "Executions: $($status.execution_count)" -ForegroundColor Cyan
        
        return $status
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─────────────────────────────────────────────────────────────────
# MAIN - Run complete workflow
# ─────────────────────────────────────────────────────────────────

function Run-CompleteWorkflow {
    Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Running Complete Remediation Workflow                              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    # 1. Health checks
    Test-Services
    
    # 2. Create anomaly
    $anomaly = Create-Anomaly
    
    # 3. Create plan
    $plan = Create-RemediationPlan
    if ($null -eq $plan) { return }
    
    # 4. Request approval
    $approval = Request-Approval -Plan $plan
    if ($null -eq $approval) { return }
    
    # 5. Approve plan
    if ($approval.status -ne "auto_approved") {
        $approveResult = Approve-Plan -ApprovalId $approval.approval_id
        if ($null -eq $approveResult) { return }
    }
    
    # 6. Execute remediation
    $execution = Execute-Remediation -Plan $plan -ApprovalId $approval.approval_id
    if ($null -eq $execution) { return }
    
    # 7. Verify remediation
    $verification = Verify-Remediation -ExecutionId $execution.execution_id -Plan $plan
    if ($null -eq $verification) { return }
    
    # 8. Send notification
    Send-Notification -Plan $plan -ExecutionId $execution.execution_id
    
    # 9. Get status
    Get-RemediationStatus
    
    Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  WORKFLOW COMPLETE - ALL STEPS SUCCESSFUL                            ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
}

# ─────────────────────────────────────────────────────────────────
# EXECUTE
# ─────────────────────────────────────────────────────────────────

Run-CompleteWorkflow
