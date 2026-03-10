"""
🧘 Guru Booking API
Endpoints for guru discovery, quiz matching, and appointment booking
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, UTC
from pydantic import BaseModel

from database import get_db
from models.database import Guru, GuruBooking, GuruAvailability, User
from modules.auth import get_current_user

router = APIRouter(prefix="/guru-booking", tags=["Guru Booking"])


# ============= Pydantic Schemas =============

class QuizResponse(BaseModel):
    question_id: int
    answer: str
    
class QuizSubmission(BaseModel):
    responses: List[QuizResponse]

class GuruResponse(BaseModel):
    id: int
    name: str
    title: str
    bio: Optional[str]
    avatar_url: Optional[str]
    specializations: List[str]
    languages: List[str]
    experience_years: int
    rating: int
    total_sessions: int
    price_per_hour: int
    match_score: Optional[int] = None
    
    model_config = {"from_attributes": True}

class TimeSlot(BaseModel):
    time: str
    available: bool

class AvailabilityResponse(BaseModel):
    date: str
    slots: List[TimeSlot]

class BookingCreate(BaseModel):
    guru_id: int
    booking_date: str  # YYYY-MM-DD
    time_slot: str  # "09:00-10:00"
    duration_minutes: int = 60
    session_type: str = "video_call"
    quiz_responses: Optional[List[QuizResponse]] = None
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    guru_id: int
    guru_name: str
    booking_date: datetime
    time_slot: str
    duration_minutes: int
    session_type: str
    status: str
    payment_status: str
    payment_amount: int
    meeting_link: Optional[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}


# ============= Quiz Questions =============

GURU_MATCHING_QUIZ = [
    {
        "id": 1,
        "question": "What is your primary reason for seeking guidance?",
        "options": [
            {"value": "career", "label": "Career and professional growth"},
            {"value": "relationship", "label": "Relationships and marriage"},
            {"value": "health", "label": "Health and well-being"},
            {"value": "spiritual", "label": "Spiritual growth and self-discovery"},
            {"value": "financial", "label": "Financial matters and wealth"}
        ],
        "category": "concern"
    },
    {
        "id": 2,
        "question": "What approach resonates with you most?",
        "options": [
            {"value": "traditional", "label": "Traditional Vedic methods and rituals"},
            {"value": "modern", "label": "Modern psychological insights combined with astrology"},
            {"value": "practical", "label": "Practical solutions and remedies"},
            {"value": "philosophical", "label": "Deep philosophical and spiritual discussions"}
        ],
        "category": "style"
    },
    {
        "id": 3,
        "question": "How detailed do you want your session to be?",
        "options": [
            {"value": "quick", "label": "Quick overview and key insights (30 min)"},
            {"value": "standard", "label": "Balanced session with Q&A (60 min)"},
            {"value": "deep", "label": "In-depth analysis with multiple aspects (90+ min)"}
        ],
        "category": "depth"
    },
    {
        "id": 4,
        "question": "What's your budget preference?",
        "options": [
            {"value": "budget", "label": "Budget-friendly (₹2,000-3,500)"},
            {"value": "mid", "label": "Mid-range (₹3,500-5,000)"},
            {"value": "premium", "label": "Premium expert (₹5,000+)"}
        ],
        "category": "budget"
    },
    {
        "id": 5,
        "question": "Which personality trait in a guru matters most to you?",
        "options": [
            {"value": "empathetic", "label": "Empathetic and understanding"},
            {"value": "analytical", "label": "Analytical and detail-oriented"},
            {"value": "motivational", "label": "Motivational and inspiring"},
            {"value": "calm", "label": "Calm and grounding"}
        ],
        "category": "personality"
    }
]


# ============= Helper Functions =============

def calculate_guru_match_score(guru: Guru, quiz_responses: List[QuizResponse]) -> int:
    """Calculate match score between user quiz responses and guru profile"""
    score = 50  # Base score
    
    responses_dict = {r.question_id: r.answer for r in quiz_responses}
    
    # Question 1: Primary concern
    concern = responses_dict.get(1, "")
    specialization_map = {
        "career": ["Career Guidance", "Professional Growth"],
        "relationship": ["Relationship Counseling", "Marriage Matching"],
        "health": ["Health & Wellness", "Remedial Astrology"],
        "spiritual": ["Spiritual Guidance", "Meditation"],
        "financial": ["Financial Astrology", "Wealth Planning"]
    }
    if concern in specialization_map:
        for spec in specialization_map[concern]:
            if any(spec.lower() in s.lower() for s in guru.specializations):
                score += 15
                break
    
    # Question 2: Style preference
    style = responses_dict.get(2, "")
    if style == "traditional" and guru.experience_years >= 10:
        score += 10
    elif style == "modern" and guru.experience_years < 10:
        score += 10
    
    # Question 4: Budget
    budget = responses_dict.get(4, "")
    if budget == "budget" and guru.price_per_hour <= 3500:
        score += 15
    elif budget == "mid" and 3500 < guru.price_per_hour <= 5000:
        score += 15
    elif budget == "premium" and guru.price_per_hour > 5000:
        score += 15
    
    # Question 5: Personality match
    personality = responses_dict.get(5, "")
    if guru.personality_tags and personality in guru.personality_tags:
        score += 20
    
    # Rating bonus
    score += guru.rating * 2
    
    # Experience bonus
    if guru.experience_years >= 15:
        score += 5
    
    return min(score, 100)


# ============= API Endpoints =============

@router.get("/quiz")
async def get_matching_quiz():
    """Get the guru matching quiz questions"""
    return {"questions": GURU_MATCHING_QUIZ}


@router.post("/match", response_model=List[GuruResponse])
async def match_gurus_from_quiz(
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get guru recommendations based on quiz responses"""
    
    # Get all active gurus
    gurus = db.query(Guru).filter(Guru.is_active == True).all()
    
    # Calculate match scores
    guru_matches = []
    for guru in gurus:
        score = calculate_guru_match_score(guru, submission.responses)
        # Use model_validate + model_dump to work with pydantic v2 config
        guru_model = GuruResponse.model_validate(guru)
        guru_dict = guru_model.model_dump()
        guru_dict['match_score'] = score
        guru_matches.append(guru_dict)
    
    # Sort by match score
    guru_matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return guru_matches[:6]  # Return top 6 matches


@router.get("/gurus", response_model=List[GuruResponse])
async def get_all_gurus(
    specialization: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all available gurus with optional filters"""
    
    query = db.query(Guru).filter(Guru.is_active == True)
    
    if specialization:
        # Filter by specialization (JSON contains)
        query = query.filter(Guru.specializations.contains(specialization))
    
    if min_price:
        query = query.filter(Guru.price_per_hour >= min_price)
    
    if max_price:
        query = query.filter(Guru.price_per_hour <= max_price)
    
    gurus = query.all()
    return gurus


@router.get("/gurus/{guru_id}", response_model=GuruResponse)
async def get_guru_details(guru_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific guru"""
    
    guru = db.query(Guru).filter(Guru.id == guru_id, Guru.is_active == True).first()
    if not guru:
        raise HTTPException(status_code=404, detail="Guru not found")
    
    return guru


@router.get("/gurus/{guru_id}/availability")
async def get_guru_availability(
    guru_id: int,
    date: Optional[str] = None,  # YYYY-MM-DD
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get available time slots for a guru.

    Priority order:
    1. Use persisted rows in guru_availability table for requested range.
    2. If none found for a given day, fall back to guru.availability_schedule (if defined).
    3. As a final fallback, generate generic 09:00-20:00 hourly slots.

    Persisted rows allow granular per–time-slot overrides and booking linkage.
    """

    guru = db.query(Guru).filter(Guru.id == guru_id, Guru.is_active == True).first()
    if not guru:
        raise HTTPException(status_code=404, detail="Guru not found")

    # Parse start date
    start_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()

    availability: List[dict] = []

    # Helper: build slot objects from a list of time-range strings
    def build_slots(slot_ranges: List[str], current_date_str: str) -> List[dict]:
        built = []
        for rng in slot_ranges:
            # rng like "09:00-10:00"
            start_hour = int(rng.split('-')[0].split(':')[0])
            booking_dt = datetime.strptime(f"{current_date_str} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
            existing_booking = db.query(GuruBooking).filter(
                GuruBooking.guru_id == guru_id,
                GuruBooking.booking_date == booking_dt,
                GuruBooking.status.in_( ["pending", "confirmed"] )
            ).first()
            built.append({"time": rng, "available": existing_booking is None})
        return built

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")

        # 1. Load persisted availability rows
        persisted_rows = db.query(GuruAvailability).filter(
            GuruAvailability.guru_id == guru_id,
            GuruAvailability.date == datetime.strptime(date_str, "%Y-%m-%d")
        ).all()

        if persisted_rows:
            slots = []
            for row in persisted_rows:
                # Determine availability from row + booking linkage
                is_available = row.is_available and row.booking_id is None
                slots.append({"time": row.time_slot, "available": is_available})
        else:
            # 2. Fall back to guru.availability_schedule for that weekday name
            weekday_key = current_date.strftime("%A").lower()  # e.g. monday
            schedule = []
            if guru.availability_schedule and weekday_key in guru.availability_schedule:
                schedule = guru.availability_schedule[weekday_key]
            # 3. Final fallback generic hourly schedule if still empty
            if not schedule:
                schedule = [f"{h:02d}:00-{h+1:02d}:00" for h in range(9, 21)]
            slots = build_slots(schedule, date_str)

        availability.append({
            "date": date_str,
            "day": current_date.strftime("%A"),
            "slots": slots
        })

    return {"availability": availability}


class AvailabilityCreate(BaseModel):
    date: str  # YYYY-MM-DD
    slots: List[str]  # ["09:00-10:00", "10:00-11:00"]
    overwrite: bool = False

@router.post("/gurus/{guru_id}/availability")
async def set_guru_availability(
    guru_id: int,
    payload: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Persist availability time-slots for a guru.

    Security: currently any authenticated user can set; in production restrict to guru/admin.
    If overwrite=True existing rows for that date are deleted first.
    """
    # Temporary security: restrict to admin until guru ownership is modeled
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Only admins can set availability right now")

    guru = db.query(Guru).filter(Guru.id == guru_id, Guru.is_active == True).first()
    if not guru:
        raise HTTPException(status_code=404, detail="Guru not found")

    target_date = datetime.strptime(payload.date, "%Y-%m-%d")

    if payload.overwrite:
        db.query(GuruAvailability).filter(
            GuruAvailability.guru_id == guru_id,
            GuruAvailability.date == target_date
        ).delete()
        db.commit()

    created = []
    for slot in payload.slots:
        existing = db.query(GuruAvailability).filter(
            GuruAvailability.guru_id == guru_id,
            GuruAvailability.date == target_date,
            GuruAvailability.time_slot == slot
        ).first()
        if existing:
            continue
        row = GuruAvailability(
            guru_id=guru_id,
            date=target_date,
            time_slot=slot,
            is_available=True
        )
        db.add(row)
        created.append(slot)

    db.commit()
    return {"message": "Availability updated", "date": payload.date, "created_slots": created}


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new guru booking"""
    
    # Verify guru exists
    guru = db.query(Guru).filter(Guru.id == booking_data.guru_id, Guru.is_active == True).first()
    if not guru:
        raise HTTPException(status_code=404, detail="Guru not found")
    
    # Parse booking datetime
    booking_datetime = datetime.strptime(
        f"{booking_data.booking_date} {booking_data.time_slot.split('-')[0]}", 
        "%Y-%m-%d %H:%M"
    )
    
    # Check if slot is available
    existing_booking = db.query(GuruBooking).filter(
        GuruBooking.guru_id == booking_data.guru_id,
        GuruBooking.booking_date == booking_datetime,
        GuruBooking.status.in_(["pending", "confirmed"])
    ).first()
    
    if existing_booking:
        raise HTTPException(status_code=400, detail="Time slot already booked")
    
    # Calculate payment amount
    price_per_minute = guru.price_per_hour / 60
    payment_amount = int(price_per_minute * booking_data.duration_minutes)
    
    # Extract concern category from quiz responses
    concern_category = None
    if booking_data.quiz_responses:
        for response in booking_data.quiz_responses:
            if response.question_id == 1:  # First question is about primary concern
                concern_category = response.answer
                break
    
    # If an availability row exists for this date/slot and is available, mark it as booked
    # Match persisted availability by date (date-only) and time slot
    target_date_only = datetime.strptime(booking_data.booking_date, "%Y-%m-%d")
    availability_row = db.query(GuruAvailability).filter(
        GuruAvailability.guru_id == booking_data.guru_id,
        GuruAvailability.date == target_date_only,
        GuruAvailability.time_slot == booking_data.time_slot
    ).first()
    if availability_row and (not availability_row.is_available or availability_row.booking_id is not None):
        raise HTTPException(status_code=400, detail="Time slot unavailable (persisted)")

    # Create booking
    new_booking = GuruBooking(
        user_id=current_user.id,
        guru_id=booking_data.guru_id,
        booking_date=booking_datetime,
        time_slot=booking_data.time_slot,
        duration_minutes=booking_data.duration_minutes,
        session_type=booking_data.session_type,
        concern_category=concern_category,
    quiz_responses=[r.model_dump() for r in booking_data.quiz_responses] if booking_data.quiz_responses else None,
        payment_amount=payment_amount,
        notes=booking_data.notes
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # Link availability row -> booking
    if availability_row:
        availability_row.is_available = False
        availability_row.booking_id = new_booking.id
        db.commit()
    
    # Update guru total sessions
    guru.total_sessions += 1
    db.commit()
    
    # Create response
    response = {
        "id": new_booking.id,
        "guru_id": guru.id,
        "guru_name": guru.name,
        "booking_date": new_booking.booking_date,
        "time_slot": new_booking.time_slot,
        "duration_minutes": new_booking.duration_minutes,
        "session_type": new_booking.session_type,
        "status": new_booking.status,
        "payment_status": new_booking.payment_status,
        "payment_amount": new_booking.payment_amount,
        "meeting_link": new_booking.meeting_link,
        "created_at": new_booking.created_at
    }
    
    return response


@router.get("/bookings", response_model=List[BookingResponse])
async def get_user_bookings(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all bookings for current user"""
    
    query = db.query(GuruBooking).filter(GuruBooking.user_id == current_user.id)
    
    if status:
        query = query.filter(GuruBooking.status == status)
    
    bookings = query.order_by(GuruBooking.booking_date.desc()).all()
    
    # Format response with guru details
    response = []
    for booking in bookings:
        guru = db.query(Guru).filter(Guru.id == booking.guru_id).first()
        response.append({
            "id": booking.id,
            "guru_id": booking.guru_id,
            "guru_name": guru.name if guru else "Unknown",
            "booking_date": booking.booking_date,
            "time_slot": booking.time_slot,
            "duration_minutes": booking.duration_minutes,
            "session_type": booking.session_type,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "payment_amount": booking.payment_amount,
            "meeting_link": booking.meeting_link,
            "created_at": booking.created_at
        })
    
    return response


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking_details(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific booking"""
    
    booking = db.query(GuruBooking).filter(
        GuruBooking.id == booking_id,
        GuruBooking.user_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    guru = db.query(Guru).filter(Guru.id == booking.guru_id).first()
    
    return {
        "id": booking.id,
        "guru_id": booking.guru_id,
        "guru_name": guru.name if guru else "Unknown",
        "booking_date": booking.booking_date,
        "time_slot": booking.time_slot,
        "duration_minutes": booking.duration_minutes,
        "session_type": booking.session_type,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "payment_amount": booking.payment_amount,
        "meeting_link": booking.meeting_link,
        "created_at": booking.created_at
    }


@router.patch("/bookings/{booking_id}/refresh-meeting-link", response_model=BookingResponse)
async def refresh_meeting_link(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate meeting link for a booking (if compromised or invalid).
    
    Only booking owner or admin can refresh. Booking must be confirmed/paid.
    """
    booking = db.query(GuruBooking).filter(GuruBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Authorization: owner or admin
    is_admin = getattr(current_user, "is_admin", False)
    if booking.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Only allow for paid bookings
    if booking.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Cannot refresh link for unpaid booking")
    
    # Import meeting link generator (avoid circular import)
    import secrets
    token = secrets.token_urlsafe(16)
    booking.meeting_link = f"https://meet.yatinveda.com/session/{booking.id}-{booking.guru_id}?t={token}"
    booking.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(booking)
    
    guru = db.query(Guru).filter(Guru.id == booking.guru_id).first()
    return {
        "id": booking.id,
        "guru_id": booking.guru_id,
        "guru_name": guru.name if guru else "Unknown",
        "booking_date": booking.booking_date,
        "time_slot": booking.time_slot,
        "duration_minutes": booking.duration_minutes,
        "session_type": booking.session_type,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "payment_amount": booking.payment_amount,
        "meeting_link": booking.meeting_link,
        "created_at": booking.created_at
    }


@router.get("/bookings/{booking_id}/video-session")
async def get_video_session(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get joinable video session details for a booking.

    If no meeting link exists and booking is paid/confirmed, generate one.
    """
    booking = db.query(GuruBooking).filter(GuruBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_admin = getattr(current_user, "is_admin", False)
    if booking.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    if booking.status not in ["confirmed", "completed"] and booking.payment_status not in ["paid", "completed"]:
        raise HTTPException(status_code=400, detail="Video session is available only for paid/confirmed bookings")

    if not booking.meeting_link:
        import secrets

        token = secrets.token_urlsafe(16)
        booking.meeting_link = f"https://meet.yatinveda.com/session/{booking.id}-{booking.guru_id}?t={token}"
        booking.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(booking)

    scheduled_start_utc = None
    scheduled_end_utc = None
    join_window_opens_utc = None
    join_window_closes_utc = None
    lifecycle_state = "join_window_open"
    can_join = True
    join_hint = "You can join this session now."

    try:
        slot_start = booking.time_slot.split("-")[0].strip()
        # booking.booking_date is persisted as datetime; this keeps the date stable.
        start_naive = datetime.fromisoformat(f"{booking.booking_date.date().isoformat()}T{slot_start}:00")
        start_utc = start_naive.replace(tzinfo=UTC)
        end_utc = start_utc + timedelta(minutes=booking.duration_minutes)
        opens_utc = start_utc - timedelta(minutes=15)
        closes_utc = end_utc + timedelta(minutes=30)

        now_utc = datetime.now(UTC)
        if now_utc < opens_utc:
            lifecycle_state = "scheduled"
            can_join = False
            join_hint = "Session not yet open. Join window starts 15 minutes before session time."
        elif now_utc > closes_utc:
            lifecycle_state = "expired"
            can_join = False
            join_hint = "Join window has ended. Refresh link if extension is allowed."

        scheduled_start_utc = start_utc.isoformat()
        scheduled_end_utc = end_utc.isoformat()
        join_window_opens_utc = opens_utc.isoformat()
        join_window_closes_utc = closes_utc.isoformat()
    except Exception:
        # If date/time parsing fails, keep endpoint usable with a permissive fallback.
        lifecycle_state = "join_window_open"
        can_join = True
        join_hint = "Session timing unavailable; join link is currently active."

    return {
        "booking_id": booking.id,
        "meeting_link": booking.meeting_link,
        "session_type": booking.session_type,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "scheduled_start_utc": scheduled_start_utc,
        "scheduled_end_utc": scheduled_end_utc,
        "join_window_opens_utc": join_window_opens_utc,
        "join_window_closes_utc": join_window_closes_utc,
        "lifecycle_state": lifecycle_state,
        "can_join": can_join,
        "join_hint": join_hint,
    }

@router.patch("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a booking"""
    
    booking = db.query(GuruBooking).filter(
        GuruBooking.id == booking_id,
        GuruBooking.user_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.status not in ["pending", "confirmed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel this booking")
    
    booking.status = "cancelled"
    # Release persisted availability slot if exists and in future
    availability_row = db.query(GuruAvailability).filter(
        GuruAvailability.booking_id == booking_id
    ).first()
    # availability_row.date is stored as a naive datetime (no timezone), so we
    # compare it against a naive "now" value to avoid offset-naive vs
    # offset-aware TypeError while still keeping our own code free of
    # datetime.utcnow() usage.
    if availability_row and availability_row.date > datetime.now():
        availability_row.is_available = True
        availability_row.booking_id = None
    db.commit()
    
    return {"message": "Booking cancelled successfully"}

# === Payment integration endpoints reside in payments.py router ===

class RescheduleRequest(BaseModel):
    new_date: str  # YYYY-MM-DD
    new_time_slot: str  # HH:MM-HH:MM

@router.patch("/bookings/{booking_id}/reschedule", response_model=BookingResponse)
async def reschedule_booking(
    booking_id: int,
    payload: RescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reschedule a booking to a new date/time if slot free. Preserves payment; guru may need manual confirmation.
    Rules:
    - Only pending or confirmed bookings can be rescheduled.
    - Cannot reschedule past bookings.
    - Availability row adjustments handled.
    """
    booking = db.query(GuruBooking).filter(
        GuruBooking.id == booking_id,
        GuruBooking.user_id == current_user.id
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in ["pending", "confirmed"]:
        raise HTTPException(status_code=400, detail="Cannot reschedule this booking")
    # booking.booking_date is stored as naive datetime; compare to naive now()
    # to avoid TypeError while still avoiding datetime.utcnow().
    if booking.booking_date < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot reschedule past booking")

    new_dt = datetime.strptime(f"{payload.new_date} {payload.new_time_slot.split('-')[0]}", "%Y-%m-%d %H:%M")

    # Check slot free among bookings
    slot_conflict = db.query(GuruBooking).filter(
        GuruBooking.guru_id == booking.guru_id,
        GuruBooking.booking_date == new_dt,
        GuruBooking.status.in_(["pending", "confirmed"])
    ).first()
    if slot_conflict:
        raise HTTPException(status_code=400, detail="New time slot already booked")

    # Handle availability rows
    new_date_only = datetime.strptime(payload.new_date, "%Y-%m-%d")
    new_av_row = db.query(GuruAvailability).filter(
        GuruAvailability.guru_id == booking.guru_id,
        GuruAvailability.date == new_date_only,
        GuruAvailability.time_slot == payload.new_time_slot
    ).first()
    if new_av_row and (not new_av_row.is_available or new_av_row.booking_id is not None):
        raise HTTPException(status_code=400, detail="New slot unavailable (persisted)")

    # Release old row
    old_av_row = db.query(GuruAvailability).filter(GuruAvailability.booking_id == booking.id).first()
    if old_av_row:
        old_av_row.is_available = True
        old_av_row.booking_id = None

    # Update booking
    booking.booking_date = new_dt
    booking.time_slot = payload.new_time_slot
    booking.updated_at = datetime.now(UTC)
    booking.status = "pending" if booking.payment_status != "paid" else "confirmed"
    db.commit()

    # Attach new row
    if new_av_row:
        new_av_row.is_available = False
        new_av_row.booking_id = booking.id
        db.commit()

    guru = db.query(Guru).filter(Guru.id == booking.guru_id).first()
    return {
        "id": booking.id,
        "guru_id": booking.guru_id,
        "guru_name": guru.name if guru else "Unknown",
        "booking_date": booking.booking_date,
        "time_slot": booking.time_slot,
        "duration_minutes": booking.duration_minutes,
        "session_type": booking.session_type,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "payment_amount": booking.payment_amount,
        "meeting_link": booking.meeting_link,
        "created_at": booking.created_at
    }
