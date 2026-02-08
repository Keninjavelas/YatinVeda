"""
Pydantic schemas for dual user registration system.
"""

from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
import re


class BaseRegistrationData(BaseModel):
    """Base registration data common to all user types."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name of the user")
    role: Literal["user", "practitioner"] = Field(..., description="User role")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        if v.lower() in ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp']:
            raise ValueError('Username is reserved')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password exceeds bcrypt 72-byte limit; reduce multi-byte characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name if provided."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) < 2:
                raise ValueError('Full name must be at least 2 characters long')
            if not re.match(r'^[a-zA-Z\s\'-\.]+$', v):
                raise ValueError('Full name can only contain letters, spaces, hyphens, apostrophes, and periods')
        return v


class UserRegistrationData(BaseRegistrationData):
    """Registration data for regular users."""
    role: Literal["user"] = "user"
    birth_details: Optional[Dict[str, Any]] = Field(None, description="Optional birth details for chart creation")
    
    @validator('birth_details')
    def validate_birth_details(cls, v):
        """Validate birth details if provided."""
        if v is not None:
            required_fields = ['birth_date', 'birth_time', 'birth_place']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f'Birth details must include {field}')
            
            # Validate birth_date format
            try:
                datetime.fromisoformat(v['birth_date'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValueError('birth_date must be in ISO format (YYYY-MM-DD)')
            
            # Validate birth_time format
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v['birth_time']):
                raise ValueError('birth_time must be in HH:MM format')
            
            # Validate birth_place is not empty
            if not isinstance(v['birth_place'], str) or len(v['birth_place'].strip()) == 0:
                raise ValueError('birth_place must be a non-empty string')
        
        return v


class PractitionerRegistrationData(BaseRegistrationData):
    """Registration data for practitioners (gurus)."""
    role: Literal["practitioner"] = "practitioner"
    
    # Required practitioner fields
    professional_title: str = Field(..., min_length=2, max_length=100, description="Professional title")
    bio: str = Field(..., min_length=50, max_length=2000, description="Professional biography")
    specializations: List[str] = Field(..., min_items=1, max_items=10, description="Areas of expertise")
    experience_years: int = Field(..., ge=0, le=50, description="Years of experience")
    certification_details: Dict[str, Any] = Field(..., description="Certification information")
    
    # Optional practitioner fields
    languages: Optional[List[str]] = Field(None, max_items=10, description="Languages spoken")
    price_per_hour: Optional[int] = Field(None, ge=100, le=50000, description="Price per hour in paise")
    availability_schedule: Optional[Dict[str, Any]] = Field(None, description="Availability schedule")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    
    @validator('professional_title')
    def validate_professional_title(cls, v):
        """Validate professional title."""
        v = v.strip()
        if not re.match(r'^[a-zA-Z\s\'-\.]+$', v):
            raise ValueError('Professional title can only contain letters, spaces, hyphens, apostrophes, and periods')
        return v
    
    @validator('bio')
    def validate_bio(cls, v):
        """Validate biography."""
        v = v.strip()
        if len(v) < 50:
            raise ValueError('Biography must be at least 50 characters long')
        return v
    
    @validator('specializations')
    def validate_specializations(cls, v):
        """Validate specializations against allowed values."""
        valid_specializations = {
            "vedic_astrology", "western_astrology", "numerology", "tarot", 
            "palmistry", "vastu", "gemology", "horoscope_matching",
            "career_guidance", "relationship_counseling", "health_astrology",
            "financial_astrology", "spiritual_guidance", "meditation",
            "yoga", "ayurveda", "reiki", "crystal_healing"
        }
        
        for spec in v:
            if spec not in valid_specializations:
                raise ValueError(f'Invalid specialization: {spec}. Must be one of: {", ".join(sorted(valid_specializations))}')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_specs = []
        for spec in v:
            if spec not in seen:
                seen.add(spec)
                unique_specs.append(spec)
        
        return unique_specs
    
    @validator('certification_details')
    def validate_certification_details(cls, v):
        """Validate certification details."""
        required_fields = ['certification_type', 'issuing_authority']
        for field in required_fields:
            if field not in v or not v[field]:
                raise ValueError(f'Certification details must include {field}')
        
        # Validate certification_type
        valid_cert_types = [
            'diploma', 'certificate', 'degree', 'professional_certification',
            'traditional_training', 'apprenticeship', 'self_taught'
        ]
        if v['certification_type'] not in valid_cert_types:
            raise ValueError(f'certification_type must be one of: {", ".join(valid_cert_types)}')
        
        # Validate issuing_authority is not empty
        if not isinstance(v['issuing_authority'], str) or len(v['issuing_authority'].strip()) == 0:
            raise ValueError('issuing_authority must be a non-empty string')
        
        return v
    
    @validator('languages')
    def validate_languages(cls, v):
        """Validate languages if provided."""
        if v is not None:
            valid_languages = {
                'english', 'hindi', 'sanskrit', 'tamil', 'telugu', 'kannada', 
                'malayalam', 'bengali', 'gujarati', 'marathi', 'punjabi', 
                'urdu', 'oriya', 'assamese', 'nepali', 'spanish', 'french',
                'german', 'chinese', 'japanese', 'arabic'
            }
            
            for lang in v:
                if lang.lower() not in valid_languages:
                    raise ValueError(f'Invalid language: {lang}. Must be one of: {", ".join(sorted(valid_languages))}')
            
            # Convert to lowercase and remove duplicates
            return list(set(lang.lower() for lang in v))
        
        return v
    
    @validator('contact_phone')
    def validate_contact_phone(cls, v):
        """Validate contact phone if provided."""
        if v is not None:
            v = v.strip()
            # Remove common separators
            phone_digits = re.sub(r'[\s\-\(\)\+]', '', v)
            if not re.match(r'^\d{10,15}$', phone_digits):
                raise ValueError('Phone number must contain 10-15 digits')
        return v
    
    @validator('availability_schedule')
    def validate_availability_schedule(cls, v):
        """Validate availability schedule if provided."""
        if v is not None:
            valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
            
            for day, schedule in v.items():
                if day.lower() not in valid_days:
                    raise ValueError(f'Invalid day: {day}. Must be one of: {", ".join(sorted(valid_days))}')
                
                if not isinstance(schedule, dict):
                    raise ValueError(f'Schedule for {day} must be a dictionary')
                
                if 'available' in schedule and not isinstance(schedule['available'], bool):
                    raise ValueError(f'available field for {day} must be boolean')
                
                if 'time_slots' in schedule:
                    if not isinstance(schedule['time_slots'], list):
                        raise ValueError(f'time_slots for {day} must be a list')
                    
                    for slot in schedule['time_slots']:
                        if not isinstance(slot, dict) or 'start' not in slot or 'end' not in slot:
                            raise ValueError(f'Each time slot must have start and end times')
                        
                        # Validate time format
                        for time_key in ['start', 'end']:
                            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', slot[time_key]):
                                raise ValueError(f'{time_key} time must be in HH:MM format')
        
        return v


# Union type for registration data
RegistrationData = Union[UserRegistrationData, PractitionerRegistrationData]


class RegistrationResponse(BaseModel):
    """Response model for successful registration."""
    message: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    role: str
    verification_status: str
    requires_verification: bool = False


class ValidationError(BaseModel):
    """Individual validation error."""
    field: str
    message: str
    code: str


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    errors: Optional[List[ValidationError]] = None
    error_code: str


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    verification_status: str
    created_at: datetime
    
    # Conditional practitioner data
    practitioner_profile: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PractitionerProfileData(BaseModel):
    """Practitioner profile data for responses."""
    guru_id: int
    professional_title: str
    bio: str
    specializations: List[str]
    experience_years: int
    languages: Optional[List[str]]
    price_per_hour: Optional[int]
    certification_details: Dict[str, Any]
    is_verified: bool
    verified_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Form configuration for frontend
class FormFieldConfig(BaseModel):
    """Configuration for form fields."""
    name: str
    type: str
    required: bool
    label: str
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    validation: Optional[Dict[str, Any]] = None


class FormConfig(BaseModel):
    """Form configuration for different user roles."""
    role: str
    fields: List[FormFieldConfig]
    
    @classmethod
    def get_user_form_config(cls) -> 'FormConfig':
        """Get form configuration for regular users."""
        return cls(
            role="user",
            fields=[
                FormFieldConfig(name="username", type="text", required=True, label="Username", placeholder="Enter username"),
                FormFieldConfig(name="email", type="email", required=True, label="Email", placeholder="Enter email address"),
                FormFieldConfig(name="password", type="password", required=True, label="Password", placeholder="Enter strong password"),
                FormFieldConfig(name="full_name", type="text", required=False, label="Full Name", placeholder="Enter your full name"),
                FormFieldConfig(name="birth_details", type="object", required=False, label="Birth Details", placeholder="Optional birth information for chart creation")
            ]
        )
    
    @classmethod
    def get_practitioner_form_config(cls) -> 'FormConfig':
        """Get form configuration for practitioners."""
        return cls(
            role="practitioner",
            fields=[
                FormFieldConfig(name="username", type="text", required=True, label="Username", placeholder="Enter username"),
                FormFieldConfig(name="email", type="email", required=True, label="Email", placeholder="Enter email address"),
                FormFieldConfig(name="password", type="password", required=True, label="Password", placeholder="Enter strong password"),
                FormFieldConfig(name="full_name", type="text", required=False, label="Full Name", placeholder="Enter your full name"),
                FormFieldConfig(name="professional_title", type="text", required=True, label="Professional Title", placeholder="e.g., Vedic Astrologer, Tarot Reader"),
                FormFieldConfig(name="bio", type="textarea", required=True, label="Biography", placeholder="Describe your experience and expertise (minimum 50 characters)"),
                FormFieldConfig(
                    name="specializations", 
                    type="multiselect", 
                    required=True, 
                    label="Specializations",
                    options=[
                        "vedic_astrology", "western_astrology", "numerology", "tarot", 
                        "palmistry", "vastu", "gemology", "horoscope_matching",
                        "career_guidance", "relationship_counseling", "health_astrology",
                        "financial_astrology", "spiritual_guidance", "meditation",
                        "yoga", "ayurveda", "reiki", "crystal_healing"
                    ]
                ),
                FormFieldConfig(name="experience_years", type="number", required=True, label="Years of Experience", validation={"min": 0, "max": 50}),
                FormFieldConfig(name="certification_details", type="object", required=True, label="Certification Details", placeholder="Provide certification information"),
                FormFieldConfig(
                    name="languages", 
                    type="multiselect", 
                    required=False, 
                    label="Languages Spoken",
                    options=[
                        "english", "hindi", "sanskrit", "tamil", "telugu", "kannada", 
                        "malayalam", "bengali", "gujarati", "marathi", "punjabi", 
                        "urdu", "oriya", "assamese", "nepali", "spanish", "french",
                        "german", "chinese", "japanese", "arabic"
                    ]
                ),
                FormFieldConfig(name="price_per_hour", type="number", required=False, label="Price per Hour (₹)", validation={"min": 1, "max": 500}),
                FormFieldConfig(name="contact_phone", type="tel", required=False, label="Contact Phone", placeholder="Enter phone number")
            ]
        )