"""
Practitioner Service Layer for dual user registration system.
Handles practitioner-specific operations, validation, and profile management.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List
import re
from datetime import datetime

from models.database import User, Guru
from schemas.dual_registration import PractitionerRegistrationData


class PractitionerService:
    """Service class for practitioner-specific operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_specializations(self, specializations: List[str]) -> bool:
        """
        Validate that all specializations are valid.
        
        Args:
            specializations: List of specialization strings
            
        Returns:
            True if all specializations are valid, False otherwise
        """
        if not specializations or len(specializations) == 0:
            return False
        
        valid_specializations = {
            "vedic_astrology", "western_astrology", "numerology", "tarot", 
            "palmistry", "vastu", "gemology", "horoscope_matching",
            "career_guidance", "relationship_counseling", "health_astrology",
            "financial_astrology", "spiritual_guidance", "meditation",
            "yoga", "ayurveda", "reiki", "crystal_healing"
        }
        
        return all(spec in valid_specializations for spec in specializations)
    
    def validate_experience_years(self, experience_years: int) -> bool:
        """
        Validate experience years.
        
        Args:
            experience_years: Number of years of experience
            
        Returns:
            True if valid, False otherwise
        """
        return 0 <= experience_years <= 50
    
    def validate_certification_details(self, certification_details: Dict[str, Any]) -> bool:
        """
        Validate certification details structure and content.
        
        Args:
            certification_details: Dictionary with certification information
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(certification_details, dict):
            return False
        
        # Required fields
        required_fields = ['certification_type', 'issuing_authority']
        for field in required_fields:
            if field not in certification_details or not certification_details[field]:
                return False
        
        # Validate certification_type
        valid_cert_types = [
            'diploma', 'certificate', 'degree', 'professional_certification',
            'traditional_training', 'apprenticeship', 'self_taught'
        ]
        if certification_details['certification_type'] not in valid_cert_types:
            return False
        
        # Validate issuing_authority is not empty
        if not isinstance(certification_details['issuing_authority'], str):
            return False
        if len(certification_details['issuing_authority'].strip()) == 0:
            return False
        
        return True
    
    def validate_languages(self, languages: Optional[List[str]]) -> bool:
        """
        Validate languages list.
        
        Args:
            languages: Optional list of language codes
            
        Returns:
            True if valid, False otherwise
        """
        if languages is None:
            return True
        
        valid_languages = {
            'english', 'hindi', 'sanskrit', 'tamil', 'telugu', 'kannada', 
            'malayalam', 'bengali', 'gujarati', 'marathi', 'punjabi', 
            'urdu', 'oriya', 'assamese', 'nepali', 'spanish', 'french',
            'german', 'chinese', 'japanese', 'arabic'
        }
        
        return all(lang.lower() in valid_languages for lang in languages)
    
    def validate_price_per_hour(self, price_per_hour: Optional[int]) -> bool:
        """
        Validate price per hour.
        
        Args:
            price_per_hour: Price in paise (optional)
            
        Returns:
            True if valid, False otherwise
        """
        if price_per_hour is None:
            return True
        
        return 100 <= price_per_hour <= 50000  # 1 rupee to 500 rupees
    
    def validate_contact_phone(self, contact_phone: Optional[str]) -> bool:
        """
        Validate contact phone number.
        
        Args:
            contact_phone: Phone number string (optional)
            
        Returns:
            True if valid, False otherwise
        """
        if contact_phone is None:
            return True
        
        # Remove common separators
        phone_digits = re.sub(r'[\s\-\(\)\+]', '', contact_phone.strip())
        return re.match(r'^\d{10,15}$', phone_digits) is not None
    
    def validate_availability_schedule(self, availability_schedule: Optional[Dict[str, Any]]) -> bool:
        """
        Validate availability schedule structure.
        
        Args:
            availability_schedule: Dictionary with schedule information
            
        Returns:
            True if valid, False otherwise
        """
        if availability_schedule is None:
            return True
        
        valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
        
        for day, schedule in availability_schedule.items():
            if day.lower() not in valid_days:
                return False
            
            if not isinstance(schedule, dict):
                return False
            
            if 'available' in schedule and not isinstance(schedule['available'], bool):
                return False
            
            if 'time_slots' in schedule:
                if not isinstance(schedule['time_slots'], list):
                    return False
                
                for slot in schedule['time_slots']:
                    if not isinstance(slot, dict) or 'start' not in slot or 'end' not in slot:
                        return False
                    
                    # Validate time format
                    for time_key in ['start', 'end']:
                        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', slot[time_key]):
                            return False
        
        return True
    
    def validate_bio(self, bio: str) -> bool:
        """
        Validate biography content.
        
        Args:
            bio: Biography text
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(bio, str):
            return False
        
        bio = bio.strip()
        return 50 <= len(bio) <= 2000
    
    def validate_professional_title(self, professional_title: str) -> bool:
        """
        Validate professional title.
        
        Args:
            professional_title: Professional title string
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(professional_title, str):
            return False
        
        title = professional_title.strip()
        if len(title) < 2 or len(title) > 100:
            return False
        
        # Only letters, spaces, hyphens, apostrophes, and periods
        return re.match(r'^[a-zA-Z\s\'-\.]+$', title) is not None
    
    def validate_practitioner_data(self, registration_data: PractitionerRegistrationData) -> List[str]:
        """
        Comprehensive validation of practitioner registration data.
        
        Args:
            registration_data: Practitioner registration data
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate professional title
        if not self.validate_professional_title(registration_data.professional_title):
            errors.append("Professional title must be 2-100 characters and contain only letters, spaces, hyphens, apostrophes, and periods")
        
        # Validate bio
        if not self.validate_bio(registration_data.bio):
            errors.append("Biography must be 50-2000 characters long")
        
        # Validate specializations
        if not self.validate_specializations(registration_data.specializations):
            errors.append("One or more specializations are invalid")
        
        # Validate experience years
        if not self.validate_experience_years(registration_data.experience_years):
            errors.append("Experience years must be between 0 and 50")
        
        # Validate certification details
        if not self.validate_certification_details(registration_data.certification_details):
            errors.append("Certification details are invalid or incomplete")
        
        # Validate optional fields
        if not self.validate_languages(registration_data.languages):
            errors.append("One or more languages are invalid")
        
        if not self.validate_price_per_hour(registration_data.price_per_hour):
            errors.append("Price per hour must be between 100 and 50000 paise (1-500 rupees)")
        
        if not self.validate_contact_phone(registration_data.contact_phone):
            errors.append("Contact phone number format is invalid")
        
        if not self.validate_availability_schedule(registration_data.availability_schedule):
            errors.append("Availability schedule format is invalid")
        
        return errors
    
    def get_practitioner_by_user_id(self, user_id: int) -> Optional[Guru]:
        """
        Get practitioner profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Guru instance or None if not found
        """
        return self.db.query(Guru).filter(Guru.user_id == user_id).first()
    
    def get_practitioner_by_id(self, guru_id: int) -> Optional[Guru]:
        """
        Get practitioner profile by guru ID.
        
        Args:
            guru_id: Guru ID
            
        Returns:
            Guru instance or None if not found
        """
        return self.db.query(Guru).filter(Guru.id == guru_id).first()
    
    def update_practitioner_profile(self, user_id: int, update_data: Dict[str, Any]) -> Guru:
        """
        Update practitioner profile information.
        
        Args:
            user_id: User ID
            update_data: Dictionary of fields to update
            
        Returns:
            Updated Guru instance
            
        Raises:
            ValueError: If practitioner not found or validation fails
        """
        guru = self.get_practitioner_by_user_id(user_id)
        if not guru:
            raise ValueError(f"Practitioner profile for user {user_id} not found")
        
        # Validate updated fields
        validation_errors = []
        
        if "professional_title" in update_data:
            if not self.validate_professional_title(update_data["professional_title"]):
                validation_errors.append("Professional title is invalid")
        
        if "bio" in update_data:
            if not self.validate_bio(update_data["bio"]):
                validation_errors.append("Biography is invalid")
        
        if "specializations" in update_data:
            if not self.validate_specializations(update_data["specializations"]):
                validation_errors.append("One or more specializations are invalid")
        
        if "experience_years" in update_data:
            if not self.validate_experience_years(update_data["experience_years"]):
                validation_errors.append("Experience years is invalid")
        
        if "certification_details" in update_data:
            if not self.validate_certification_details(update_data["certification_details"]):
                validation_errors.append("Certification details are invalid")
        
        if "languages" in update_data:
            if not self.validate_languages(update_data["languages"]):
                validation_errors.append("One or more languages are invalid")
        
        if "price_per_hour" in update_data:
            if not self.validate_price_per_hour(update_data["price_per_hour"]):
                validation_errors.append("Price per hour is invalid")
        
        if "contact_phone" in update_data:
            if not self.validate_contact_phone(update_data["contact_phone"]):
                validation_errors.append("Contact phone is invalid")
        
        if "availability_schedule" in update_data:
            if not self.validate_availability_schedule(update_data["availability_schedule"]):
                validation_errors.append("Availability schedule is invalid")
        
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        
        # Update allowed fields
        allowed_fields = {
            "professional_title", "bio", "specializations", "experience_years",
            "certification_details", "languages", "price_per_hour", 
            "contact_phone", "availability_schedule"
        }
        
        # Check if critical fields are being updated (requires re-verification)
        critical_fields = {
            "professional_title", "bio", "specializations", "experience_years",
            "certification_details"
        }
        
        requires_reverification = any(field in update_data for field in critical_fields)
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(guru, field):
                setattr(guru, field, value)
        
        # Reset verification if critical fields changed
        if requires_reverification and guru.is_verified:
            guru.is_verified = False
            guru.verified_at = None
            guru.verified_by = None
            
            # Update user verification status
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.verification_status = "pending_verification"
        
        try:
            self.db.commit()
            self.db.refresh(guru)
            return guru
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError("Profile update failed due to database constraint violation")
    
    def get_practitioner_profile_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete practitioner profile data.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with practitioner profile data or None if not found
        """
        guru = self.get_practitioner_by_user_id(user_id)
        if not guru:
            return None
        
        return {
            "guru_id": guru.id,
            "user_id": guru.user_id,
            "professional_title": guru.professional_title,
            "bio": guru.bio,
            "specializations": guru.specializations,
            "experience_years": guru.experience_years,
            "certification_details": guru.certification_details,
            "languages": guru.languages,
            "price_per_hour": guru.price_per_hour,
            "availability_schedule": guru.availability_schedule,
            "contact_phone": guru.contact_phone,
            "is_verified": guru.is_verified,
            "verified_at": guru.verified_at,
            "verified_by": guru.verified_by,
            "created_at": guru.created_at,
            "is_active": guru.is_active,
            "rating": guru.rating,
            "total_sessions": guru.total_sessions
        }
    
    def get_pending_verifications(self) -> List[Dict[str, Any]]:
        """
        Get list of practitioners pending verification.
        
        Returns:
            List of dictionaries with practitioner information
        """
        pending_gurus = (
            self.db.query(Guru, User)
            .join(User, Guru.user_id == User.id)
            .filter(User.verification_status == "pending_verification")
            .filter(Guru.is_verified == False)
            .all()
        )
        
        result = []
        for guru, user in pending_gurus:
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
                "created_at": guru.created_at,
                "verification_status": user.verification_status
            })
        
        return result
    
    def is_ready_for_verification(self, user_id: int) -> tuple[bool, List[str]]:
        """
        Check if practitioner is ready for verification.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (is_ready, list_of_missing_requirements)
        """
        guru = self.get_practitioner_by_user_id(user_id)
        if not guru:
            return False, ["Practitioner profile not found"]
        
        missing_requirements = []
        
        # Check required fields
        if not guru.professional_title or len(guru.professional_title.strip()) == 0:
            missing_requirements.append("Professional title is required")
        
        if not guru.bio or len(guru.bio.strip()) < 50:
            missing_requirements.append("Biography must be at least 50 characters")
        
        if not guru.specializations or len(guru.specializations) == 0:
            missing_requirements.append("At least one specialization is required")
        
        if guru.experience_years is None or guru.experience_years < 0:
            missing_requirements.append("Valid experience years is required")
        
        if not guru.certification_details or not self.validate_certification_details(guru.certification_details):
            missing_requirements.append("Valid certification details are required")
        
        return len(missing_requirements) == 0, missing_requirements