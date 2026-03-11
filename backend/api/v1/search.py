"""Advanced search API endpoints.

Provides full-text search across users, community posts, and practitioners
via Elasticsearch when available, with SQLAlchemy fallback.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import logging

from database import get_db
from models.database import User, Guru, CommunityPost
from modules.auth import get_current_user
from services.search_service import get_search_service

router = APIRouter(prefix="/search", tags=["Search"])
logger = logging.getLogger(__name__)


@router.get("/global")
async def global_search(
    q: str = Query(..., min_length=1, max_length=200),
    category: Optional[str] = Query(None, regex="^(users|posts|practitioners|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Search across all content types or a specific category."""
    search = get_search_service()
    cat = category or "all"

    if search.enabled:
        return _search_elasticsearch(search, q, cat, page, page_size)
    return _search_database(db, q, cat, page, page_size)


def _search_elasticsearch(search, q: str, category: str, page: int, size: int) -> Dict:
    results: Dict[str, Any] = {}

    if category in ("users", "all"):
        results["users"] = search.search(
            "users", q, fields=["username", "full_name", "bio"], page=page, page_size=size,
        )
    if category in ("posts", "all"):
        results["posts"] = search.search(
            "community_posts", q, fields=["title", "content", "author"], page=page, page_size=size,
        )
    if category in ("practitioners", "all"):
        results["practitioners"] = search.search(
            "practitioners", q, fields=["name", "title", "bio", "specializations"],
            page=page, page_size=size, filters={"verified": True},
        )

    return results


def _search_database(db: Session, q: str, category: str, page: int, size: int) -> Dict:
    """Fallback search using SQLAlchemy ILIKE."""
    pattern = f"%{q}%"
    offset = (page - 1) * size
    results: Dict[str, Any] = {}

    if category in ("users", "all"):
        query = db.query(User).filter(
            (User.username.ilike(pattern)) | (User.full_name.ilike(pattern))
        )
        total = query.count()
        rows = query.offset(offset).limit(size).all()
        results["users"] = {
            "hits": [
                {"_id": str(u.id), "username": u.username, "full_name": u.full_name, "role": u.role}
                for u in rows
            ],
            "total": total,
            "page": page,
            "page_size": size,
        }

    if category in ("posts", "all"):
        query = db.query(CommunityPost).filter(
            (CommunityPost.title.ilike(pattern)) | (CommunityPost.content.ilike(pattern))
        )
        total = query.count()
        rows = query.offset(offset).limit(size).all()
        results["posts"] = {
            "hits": [
                {"_id": str(p.id), "title": p.title, "content": (p.content or "")[:200], "author_id": p.user_id}
                for p in rows
            ],
            "total": total,
            "page": page,
            "page_size": size,
        }

    if category in ("practitioners", "all"):
        query = (
            db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(User.verification_status == "verified")
            .filter(
                (User.full_name.ilike(pattern))
                | (Guru.bio.ilike(pattern))
                | (Guru.title.ilike(pattern))
            )
        )
        total = query.count()
        rows = query.offset(offset).limit(size).all()
        results["practitioners"] = {
            "hits": [
                {
                    "_id": str(g.id),
                    "name": u.full_name or u.username,
                    "title": g.title,
                    "specializations": g.specializations or [],
                    "experience_years": g.experience_years,
                }
                for g, u in rows
            ],
            "total": total,
            "page": page,
            "page_size": size,
        }

    return results


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=100),
    index: str = Query("users", regex="^(users|community_posts|practitioners)$"),
    field: str = Query("username"),
    current_user: dict = Depends(get_current_user),
) -> List[str]:
    """Return autocomplete suggestions for a field."""
    search = get_search_service()
    if not search.enabled:
        return []
    return search.autocomplete(index, field, q)
