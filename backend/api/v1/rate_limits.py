"""Rate limit tier management endpoints.

Exposes tier information and current usage statistics
so users can see their limits and upgrade paths.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List
import logging

from database import get_db
from modules.auth import get_current_user
from middleware.rate_limit_tiers import get_tiered_rate_limiter, TIERS

router = APIRouter(prefix="/rate-limits", tags=["Rate Limits"])
logger = logging.getLogger(__name__)


@router.get("/tiers")
async def list_tiers() -> List[Dict[str, Any]]:
    """List all available rate limit tiers and their limits."""
    limiter = get_tiered_rate_limiter()
    return [limiter.get_tier_info(name) for name in TIERS]


@router.get("/current")
async def current_tier(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get the current user's rate limit tier and usage."""
    limiter = get_tiered_rate_limiter()
    tier = limiter.get_user_tier(current_user["user_id"], db)
    allowed, info = limiter.check_rate_limit(current_user["user_id"], tier)

    return {
        "user_id": current_user["user_id"],
        "tier": tier,
        "tier_info": limiter.get_tier_info(tier),
        "current_usage": info,
    }
