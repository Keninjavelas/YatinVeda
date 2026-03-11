"""Advanced remedies API endpoints.

Provides personalized remedy recommendations, tracking plans,
and adherence monitoring based on birth chart analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from database import get_db
from models.database import Chart
from modules.auth import get_current_user
from modules.remedy_engine import get_remedy_engine

router = APIRouter(prefix="/remedies", tags=["Remedies"])
logger = logging.getLogger(__name__)


class RemedyRequest(BaseModel):
    chart_id: Optional[int] = None
    concerns: Optional[List[str]] = None  # e.g. ["career", "health", "relationship"]


class TrackingPlanRequest(BaseModel):
    remedies: List[Dict[str, Any]]
    start_date: Optional[str] = None  # ISO format


@router.post("/recommend")
async def recommend_remedies(
    request: RemedyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get personalized remedy recommendations based on birth chart."""
    engine = get_remedy_engine()

    chart_data: Dict[str, Any] = {}
    if request.chart_id:
        chart = db.query(Chart).filter(
            Chart.id == request.chart_id,
            Chart.user_id == current_user["user_id"],
        ).first()
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")
        chart_data = chart.chart_data or {}
    else:
        # Try to get primary chart
        chart = db.query(Chart).filter(
            Chart.user_id == current_user["user_id"],
            Chart.is_primary == True,
        ).first()
        if chart:
            chart_data = chart.chart_data or {}

    if not chart_data.get("planets"):
        raise HTTPException(
            status_code=400,
            detail="No chart data available. Please generate a birth chart first.",
        )

    recommendations = engine.recommend_remedies(chart_data, request.concerns)

    return {
        "recommendations": recommendations,
        "total": len(recommendations),
        "concerns": request.concerns or [],
    }


@router.post("/tracking-plan")
async def create_tracking_plan(
    request: TrackingPlanRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a structured tracking plan for selected remedies."""
    engine = get_remedy_engine()

    start_date = None
    if request.start_date:
        try:
            start_date = datetime.fromisoformat(request.start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    plan = engine.create_tracking_plan(request.remedies, start_date)

    return {
        "tracking_plan": plan,
        "total_remedies": len(plan),
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/categories")
async def get_remedy_categories(
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, str]]:
    """Get available remedy categories."""
    from modules.remedy_engine import RemedyCategory
    return [
        {"value": c.value, "label": c.value.replace("_", " ").title()}
        for c in RemedyCategory
    ]


@router.get("/planets/{planet}")
async def get_planet_remedies(
    planet: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all available remedies for a specific planet."""
    from modules.remedy_engine import PLANETARY_REMEDIES
    planet_name = planet.capitalize()
    remedies = PLANETARY_REMEDIES.get(planet_name, [])
    if not remedies:
        raise HTTPException(status_code=404, detail=f"No remedies found for planet: {planet}")

    return {
        "planet": planet_name,
        "remedies": [r.to_dict() for r in remedies],
        "total": len(remedies),
    }
