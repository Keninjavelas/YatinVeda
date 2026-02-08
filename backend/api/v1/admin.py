"""
Admin endpoints for dual user registration system.
Handles practitioner verification and admin-only operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database import get_db
from models.database import User, Guru
from modules.role_based_access import require_admin_dependency
from modules.auth import get_current_user

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