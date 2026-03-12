"""
📋 Prescription & Remedy API
Manage remedy prescriptions with digital signatures and follow-up reminders
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from database import get_db
from models.database import (
    User, Guru, GuruBooking, Prescription, PrescriptionReminder
)
from modules.auth import get_current_user
from modules.prescription_generator import PrescriptionGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class RemedyItem(BaseModel):
    """Individual remedy item"""
    category: str = Field(..., description="Remedy category (lal_kitab, gemstones, etc.)")
    description: str = Field(..., description="Remedy description")
    duration: Optional[str] = Field(None, description="Duration (e.g., '21 days', '3 months')")
    frequency: Optional[str] = Field(None, description="Frequency (e.g., 'Daily', 'Every Tuesday')")
    product_url: Optional[str] = Field(None, description="Link to purchase remedy products")


class CreatePrescriptionRequest(BaseModel):
    """Request to create a new prescription"""
    booking_id: int = Field(..., description="Guru booking ID")
    title: str = Field(..., max_length=200, description="Prescription title")
    diagnosis: Optional[str] = Field(None, description="Astrological analysis/diagnosis")
    remedies: List[RemedyItem] = Field(..., min_length=1, description="List of remedies")
    follow_up_date: Optional[str] = Field(None, description="Follow-up date (YYYY-MM-DD)")
    notes: Optional[str] = Field(None, description="Additional instructions")


class UpdatePrescriptionRequest(BaseModel):
    """Request to update a prescription"""
    title: Optional[str] = Field(None, max_length=200)
    diagnosis: Optional[str] = None
    remedies: Optional[List[RemedyItem]] = None
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CreateReminderRequest(BaseModel):
    """Request to create a prescription reminder"""
    prescription_id: int
    reminder_type: str = Field(..., description="Type: remedy_completion, follow_up, custom")
    reminder_text: str = Field(..., max_length=500)
    scheduled_at: str = Field(..., description="Reminder datetime (YYYY-MM-DD HH:MM)")


# ============================================================================
# Prescription Management Endpoints
# ============================================================================

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_prescription(
    request: CreatePrescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new prescription for a consultation
    
    - **Guru-only**: Only consultants can create prescriptions
    - Validates booking exists and consultation is completed
    - Generates PDF with remedies and QR code
    - Creates verification code for authenticity
    """
    # Verify user is a guru
    guru = db.query(Guru).filter(Guru.user_id == current_user.id).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consultants can create prescriptions"
        )
    
    # Verify booking exists and belongs to this guru
    booking = db.query(GuruBooking).filter(
        GuruBooking.id == request.booking_id,
        GuruBooking.guru_id == guru.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or not authorized"
        )
    
    # Check if booking is completed
    if booking.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only create prescriptions for completed consultations"
        )
    
    # Get patient information
    patient = db.query(User).filter(User.id == booking.user_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Initialize prescription generator
    generator = PrescriptionGenerator()
    
    # Generate verification code
    prescription_data = {
        "user_id": patient.id,
        "guru_id": guru.id,
        "booking_id": booking.id
    }
    verification_code = generator.generate_verification_code(prescription_data)
    
    # Create prescription record
    new_prescription = Prescription(
        booking_id=request.booking_id,
        guru_id=guru.id,
        user_id=patient.id,
        title=request.title,
        diagnosis=request.diagnosis,
        remedies=json.dumps([remedy.model_dump() for remedy in request.remedies]),
        follow_up_date=request.follow_up_date,
        notes=request.notes,
        verification_code=verification_code,
        is_active=True
    )
    
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)
    
    # Generate PDF
    try:
        # Get patient birth details from primary chart
        from models.database import Chart
        primary_chart = db.query(Chart).filter(
            Chart.user_id == patient.id,
            Chart.is_primary == True
        ).first()
        
        if primary_chart and primary_chart.birth_details:
            birth_date = primary_chart.birth_details.get("date", "N/A")
            birth_place = primary_chart.birth_details.get("place", "N/A")
        else:
            # Fallback to first chart if no primary chart set
            fallback_chart = db.query(Chart).filter(Chart.user_id == patient.id).first()
            if fallback_chart and fallback_chart.birth_details:
                birth_date = fallback_chart.birth_details.get("date", "N/A")
                birth_place = fallback_chart.birth_details.get("place", "N/A")
            else:
                birth_date = "N/A"
                birth_place = "N/A"
        
        patient_data = {
            "name": patient.full_name or patient.email.split('@')[0],
            "birth_date": birth_date,
            "birth_place": birth_place
        }
        
        guru_user = db.query(User).filter(User.id == guru.user_id).first()
        guru_data = {
            "name": guru.name,
            "specialization": (guru.specializations[0] if guru.specializations else "Vedic Astrology") if guru else "Vedic Astrology",
            "email": guru_user.email if guru_user else "N/A"
        }
        
        prescription_info = {
            "id": new_prescription.id,
            "title": new_prescription.title,
            "diagnosis": new_prescription.diagnosis,
            "notes": new_prescription.notes,
            "follow_up_date": new_prescription.follow_up_date,
            "verification_code": new_prescription.verification_code
        }
        
        pdf_bytes = generator.generate_prescription_pdf(
            prescription_data=prescription_info,
            user_data=patient_data,
            guru_data=guru_data,
            remedies=[remedy.model_dump() for remedy in request.remedies]
        )
        
        # Save PDF to file system
        prescriptions_dir = Path("backend/generated_prescriptions")
        prescriptions_dir.mkdir(exist_ok=True)
        
        pdf_filename = f"prescription_{new_prescription.id}_{verification_code}.pdf"
        pdf_path = prescriptions_dir / pdf_filename
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Update prescription with PDF URL
        new_prescription.pdf_url = f"/prescriptions/download/{pdf_filename}"
        db.commit()
        
        # Generate QR code
        verification_url = f"https://yatinveda.com/verify/{verification_code}"
        qr_buffer = generator.generate_qr_code(verification_url)
        
        qr_filename = f"qr_{new_prescription.id}_{verification_code}.png"
        qr_path = prescriptions_dir / qr_filename
        
        with open(qr_path, "wb") as f:
            f.write(qr_buffer.getvalue())
        
        new_prescription.qr_code_url = f"/prescriptions/qr/{qr_filename}"
        db.commit()
        
    except Exception as e:
        logger.error(f"Error generating prescription PDF: {e}", exc_info=True)
        # Continue anyway - prescription is created, PDF can be regenerated
    
    # Auto-create follow-up reminder if date is set
    if request.follow_up_date:
        try:
            follow_up_datetime = datetime.strptime(request.follow_up_date, "%Y-%m-%d")
            reminder_date = follow_up_datetime - timedelta(days=1)  # Remind 1 day before
            
            reminder = PrescriptionReminder(
                prescription_id=new_prescription.id,
                reminder_type="follow_up",
                reminder_text=f"Follow-up consultation scheduled for {request.follow_up_date}",
                scheduled_at=reminder_date,
                status="pending"
            )
            db.add(reminder)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not create follow-up reminder: {e}")
    
    return {
        "message": "Prescription created successfully",
        "prescription_id": new_prescription.id,
        "verification_code": verification_code,
        "pdf_url": new_prescription.pdf_url,
        "qr_code_url": new_prescription.qr_code_url
    }


@router.get("/{prescription_id}")
async def get_prescription(
    prescription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get prescription details
    
    - Accessible by prescription owner (patient) or creator (guru)
    - Returns complete prescription with remedies
    """
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id
    ).first()
    
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Check authorization (patient or guru)
    guru = db.query(Guru).filter(Guru.user_id == current_user.id).first()
    is_authorized = (
        prescription.user_id == current_user.id or
        (guru and prescription.guru_id == guru.id)
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this prescription"
        )
    
    # Get guru details
    guru_obj = db.query(Guru).filter(Guru.id == prescription.guru_id).first()
    
    remedies = json.loads(prescription.remedies) if prescription.remedies else []
    
    return {
        "id": prescription.id,
        "booking_id": prescription.booking_id,
        "title": prescription.title,
        "diagnosis": prescription.diagnosis,
        "remedies": remedies,
        "follow_up_date": prescription.follow_up_date,
        "notes": prescription.notes,
        "pdf_url": prescription.pdf_url,
        "qr_code_url": prescription.qr_code_url,
        "verification_code": prescription.verification_code,
        "is_active": prescription.is_active,
        "created_at": prescription.created_at,
        "guru": {
            "name": guru_obj.name if guru_obj else "N/A",
            "specialization": (guru_obj.specializations[0] if guru_obj.specializations else None) if guru_obj else None
        }
    }


@router.get("/user/my-prescriptions")
async def get_my_prescriptions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's prescriptions
    
    - Returns all prescriptions for the current user
    - Sorted by creation date (newest first)
    """
    prescriptions = db.query(Prescription).filter(
        Prescription.user_id == current_user.id,
        Prescription.is_active == True
    ).order_by(Prescription.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for prescription in prescriptions:
        guru = db.query(Guru).filter(Guru.id == prescription.guru_id).first()
        
        result.append({
            "id": prescription.id,
            "title": prescription.title,
            "diagnosis": prescription.diagnosis,
            "follow_up_date": prescription.follow_up_date,
            "pdf_url": prescription.pdf_url,
            "created_at": prescription.created_at,
            "guru_name": guru.name if guru else "N/A"
        })
    
    return {
        "prescriptions": result,
        "total": len(prescriptions)
    }


@router.get("/guru/my-created-prescriptions")
async def get_guru_prescriptions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get prescriptions created by current guru
    
    - Guru-only endpoint
    - Returns all prescriptions created by this consultant
    """
    guru = db.query(Guru).filter(Guru.user_id == current_user.id).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consultants can access this endpoint"
        )
    
    prescriptions = db.query(Prescription).filter(
        Prescription.guru_id == guru.id
    ).order_by(Prescription.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for prescription in prescriptions:
        patient = db.query(User).filter(User.id == prescription.user_id).first()
        
        result.append({
            "id": prescription.id,
            "title": prescription.title,
            "patient_name": patient.full_name if patient else "N/A",
            "created_at": prescription.created_at,
            "follow_up_date": prescription.follow_up_date,
            "is_active": prescription.is_active
        })
    
    return {
        "prescriptions": result,
        "total": len(prescriptions)
    }


@router.put("/{prescription_id}")
async def update_prescription(
    prescription_id: int,
    request: UpdatePrescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update prescription details
    
    - Guru-only: Only creator can update
    - Can update title, diagnosis, remedies, notes, status
    """
    guru = db.query(Guru).filter(Guru.user_id == current_user.id).first()
    if not guru:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consultants can update prescriptions"
        )
    
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.guru_id == guru.id
    ).first()
    
    if not prescription:
        raise HTTPException(
            status_code=404,
            detail="Prescription not found or not authorized"
        )
    
    # Update fields
    if request.title is not None:
        prescription.title = request.title
    if request.diagnosis is not None:
        prescription.diagnosis = request.diagnosis
    if request.remedies is not None:
        prescription.remedies = json.dumps([remedy.model_dump() for remedy in request.remedies])
    if request.follow_up_date is not None:
        prescription.follow_up_date = request.follow_up_date
    if request.notes is not None:
        prescription.notes = request.notes
    if request.is_active is not None:
        prescription.is_active = request.is_active
    
    db.commit()
    
    return {"message": "Prescription updated successfully"}


# ============================================================================
# Prescription Reminders
# ============================================================================

@router.post("/reminders/create")
async def create_reminder(
    request: CreateReminderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a prescription reminder
    
    - Accessible by prescription owner (patient) or creator (guru)
    - Types: remedy_completion, follow_up, custom
    """
    prescription = db.query(Prescription).filter(
        Prescription.id == request.prescription_id
    ).first()
    
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Check authorization
    guru = db.query(Guru).filter(Guru.user_id == current_user.id).first()
    is_authorized = (
        prescription.user_id == current_user.id or
        (guru and prescription.guru_id == guru.id)
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create reminders for this prescription"
        )
    
    # Parse scheduled datetime
    try:
        scheduled_at = datetime.strptime(request.scheduled_at, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid datetime format. Use YYYY-MM-DD HH:MM"
        )
    
    # Create reminder
    reminder = PrescriptionReminder(
        prescription_id=request.prescription_id,
        reminder_type=request.reminder_type,
        reminder_text=request.reminder_text,
        scheduled_at=scheduled_at,
        status="pending"
    )
    
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    return {
        "message": "Reminder created successfully",
        "reminder_id": reminder.id,
        "scheduled_at": reminder.scheduled_at
    }


@router.get("/reminders/upcoming")
async def get_upcoming_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's upcoming prescription reminders
    
    - Returns all pending reminders for user's prescriptions
    - Sorted by scheduled time
    """
    # Get user's prescriptions
    user_prescriptions = db.query(Prescription).filter(
        Prescription.user_id == current_user.id,
        Prescription.is_active == True
    ).all()
    
    prescription_ids = [p.id for p in user_prescriptions]
    
    # Get pending reminders
    reminders = db.query(PrescriptionReminder).filter(
        PrescriptionReminder.prescription_id.in_(prescription_ids),
        PrescriptionReminder.status == "pending",
        PrescriptionReminder.scheduled_at >= datetime.now()
    ).order_by(PrescriptionReminder.scheduled_at).all()
    
    result = []
    for reminder in reminders:
        prescription = db.query(Prescription).filter(
            Prescription.id == reminder.prescription_id
        ).first()
        
        result.append({
            "id": reminder.id,
            "prescription_id": reminder.prescription_id,
            "prescription_title": prescription.title if prescription else "N/A",
            "reminder_type": reminder.reminder_type,
            "reminder_text": reminder.reminder_text,
            "scheduled_at": reminder.scheduled_at,
            "status": reminder.status
        })
    
    return {
        "reminders": result,
        "total": len(result)
    }


# ============================================================================
# Prescription Verification
# ============================================================================

@router.get("/verify/{verification_code}")
async def verify_prescription(
    verification_code: str,
    db: Session = Depends(get_db)
):
    """
    Verify prescription authenticity
    
    - Public endpoint (no authentication required)
    - Validates prescription using verification code
    - Returns basic prescription info without sensitive details
    """
    prescription = db.query(Prescription).filter(
        Prescription.verification_code == verification_code,
        Prescription.is_active == True
    ).first()
    
    if not prescription:
        return {
            "verified": False,
            "message": "Invalid verification code or prescription not found"
        }
    
    # Get guru details
    guru = db.query(Guru).filter(Guru.id == prescription.guru_id).first()
    
    return {
        "verified": True,
        "message": "Prescription verified successfully",
        "prescription": {
            "id": prescription.id,
            "title": prescription.title,
            "created_at": prescription.created_at,
            "consultant": guru.name if guru else "N/A",
            "specialization": (guru.specializations[0] if guru.specializations else None) if guru else None
        }
    }
