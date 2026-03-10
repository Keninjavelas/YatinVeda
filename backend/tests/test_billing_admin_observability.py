"""Tests for billing/admin observability endpoints."""

import json
from unittest.mock import patch

from models.database import User, UserSubscription
from modules.auth import create_access_token


def _admin_headers(user: User) -> dict:
    token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": True,
            "role": user.role,
            "verification_status": user.verification_status,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def _create_admin(db_session, username: str, email: str) -> User:
    admin = User(
        username=username,
        email=email,
        password_hash="hash",
        full_name=username,
        role="user",
        verification_status="active",
        is_admin=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@patch("api.v1.payments.razorpay_manager.verify_webhook_signature")
def test_admin_can_list_billing_webhook_events(mock_verify, client, db_session):
    mock_verify.return_value = True
    admin = _create_admin(db_session, "obs-admin", "obs-admin@example.com")

    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_obs_01",
                    "order_id": "order_obs_01",
                    "status": "failed",
                }
            }
        },
    }

    # Create webhook event records via webhook handler.
    client.post(
        "/api/v1/payments/webhook",
        content=json.dumps(payload),
        headers={"x-razorpay-signature": "sig_test"},
    )

    response = client.get(
        "/api/v1/payments/admin/webhook-events?provider=razorpay&status_filter=processed",
        headers=_admin_headers(admin),
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 1
    assert rows[0]["provider"] == "razorpay"


@patch("api.v1.payments.razorpay_manager.verify_webhook_signature")
def test_subscription_audit_filters(mock_verify, client, db_session):
    mock_verify.return_value = True
    admin = _create_admin(db_session, "audit-admin", "audit-admin@example.com")

    target = User(
        username="audit-target",
        email="audit-target@example.com",
        password_hash="hash",
        full_name="audit-target",
        role="user",
        verification_status="active",
        is_active=True,
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)

    db_session.add(UserSubscription(
        user_id=target.id,
        subscription_plan="starter",
        subscription_status="trial",
    ))
    db_session.commit()

    update_response = client.patch(
        f"/api/v1/auth/entitlements/{target.id}",
        json={
            "subscription_plan": "growth",
            "subscription_status": "active",
            "reason": "upgrade-for-team",
        },
        headers=_admin_headers(admin),
    )
    assert update_response.status_code == 200

    audit_response = client.get(
        f"/api/v1/auth/entitlements/audit?user_id={target.id}&actor_user_id={admin.id}&plan=growth&status_filter=active",
        headers=_admin_headers(admin),
    )
    assert audit_response.status_code == 200
    rows = audit_response.json()
    assert len(rows) >= 1
    assert rows[0]["target_user_id"] == target.id
    assert rows[0]["actor_user_id"] == admin.id
    assert rows[0]["new_plan"] == "growth"
