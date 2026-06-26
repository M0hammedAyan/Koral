"""Slack notification helper for KORAL Notifier."""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", os.getenv("SLACK_WEBHOOK", ""))


def send_slack_alert(
    service: str = "backend",
    issue: str = "",
    root_cause: str = "",
    suggested_fix: str = "",
    confidence: float | str = 0.0,
) -> bool:
    """Send a Slack alert via incoming webhook."""
    webhook = SLACK_WEBHOOK_URL
    if not webhook:
        logger.warning("Slack webhook URL not configured")
        return False

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚨 KORAL Alert"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Service:*\n{service}"},
                {"type": "mrkdwn", "text": f"*Root Cause:*\n{root_cause}"},
                {"type": "mrkdwn", "text": f"*Issue:*\n{issue}"},
                {"type": "mrkdwn", "text": f"*Suggested Fix:*\n{suggested_fix}"},
                {"type": "mrkdwn", "text": f"*Confidence:*\n{confidence}"},
            ],
        },
    ]

    payload = {"blocks": blocks, "text": f"KORAL Alert: {issue}"}

    try:
        resp = httpx.post(webhook, json=payload, timeout=10.0)
        if resp.status_code == 200:
            logger.info("Slack alert sent successfully")
            return True
        else:
            logger.error(f"Slack webhook error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Slack send failed: {e}")
        return False
