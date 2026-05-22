"""Slack notification helper for KORAL incidents."""

from __future__ import annotations

import logging
import os

import requests
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential
from prometheus_client import Counter


logger = logging.getLogger(__name__)

slack_notifications_sent = Counter("slack_notifications_sent", "Slack notifications sent")
slack_notification_failures = Counter("slack_notification_failures", "Slack notification failures")
SLACK_BREAKER = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _deliver_slack(webhook_url: str, message: str):
    response = requests.post(webhook_url, json={"text": message}, timeout=10)
    if not response.ok:
        raise RuntimeError(f"Slack webhook error: {response.status_code}")
    return response


def _format_message(service: str, issue: str, root_cause: str, suggested_fix: str, confidence: str | int | float) -> str:
    if isinstance(confidence, str):
        confidence_text = confidence
    else:
        confidence_value = float(confidence)
        confidence_text = f"{confidence_value:.0f}%" if confidence_value > 1 else f"{confidence_value * 100:.0f}%"

    return (
        "🚨 KORAL INCIDENT\n\n"
        f"Service:\n{service}\n\n"
        f"Issue:\n{issue}\n\n"
        f"Root Cause:\n{root_cause}\n\n"
        f"Suggested Fix:\n{suggested_fix}\n\n"
        f"Confidence:\n{confidence_text}\n\n"
        "Status:\nCritical"
    )


def send_slack_alert(service: str, issue: str, root_cause: str, suggested_fix: str, confidence: str | int | float) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", os.getenv("SLACK_WEBHOOK", ""))
    if not webhook_url:
        logger.info("Slack disabled: missing webhook URL")
        return False

    message = _format_message(service, issue, root_cause, suggested_fix, confidence)
    try:
        SLACK_BREAKER.call(_deliver_slack, webhook_url, message)
        slack_notifications_sent.inc()
        return True
    except Exception as exc:
        slack_notification_failures.inc()
        logger.error("Slack send failed: %s", exc)
        return False