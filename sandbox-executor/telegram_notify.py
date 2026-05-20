from __future__ import annotations

import os
from typing import Dict, Any

from telegram import Bot


def format_message(payload: Dict[str, Any]) -> str:
    return (
        "🚨 KORAL INCIDENT\n"
        f"Service: {payload.get('service', 'backend')}\n"
        f"Issue: {payload.get('issue', payload.get('root_cause', 'unknown'))}\n"
        f"AI Root Cause: {payload.get('root_cause', 'unknown')}\n"
        f"Action: {payload.get('action', payload.get('command', 'review'))}\n"
        f"Verification: {payload.get('verification_status', 'pending')}\n"
        f"Confidence: {payload.get('confidence', 0)}"
    )


async def send(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False
    bot = Bot(token=token)
    await bot.send_message(chat_id=chat_id, text=message)
    return True
