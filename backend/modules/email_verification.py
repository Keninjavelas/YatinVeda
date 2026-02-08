"""
Email Verification Module for YatinVeda

Handles email verification flow for new user registrations.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.database import User, EmailVerificationToken
from modules.email_utils import send_email
import logging
import os

logger = logging.getLogger(__name__)

# Configuration
EMAIL_VERIFICATION_TOKEN_LENGTH = int(os.getenv("EMAIL_VERIFICATION_TOKEN_LENGTH", "32"))
EMAIL_VERIFICATION_EXPIRY_HOURS = int(os.getenv("EMAIL_VERIFICATION_EXPIRY_HOURS", "24"))


def generate_verification_token(length: int = EMAIL_VERIFICATION_TOKEN_LENGTH) -> str:
    """
    Generate a secure random verification token.
    
    Args:
        length: Length of the token (default 32 characters)
        
    Returns:
        Generated verification token
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_email_verification_token(db: Session, user_id: int) -> EmailVerificationToken:
    """
    Create a new email verification token for a user.
    
    Args:
        db: Database session
        user_id: ID of the user to create token for
        
    Returns:
        Created EmailVerificationToken object
        
    Raises:
        ValueError: If user doesn't exist
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User with ID {user_id} does not exist")
    
    # Generate token and expiry
    token = generate_verification_token()
    expires_at = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)
    
    # Create token record
    verification_token = EmailVerificationToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    try:
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)
        return verification_token
    except IntegrityError:
        db.rollback()
        # Retry with a new token in case of collision
        token = generate_verification_token()
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)
        return verification_token


def send_verification_email(db: Session, user_id: int) -> bool:
    """
    Send verification email to user's email address.
    
    Args:
        db: Database session
        user_id: ID of the user to send verification email to
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"Cannot send verification email: User with ID {user_id} does not exist")
        return False
    
    # Create verification token
    try:
        verification_token = create_email_verification_token(db, user_id)
    except ValueError as e:
        logger.error(f"Cannot create verification token: {str(e)}")
        return False
    
    # Prepare email content
    subject = "📧 Verify Your YatinVeda Account"
    verification_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token.token}"
    
    body = f"""
Dear {user.full_name or user.username},

Thank you for registering with YatinVeda! Please verify your email address by clicking the link below:

{verification_link}

This link will expire in {EMAIL_VERIFICATION_EXPIRY_HOURS} hours. If you didn't create an account with us, please ignore this email.

Best regards,
Team YatinVeda
    """.strip()
    
    try:
        send_email(user.email, subject, body)
        logger.info(f"Verification email sent to user {user_id} ({user.email})")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to user {user_id}: {str(e)}")
        return False


def verify_email_token(db: Session, token: str) -> tuple[bool, Optional[str], Optional[User]]:
    """
    Verify an email verification token and update user's verification status.
    
    Args:
        db: Database session
        token: Verification token to validate
        
    Returns:
        Tuple of (success, message, user) where:
        - success: True if verification was successful
        - message: Human-readable message about the result
        - user: User object if successful, None otherwise
    """
    # Find the token in the database
    verification_record = (
        db.query(EmailVerificationToken)
        .filter(EmailVerificationToken.token == token)
        .first()
    )
    
    if not verification_record:
        return False, "Invalid verification token", None
    
    # Check if token is already used
    if verification_record.is_used():
        return False, "Verification token has already been used", None
    
    # Check if token has expired
    if verification_record.is_expired():
        return False, "Verification token has expired", None
    
    # Get the associated user
    user = db.query(User).filter(User.id == verification_record.user_id).first()
    if not user:
        return False, "Associated user not found", None
    
    # Update verification status
    user.verification_status = "active"  # Change to active upon email verification
    verification_record.used_at = datetime.utcnow()
    
    try:
        db.commit()
        logger.info(f"Email verified for user {user.id} ({user.email})")
        return True, "Email verified successfully", user
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update user verification status: {str(e)}")
        return False, "Failed to update verification status", None


def is_email_verified(db: Session, user_id: int) -> bool:
    """
    Check if a user's email is verified.
    
    Args:
        db: Database session
        user_id: ID of the user to check
        
    Returns:
        True if email is verified, False otherwise
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # In this implementation, we consider email verified if verification_status is 'active'
    # This is a simplification - in a real system you might want a separate email_verified field
    return user.verification_status == "active"


def resend_verification_email(db: Session, user_id: int) -> bool:
    """
    Resend verification email to a user.
    
    Args:
        db: Database session
        user_id: ID of the user to resend verification email to
        
    Returns:
        True if email was resent successfully, False otherwise
    """
    # Check if user exists and is not already verified
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"Cannot resend verification: User with ID {user_id} does not exist")
        return False
    
    if user.verification_status == "active":
        logger.warning(f"User {user_id} is already verified")
        return False
    
    # Delete existing unused tokens for this user
    existing_tokens = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None)
        )
    )
    existing_tokens.delete()
    db.commit()
    
    # Send new verification email
    return send_verification_email(db, user_id)