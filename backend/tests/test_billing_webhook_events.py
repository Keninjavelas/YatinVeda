"""Tests for billing webhook abstraction and idempotent event persistence."""

import json
from unittest.mock import patch

from models.database import BillingWebhookEvent


@patch("api.v1.payments.razorpay_manager.verify_webhook_signature")
def test_webhook_persists_billing_event(mock_verify, client):
    mock_verify.return_value = True

    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_evt_101",
                    "order_id": "order_evt_101",
                    "status": "failed",
                }
            }
        },
    }

    response = client.post(
        "/api/v1/payments/webhook",
        content=json.dumps(payload),
        headers={"x-razorpay-signature": "sig_test"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


@patch("api.v1.payments.razorpay_manager.verify_webhook_signature")
def test_webhook_idempotency_duplicate_event(mock_verify, client, db_session):
    mock_verify.return_value = True

    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_evt_dup",
                    "order_id": "order_evt_dup",
                    "status": "failed",
                }
            }
        },
    }

    first = client.post(
        "/api/v1/payments/webhook",
        content=json.dumps(payload),
        headers={"x-razorpay-signature": "sig_test"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/payments/webhook",
        content=json.dumps(payload),
        headers={"x-razorpay-signature": "sig_test"},
    )
    assert second.status_code == 200
    assert second.json().get("duplicate") is True

    events = db_session.query(BillingWebhookEvent).filter(BillingWebhookEvent.event_id == "pay_evt_dup").all()
    assert len(events) == 1
    assert events[0].status == "processed"
