"""Notification event handler used by both Kafka consumers and local fallback."""

import asyncio
import html
import logging

from app.core.config import settings
from app.utils.email_utils import send_email

logger = logging.getLogger(__name__)


async def handle_event_event(event: dict) -> None:
    if not settings.FEATURE_EMAIL:
        return

    event_type = event.get("type", "notification")
    data = event.get("data") or {}
    recipient = data.get("email")
    if not recipient:
        logger.warning("Notification event %s has no recipient", event_type)
        return
    if not settings.MAIL_HOST:
        logger.warning("SMTP is not configured; skipped %s for %s", event_type, recipient)
        return

    subject = {
        "purchase_email": "Purchase confirmation",
        "auto_signup_email": "Your account is ready",
    }.get(event_type, "Notification")
    safe_rows = []
    for key, value in data.items():
        if key.lower() in {"password", "token", "secret"}:
            continue
        safe_rows.append(f"<p><strong>{html.escape(str(key).replace('_', ' ').title())}:</strong> {html.escape(str(value))}</p>")
    await asyncio.to_thread(send_email, recipient, subject, "".join(safe_rows))
