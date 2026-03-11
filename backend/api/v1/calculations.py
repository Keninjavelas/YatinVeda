"""Native astrology calculation endpoints.

Provides birth chart generation, compatibility analysis, and
Dasha period computation using the built-in calculation engine.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from modules.auth import get_current_user
from modules.astrology_engine import get_astrology_engine

router = APIRouter(prefix="/calculations", tags=["Astrological Calculations"])
logger = logging.getLogger(__name__)


class ChartCalculationRequest(BaseModel):
    birth_date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    birth_time: str = Field(..., description="Birth time in HH:MM format (24-hour)")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone_offset: float = Field(5.5, description="UTC offset in hours (e.g. 5.5 for IST)")


class CompatibilityRequest(BaseModel):
    person1: ChartCalculationRequest
    person2: ChartCalculationRequest


@router.post("/chart")
async def calculate_birth_chart(
    request: ChartCalculationRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Calculate a full Vedic birth chart with planetary positions and Dasha periods."""
    try:
        dt = datetime.strptime(f"{request.birth_date} {request.birth_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date/time format. Use YYYY-MM-DD and HH:MM")

    engine = get_astrology_engine()
    chart = engine.calculate_chart(dt, request.latitude, request.longitude, request.timezone_offset)
    return chart.to_dict()


@router.post("/compatibility")
async def calculate_compatibility(
    request: CompatibilityRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Calculate Ashtakoot compatibility between two birth charts."""
    engine = get_astrology_engine()

    try:
        dt1 = datetime.strptime(f"{request.person1.birth_date} {request.person1.birth_time}", "%Y-%m-%d %H:%M")
        dt2 = datetime.strptime(f"{request.person2.birth_date} {request.person2.birth_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date/time format")

    chart1 = engine.calculate_chart(dt1, request.person1.latitude, request.person1.longitude, request.person1.timezone_offset)
    chart2 = engine.calculate_chart(dt2, request.person2.latitude, request.person2.longitude, request.person2.timezone_offset)

    compatibility = engine.calculate_compatibility(chart1, chart2)

    return {
        "person1_chart": chart1.to_dict(),
        "person2_chart": chart2.to_dict(),
        "compatibility": compatibility,
    }


@router.post("/dasha")
async def calculate_dasha_periods(
    request: ChartCalculationRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Calculate Vimshottari Dasha periods for a birth chart."""
    try:
        dt = datetime.strptime(f"{request.birth_date} {request.birth_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date/time format")

    engine = get_astrology_engine()
    chart = engine.calculate_chart(dt, request.latitude, request.longitude, request.timezone_offset)

    # Find currently active Dasha
    now = datetime.utcnow()
    active_dasha = None
    for d in chart.dashas:
        if d.start <= now <= d.end:
            active_dasha = d.to_dict()
            break

    return {
        "dashas": [d.to_dict() for d in chart.dashas],
        "active_dasha": active_dasha,
        "calculation_method": chart.calculation_method,
    }
