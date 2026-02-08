"""
User Service Layer for dual user registration system.
Handles user creation, validation, and profile management.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
import re
from datetime import datetime

from models.database import User, Guru
from schemas.dual_registration import UserRegistrationData, PractitionerRegistrationData
from modules.auth import get_password_hash, verify_password


class UserService:
    """Service class for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_email_uniqueness(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Validate that email is unique across all users.
        
        Args:
            email: Email address to validate
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if email is unique, False otherwise
        """
        query = self.db.query(User).filter(User.email == email.lower())
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        existing_user = query.first()
        return existing_user is None
    
    def validate_username_uniqueness(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Validate that username is unique across all users.
        
        Args:
            username: Username to validate
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if username is unique, False otherwise
        """
        query = self.db.query(User).filter(User.username == username.lower())
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        existing_user = query.first()
        return existing_user is None
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt algorithm (for compatibility with existing auth system).
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return get_password_hash(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Stored hash
            
        Returns:
            True if password matches, False otherwise
        """
        return verify_password(password, hashed_password)
    
    def create_user(self, registration_data: UserRegistrationData) -> User:
        """
        Create a new regular user.
        
        Args:
            registration_data: Validated user registration data
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If email or username already exists
            IntegrityError: If database constraint violation occurs
        """
        # Validate uniqueness
        if not self.validate_email_uniqueness(registration_data.email):
            raise ValueError(f"Email {registration_data.email} is already registered")
        
        if not self.validate_username_uniqueness(registration_data.username):
            raise ValueError(f"Username {registration_data.username} is already taken")
        
        # Hash password
        hashed_password = self.hash_password(registration_data.password)
        
        # Create user instance
        user = User(
            username=registration_data.username.lower(),
            email=registration_data.email.lower(),
            password_hash=hashed_password,
            full_name=registration_data.full_name,
            role="user",
            verification_status="active",  # Regular users are active immediately
            created_at=datetime.utcnow()
        )
        
        # Store birth details if provided (only if column exists)
        if registration_data.birth_details and hasattr(user, 'birth_details'):
            user.birth_details = registration_data.birth_details
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            # Check specific constraint violations
            if "email" in str(e).lower():
                raise ValueError(f"Email {registration_data.email} is already registered")
            elif "username" in str(e).lower():
                raise ValueError(f"Username {registration_data.username} is already taken")
            else:
                raise ValueError("User creation failed due to database constraint violation")
    
    def create_practitioner(self, registration_data: PractitionerRegistrationData) -> tuple[User, Guru]:
        """
        Create a new practitioner (user + guru profile).
        
        Args:
            registration_data: Validated practitioner registration data
            
        Returns:
            Tuple of (User, Guru) instances
            
        Raises:
            ValueError: If email or username already exists
            IntegrityError: If database constraint violation occurs
        """
        # Validate uniqueness
        if not self.validate_email_uniqueness(registration_data.email):
            raise ValueError(f"Email {registration_data.email} is already registered")
        
        if not self.validate_username_uniqueness(registration_data.username):
            raise ValueError(f"Username {registration_data.username} is already taken")
        
        # Hash password
        hashed_password = self.hash_password(registration_data.password)
        
        # Create user instance
        user = User(
            username=registration_data.username.lower(),
            email=registration_data.email.lower(),
            password_hash=hashed_password,
            full_name=registration_data.full_name,
            role="practitioner",
            verification_status="pending_verification",  # Practitioners need verification
            created_at=datetime.utcnow()
        )
        
        try:
            self.db.add(user)
            self.db.flush()  # Get user ID without committing
            
            # Create guru profile
            guru = Guru(
                user_id=user.id,
                title=registration_data.professional_title,  # Use title instead of professional_title
                name=registration_data.full_name or registration_data.username,  # Use name field
                bio=registration_data.bio,
                specializations=registration_data.specializations,
                experience_years=registration_data.experience_years,
                certification_details=registration_data.certification_details,
                languages=registration_data.languages,
                price_per_hour=registration_data.price_per_hour or 0,  # Default to 0 if None to satisfy NOT NULL constraint
                availability_schedule=registration_data.availability_schedule,
                # contact_phone=registration_data.contact_phone,  # Skip until column exists
                # is_verified=False,  # Skip until column exists
                # created_at=datetime.utcnow()  # Skip until column exists
            )
            
            self.db.add(guru)
            self.db.commit()
            self.db.refresh(user)
            self.db.refresh(guru)
            
            return user, guru
            
        except IntegrityError as e:
            self.db.rollback()
            # Check specific constraint violations
            if "email" in str(e).lower():
                raise ValueError(f"Email {registration_data.email} is already registered")
            elif "username" in str(e).lower():
                raise ValueError(f"Username {registration_data.username} is already taken")
            else:
                raise ValueError("Practitioner creation failed due to database constraint violation")
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email.
        
        Args:
            email: Email address
            
        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.email == email.lower()).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username.
        
        Args:
            username: Username
            
        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(User.username == username.lower()).first()
    
    def update_user_profile(self, user_id: int, update_data: Dict[str, Any]) -> User:
        """
        Update user profile information.
        
        Args:
            user_id: User ID
            update_data: Dictionary of fields to update
            
        Returns:
            Updated User instance
            
        Raises:
            ValueError: If user not found or validation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Validate email uniqueness if being updated
        if "email" in update_data:
            if not self.validate_email_uniqueness(update_data["email"], exclude_user_id=user_id):
                raise ValueError(f"Email {update_data['email']} is already registered")
            update_data["email"] = update_data["email"].lower()
        
        # Validate username uniqueness if being updated
        if "username" in update_data:
            if not self.validate_username_uniqueness(update_data["username"], exclude_user_id=user_id):
                raise ValueError(f"Username {update_data['username']} is already taken")
            update_data["username"] = update_data["username"].lower()
        
        # Hash password if being updated
        if "password" in update_data:
            update_data["password_hash"] = self.hash_password(update_data["password"])
            del update_data["password"]
        
        # Update allowed fields
        allowed_fields = {
            "username", "email", "password_hash", "full_name"
        }
        
        # Add birth_details only if the column exists
        if hasattr(User, 'birth_details'):
            allowed_fields.add("birth_details")
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            if "email" in str(e).lower():
                raise ValueError(f"Email {update_data.get('email', '')} is already registered")
            elif "username" in str(e).lower():
                raise ValueError(f"Username {update_data.get('username', '')} is already taken")
            else:
                raise ValueError("Profile update failed due to database constraint violation")
    
    def authenticate_user(self, login: str, password: str) -> Optional[User]:
        """
        Authenticate user by email/username and password.
        
        Args:
            login: Email or username
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        # Try to find user by email first, then username
        user = self.get_user_by_email(login)
        if not user:
            user = self.get_user_by_username(login)
        
        if not user:
            return None
        
        # Verify password
        if self.verify_password(password, user.password_hash):
            return user
        
        return None
    
    def get_user_profile_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile data including practitioner info if applicable.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user profile data or None if not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        profile_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "verification_status": user.verification_status,
            "created_at": user.created_at
        }
        
        # Add birth_details only if column exists
        if hasattr(user, 'birth_details'):
            profile_data["birth_details"] = user.birth_details
        
        # Add practitioner profile if user is a practitioner
        if user.role == "practitioner":
            guru = self.db.query(Guru).filter(Guru.user_id == user.id).first()
            if guru:
                profile_data["practitioner_profile"] = {
                    "guru_id": guru.id,
                    "professional_title": guru.title,  # Use title instead of professional_title
                    "bio": guru.bio,
                    "specializations": guru.specializations,
                    "experience_years": guru.experience_years,
                    "certification_details": guru.certification_details,
                    "languages": guru.languages,
                    "price_per_hour": guru.price_per_hour,
                    "availability_schedule": guru.availability_schedule,
                    "rating": guru.rating,
                    "total_sessions": guru.total_sessions,
                    # "contact_phone": guru.contact_phone,  # Skip until column exists
                    # "is_verified": guru.is_verified,  # Skip until column exists
                    "verified_at": guru.verified_at,
                    # "created_at": guru.created_at  # Skip until column exists
                }
        
        return profile_data