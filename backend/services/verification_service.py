"""
Verification Service Layer for dual user registration system.
Handles admin approval workflow for practitioner verification.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from models.database import User, Guru


class VerificationService:
    """Service class for practitioner verification operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def get_pending_verifications(self) -> List[Dict[str, Any]]:
        """
        Get list of practitioners pending verification.
        
        Returns:
            List of dictionaries with practitioner information
        """
        pending_practitioners = (
            self.db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(User.verification_status.in_(["pending_verification", "pending"]))
            .filter(Guru.is_verified == False)
            .order_by(Guru.created_at.asc())
            .all()
        )
        
        result = []
        for guru, user in pending_practitioners:
            result.append({
                "guru_id": guru.id,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "professional_title": guru.professional_title,
                "bio": guru.bio,
                "specializations": guru.specializations,
                "experience_years": guru.experience_years,
                "certification_details": guru.certification_details,
                "languages": guru.languages,
                "contact_phone": guru.contact_phone,
                "created_at": guru.created_at,
                "verification_status": user.verification_status,
                "is_ready_for_verification": self._is_ready_for_verification(guru)
            })
        
        return result
    
    def get_verification_details(self, guru_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed verification information for a specific practitioner.
        
        Args:
            guru_id: Guru ID
            
        Returns:
            Dictionary with detailed verification information or None if not found
        """
        guru_user = (
            self.db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(Guru.id == guru_id)
            .first()
        )
        
        if not guru_user:
            return None
        
        guru, user = guru_user
        
        return {
            "guru_id": guru.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "professional_title": guru.professional_title,
            "bio": guru.bio,
            "specializations": guru.specializations,
            "experience_years": guru.experience_years,
            "certification_details": guru.certification_details,
            "verification_documents": guru.verification_documents,
            "languages": guru.languages,
            "price_per_hour": guru.price_per_hour,
            "availability_schedule": guru.availability_schedule,
            "contact_phone": guru.contact_phone,
            "created_at": guru.created_at,
            "verification_status": user.verification_status,
            "is_verified": guru.is_verified,
            "verified_at": guru.verified_at,
            "verified_by": guru.verified_by,
            "is_ready_for_verification": self._is_ready_for_verification(guru),
            "verification_requirements": self._get_verification_requirements(guru)
        }
    
    def approve_practitioner(self, guru_id: int, admin_user_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Approve a practitioner for verification.
        
        Args:
            guru_id: Guru ID to approve
            admin_user_id: ID of admin user performing the approval
            notes: Optional approval notes
            
        Returns:
            Dictionary with approval result
            
        Raises:
            ValueError: If practitioner not found or not eligible for approval
        """
        # Get practitioner and user
        guru_user = (
            self.db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(Guru.id == guru_id)
            .first()
        )
        
        if not guru_user:
            raise ValueError(f"Practitioner with ID {guru_id} not found")
        
        guru, user = guru_user
        
        # Validate admin user exists
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not admin_user:
            raise ValueError(f"Admin user with ID {admin_user_id} not found")
        
        # Check if practitioner is eligible for approval
        if guru.is_verified:
            raise ValueError("Practitioner is already verified")
        
        if user.verification_status not in ["pending_verification", "pending"]:
            raise ValueError(f"Practitioner verification status is {user.verification_status}, cannot approve")
        
        # Check if practitioner meets verification requirements
        if not self._is_ready_for_verification(guru):
            requirements = self._get_verification_requirements(guru)
            missing = [req for req in requirements if not req["satisfied"]]
            raise ValueError(f"Practitioner does not meet verification requirements: {[req['requirement'] for req in missing]}")
        
        # Perform approval
        try:
            # Update guru verification status
            guru.is_verified = True
            guru.verified_at = datetime.utcnow()
            guru.verified_by = admin_user_id
            
            # Update user verification status
            user.verification_status = "verified"
            
            # Log the approval
            self.logger.info(
                f"Practitioner approved: guru_id={guru_id}, user_id={user.id}, "
                f"admin_id={admin_user_id}, notes={notes}"
            )
            
            self.db.commit()
            self.db.refresh(guru)
            self.db.refresh(user)
            
            return {
                "success": True,
                "message": "Practitioner approved successfully",
                "guru_id": guru.id,
                "user_id": user.id,
                "verified_at": guru.verified_at,
                "verified_by": guru.verified_by,
                "verification_status": user.verification_status
            }
            
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database error during approval: {e}")
            raise ValueError("Approval failed due to database error")
    
    def reject_practitioner(self, guru_id: int, admin_user_id: int, reason: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject a practitioner's verification request.
        
        Args:
            guru_id: Guru ID to reject
            admin_user_id: ID of admin user performing the rejection
            reason: Reason for rejection
            notes: Optional rejection notes
            
        Returns:
            Dictionary with rejection result
            
        Raises:
            ValueError: If practitioner not found or not eligible for rejection
        """
        if not reason or len(reason.strip()) == 0:
            raise ValueError("Rejection reason is required")
        
        # Get practitioner and user
        guru_user = (
            self.db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(Guru.id == guru_id)
            .first()
        )
        
        if not guru_user:
            raise ValueError(f"Practitioner with ID {guru_id} not found")
        
        guru, user = guru_user
        
        # Validate admin user exists
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not admin_user:
            raise ValueError(f"Admin user with ID {admin_user_id} not found")
        
        # Check if practitioner is eligible for rejection
        if guru.is_verified:
            raise ValueError("Cannot reject an already verified practitioner")
        
        if user.verification_status not in ["pending_verification", "pending"]:
            raise ValueError(f"Practitioner verification status is {user.verification_status}, cannot reject")
        
        # Perform rejection
        try:
            # Update user verification status
            user.verification_status = "rejected"
            
            # Store rejection information in verification_documents
            rejection_info = {
                "rejected_at": datetime.utcnow().isoformat(),
                "rejected_by": admin_user_id,
                "rejection_reason": reason.strip(),
                "rejection_notes": notes.strip() if notes else None
            }
            
            if guru.verification_documents:
                guru.verification_documents["rejection_info"] = rejection_info
            else:
                guru.verification_documents = {"rejection_info": rejection_info}
            
            # Log the rejection
            self.logger.info(
                f"Practitioner rejected: guru_id={guru_id}, user_id={user.id}, "
                f"admin_id={admin_user_id}, reason={reason}, notes={notes}"
            )
            
            self.db.commit()
            self.db.refresh(guru)
            self.db.refresh(user)
            
            return {
                "success": True,
                "message": "Practitioner rejected",
                "guru_id": guru.id,
                "user_id": user.id,
                "rejected_at": rejection_info["rejected_at"],
                "rejected_by": admin_user_id,
                "rejection_reason": reason,
                "verification_status": user.verification_status
            }
            
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database error during rejection: {e}")
            raise ValueError("Rejection failed due to database error")
    
    def reset_verification_status(self, guru_id: int, admin_user_id: int, reason: str) -> Dict[str, Any]:
        """
        Reset a practitioner's verification status back to pending.
        This can be used to re-review a practitioner or reset after profile changes.
        
        Args:
            guru_id: Guru ID to reset
            admin_user_id: ID of admin user performing the reset
            reason: Reason for reset
            
        Returns:
            Dictionary with reset result
            
        Raises:
            ValueError: If practitioner not found or not eligible for reset
        """
        if not reason or len(reason.strip()) == 0:
            raise ValueError("Reset reason is required")
        
        # Get practitioner and user
        guru_user = (
            self.db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(Guru.id == guru_id)
            .first()
        )
        
        if not guru_user:
            raise ValueError(f"Practitioner with ID {guru_id} not found")
        
        guru, user = guru_user
        
        # Validate admin user exists
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not admin_user:
            raise ValueError(f"Admin user with ID {admin_user_id} not found")
        
        # Perform reset
        try:
            # Reset guru verification status
            guru.is_verified = False
            guru.verified_at = None
            guru.verified_by = None
            
            # Update user verification status
            user.verification_status = "pending_verification"
            
            # Store reset information
            reset_info = {
                "reset_at": datetime.utcnow().isoformat(),
                "reset_by": admin_user_id,
                "reset_reason": reason.strip()
            }
            
            if guru.verification_documents:
                if "reset_history" not in guru.verification_documents:
                    guru.verification_documents["reset_history"] = []
                guru.verification_documents["reset_history"].append(reset_info)
            else:
                guru.verification_documents = {"reset_history": [reset_info]}
            
            # Log the reset
            self.logger.info(
                f"Practitioner verification reset: guru_id={guru_id}, user_id={user.id}, "
                f"admin_id={admin_user_id}, reason={reason}"
            )
            
            self.db.commit()
            self.db.refresh(guru)
            self.db.refresh(user)
            
            return {
                "success": True,
                "message": "Practitioner verification status reset",
                "guru_id": guru.id,
                "user_id": user.id,
                "reset_at": reset_info["reset_at"],
                "reset_by": admin_user_id,
                "reset_reason": reason,
                "verification_status": user.verification_status
            }
            
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database error during reset: {e}")
            raise ValueError("Reset failed due to database error")
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Get verification statistics for admin dashboard.
        
        Returns:
            Dictionary with verification statistics
        """
        # Count practitioners by verification status
        pending_count = (
            self.db.query(User)
            .filter(User.role == "practitioner")
            .filter(User.verification_status.in_(["pending_verification", "pending"]))
            .count()
        )
        
        verified_count = (
            self.db.query(User)
            .filter(User.role == "practitioner")
            .filter(User.verification_status == "verified")
            .count()
        )
        
        rejected_count = (
            self.db.query(User)
            .filter(User.role == "practitioner")
            .filter(User.verification_status == "rejected")
            .count()
        )
        
        total_practitioners = (
            self.db.query(User)
            .filter(User.role == "practitioner")
            .count()
        )
        
        # Get recent verifications (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_verifications = (
            self.db.query(Guru)
            .filter(Guru.verified_at >= thirty_days_ago)
            .count()
        )
        
        return {
            "total_practitioners": total_practitioners,
            "pending_verification": pending_count,
            "verified": verified_count,
            "rejected": rejected_count,
            "recent_verifications_30_days": recent_verifications,
            "verification_rate": (verified_count / total_practitioners * 100) if total_practitioners > 0 else 0
        }
    
    def _is_ready_for_verification(self, guru: Guru) -> bool:
        """
        Check if a practitioner is ready for verification.
        
        Args:
            guru: Guru instance
            
        Returns:
            True if ready for verification, False otherwise
        """
        # Check required fields
        if not guru.professional_title or len(guru.professional_title.strip()) == 0:
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
    
    def _get_verification_requirements(self, guru: Guru) -> List[Dict[str, Any]]:
        """
        Get list of verification requirements and their satisfaction status.
        
        Args:
            guru: Guru instance
            
        Returns:
            List of requirement dictionaries
        """
        requirements = []
        
        # Professional title
        requirements.append({
            "requirement": "Professional title",
            "description": "Must provide a professional title",
            "satisfied": bool(guru.professional_title and len(guru.professional_title.strip()) > 0),
            "current_value": guru.professional_title
        })
        
        # Biography
        bio_satisfied = bool(guru.bio and len(guru.bio.strip()) >= 50)
        requirements.append({
            "requirement": "Biography",
            "description": "Must provide a biography of at least 50 characters",
            "satisfied": bio_satisfied,
            "current_value": f"{len(guru.bio) if guru.bio else 0} characters"
        })
        
        # Specializations
        spec_satisfied = bool(guru.specializations and len(guru.specializations) > 0)
        requirements.append({
            "requirement": "Specializations",
            "description": "Must provide at least one specialization",
            "satisfied": spec_satisfied,
            "current_value": guru.specializations if guru.specializations else []
        })
        
        # Experience years
        exp_satisfied = guru.experience_years is not None and guru.experience_years >= 0
        requirements.append({
            "requirement": "Experience years",
            "description": "Must provide valid experience years (0 or more)",
            "satisfied": exp_satisfied,
            "current_value": guru.experience_years
        })
        
        # Certification details
        cert_satisfied = False
        if guru.certification_details:
            required_fields = ['certification_type', 'issuing_authority']
            cert_satisfied = all(
                field in guru.certification_details and guru.certification_details[field]
                for field in required_fields
            )
        
        requirements.append({
            "requirement": "Certification details",
            "description": "Must provide certification type and issuing authority",
            "satisfied": cert_satisfied,
            "current_value": guru.certification_details if guru.certification_details else {}
        })
        
        return requirements