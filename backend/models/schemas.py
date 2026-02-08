"""
Pydantic schemas for AI chat functionality
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ChatMessage(BaseModel):
    """User message to AI assistant"""
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """AI assistant response"""
    response: str
    suggestions: List[str] = []
    related_topics: List[str] = []
    session_id: Optional[str] = None


class ChartData(BaseModel):
    """Birth chart data for AI context"""
    chart_name: str
    birth_details: Dict[str, Any]
    chart_data: Dict[str, Any]
    chart_type: str = "D1"
