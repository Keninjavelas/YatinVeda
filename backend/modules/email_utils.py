"""Email utilities for YatinVeda backend.

This module sends transactional emails (welcome, password reset
notifications) via SendGrid's HTTP API for better deliverability.

Configuration via environment variables:
- SENDGRID_API_KEY (required to actually send)
- EMAIL_FROM (fallback: noreply@yatinveda.com)
- EMAIL_FROM_NAME (optional, e.g. "YatinVeda")

If SENDGRID_API_KEY is missing or sending fails, functions log errors
but DO NOT raise, so API flows remain unaffected.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Optional
from urllib import request, error as urllib_error

logger = logging.getLogger(__name__)


SENDGRID_API_KEY_ENV = "SENDGRID_API_KEY"
SENDGRID_ENDPOINT = "https://api.sendgrid.com/v3/mail/send"


def _get_sendgrid_api_key() -> Optional[str]:
    api_key = os.getenv(SENDGRID_API_KEY_ENV)
    if not api_key:
        logger.warning(
            "SENDGRID_API_KEY is not set; emails will not be sent. "
            "Configure SENDGRID_API_KEY to enable transactional email."
        )
        return None
    return api_key


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send an email using SendGrid's HTTP API.

    This is best-effort: logs errors and returns without raising so
    that registration/reset flows continue even if email delivery
    fails.
    """
    api_key = _get_sendgrid_api_key()
    if not api_key:
        return

    from_email = os.getenv("EMAIL_FROM", "marcsnuffy@gmail.com")
    from_name = os.getenv("EMAIL_FROM_NAME", "YatinVeda")

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
            }
        ],
        "from": {"email": from_email, "name": from_name},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": body},
        ],
    }

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        SENDGRID_ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=10) as resp:
            # 202 is expected for SendGrid success
            if resp.status != 202:
                logger.error(
                    "SendGrid email send returned non-202 status",
                    extra={"status": resp.status, "to": to_email, "subject": subject},
                )
            else:
                logger.info("Email sent", extra={"to": to_email, "subject": subject})
    except urllib_error.HTTPError as e:
        body_bytes = e.read()
        try:
            error_body = body_bytes.decode("utf-8")
        except Exception:
            error_body = str(body_bytes)
        logger.exception(
            "SendGrid HTTPError while sending email",
            extra={"status": e.code, "reason": e.reason, "body": error_body, "to": to_email},
        )
    except Exception:
        logger.exception("Failed to send email via SendGrid", extra={"to": to_email, "subject": subject})


def send_welcome_email(to_email: str, name: Optional[str] = None) -> None:
    """Send a friendly welcome email after successful signup."""
    display_name = name or to_email.split("@")[0]
    subject = "🌌 Welcome to YatinVeda"
    body = (
        f"Dear {display_name},\n\n"
        "Welcome to YatinVeda! Your account has been created successfully. "
        "You can now sign in, generate charts, book sessions with gurus, and explore "
        "your personalized Vedic astrology journey.\n\n"
        "If you did not sign up for this account, please contact support immediately.\n\n"
        "With gratitude,\n"
        "Team YatinVeda"
    )
    send_email(to_email, subject, body)


def send_password_reset_confirmation(to_email: str, name: Optional[str] = None) -> None:
    """Send a confirmation email when a password has been reset."""
    display_name = name or to_email.split("@")[0]
    subject = "🔐 Your YatinVeda password was changed"
    body = (
        f"Dear {display_name},\n\n"
        "This is a quick note to let you know that the password for your YatinVeda "
        "account was just updated via the reset screen.\n\n"
        "If you made this change, no further action is needed.\n"
        "If you did NOT request this change, please reset your password again "
        "immediately and contact support.\n\n"
        "With care,\n"
        "Team YatinVeda"
    )
    send_email(to_email, subject, body)
