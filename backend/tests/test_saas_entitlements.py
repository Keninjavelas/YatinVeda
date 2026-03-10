"""Tests for SaaS entitlements and subscription admin controls."""

from datetime import datetime, timedelta

from modules.auth import create_access_token
from models.database import User, UserSubscription, Guru


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin,
            "role": user.role,
            "verification_status": user.verification_status,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_get_my_entitlements_defaults(client, db_session):
    user = User(
        username="ent-user",
        email="ent-user@example.com",
        password_hash="hash",
        full_name="Ent User",
        role="user",
        verification_status="active",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    db_session.add(UserSubscription(
        user_id=user.id,
        subscription_plan="starter",
        subscription_status="trial",
        trial_ends_at=datetime.utcnow() + timedelta(days=7),
    ))
    db_session.commit()

    response = client.get("/api/v1/auth/entitlements", headers=_auth_headers_for_user(user))

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "starter"
    assert body["status"] == "trial"
    assert body["is_active"] is True
    assert body["features"]["video_consult"] is True
    assert body["features"]["advanced_analytics"] is False


def test_admin_can_update_user_entitlements(client, db_session):
    admin = User(
        username="ent-admin",
        email="ent-admin@example.com",
        password_hash="hash",
        full_name="Ent Admin",
        role="user",
        verification_status="active",
        is_admin=True,
        is_active=True,
    )
    target = User(
        username="ent-target",
        email="ent-target@example.com",
        password_hash="hash",
        full_name="Ent Target",
        role="user",
        verification_status="active",
        is_active=True,
    )
    db_session.add(admin)
    db_session.add(target)
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(target)

    db_session.add(UserSubscription(
        user_id=admin.id,
        subscription_plan="professional",
        subscription_status="active",
    ))
    db_session.add(UserSubscription(
        user_id=target.id,
        subscription_plan="starter",
        subscription_status="trial",
        trial_ends_at=datetime.utcnow() + timedelta(days=14),
    ))
    db_session.commit()

    payload = {
        "subscription_plan": "growth",
        "subscription_status": "active",
        "plan_duration_days": 30,
    }

    response = client.patch(
        f"/api/v1/auth/entitlements/{target.id}",
        json=payload,
        headers=_auth_headers_for_user(admin),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "growth"
    assert body["status"] == "active"
    assert body["features"]["advanced_analytics"] is True
    assert body["features"]["team_management"] is True

    audit_response = client.get(
        f"/api/v1/auth/entitlements/audit?user_id={target.id}",
        headers=_auth_headers_for_user(admin),
    )
    assert audit_response.status_code == 200
    entries = audit_response.json()
    assert len(entries) >= 1
    assert entries[0]["target_user_id"] == target.id
    assert entries[0]["new_plan"] == "growth"


def test_admin_analytics_requires_advanced_analytics_plan(client, db_session):
    admin = User(
        username="admin-analytics",
        email="admin-analytics@example.com",
        password_hash="hash",
        full_name="Admin Analytics",
        role="user",
        verification_status="active",
        is_admin=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    # Starter plan should not have advanced analytics entitlement.
    db_session.add(UserSubscription(
        user_id=admin.id,
        subscription_plan="starter",
        subscription_status="active",
    ))
    db_session.commit()

    forbidden = client.get("/api/v1/admin/analytics?period_days=30", headers=_auth_headers_for_user(admin))
    assert forbidden.status_code == 403

    # Upgrade to growth plan, then access should be allowed.
    sub = db_session.query(UserSubscription).filter(UserSubscription.user_id == admin.id).first()
    sub.subscription_plan = "growth"
    db_session.commit()

    allowed = client.get("/api/v1/admin/analytics?period_days=30", headers=_auth_headers_for_user(admin))
    assert allowed.status_code == 200


def test_practitioner_clients_requires_team_management(client, db_session):
    practitioner = User(
        username="practitioner-team",
        email="practitioner-team@example.com",
        password_hash="hash",
        full_name="Practitioner Team",
        role="practitioner",
        verification_status="verified",
        is_active=True,
    )
    db_session.add(practitioner)
    db_session.commit()
    db_session.refresh(practitioner)

    guru = Guru(
        user_id=practitioner.id,
        name="Practitioner Team",
        title="Vedic Astrologer",
        bio="Experienced practitioner profile for entitlement checks.",
        specializations=["career_guidance"],
        languages=["English"],
        experience_years=5,
        price_per_hour=1000,
        is_active=True,
    )
    db_session.add(guru)
    db_session.add(UserSubscription(
        user_id=practitioner.id,
        subscription_plan="starter",
        subscription_status="active",
    ))
    db_session.commit()

    headers = _auth_headers_for_user(practitioner)
    forbidden = client.get("/api/v1/practitioner/clients", headers=headers)
    assert forbidden.status_code == 403

    sub = db_session.query(UserSubscription).filter(UserSubscription.user_id == practitioner.id).first()
    sub.subscription_plan = "growth"
    db_session.commit()

    allowed = client.get("/api/v1/practitioner/clients", headers=headers)
    assert allowed.status_code == 200
    assert isinstance(allowed.json(), list)
