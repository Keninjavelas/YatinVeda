"""
👨‍⚕️ Practitioner Portal API
Endpoints for practitioners/gurus to manage their professional business:
- Profile management
- Availability scheduling
- Booking management
- Analytics (earnings, reviews, sessions)
- Client relationship management
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from database import get_db
from models.database import User, Guru, GuruBooking, GuruAvailability, Payment, Notification
from modules.auth import get_current_user
from modules.entitlements import require_feature

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/practitioner", tags=["Practitioner Portal"])


# ====== PYDANTIC MODELS ======

class PractitionerProfileResponse(BaseModel):
    """Practitioner's own profile information"""
    guru_id: int
    user_id: int
    professional_title: Optional[str] = None
    bio: Optional[str] = None
    specializations: List[str]
    experience_years: int
    languages: List[str]
    price_per_hour: float
    verification_status: str
    verification_tier: str = "standard"
    rating: Optional[float] = None
    
    class Config:
        from_attributes = True


class BookingResponse(BaseModel):
    """Booking details for practitioner"""
    id: int
    client_name: str
    client_email: str
    booking_date: str
    time_slot: str
    duration_minutes: int
    session_type: str
    status: str
    payment_status: str
    payment_amount: float
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class BookingAction(BaseModel):
    """Action on a booking (accept/decline/reschedule)"""
    action: str = Field(..., description="accept, decline, or reschedule")
    notes: Optional[str] = Field(None, description="Optional notes/feedback")
    new_date: Optional[str] = Field(None, description="For reschedule: new date (YYYY-MM-DD)")
    new_time: Optional[str] = Field(None, description="For reschedule: new time (HH:MM)")


class AvailabilitySlot(BaseModel):
    """Single availability slot"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    is_available: bool = Field(default=True, description="True if available, False for blocked")


class BulkAvailabilityRequest(BaseModel):
    """Bulk availability update request"""
    slots: List[AvailabilitySlot]
    clear_existing: bool = Field(default=False, description="Clear existing slots first")


class EarningsResponse(BaseModel):
    """Earnings analytics for practitioner"""
    total_earnings: float
    earnings_this_month: float
    earnings_this_year: float
    pending_amount: float
    completed_sessions: int
    average_session_value: float
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Review details"""
    id: int
    client_name: str
    rating: int
    review_text: str
    created_at: str
    
    class Config:
        from_attributes = True


class ReviewsAnalyticsResponse(BaseModel):
    """Reviews analytics for practitioner"""
    average_rating: float
    total_reviews: int
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int
    recent_reviews: List[ReviewResponse]


class ClientResponse(BaseModel):
    """Client information"""
    user_id: int
    name: str
    email: str
    total_bookings: int
    total_spent: float
    last_booking_date: Optional[str] = None
    
    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Notification for practitioner"""
    id: int
    type: str
    title: str
    message: str
    read: bool
    created_at: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# ====== ENDPOINTS ======

@router.get("/profile", response_model=PractitionerProfileResponse)
async def get_practitioner_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current practitioner's own profile"""
    
    # Verify user is a practitioner
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    # Get guru profile
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner profile not found"
        )
    
    user = db.query(User).filter(User.id == guru.user_id).first()
    return PractitionerProfileResponse(
        guru_id=guru.id,
        user_id=guru.user_id,
        professional_title=guru.title,
        bio=guru.bio,
        specializations=guru.specializations or [],
        experience_years=guru.experience_years or 0,
        languages=guru.languages or [],
        price_per_hour=float(guru.price_per_hour or 0),
        verification_status=(user.verification_status if user else "pending_verification"),
        verification_tier="standard",
        rating=float(guru.rating or 0),
    )


@router.patch("/profile", response_model=PractitionerProfileResponse)
async def update_practitioner_profile(
    profile_update: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update practitioner's own profile"""
    
    # Verify user is a practitioner
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    # Get guru profile
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner profile not found"
        )
    
    # Update fields
    mapping = {
        "professional_title": "title",
        "bio": "bio",
        "specializations": "specializations",
        "experience_years": "experience_years",
        "languages": "languages",
        "price_per_hour": "price_per_hour",
    }

    for field, value in profile_update.items():
        if field in mapping and value is not None:
            setattr(guru, mapping[field], value)

    db.commit()
    db.refresh(guru)
    
    logger.info(f"Practitioner profile updated: guru_id={guru.id}")
    
    user = db.query(User).filter(User.id == guru.user_id).first()
    return PractitionerProfileResponse(
        guru_id=guru.id,
        user_id=guru.user_id,
        professional_title=guru.title,
        bio=guru.bio,
        specializations=guru.specializations or [],
        experience_years=guru.experience_years or 0,
        languages=guru.languages or [],
        price_per_hour=float(guru.price_per_hour or 0),
        verification_status=(user.verification_status if user else "pending_verification"),
        verification_tier="standard",
        rating=float(guru.rating or 0),
    )


@router.get("/bookings", response_model=List[BookingResponse])
async def get_practitioner_bookings(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, confirmed, completed, cancelled"),
    period: Optional[str] = Query("upcoming", description="upcoming, past, or all"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get practitioner's bookings"""
    
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    # Get practitioner's guru record
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner profile not found"
        )
    
    # Build query
    query = db.query(GuruBooking).filter(GuruBooking.guru_id == guru.id)
    
    # Filter by status if provided
    if status_filter:
        query = query.filter(GuruBooking.status == status_filter)
    
    # Filter by period
    now = datetime.utcnow()
    if period == "upcoming":
        query = query.filter(GuruBooking.booking_date >= now)
    elif period == "past":
        query = query.filter(GuruBooking.booking_date < now)
    
    bookings = query.order_by(desc(GuruBooking.booking_date)).all()
    
    # Convert to response format
    result = []
    for booking in bookings:
        client = db.query(User).filter(User.id == booking.user_id).first()
        payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
        
        result.append(BookingResponse(
            id=booking.id,
            client_name=client.full_name if client else "Unknown",
            client_email=client.email if client else "Unknown",
            booking_date=booking.booking_date.isoformat(),
            time_slot=booking.time_slot,
            duration_minutes=booking.duration_minutes,
            session_type=booking.session_type or "consultation",
            status=booking.status,
            payment_status=booking.payment_status or (payment.status if payment else "pending"),
            payment_amount=(booking.payment_amount / 100) if booking.payment_amount else (payment.amount / 100 if payment else 0),
            meeting_link=booking.meeting_link,
            notes=booking.notes,
            created_at=booking.created_at.isoformat()
        ))
    
    return result


@router.patch("/bookings/{booking_id}", response_model=Dict[str, str])
async def update_booking(
    booking_id: int,
    action: BookingAction,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manage booking (accept/decline/reschedule)"""
    
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    # Get booking
    booking = db.query(GuruBooking).filter(GuruBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Verify practitioner owns this booking
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if booking.guru_id != guru.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this booking"
        )
    
    # Process action
    if action.action == "accept":
        booking.status = "confirmed"
        message = "Booking accepted"
    elif action.action == "decline":
        booking.status = "cancelled"
        # Optionally initiate refund
        message = "Booking declined"
    elif action.action == "reschedule":
        if not action.new_date or not action.new_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new_date and new_time required for reschedule"
            )
        booking.booking_date = datetime.fromisoformat(f"{action.new_date}T{action.new_time}")
        booking.time_slot = action.new_time
        booking.status = "confirmed"
        message = "Booking rescheduled"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be accept, decline, or reschedule"
        )
    
    if action.notes:
        booking.notes = action.notes
    
    db.commit()
    logger.info(f"Booking {booking_id} {action.action}: guru_id={guru.id}")
    
    return {"message": message, "status": booking.status}


@router.get("/analytics/earnings", response_model=EarningsResponse)
async def get_earnings_analytics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get earnings analytics for practitioner"""
    
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner profile not found"
        )
    
    now = datetime.utcnow()
    month_start = now.replace(day=1)
    year_start = now.replace(month=1, day=1)
    
    # Get payments for this practitioner
    all_payments = db.query(Payment).join(
        GuruBooking, Payment.booking_id == GuruBooking.id
    ).filter(GuruBooking.guru_id == guru.id).all()
    
    # Calculate totals
    total_earnings = sum(p.amount for p in all_payments if p.status == "completed") / 100
    earnings_this_month = sum(
        p.amount for p in all_payments 
        if p.status == "completed" and p.created_at >= month_start
    ) / 100
    earnings_this_year = sum(
        p.amount for p in all_payments 
        if p.status == "completed" and p.created_at >= year_start
    ) / 100
    pending_amount = sum(p.amount for p in all_payments if p.status == "pending") / 100
    
    # Count completed sessions
    completed_bookings = db.query(GuruBooking).filter(
        and_(GuruBooking.guru_id == guru.id, GuruBooking.status == "completed")
    ).count()
    
    avg_session_value = total_earnings / completed_bookings if completed_bookings > 0 else 0
    
    return EarningsResponse(
        total_earnings=round(total_earnings, 2),
        earnings_this_month=round(earnings_this_month, 2),
        earnings_this_year=round(earnings_this_year, 2),
        pending_amount=round(pending_amount, 2),
        completed_sessions=completed_bookings,
        average_session_value=round(avg_session_value, 2)
    )


@router.get("/analytics/reviews", response_model=ReviewsAnalyticsResponse)
async def get_reviews_analytics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reviews and ratings analytics"""
    
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner profile not found"
        )
    
    # The current schema does not persist per-booking text reviews.
    # We expose aggregate rating from Guru and keep review list empty.
    avg_rating = float(guru.rating or 0)
    recent_reviews: List[ReviewResponse] = []
    count = guru.total_sessions or 0
    
    return ReviewsAnalyticsResponse(
        average_rating=round(avg_rating, 2),
        total_reviews=count,
        five_star_count=0,
        four_star_count=0,
        three_star_count=0,
        two_star_count=0,
        one_star_count=0,
        recent_reviews=recent_reviews
    )


@router.post("/availability/bulk", response_model=Dict[str, str])
async def bulk_set_availability(
    availability_request: BulkAvailabilityRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk update availability slots"""
    
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner profile not found"
        )
    
    # Clear existing if requested
    if availability_request.clear_existing:
        db.query(GuruAvailability).filter(GuruAvailability.guru_id == guru.id).delete()
    
    # Add new availability slots
    count = 0
    for slot in availability_request.slots:
        try:
            slot_date = datetime.fromisoformat(f"{slot.date}T{slot.start_time}")
            
            # Check if slot already exists
            existing = db.query(GuruAvailability).filter(
                and_(
                    GuruAvailability.guru_id == guru.id,
                    GuruAvailability.date == slot_date,
                    GuruAvailability.time_slot == slot.start_time
                )
            ).first()
            
            if not existing:
                new_slot = GuruAvailability(
                    guru_id=guru.id,
                    date=slot_date,
                    time_slot=slot.start_time,
                    is_available=slot.is_available
                )
                db.add(new_slot)
                count += 1
        except ValueError:
            continue
    
    db.commit()
    logger.info(f"Updated {count} availability slots for guru_id={guru.id}")
    
    return {"message": f"Updated {count} availability slots"}


@router.get("/clients", response_model=List[ClientResponse])
async def get_clients(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _entitlements: dict = Depends(require_feature("team_management")),
):
    """Get list of all clients who have booked with this practitioner"""
    
    if current_user.get("role") != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practitioners can access this endpoint"
        )
    
    guru = db.query(Guru).filter(Guru.user_id == current_user["user_id"]).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner profile not found"
        )
    
    # Get unique clients
    bookings = db.query(GuruBooking).filter(GuruBooking.guru_id == guru.id).all()
    
    clients_dict = {}
    for booking in bookings:
        user = db.query(User).filter(User.id == booking.user_id).first()
        if user and user.id not in clients_dict:
            clients_dict[user.id] = {
                "user": user,
                "total_bookings": 0,
                "total_spent": 0,
                "last_booking": None
            }
        
        if user:
            clients_dict[user.id]["total_bookings"] += 1
            if booking.status == "completed" or booking.status == "confirmed":
                payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
                if payment:
                    clients_dict[user.id]["total_spent"] += payment.amount / 100
            
            if not clients_dict[user.id]["last_booking"] or booking.booking_date > clients_dict[user.id]["last_booking"]:
                clients_dict[user.id]["last_booking"] = booking.booking_date
    
    # Convert to response
    result = []
    for user_id, data in clients_dict.items():
        user = data["user"]
        result.append(ClientResponse(
            user_id=user.id,
            name=user.full_name,
            email=user.email,
            total_bookings=data["total_bookings"],
            total_spent=round(data["total_spent"], 2),
            last_booking_date=data["last_booking"].isoformat() if data["last_booking"] else None
        ))
    
    return sorted(result, key=lambda x: x.last_booking_date or "", reverse=True)


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Get only unread notifications"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get practitioner's notifications"""
    
    query = db.query(Notification).filter(Notification.user_id == current_user["user_id"])
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(desc(Notification.created_at)).limit(50).all()
    
    return [
        NotificationResponse(
            id=n.id,
            type=n.notification_type,
            title=n.notification_type.replace("_", " ").title(),
            message=n.content,
            read=n.is_read,
            created_at=n.created_at.isoformat(),
            data={"link": n.link} if n.link else None
        )
        for n in notifications
    ]


__all__ = ["router"]
