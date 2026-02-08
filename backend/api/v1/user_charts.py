"""
📊 Chart Management API Endpoints (CRUD)
Handles user's saved charts: create, read, update, delete
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from database import get_db
from models.database import Chart, User
from modules.auth import get_current_user_401 as get_current_user
import logging

router = APIRouter()

# Pydantic schemas
class ChartCreate(BaseModel):
    chart_name: str
    birth_details: dict
    chart_data: dict
    chart_type: str = "D1"
    is_public: bool = False

class ChartUpdate(BaseModel):
    chart_name: str | None = None
    is_public: bool | None = None

class ChartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    chart_name: str
    birth_details: dict
    chart_data: dict
    chart_type: str
    is_public: bool
    created_at: datetime
    updated_at: datetime

@router.post("/", response_model=ChartResponse, status_code=status.HTTP_201_CREATED)
async def create_chart(
    chart: ChartCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a new birth chart for the current user
    """
    try:
        new_chart = Chart(
            user_id=current_user["user_id"],
            chart_name=chart.chart_name,
            birth_details=chart.birth_details,
            chart_data=chart.chart_data,
            chart_type=chart.chart_type,
            is_public=chart.is_public
        )
        db.add(new_chart)
        db.commit()
        db.refresh(new_chart)
        
        return new_chart
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving chart"
        )

@router.get("/", response_model=List[ChartResponse])
async def list_user_charts(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all charts for the current user
    """
    try:
        return db.query(Chart).filter(
            Chart.user_id == current_user["user_id"]
        ).order_by(Chart.created_at.desc(), Chart.id.desc()).offset(skip).limit(limit).all()
        
    except Exception as e:
        logging.error(f"Error listing charts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving charts"
        )

@router.get("/{chart_id}", response_model=ChartResponse)
async def get_chart(
    chart_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific chart by ID
    """
    try:
        chart = db.query(Chart).filter(Chart.id == chart_id).first()
        
        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chart not found"
            )
        
        # Check ownership or public access
        if chart.user_id != current_user["user_id"] and not chart.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this chart"
            )
        
        return chart
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chart"
        )

@router.put("/{chart_id}", response_model=ChartResponse)
async def update_chart(
    chart_id: int,
    chart_update: ChartUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a chart's name or privacy settings
    """
    try:
        chart = db.query(Chart).filter(Chart.id == chart_id).first()
        
        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chart not found"
            )
        
        # Check ownership
        if chart.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this chart"
            )
        
        # Update fields
        if chart_update.chart_name is not None:
            chart.chart_name = chart_update.chart_name
        if chart_update.is_public is not None:
            chart.is_public = chart_update.is_public
        
        chart.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(chart)
        
        return chart
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating chart"
        )

@router.delete("/{chart_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chart(
    chart_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chart
    """
    try:
        chart = db.query(Chart).filter(Chart.id == chart_id).first()
        
        if not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chart not found"
            )
        
        # Check ownership
        if chart.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this chart"
            )
        
        db.delete(chart)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting chart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting chart"
        )
