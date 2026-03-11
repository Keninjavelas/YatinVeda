"""API rate-limit tiers tied to subscription plans.

Provides per-user rate limits that scale with their subscription tier:
  - free:    30 req/min
  - starter: 60 req/min
  - pro:    200 req/min
  - premium: 600 req/min

Works with the existing slowapi-based rate limiter by dynamically selecting
the key function and default limits based on the authenticated user's plan.
"""

import os
import time
import logging
from typing import Any, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TierConfig:
    name: str
    requests_per_minute: int
    requests_per_hour: int
    daily_ai_queries: int
    max_charts: int
    description: str = ""


# Define tiers
TIERS: Dict[str, TierConfig] = {
    "free": TierConfig(
        name="Free",
        requests_per_minute=30,
        requests_per_hour=500,
        daily_ai_queries=5,
        max_charts=3,
        description="Free tier with basic access",
    ),
    "starter": TierConfig(
        name="Starter",
        requests_per_minute=60,
        requests_per_hour=2000,
        daily_ai_queries=25,
        max_charts=10,
        description="Starter plan with enhanced limits",
    ),
    "pro": TierConfig(
        name="Pro",
        requests_per_minute=200,
        requests_per_hour=8000,
        daily_ai_queries=100,
        max_charts=50,
        description="Professional plan with high limits",
    ),
    "premium": TierConfig(
        name="Premium",
        requests_per_minute=600,
        requests_per_hour=20000,
        daily_ai_queries=500,
        max_charts=0,  # unlimited
        description="Premium plan with maximum limits",
    ),
}


class TieredRateLimiter:
    """In-memory per-user rate limiter with tier-aware limits.

    Uses a sliding window counter pattern.  In production,
    back this with Redis for multi-process consistency.
    """

    def __init__(self) -> None:
        # key: (user_id, window_key) → list of timestamps
        self._windows: Dict[str, list] = defaultdict(list)

    def _clean_window(self, key: str, window_seconds: int) -> None:
        now = time.time()
        cutoff = now - window_seconds
        self._windows[key] = [t for t in self._windows[key] if t > cutoff]

    def check_rate_limit(self, user_id: int, tier: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if the user is within their rate limit.

        Returns:
            (allowed, info_dict)
        """
        config = TIERS.get(tier, TIERS["free"])
        now = time.time()

        # Per-minute window
        minute_key = f"{user_id}:minute"
        self._clean_window(minute_key, 60)
        minute_count = len(self._windows[minute_key])

        if minute_count >= config.requests_per_minute:
            return False, {
                "tier": tier,
                "limit": config.requests_per_minute,
                "remaining": 0,
                "reset_seconds": 60,
                "window": "minute",
            }

        # Per-hour window
        hour_key = f"{user_id}:hour"
        self._clean_window(hour_key, 3600)
        hour_count = len(self._windows[hour_key])

        if hour_count >= config.requests_per_hour:
            return False, {
                "tier": tier,
                "limit": config.requests_per_hour,
                "remaining": 0,
                "reset_seconds": 3600,
                "window": "hour",
            }

        # Record this request
        self._windows[minute_key].append(now)
        self._windows[hour_key].append(now)

        return True, {
            "tier": tier,
            "minute_limit": config.requests_per_minute,
            "minute_remaining": config.requests_per_minute - minute_count - 1,
            "hour_limit": config.requests_per_hour,
            "hour_remaining": config.requests_per_hour - hour_count - 1,
        }

    def get_user_tier(self, user_id: int, db_session: Any = None) -> str:
        """Determine the user's tier from their subscription.

        Falls back to 'free' if no subscription is found or DB is unavailable.
        """
        if db_session is None:
            return "free"
        try:
            from models.database import UserSubscription
            sub = (
                db_session.query(UserSubscription)
                .filter(UserSubscription.user_id == user_id, UserSubscription.status == "active")
                .first()
            )
            if sub and sub.plan in TIERS:
                return sub.plan
        except Exception as e:
            logger.debug("Tier lookup failed for user %s: %s", user_id, e)
        return "free"

    def get_tier_info(self, tier: str) -> Dict[str, Any]:
        config = TIERS.get(tier, TIERS["free"])
        return {
            "name": config.name,
            "requests_per_minute": config.requests_per_minute,
            "requests_per_hour": config.requests_per_hour,
            "daily_ai_queries": config.daily_ai_queries,
            "max_charts": config.max_charts,
            "description": config.description,
        }


# Module-level singleton
_limiter: Optional[TieredRateLimiter] = None


def get_tiered_rate_limiter() -> TieredRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = TieredRateLimiter()
    return _limiter
