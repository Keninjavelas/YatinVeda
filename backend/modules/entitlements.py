"""Plan entitlements and feature-access helpers for SaaS subscriptions."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.database import User, UserSubscription
from modules.auth import get_current_user

PLAN_CATALOG: Dict[str, Dict[str, Any]] = {
    "starter": {
        "limits": {
            "monthly_bookings": 30,
            "practitioner_count": 1,
        },
        "features": {
            "video_consult": True,
            "advanced_analytics": False,
            "team_management": False,
            "priority_support": False,
            "api_access": False,
        },
    },
    "growth": {
        "limits": {
            "monthly_bookings": 300,
            "practitioner_count": 5,
        },
        "features": {
            "video_consult": True,
            "advanced_analytics": True,
            "team_management": True,
            "priority_support": False,
            "api_access": True,
        },
    },
    "professional": {
        "limits": {
            "monthly_bookings": 2000,
            "practitioner_count": 25,
        },
        "features": {
            "video_consult": True,
            "advanced_analytics": True,
            "team_management": True,
            "priority_support": True,
            "api_access": True,
        },
    },
}

ACTIVE_STATUSES = {"trial", "active", "grace_period"}


def _is_trial_active(subscription: UserSubscription) -> bool:
    if subscription.subscription_status != "trial":
        return False
    if subscription.trial_ends_at is None:
        return True
    return subscription.trial_ends_at >= datetime.utcnow()


def _is_subscription_active(subscription: UserSubscription) -> bool:
    if subscription.subscription_status == "trial":
        return _is_trial_active(subscription)

    if subscription.subscription_status not in ACTIVE_STATUSES:
        return False

    if subscription.plan_expires_at is None:
        return True

    return subscription.plan_expires_at >= datetime.utcnow()


def get_or_create_subscription(user: User, db: Session) -> UserSubscription:
    subscription = db.query(UserSubscription).filter(UserSubscription.user_id == user.id).first()
    if subscription:
        return subscription

    trial_end = (user.created_at or datetime.utcnow()) + timedelta(days=14)
    subscription = UserSubscription(
        user_id=user.id,
        subscription_plan="starter",
        subscription_status="trial",
        trial_ends_at=trial_end,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def resolve_entitlements(subscription: UserSubscription) -> Dict[str, Any]:
    plan = subscription.subscription_plan if subscription.subscription_plan in PLAN_CATALOG else "starter"
    config = PLAN_CATALOG[plan]

    return {
        "plan": plan,
        "status": subscription.subscription_status,
        "is_active": _is_subscription_active(subscription),
        "trial_active": _is_trial_active(subscription),
        "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
        "plan_expires_at": subscription.plan_expires_at.isoformat() if subscription.plan_expires_at else None,
        "limits": config["limits"],
        "features": config["features"],
    }


def require_feature(feature_key: str):
    """FastAPI dependency factory that enforces feature entitlement."""

    async def _dependency(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        subscription = get_or_create_subscription(user, db)
        entitlements = resolve_entitlements(subscription)
        if not entitlements["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Subscription is not active",
            )

        if not entitlements["features"].get(feature_key, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_key}' is not available on your plan",
            )

        return entitlements

    return _dependency
