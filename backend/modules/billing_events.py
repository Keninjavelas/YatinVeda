"""Billing webhook normalization and idempotency helpers."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict


def _first_non_empty(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def normalize_razorpay_event(event_data: Dict[str, Any], raw_body: str) -> Dict[str, Any]:
    """Normalize Razorpay webhook payload to a provider-agnostic event envelope."""
    event_type = event_data.get("event", "unknown")
    payment_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
    refund_entity = event_data.get("payload", {}).get("refund", {}).get("entity", {})

    event_id = _first_non_empty(
        payment_entity.get("id"),
        refund_entity.get("id"),
        event_data.get("id"),
    )

    if event_id:
        idempotency_key = f"razorpay:{event_type}:{event_id}"
    else:
        fingerprint = hashlib.sha256(raw_body.encode("utf-8")).hexdigest()[:24]
        idempotency_key = f"razorpay:{event_type}:{fingerprint}"

    return {
        "provider": "razorpay",
        "event_type": event_type,
        "event_id": event_id,
        "idempotency_key": idempotency_key,
        "occurred_at": datetime.utcnow().isoformat(),
        "payload": event_data,
    }


def verify_razorpay_webhook_signature(
    manager: Any,
    body_str: str,
    signature: str | None,
    secret: str,
) -> bool:
    """Signature verification indirection for easier provider swaps and testing."""
    if not signature:
        return False
    return bool(manager.verify_webhook_signature(body_str, signature, secret))
