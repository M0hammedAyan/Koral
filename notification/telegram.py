"""Telegram notification helper for incident alerts."""

from __future__ import annotations

from typing import Any, Dict

from telegram import Bot

from backend.resilience import CircuitBreaker, call_with_circuit
from tenacity import retry, stop_after_attempt, wait_exponential


TELEGRAM_BREAKER = CircuitBreaker(fail_threshold=5, reset_timeout=30)


def format_telegram_message(incident: Dict[str, Any]) -> str:
    severity = str(incident.get("severity", "medium")).upper()
    service = incident.get("service", incident.get("namespace", "koral"))
    issue = incident.get("summary", incident.get("root_cause", "Unknown issue"))
    cause = incident.get("root_cause", "Unknown")
    remediation = incident.get("ai_action", incident.get("recommended_action", "review incident"))
    confidence = incident.get("confidence", 0)
    if isinstance(confidence, str):
        confidence_text = confidence
    else:
        confidence_value = float(confidence)
        confidence_text = f"{confidence_value * 100:.0f}%" if confidence_value <= 1 else f"{confidence_value:.0f}%"
    return (
        "🚨 Incident\n"
        f"Service: {service}\n"
        f"Issue: {issue}\n"
        f"Cause: {cause}\n"
        f"Suggested fix: {remediation}\n"
        f"Severity: {severity}\n"
        f"Confidence: {confidence_text}"
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
async def _send_telegram_once(bot_token: str, chat_id: str, message: str) -> bool:
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message)
    return True


async def send_telegram_alert(bot_token: str, chat_id: str, message: str) -> bool:
    if not bot_token or not chat_id:
        return False
    try:
        return await call_with_circuit(TELEGRAM_BREAKER, _send_telegram_once, bot_token, chat_id, message, timeout=10)
    except Exception:
        return False