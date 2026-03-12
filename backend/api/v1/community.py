"""
🌐 Community & Social Networking API
Social media-like features: posts, comments, likes, follows, events
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from database import get_db
from models.database import (
    User, CommunityPost, PostComment, PostLike, CommentLike,
    UserFollow, CommunityEvent, EventRegistration, UserProfile, Notification
)
from modules.auth import get_current_user

router = APIRouter()


def _get_user_from_db(db: Session, user_id: int) -> User:
    """Fetch the actual User ORM model from DB (current_user is UserInfo without full_name)."""
    return db.query(User).filter(User.id == user_id).first()


# ==================== Pydantic Models ====================

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    post_type: str = Field(default="text")  # text, chart_share, achievement, event, ritual
    media_url: Optional[str] = None
    chart_id: Optional[int] = None
    tags: Optional[List[str]] = None
    visibility: str = Field(default="public")  # public, friends, private


class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    media_url: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    content: str
    post_type: str
    media_url: Optional[str]
    chart_id: Optional[int]
    tags: Optional[List[str]]
    visibility: str
    likes_count: int
    comments_count: int
    shares_count: int
    is_pinned: bool
    is_edited: bool
    edited_at: Optional[datetime]
    created_at: datetime
    is_liked_by_user: bool = False
    is_own_post: bool = False


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_comment_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    parent_comment_id: Optional[int]
    content: str
    likes_count: int
    is_edited: bool
    edited_at: Optional[datetime]
    created_at: datetime
    is_liked_by_user: bool = False
    replies_count: int = 0


class UserProfileUpdate(BaseModel):
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    interests: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None


class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    cover_image_url: Optional[str]
    location: Optional[str]
    website: Optional[str]
    interests: Optional[List[str]]
    expertise_areas: Optional[List[str]]
    is_verified: bool
    followers_count: int
    following_count: int
    posts_count: int
    is_following: bool = False
    is_followed_by: bool = False
    is_own_profile: bool = False


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    event_type: str  # ritual, webinar, study_group, circle_story
    event_date: datetime
    duration_minutes: int
    location: Optional[str] = None
    max_participants: Optional[int] = None
    is_public: bool = True
    tags: Optional[List[str]] = None
    cover_image_url: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    created_by: int
    creator_username: str
    creator_name: Optional[str]
    title: str
    description: str
    event_type: str
    event_date: datetime
    duration_minutes: int
    location: Optional[str]
    max_participants: Optional[int]
    participants_count: int
    is_public: bool
    tags: Optional[List[str]]
    cover_image_url: Optional[str]
    status: str
    created_at: datetime
    is_registered: bool = False
    is_creator: bool = False


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    content: str
    link_url: Optional[str]
    related_user_id: Optional[int]
    related_username: Optional[str]
    is_read: bool
    created_at: datetime


# ==================== Helper Functions ====================

def get_user_profile_or_create(db: Session, user_id: int) -> UserProfile:
    """Get or create user profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def create_notification(db: Session, user_id: int, notification_type: str, title: str, content: str, link_url: Optional[str] = None, related_user_id: Optional[int] = None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        link_url=link_url,
        related_user_id=related_user_id
    )
    db.add(notification)
    db.commit()


# ==================== Posts Endpoints ====================

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new community post"""
    user = _get_user_from_db(db, current_user.id)
    # Validate chart_id if provided
    if post_data.chart_id:
        from models.database import Chart
        chart = db.query(Chart).filter(Chart.id == post_data.chart_id, Chart.user_id == current_user.id).first()
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")
    
    # Create post
    new_post = CommunityPost(
        user_id=current_user.id,
        content=post_data.content,
        post_type=post_data.post_type,
        media_url=post_data.media_url,
        chart_id=post_data.chart_id,
        tags=post_data.tags,
        visibility=post_data.visibility
    )
    db.add(new_post)
    
    # Update user profile post count
    profile = get_user_profile_or_create(db, current_user.id)
    profile.posts_count += 1
    
    db.commit()
    db.refresh(new_post)
    
    # Get profile for avatar
    return PostResponse(
        id=new_post.id,
        user_id=new_post.user_id,
        username=current_user.username,
        full_name=user.full_name if user else None,
        avatar_url=profile.avatar_url,
        content=new_post.content,
        post_type=new_post.post_type,
        media_url=new_post.media_url,
        chart_id=new_post.chart_id,
        tags=new_post.tags,
        visibility=new_post.visibility,
        likes_count=0,
        comments_count=0,
        shares_count=0,
        is_pinned=False,
        is_edited=False,
        edited_at=None,
        created_at=new_post.created_at,
        is_liked_by_user=False,
        is_own_post=True
    )


@router.get("/posts", response_model=List[PostResponse])
async def get_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    feed_type: str = Query("public", pattern="^(public|following|user)$"),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get community feed - public, following, or specific user posts"""
    query = db.query(CommunityPost).options(joinedload(CommunityPost.user))
    
    if feed_type == "following":
        # Get posts from users the current user follows
        following_ids = db.query(UserFollow.following_id).filter(
            UserFollow.follower_id == current_user.id
        ).subquery()
        query = query.filter(CommunityPost.user_id.in_(following_ids))
    elif feed_type == "user":
        # Get posts from a specific user
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required for user feed")
        query = query.filter(CommunityPost.user_id == user_id)
    
    # Filter by visibility
    if feed_type != "user" or user_id != current_user.id:
        query = query.filter(CommunityPost.visibility == "public")
    
    posts = query.order_by(desc(CommunityPost.created_at)).offset(skip).limit(limit).all()
    
    # Handle empty posts case
    if not posts:
        return []
    
    # Get user likes for these posts
    post_ids = [post.id for post in posts]
    user_likes = db.query(PostLike.post_id).filter(
        PostLike.post_id.in_(post_ids),
        PostLike.user_id == current_user.id
    ).all()
    liked_post_ids = {like.post_id for like in user_likes}
    
    # Get user profiles for avatars
    user_ids = list(set([post.user_id for post in posts]))
    profiles = db.query(UserProfile).filter(UserProfile.user_id.in_(user_ids)).all()
    profile_map = {p.user_id: p for p in profiles}
    
    return [
        PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=post.user.username,
            full_name=post.user.full_name,
            avatar_url=profile_map[post.user_id].avatar_url if post.user_id in profile_map and profile_map[post.user_id] else None,
            content=post.content,
            post_type=post.post_type,
            media_url=post.media_url,
            chart_id=post.chart_id,
            tags=post.tags,
            visibility=post.visibility,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            shares_count=post.shares_count,
            is_pinned=post.is_pinned,
            is_edited=post.is_edited,
            edited_at=post.edited_at,
            created_at=post.created_at,
            is_liked_by_user=post.id in liked_post_ids,
            is_own_post=post.user_id == current_user.id
        )
        for post in posts
    ]


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific post"""
    post = db.query(CommunityPost).options(joinedload(CommunityPost.user)).filter(
        CommunityPost.id == post_id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user liked this post
    user_like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    ).first()
    
    # Get profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == post.user_id).first()
    
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        username=post.user.username,
        full_name=post.user.full_name,
        avatar_url=profile.avatar_url if profile else None,
        content=post.content,
        post_type=post.post_type,
        media_url=post.media_url,
        chart_id=post.chart_id,
        tags=post.tags,
        visibility=post.visibility,
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        shares_count=post.shares_count,
        is_pinned=post.is_pinned,
        is_edited=post.is_edited,
        edited_at=post.edited_at,
        created_at=post.created_at,
        is_liked_by_user=bool(user_like),
        is_own_post=post.user_id == current_user.id
    )


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a post (only by post owner)"""
    user = _get_user_from_db(db, current_user.id)
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    
    # Update fields
    if post_data.content:
        post.content = post_data.content
    if post_data.media_url is not None:
        post.media_url = post_data.media_url
    if post_data.tags is not None:
        post.tags = post_data.tags
    if post_data.visibility:
        post.visibility = post_data.visibility
    
    post.is_edited = True
    post.edited_at = datetime.utcnow()
    
    db.commit()
    db.refresh(post)
    
    # Get profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == post.user_id).first()
    
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        username=current_user.username,
        full_name=user.full_name if user else None,
        avatar_url=profile.avatar_url if profile else None,
        content=post.content,
        post_type=post.post_type,
        media_url=post.media_url,
        chart_id=post.chart_id,
        tags=post.tags,
        visibility=post.visibility,
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        shares_count=post.shares_count,
        is_pinned=post.is_pinned,
        is_edited=post.is_edited,
        edited_at=post.edited_at,
        created_at=post.created_at,
        is_liked_by_user=False,
        is_own_post=True
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post (only by post owner or admin)"""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    # Update user profile post count
    profile = get_user_profile_or_create(db, post.user_id)
    profile.posts_count = max(0, profile.posts_count - 1)
    
    db.delete(post)
    db.commit()


# ==================== Likes Endpoints ====================

@router.post("/posts/{post_id}/like", status_code=status.HTTP_201_CREATED)
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Like a post"""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if already liked
    existing_like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        return {"message": "Already liked", "likes_count": post.likes_count}
    
    # Create like
    new_like = PostLike(post_id=post_id, user_id=current_user.id)
    db.add(new_like)
    
    # Increment count
    post.likes_count += 1
    db.commit()
    
    # Create notification for post owner
    if post.user_id != current_user.id:
        create_notification(
            db=db,
            user_id=post.user_id,
            notification_type="like",
            title="New Like",
            content=f"{current_user.username} liked your post",
            link_url=f"/community/posts/{post_id}",
            related_user_id=current_user.id
        )
    
    return {"message": "Post liked successfully", "likes_count": post.likes_count}


@router.delete("/posts/{post_id}/like", status_code=status.HTTP_200_OK)
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlike a post"""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    ).first()
    
    if not like:
        return {"message": "Not liked", "likes_count": post.likes_count}
    
    db.delete(like)
    post.likes_count = max(0, post.likes_count - 1)
    db.commit()
    
    return {"message": "Post unliked successfully", "likes_count": post.likes_count}


# ==================== Comments Endpoints ====================

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a post"""
    user = _get_user_from_db(db, current_user.id)
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Validate parent comment if provided
    if comment_data.parent_comment_id:
        parent = db.query(PostComment).filter(
            PostComment.id == comment_data.parent_comment_id,
            PostComment.post_id == post_id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    # Create comment
    new_comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        parent_comment_id=comment_data.parent_comment_id,
        content=comment_data.content
    )
    db.add(new_comment)
    
    # Increment post comment count
    post.comments_count += 1
    db.commit()
    db.refresh(new_comment)
    
    # Create notification for post owner
    if post.user_id != current_user.id:
        create_notification(
            db=db,
            user_id=post.user_id,
            notification_type="comment",
            title="New Comment",
            content=f"{current_user.username} commented on your post",
            link_url=f"/community/posts/{post_id}",
            related_user_id=current_user.id
        )
    
    # Get profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    return CommentResponse(
        id=new_comment.id,
        post_id=new_comment.post_id,
        user_id=new_comment.user_id,
        username=current_user.username,
        full_name=user.full_name if user else None,
        avatar_url=profile.avatar_url if profile else None,
        parent_comment_id=new_comment.parent_comment_id,
        content=new_comment.content,
        likes_count=0,
        is_edited=False,
        edited_at=None,
        created_at=new_comment.created_at,
        is_liked_by_user=False,
        replies_count=0
    )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comments for a post"""
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get top-level comments (no parent)
    comments = db.query(PostComment).options(joinedload(PostComment.user)).filter(
        PostComment.post_id == post_id,
        PostComment.parent_comment_id.is_(None)
    ).order_by(desc(PostComment.created_at)).offset(skip).limit(limit).all()
    
    # Handle empty comments case
    if not comments:
        return []
    
    # Get user likes
    comment_ids = [c.id for c in comments]
    user_likes = db.query(CommentLike.comment_id).filter(
        CommentLike.comment_id.in_(comment_ids),
        CommentLike.user_id == current_user.id
    ).all()
    liked_comment_ids = {like.comment_id for like in user_likes}
    
    # Get reply counts
    reply_counts = db.query(
        PostComment.parent_comment_id,
        func.count(PostComment.id).label("count")
    ).filter(
        PostComment.parent_comment_id.in_(comment_ids)
    ).group_by(PostComment.parent_comment_id).all()
    reply_count_map = {rc.parent_comment_id: rc.count for rc in reply_counts}
    
    # Get profiles
    user_ids = list(set([c.user_id for c in comments]))
    profiles = db.query(UserProfile).filter(UserProfile.user_id.in_(user_ids)).all()
    profile_map = {p.user_id: p for p in profiles}
    
    return [
        CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            username=comment.user.username,
            full_name=comment.user.full_name,
            avatar_url=profile_map[comment.user_id].avatar_url if comment.user_id in profile_map and profile_map[comment.user_id] else None,
            parent_comment_id=comment.parent_comment_id,
            content=comment.content,
            likes_count=comment.likes_count,
            is_edited=comment.is_edited,
            edited_at=comment.edited_at,
            created_at=comment.created_at,
            is_liked_by_user=comment.id in liked_comment_ids,
            replies_count=reply_count_map.get(comment.id, 0)
        )
        for comment in comments
    ]


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comment"""
    comment = db.query(PostComment).filter(PostComment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    # Update post comment count
    post = db.query(CommunityPost).filter(CommunityPost.id == comment.post_id).first()
    if post:
        post.comments_count = max(0, post.comments_count - 1)
    
    db.delete(comment)
    db.commit()


# ==================== Follow Endpoints ====================

@router.post("/users/{user_id}/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow a user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = db.query(UserFollow).filter(
        UserFollow.follower_id == current_user.id,
        UserFollow.following_id == user_id
    ).first()
    
    if existing_follow:
        return {"message": "Already following"}
    
    # Create follow relationship
    new_follow = UserFollow(follower_id=current_user.id, following_id=user_id)
    db.add(new_follow)
    
    # Update profiles
    follower_profile = get_user_profile_or_create(db, current_user.id)
    follower_profile.following_count += 1
    
    following_profile = get_user_profile_or_create(db, user_id)
    following_profile.followers_count += 1
    
    db.commit()
    
    # Create notification
    create_notification(
        db=db,
        user_id=user_id,
        notification_type="follow",
        title="New Follower",
        content=f"{current_user.username} started following you",
        link_url=f"/community/users/{current_user.id}",
        related_user_id=current_user.id
    )
    
    return {"message": "User followed successfully"}


@router.delete("/users/{user_id}/follow", status_code=status.HTTP_200_OK)
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unfollow a user"""
    follow = db.query(UserFollow).filter(
        UserFollow.follower_id == current_user.id,
        UserFollow.following_id == user_id
    ).first()
    
    if not follow:
        return {"message": "Not following"}
    
    db.delete(follow)
    
    # Update profiles
    follower_profile = get_user_profile_or_create(db, current_user.id)
    follower_profile.following_count = max(0, follower_profile.following_count - 1)
    
    following_profile = get_user_profile_or_create(db, user_id)
    following_profile.followers_count = max(0, following_profile.followers_count - 1)
    
    db.commit()
    
    return {"message": "User unfollowed successfully"}


# ==================== Profile Endpoints ====================

@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a user's profile"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = get_user_profile_or_create(db, user_id)
    
    # Check follow relationships
    is_following = db.query(UserFollow).filter(
        UserFollow.follower_id == current_user.id,
        UserFollow.following_id == user_id
    ).first() is not None
    
    is_followed_by = db.query(UserFollow).filter(
        UserFollow.follower_id == user_id,
        UserFollow.following_id == current_user.id
    ).first() is not None
    
    return UserProfileResponse(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        cover_image_url=profile.cover_image_url,
        location=profile.location,
        website=profile.website,
        interests=profile.interests,
        expertise_areas=profile.expertise_areas,
        is_verified=profile.is_verified,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        posts_count=profile.posts_count,
        is_following=is_following,
        is_followed_by=is_followed_by,
        is_own_profile=user_id == current_user.id
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    user = _get_user_from_db(db, current_user.id)
    profile = get_user_profile_or_create(db, current_user.id)
    
    # Update fields
    if profile_data.bio is not None:
        profile.bio = profile_data.bio
    if profile_data.avatar_url is not None:
        profile.avatar_url = profile_data.avatar_url
    if profile_data.cover_image_url is not None:
        profile.cover_image_url = profile_data.cover_image_url
    if profile_data.location is not None:
        profile.location = profile_data.location
    if profile_data.website is not None:
        profile.website = profile_data.website
    if profile_data.interests is not None:
        profile.interests = profile_data.interests
    if profile_data.expertise_areas is not None:
        profile.expertise_areas = profile_data.expertise_areas
    
    db.commit()
    db.refresh(profile)
    
    return UserProfileResponse(
        user_id=current_user.id,
        username=current_user.username,
        full_name=user.full_name if user else None,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        cover_image_url=profile.cover_image_url,
        location=profile.location,
        website=profile.website,
        interests=profile.interests,
        expertise_areas=profile.expertise_areas,
        is_verified=profile.is_verified,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        posts_count=profile.posts_count,
        is_following=False,
        is_followed_by=False,
        is_own_profile=True
    )


# ==================== Events Endpoints ====================

@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a community event"""
    user = _get_user_from_db(db, current_user.id)
    new_event = CommunityEvent(
        created_by=current_user.id,
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        event_date=event_data.event_date,
        duration_minutes=event_data.duration_minutes,
        location=event_data.location,
        max_participants=event_data.max_participants,
        is_public=event_data.is_public,
        tags=event_data.tags,
        cover_image_url=event_data.cover_image_url
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return EventResponse(
        id=new_event.id,
        created_by=new_event.created_by,
        creator_username=current_user.username,
        creator_name=user.full_name if user else None,
        title=new_event.title,
        description=new_event.description,
        event_type=new_event.event_type,
        event_date=new_event.event_date,
        duration_minutes=new_event.duration_minutes,
        location=new_event.location,
        max_participants=new_event.max_participants,
        participants_count=0,
        is_public=new_event.is_public,
        tags=new_event.tags,
        cover_image_url=new_event.cover_image_url,
        status=new_event.status,
        created_at=new_event.created_at,
        is_registered=False,
        is_creator=True
    )


@router.get("/events", response_model=List[EventResponse])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    status: str = Query("upcoming"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get community events"""
    query = db.query(CommunityEvent).options(joinedload(CommunityEvent.creator))
    
    if event_type:
        query = query.filter(CommunityEvent.event_type == event_type)
    
    query = query.filter(CommunityEvent.status == status)
    query = query.filter(CommunityEvent.is_public == True)
    
    events = query.order_by(CommunityEvent.event_date).offset(skip).limit(limit).all()
    
    # Check user registrations
    event_ids = [e.id for e in events]
    registrations = db.query(EventRegistration.event_id).filter(
        EventRegistration.event_id.in_(event_ids),
        EventRegistration.user_id == current_user.id
    ).all()
    registered_event_ids = {r.event_id for r in registrations}
    
    return [
        EventResponse(
            id=event.id,
            created_by=event.created_by,
            creator_username=event.creator.username,
            creator_name=event.creator.full_name,
            title=event.title,
            description=event.description,
            event_type=event.event_type,
            event_date=event.event_date,
            duration_minutes=event.duration_minutes,
            location=event.location,
            max_participants=event.max_participants,
            participants_count=event.participants_count,
            is_public=event.is_public,
            tags=event.tags,
            cover_image_url=event.cover_image_url,
            status=event.status,
            created_at=event.created_at,
            is_registered=event.id in registered_event_ids,
            is_creator=event.created_by == current_user.id
        )
        for event in events
    ]


@router.post("/events/{event_id}/register", status_code=status.HTTP_201_CREATED)
async def register_for_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register for a community event"""
    event = db.query(CommunityEvent).filter(CommunityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already registered
    existing_reg = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.user_id == current_user.id
    ).first()
    
    if existing_reg:
        return {"message": "Already registered"}
    
    # Check capacity
    if event.max_participants and event.participants_count >= event.max_participants:
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Create registration
    new_reg = EventRegistration(event_id=event_id, user_id=current_user.id)
    db.add(new_reg)
    event.participants_count += 1
    db.commit()
    
    return {"message": "Registered successfully"}


# ==================== Notifications Endpoints ====================

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
    
    # Get related usernames
    related_user_ids = [n.related_user_id for n in notifications if n.related_user_id]
    users = db.query(User).filter(User.id.in_(related_user_ids)).all()
    user_map = {u.id: u.username for u in users}
    
    return [
        NotificationResponse(
            id=notif.id,
            notification_type=notif.notification_type,
            title=notif.title,
            content=notif.content,
            link_url=notif.link_url,
            related_user_id=notif.related_user_id,
            related_username=user_map.get(notif.related_user_id) if notif.related_user_id else None,
            is_read=notif.is_read,
            created_at=notif.created_at
        )
        for notif in notifications
    ]


@router.put("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notif.is_read = True
    db.commit()
    
    return {"message": "Marked as read"}


@router.put("/notifications/read-all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    return {"message": "All notifications marked as read"}
