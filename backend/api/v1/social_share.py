"""Social media sharing endpoints.

Generates share-ready content and URLs for charts, prescriptions,
community posts, and events across different social platforms.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from urllib.parse import quote
import logging

from database import get_db
from models.database import Chart, CommunityPost, CommunityEvent
from modules.auth import get_current_user

router = APIRouter(prefix="/share", tags=["Social Media"])
logger = logging.getLogger(__name__)

FRONTEND_URL = "http://localhost:3000"


class ShareRequest(BaseModel):
    content_type: str  # "chart", "post", "event", "insight"
    content_id: int
    platform: str  # "twitter", "facebook", "whatsapp", "linkedin", "copy"
    custom_message: Optional[str] = None


class ShareResponse(BaseModel):
    share_url: str
    preview_text: str
    platform: str
    content_type: str


def _build_share_url(platform: str, text: str, url: str) -> str:
    """Build platform-specific share URL."""
    encoded_text = quote(text)
    encoded_url = quote(url)

    urls = {
        "twitter": f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}&quote={encoded_text}",
        "whatsapp": f"https://wa.me/?text={encoded_text}%20{encoded_url}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}",
        "copy": url,
    }
    return urls.get(platform, url)


@router.post("/generate", response_model=ShareResponse)
async def generate_share_link(
    request: ShareRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a shareable link for content."""
    if request.platform not in {"twitter", "facebook", "whatsapp", "linkedin", "copy"}:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    text = ""
    content_url = ""

    if request.content_type == "chart":
        chart = db.query(Chart).filter(
            Chart.id == request.content_id,
            Chart.user_id == current_user["user_id"],
        ).first()
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")
        text = request.custom_message or "Check out my Vedic birth chart analysis on YatinVeda! 🌟"
        content_url = f"{FRONTEND_URL}/chart/{chart.id}"

    elif request.content_type == "post":
        post = db.query(CommunityPost).filter(CommunityPost.id == request.content_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        title = post.title or "Community Post"
        text = request.custom_message or f"Read '{title}' on YatinVeda Community 📖"
        content_url = f"{FRONTEND_URL}/community/{post.id}"

    elif request.content_type == "event":
        event = db.query(CommunityEvent).filter(CommunityEvent.id == request.content_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        text = request.custom_message or f"Join '{event.title}' on YatinVeda! 🎉"
        content_url = f"{FRONTEND_URL}/community/events/{event.id}"

    elif request.content_type == "insight":
        text = request.custom_message or "Discover Vedic astrological insights on YatinVeda 🔮"
        content_url = f"{FRONTEND_URL}"

    else:
        raise HTTPException(status_code=400, detail="Invalid content_type")

    share_url = _build_share_url(request.platform, text, content_url)

    return ShareResponse(
        share_url=share_url,
        preview_text=text,
        platform=request.platform,
        content_type=request.content_type,
    )


@router.get("/platforms")
async def list_platforms() -> list:
    """List supported social media platforms."""
    return [
        {"id": "twitter", "name": "Twitter / X", "icon": "twitter"},
        {"id": "facebook", "name": "Facebook", "icon": "facebook"},
        {"id": "whatsapp", "name": "WhatsApp", "icon": "message-circle"},
        {"id": "linkedin", "name": "LinkedIn", "icon": "linkedin"},
        {"id": "copy", "name": "Copy Link", "icon": "copy"},
    ]
