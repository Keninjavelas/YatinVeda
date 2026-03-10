"""
Admin endpoints for dual user registration system.
Handles practitioner verification and admin-only operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import Counter
import logging

from database import get_db
from models.database import User, Guru, GuruBooking, Payment
from modules.role_based_access import require_admin_dependency
from modules.auth import get_current_user
from modules.entitlements import require_feature

router = APIRouter(tags=["admin"])
logger = logging.getLogger(__name__)


class VerificationRequest(BaseModel):
    """Request model for practitioner verification."""
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    """Request model for practitioner rejection."""
    reason: str
    notes: Optional[str] = None


class PendingPractitioner(BaseModel):
    """Response model for pending practitioner."""
    guru_id: int
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    professional_title: str
    bio: str
    specializations: List[str]
    experience_years: int
    certification_details: Dict[str, Any]
    languages: Optional[List[str]]
    price_per_hour: Optional[int]
    created_at: datetime
    verification_status: str
    is_ready_for_verification: bool


class VerificationResponse(BaseModel):
    """Response model for verification actions."""
    success: bool
    message: str
    guru_id: int
    user_id: int
    verification_status: str
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None


class CertificateAlertItem(BaseModel):
    domain: str
    status: str
    expires_at: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    issuer: Optional[str] = None
    needs_attention: bool


@router.get("/pending-verifications", response_model=List[PendingPractitioner])
async def get_pending_verifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dependency)
):
    """
    Get list of practitioners pending verification.
    Only accessible to admin users.
    """
    try:
        # Query practitioners with pending verification status
        pending_practitioners = (
            db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(User.verification_status == "pending_verification")
            .filter(User.role == "practitioner")
            .order_by(User.created_at.asc())
            .all()
        )
        
        result = []
        for guru, user in pending_practitioners:
            # Check if practitioner is ready for verification
            is_ready = _is_ready_for_verification(guru)
            
            result.append(PendingPractitioner(
                guru_id=guru.id,
                user_id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                professional_title=guru.title or "",  # Use title field
                bio=guru.bio or "",
                specializations=guru.specializations or [],
                experience_years=guru.experience_years or 0,
                certification_details=guru.certification_details or {},
                languages=guru.languages,
                price_per_hour=guru.price_per_hour,
                created_at=user.created_at,
                verification_status=user.verification_status,
                is_ready_for_verification=is_ready
            ))
        
        logger.info(f"Admin {current_user['username']} retrieved {len(result)} pending verifications")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving pending verifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving pending verifications"
        )


@router.post("/verify/{practitioner_id}", response_model=VerificationResponse)
async def verify_practitioner(
    practitioner_id: int,
    request: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dependency)
):
    """
    Approve a practitioner for verification.
    Only accessible to admin users.
    """
    try:
        # Get practitioner and user
        guru_user = (
            db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(Guru.id == practitioner_id)
            .first()
        )
        
        if not guru_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Practitioner with ID {practitioner_id} not found"
            )
        
        guru, user = guru_user
        
        # Check if practitioner is eligible for approval
        if user.verification_status == "verified":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Practitioner is already verified"
            )
        
        if user.verification_status != "pending_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Practitioner verification status is {user.verification_status}, cannot approve"
            )
        
        # Check if practitioner meets verification requirements
        if not _is_ready_for_verification(guru):
            missing_requirements = _get_missing_requirements(guru)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Practitioner does not meet verification requirements: {missing_requirements}"
            )
        
        # Perform approval
        user.verification_status = "verified"
        guru.verified_at = datetime.utcnow()
        guru.verified_by = current_user["user_id"]
        
        # Store approval notes if provided
        if request.notes:
            if guru.verification_documents:
                guru.verification_documents["approval_notes"] = request.notes
            else:
                guru.verification_documents = {"approval_notes": request.notes}
        
        db.commit()
        db.refresh(guru)
        db.refresh(user)
        
        logger.info(
            f"Practitioner approved: guru_id={guru.id}, user_id={user.id}, "
            f"admin={current_user['username']}, notes={request.notes}"
        )
        
        return VerificationResponse(
            success=True,
            message="Practitioner approved successfully",
            guru_id=guru.id,
            user_id=user.id,
            verification_status=user.verification_status,
            verified_at=guru.verified_at,
            verified_by=guru.verified_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving practitioner {practitioner_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error approving practitioner"
        )


@router.post("/reject/{practitioner_id}", response_model=VerificationResponse)
async def reject_practitioner(
    practitioner_id: int,
    request: RejectionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dependency)
):
    """
    Reject a practitioner's verification request.
    Only accessible to admin users.
    """
    try:
        if not request.reason or len(request.reason.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required"
            )
        
        # Get practitioner and user
        guru_user = (
            db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(Guru.id == practitioner_id)
            .first()
        )
        
        if not guru_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Practitioner with ID {practitioner_id} not found"
            )
        
        guru, user = guru_user
        
        # Check if practitioner is eligible for rejection
        if user.verification_status == "verified":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reject an already verified practitioner"
            )
        
        if user.verification_status != "pending_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Practitioner verification status is {user.verification_status}, cannot reject"
            )
        
        # Perform rejection
        user.verification_status = "rejected"
        
        # Store rejection information
        rejection_info = {
            "rejected_at": datetime.utcnow().isoformat(),
            "rejected_by": current_user["user_id"],
            "rejection_reason": request.reason.strip(),
            "rejection_notes": request.notes.strip() if request.notes else None
        }
        
        if guru.verification_documents:
            guru.verification_documents["rejection_info"] = rejection_info
        else:
            guru.verification_documents = {"rejection_info": rejection_info}
        
        db.commit()
        db.refresh(guru)
        db.refresh(user)
        
        logger.info(
            f"Practitioner rejected: guru_id={guru.id}, user_id={user.id}, "
            f"admin={current_user['username']}, reason={request.reason}, notes={request.notes}"
        )
        
        return VerificationResponse(
            success=True,
            message="Practitioner rejected",
            guru_id=guru.id,
            user_id=user.id,
            verification_status=user.verification_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting practitioner {practitioner_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error rejecting practitioner"
        )


@router.get("/verification-stats", response_model=Dict[str, Any])
async def get_verification_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dependency)
):
    """
    Get verification statistics for admin dashboard.
    Only accessible to admin users.
    """
    try:
        # Count practitioners by verification status
        pending_count = (
            db.query(User)
            .filter(User.role == "practitioner")
            .filter(User.verification_status == "pending_verification")
            .count()
        )
        
        verified_count = (
            db.query(User)
            .filter(User.role == "practitioner")
            .filter(User.verification_status == "verified")
            .count()
        )
        
        rejected_count = (
            db.query(User)
            .filter(User.role == "practitioner")
            .filter(User.verification_status == "rejected")
            .count()
        )
        
        total_practitioners = (
            db.query(User)
            .filter(User.role == "practitioner")
            .count()
        )
        
        # Get recent verifications (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_verifications = (
            db.query(Guru)
            .filter(Guru.verified_at >= thirty_days_ago)
            .count()
        )
        
        stats = {
            "total_practitioners": total_practitioners,
            "pending_verification": pending_count,
            "verified": verified_count,
            "rejected": rejected_count,
            "recent_verifications_30_days": recent_verifications,
            "verification_rate": (verified_count / total_practitioners * 100) if total_practitioners > 0 else 0
        }
        
        logger.info(f"Admin {current_user['username']} retrieved verification statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving verification statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving verification statistics"
        )


@router.get("/certificate-alerts", response_model=List[CertificateAlertItem])
async def get_certificate_alerts(
    current_user: dict = Depends(require_admin_dependency),
):
    """Return certificate status and expiry alerts for configured domains."""
    try:
        from modules.certificate_manager import get_certificate_manager

        manager = get_certificate_manager()
        domains = manager.config.get("domains", [])

        alerts: List[CertificateAlertItem] = []
        now = datetime.utcnow()
        for domain in domains:
            status_obj = await manager.get_certificate_status(domain)
            days_until_expiry = None
            if status_obj.expires_at:
                days_until_expiry = (status_obj.expires_at - now).days

            needs_attention = bool(
                status_obj.status.value in {"expiring", "expired", "invalid"}
                or (days_until_expiry is not None and days_until_expiry <= 14)
            )

            alerts.append(
                CertificateAlertItem(
                    domain=status_obj.domain,
                    status=status_obj.status.value,
                    expires_at=status_obj.expires_at,
                    days_until_expiry=days_until_expiry,
                    certificate_path=status_obj.certificate_path,
                    private_key_path=status_obj.private_key_path,
                    issuer=status_obj.issuer,
                    needs_attention=needs_attention,
                )
            )

        logger.info(f"Admin {current_user['username']} retrieved certificate alerts for {len(alerts)} domains")
        return alerts
    except Exception as e:
        logger.error(f"Error retrieving certificate alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving certificate alerts",
        )


def _is_ready_for_verification(guru: Guru) -> bool:
    """
    Check if a practitioner is ready for verification.
    
    Args:
        guru: Guru instance
        
    Returns:
        True if ready for verification, False otherwise
    """
    # Check required fields
    if not guru.title or len(guru.title.strip()) == 0:
        return False
    
    if not guru.bio or len(guru.bio.strip()) < 50:
        return False
    
    if not guru.specializations or len(guru.specializations) == 0:
        return False
    
    if guru.experience_years is None or guru.experience_years < 0:
        return False
    
    if not guru.certification_details:
        return False
    
    # Check certification details structure
    required_cert_fields = ['certification_type', 'issuing_authority']
    for field in required_cert_fields:
        if field not in guru.certification_details or not guru.certification_details[field]:
            return False
    
    return True


def _get_missing_requirements(guru: Guru) -> List[str]:
    """
    Get list of missing verification requirements.
    
    Args:
        guru: Guru instance
        
    Returns:
        List of missing requirement descriptions
    """
    missing = []
    
    if not guru.title or len(guru.title.strip()) == 0:
        missing.append("Professional title")
    
    if not guru.bio or len(guru.bio.strip()) < 50:
        missing.append("Biography (minimum 50 characters)")
    
    if not guru.specializations or len(guru.specializations) == 0:
        missing.append("At least one specialization")
    
    if guru.experience_years is None or guru.experience_years < 0:
        missing.append("Valid experience years")
    
    if not guru.certification_details:
        missing.append("Certification details")
    else:
        required_cert_fields = ['certification_type', 'issuing_authority']
        for field in required_cert_fields:
            if field not in guru.certification_details or not guru.certification_details[field]:
                missing.append(f"Certification {field.replace('_', ' ')}")
    
    return missing


@router.get("/analytics", response_model=Dict[str, Any])
async def get_advanced_analytics(
    period_days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dependency),
    _entitlements: dict = Depends(require_feature("advanced_analytics")),
):
    """Advanced analytics for admin dashboard (growth, bookings, revenue)."""
    try:
        if period_days not in {7, 30, 90, 365}:
            raise HTTPException(status_code=400, detail="period_days must be one of 7, 30, 90, 365")

        now = datetime.utcnow()
        since = now - timedelta(days=period_days)

        total_users = db.query(User).count()
        new_users = db.query(User).filter(User.created_at >= since).count()

        total_practitioners = db.query(User).filter(User.role == "practitioner").count()
        verified_practitioners = db.query(User).filter(User.role == "practitioner", User.verification_status == "verified").count()

        bookings_total = db.query(GuruBooking).count()
        bookings_in_period_rows = db.query(GuruBooking).filter(GuruBooking.created_at >= since).all()
        bookings_in_period = len(bookings_in_period_rows)
        completed_in_period = db.query(GuruBooking).filter(
            GuruBooking.created_at >= since,
            GuruBooking.status == "completed",
        ).count()

        payments_in_period = db.query(Payment).filter(Payment.created_at >= since).all()
        gross_revenue = sum(p.amount for p in payments_in_period if p.status in {"paid", "completed"})
        refunds = sum(p.amount for p in payments_in_period if p.status == "refunded")
        net_revenue = gross_revenue - refunds

        daily_trends: Dict[str, Dict[str, Any]] = {}
        for day_offset in range(period_days):
            day = (since + timedelta(days=day_offset)).date().isoformat()
            daily_trends[day] = {
                "date": day,
                "new_users": 0,
                "new_bookings": 0,
                "completed_bookings": 0,
                "gross_paise": 0,
                "refund_paise": 0,
                "net_paise": 0,
            }

        new_user_rows = db.query(User.created_at).filter(User.created_at >= since).all()
        for created_at, in new_user_rows:
            key = created_at.date().isoformat()
            if key in daily_trends:
                daily_trends[key]["new_users"] += 1

        booking_status_breakdown = Counter()
        for booking in bookings_in_period_rows:
            key = booking.created_at.date().isoformat()
            if key in daily_trends:
                daily_trends[key]["new_bookings"] += 1
                if booking.status == "completed":
                    daily_trends[key]["completed_bookings"] += 1
            booking_status_breakdown[booking.status or "unknown"] += 1

        payment_status_breakdown = Counter()
        for payment in payments_in_period:
            key = payment.created_at.date().isoformat()
            if key in daily_trends:
                if payment.status in {"paid", "completed"}:
                    daily_trends[key]["gross_paise"] += payment.amount
                if payment.status == "refunded":
                    daily_trends[key]["refund_paise"] += payment.amount
            payment_status_breakdown[payment.status or "unknown"] += 1

        trend_list = []
        for day in sorted(daily_trends.keys()):
            item = daily_trends[day]
            item["net_paise"] = item["gross_paise"] - item["refund_paise"]
            item["gross_inr"] = round(item["gross_paise"] / 100, 2)
            item["refund_inr"] = round(item["refund_paise"] / 100, 2)
            item["net_inr"] = round(item["net_paise"] / 100, 2)
            trend_list.append(item)

        return {
            "period_days": period_days,
            "users": {
                "total": total_users,
                "new_in_period": new_users,
            },
            "practitioners": {
                "total": total_practitioners,
                "verified": verified_practitioners,
            },
            "bookings": {
                "total": bookings_total,
                "in_period": bookings_in_period,
                "completed_in_period": completed_in_period,
                "by_status": dict(booking_status_breakdown),
            },
            "revenue": {
                "gross_paise": gross_revenue,
                "refund_paise": refunds,
                "net_paise": net_revenue,
                "gross_inr": round(gross_revenue / 100, 2),
                "refund_inr": round(refunds / 100, 2),
                "net_inr": round(net_revenue / 100, 2),
                "by_payment_status": dict(payment_status_breakdown),
            },
            "daily_trends": trend_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving advanced analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving advanced analytics")