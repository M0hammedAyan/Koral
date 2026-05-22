"""
KORAL Email Service — Anomaly Fix Notifications
Sends detailed fix reports back to developers with what was detected and what was fixed.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import os
from datetime import datetime
import logging

import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
KORAL_ENV = os.getenv("KORAL_NAMESPACE", "koral-system")
EMAIL_BREAKER = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _deliver_email(message: str, sender: str, recipient: str) -> None:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(sender, [recipient], message)


def send_fix_notification(
    incident_id: str,
    severity: str,
    root_cause: str,
    summary: str,
    affected_pods: List[str],
    fix_applied: Optional[str],
    fix_description: Optional[str],
    ai_explanation: str,
    model_used: str,
    recipient_email: Optional[str] = None,
) -> bool:
    """
    Send detailed anomaly fix report to developer.
    
    Args:
        incident_id: Unique incident identifier
        severity: Severity level (low, medium, high, critical)
        root_cause: Root cause classification
        summary: Human-readable incident summary
        affected_pods: List of affected pod names
        fix_applied: Type of fix applied (or None if no fix)
        fix_description: Description of fix that was applied
        ai_explanation: AI's explanation of the incident
        model_used: Which AI model was used (GPT-4o, Claude, RuleEngine)
        recipient_email: Email to send to (default: ALERT_EMAIL)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not ALERT_EMAIL and not recipient_email:
        logger.warning("[email] No recipient email configured")
        return False
    
    if not SMTP_USER or not SMTP_PASS or SMTP_PASS == "testpass":
        logger.warning(f"[email] SMTP not configured properly")
        return False
    
    recipient = recipient_email or ALERT_EMAIL
    
    try:
        # Build HTML email
        html_body = _build_fix_report_html(
            incident_id=incident_id,
            severity=severity,
            root_cause=root_cause,
            summary=summary,
            affected_pods=affected_pods,
            fix_applied=fix_applied,
            fix_description=fix_description,
            ai_explanation=ai_explanation,
            model_used=model_used,
        )
        
        # Determine severity emoji and action
        severity_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴",
            "critical": "🚨",
        }.get(severity.lower(), "❓")
        
        subject = f"{severity_emoji} KORAL Anomaly Fixed: {root_cause} (ID: {incident_id[:8]}...)"
        
        # Send email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))
        
        EMAIL_BREAKER.call(_deliver_email, msg.as_string(), SMTP_USER, recipient)
        
        logger.info(f"[email] Fix notification sent to {recipient} for incident {incident_id}")
        return True
    
    except Exception as e:
        logger.error(f"[email] Failed to send email: {e}")
        return False


def _build_fix_report_html(
    incident_id: str,
    severity: str,
    root_cause: str,
    summary: str,
    affected_pods: List[str],
    fix_applied: Optional[str],
    fix_description: Optional[str],
    ai_explanation: str,
    model_used: str,
) -> str:
    """Build professional HTML email report."""
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    severity_color = {
        "low": "#28a745",
        "medium": "#ffc107",
        "high": "#fd7e14",
        "critical": "#dc3545",
    }.get(severity.lower(), "#6c757d")
    
    fix_status_html = ""
    if fix_applied:
        fix_status_html = f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; background: #f0f8f0;">
                <strong>✅ Fix Applied:</strong> {fix_applied}
            </td>
        </tr>
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; background: #f0f8f0;">
                <strong>Details:</strong> {fix_description}
            </td>
        </tr>
        """
    else:
        fix_status_html = """
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; background: #fff3cd;">
                <strong>⚠️ Flagged for Review:</strong> Manual intervention recommended
            </td>
        </tr>
        """
    
    affected_pods_html = "".join([f"<li>{pod}</li>" for pod in affected_pods])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {severity_color}; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .section-title {{ font-weight: bold; font-size: 16px; margin-bottom: 10px; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            .label {{ font-weight: bold; color: #555; width: 150px; }}
            .footer {{ text-align: center; font-size: 12px; color: #999; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔧 KORAL Anomaly Detection Report</h2>
                <p>An anomaly was detected and processed by the KORAL AI Engine</p>
            </div>
            
            <div class="section">
                <div class="section-title">📊 Incident Summary</div>
                <table>
                    <tr>
                        <td class="label">Incident ID:</td>
                        <td><code>{incident_id}</code></td>
                    </tr>
                    <tr>
                        <td class="label">Severity:</td>
                        <td><strong style="color: {severity_color};">{severity.upper()}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">Root Cause:</td>
                        <td>{root_cause}</td>
                    </tr>
                    <tr>
                        <td class="label">Summary:</td>
                        <td>{summary}</td>
                    </tr>
                    <tr>
                        <td class="label">Timestamp:</td>
                        <td>{timestamp}</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <div class="section-title">☸️ Affected Resources</div>
                <ul>
                    {affected_pods_html}
                </ul>
            </div>
            
            <div class="section">
                <div class="section-title">🤖 AI Analysis</div>
                <p><strong>Explanation:</strong></p>
                <p style="background: #f5f5f5; padding: 10px; border-left: 4px solid {severity_color}; margin: 10px 0;">
                    {ai_explanation}
                </p>
                <p><strong>Model Used:</strong> {model_used}</p>
            </div>
            
            <div class="section">
                <div class="section-title">✅ Action Taken</div>
                <table>
                    {fix_status_html}
                </table>
            </div>
            
            <div class="footer">
                <p>KORAL Anomaly Detection System | {KORAL_ENV}</p>
                <p>Environment: {os.getenv("ENVIRONMENT", "production")}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_batch_summary_email(fixes_summary: List[dict], recipient_email: Optional[str] = None) -> bool:
    """
    Send batch summary of all fixes performed in a time period.
    
    Args:
        fixes_summary: List of fix dictionaries with incident details
        recipient_email: Email to send to (default: ALERT_EMAIL)
    
    Returns:
        bool: True if email sent successfully
    """
    if not ALERT_EMAIL and not recipient_email:
        logger.warning("[email] No recipient email configured for batch summary")
        return False
    
    recipient = recipient_email or ALERT_EMAIL
    
    try:
        html_body = _build_batch_summary_html(fixes_summary)
        subject = f"KORAL Daily Fix Summary - {len(fixes_summary)} Anomalies Handled"
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))
        
        EMAIL_BREAKER.call(_deliver_email, msg.as_string(), SMTP_USER, recipient)
        
        logger.info(f"[email] Batch summary sent to {recipient}")
        return True
    
    except Exception as e:
        logger.error(f"[email] Failed to send batch summary: {e}")
        return False


def _build_batch_summary_html(fixes_summary: List[dict]) -> str:
    """Build HTML for batch summary report."""
    
    total = len(fixes_summary)
    auto_fixed = len([f for f in fixes_summary if f.get("fix_applied")])
    flagged = total - auto_fixed
    
    severity_counts = {}
    for fix in fixes_summary:
        sev = fix.get("severity", "unknown").lower()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    rows = ""
    for fix in fixes_summary:
        status = "✅ Auto-Fixed" if fix.get("fix_applied") else "⚠️ Flagged for Review"
        rows += f"""
        <tr>
            <td>{fix.get('incident_id', 'N/A')[:12]}</td>
            <td>{fix.get('root_cause', 'N/A')}</td>
            <td>{fix.get('severity', 'unknown').upper()}</td>
            <td>{status}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #007bff; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 20px 0; }}
            .stat-box {{ background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; }}
            .stat-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background: #f5f5f5; padding: 10px; text-align: left; border-bottom: 2px solid #ddd; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📊 KORAL Daily Fix Summary</h2>
                <p>Automated anomaly detection and resolution report</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{total}</div>
                    <div>Total Anomalies</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" style="color: #28a745;">{auto_fixed}</div>
                    <div>Auto-Fixed</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" style="color: #ffc107;">{flagged}</div>
                    <div>Flagged for Review</div>
                </div>
            </div>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Severity Breakdown:</strong>
                {', '.join([f'{sev.upper()}: {count}' for sev, count in sorted(severity_counts.items())])}
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Incident ID</th>
                        <th>Root Cause</th>
                        <th>Severity</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            
            <div class="footer">
                <p>This is an automated report from KORAL Anomaly Detection System</p>
                <p>Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
