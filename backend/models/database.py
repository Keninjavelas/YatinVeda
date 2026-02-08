"""Core SQLAlchemy models used by the backend and tests.

This file defines a minimal schema sufficient for the guru booking and
payments test suites. It is intentionally focused on the fields that are
actually exercised in tests.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    # birth_details = Column(JSON, nullable=True)  # For birth chart information - commented out until migration is added
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # New fields for dual user registration
    role = Column(String(20), default="user", nullable=False)  # "user" or "practitioner"
    verification_status = Column(String(30), default="active", nullable=False)  # "active", "pending_verification", "verified", "rejected"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guru_profile = relationship("Guru", back_populates="user", uselist=False, foreign_keys="Guru.user_id")
    
    # Email verification
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    
    # Validation methods
    def is_practitioner(self) -> bool:
        """Check if user is a practitioner."""
        return bool(self.role == "practitioner")
    
    def is_verified_practitioner(self) -> bool:
        """Check if user is a verified practitioner."""
        return bool(self.role == "practitioner" and self.verification_status == "verified")
    
    def can_create_bookings(self) -> bool:
        """Check if practitioner can create bookings (must be verified)."""
        return self.is_practitioner() and self.verification_status in ["verified", "active"]
    
    def needs_verification(self) -> bool:
        """Check if user needs verification."""
        return bool(self.role == "practitioner" and self.verification_status == "pending_verification")
    
    @classmethod
    def get_valid_roles(cls):
        """Get list of valid user roles."""
        return ["user", "practitioner"]
    
    @classmethod
    def get_valid_verification_statuses(cls):
        """Get list of valid verification statuses."""
        return ["active", "pending_verification", "verified", "rejected"]


class Guru(Base):
    __tablename__ = "gurus"

    id = Column(Integer, primary_key=True, index=True)
    
    # New field for user linkage
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    
    # Core practitioner fields
    # professional_title = Column(String, nullable=True)  # Maps to title - commented out until migration
    name = Column(String, nullable=True)  # Keep for backward compatibility
    title = Column(String, nullable=True)  # Keep for backward compatibility
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    specializations = Column(JSON, nullable=True)
    languages = Column(JSON, nullable=True)
    experience_years = Column(Integer, default=0)
    rating = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    price_per_hour = Column(Integer, nullable=True)  # Optional for practitioners
    availability_schedule = Column(JSON, nullable=True)
    # contact_phone = Column(String, nullable=True)  # New field for practitioners - commented out until migration
    is_active = Column(Boolean, default=True)
    personality_tags = Column(JSON, nullable=True)
    
    # New verification fields
    certification_details = Column(JSON, nullable=True)
    verification_documents = Column(JSON, nullable=True)
    # is_verified = Column(Boolean, default=False)  # New field for verification status - commented out until migration
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    # created_at = Column(DateTime, default=datetime.utcnow)  # New field for creation timestamp - commented out until migration

    # Relationships
    user = relationship("User", back_populates="guru_profile", foreign_keys=[user_id])
    verifier = relationship("User", foreign_keys=[verified_by], post_update=True)
    bookings = relationship("GuruBooking", back_populates="guru")
    
    # Validation methods
    def can_accept_bookings(self) -> bool:
        """Check if guru can accept bookings (must be verified and active)."""
        return bool(self.is_verified and self.is_active)
    
    def has_certification_details(self) -> bool:
        """Check if guru has provided certification details."""
        return bool(self.certification_details is not None and self.certification_details and len(str(self.certification_details)) > 0)
    
    def has_verification_documents(self) -> bool:
        """Check if guru has uploaded verification documents."""
        return bool(self.verification_documents is not None and self.verification_documents and len(str(self.verification_documents)) > 0)
    
    def is_ready_for_verification(self) -> bool:
        """Check if guru has all required information for verification."""
        return bool(self.has_certification_details() and 
                self.bio is not None and self.bio.strip() and len(self.bio.strip()) > 0 and
                self.specializations is not None and self.specializations and len(str(self.specializations)) > 0 and
                self.experience_years is not None and self.experience_years >= 0)
    
    @classmethod
    def get_valid_specializations(cls):
        """Get list of valid specializations."""
        return [
            "vedic_astrology", "western_astrology", "numerology", "tarot", 
            "palmistry", "vastu", "gemology", "horoscope_matching",
            "career_guidance", "relationship_counseling", "health_astrology",
            "financial_astrology", "spiritual_guidance"
        ]


class GuruBooking(Base):
    __tablename__ = "guru_bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    guru_id = Column(Integer, ForeignKey("gurus.id"), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    time_slot = Column(String, nullable=False)
    duration_minutes = Column(Integer, default=60)
    session_type = Column(String, default="video_call")
    concern_category = Column(String, nullable=True)
    quiz_responses = Column(JSON, nullable=True)
    payment_amount = Column(Integer, default=0)
    status = Column(String, default="pending")
    payment_status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    meeting_link = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    guru = relationship("Guru", back_populates="bookings")
    availability_rows = relationship("GuruAvailability", back_populates="booking")


class GuruAvailability(Base):
    __tablename__ = "guru_availability"

    id = Column(Integer, primary_key=True, index=True)
    guru_id = Column(Integer, ForeignKey("gurus.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    time_slot = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)
    booking_id = Column(Integer, ForeignKey("guru_bookings.id"), nullable=True)

    guru = relationship("Guru")
    booking = relationship("GuruBooking", back_populates="availability_rows")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("guru_bookings.id"), nullable=True)
    order_id = Column(String, index=True, nullable=True)
    payment_id = Column(String, index=True, nullable=True)
    amount = Column(Integer, nullable=False)  # stored in paise
    base_amount = Column(Integer, nullable=False)
    gst_amount = Column(Integer, default=0)
    status = Column(String, default="created")
    payment_method = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)
    razorpay_response = Column(JSON, nullable=True)
    receipt = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    user = relationship("User")
    booking = relationship("GuruBooking")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    refund_id = Column(String, index=True, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    reason = Column(String, nullable=True)
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    razorpay_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    payment = relationship("Payment")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0)  # stored in paise
    currency = Column(String, default="INR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    transactions = relationship("WalletTransaction", back_populates="wallet")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # positive for credit, negative for debit
    transaction_type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    reference_id = Column(String, nullable=True)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="transactions")


# Optional Chart model used by some fixtures; not exercised heavily in current tests
class Chart(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chart_name = Column(String, nullable=False)
    birth_details = Column(JSON, nullable=False)
    chart_data = Column(JSON, nullable=False)
    chart_type = Column(String, default="D1")
    is_public = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    jti = Column(String, nullable=True, index=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)


class MFASettings(Base):
    """Multi-Factor Authentication settings for users"""
    __tablename__ = "mfa_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False)
    secret_key = Column(String, nullable=False)  # TOTP secret, encrypted in production
    backup_codes_hash = Column(Text, nullable=True)  # JSON array of hashed backup codes
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    trusted_devices = relationship("TrustedDevice", back_populates="mfa_settings", cascade="all, delete-orphan")


class TrustedDevice(Base):
    """Trusted devices that skip MFA for 30 days"""
    __tablename__ = "trusted_devices"

    id = Column(Integer, primary_key=True, index=True)
    mfa_settings_id = Column(Integer, ForeignKey("mfa_settings.id"), nullable=False, index=True)
    device_fingerprint = Column(String, unique=True, nullable=False, index=True)  # Hash of user-agent + IP pattern
    device_name = Column(String, nullable=True)  # User-friendly name (e.g., "Chrome on Windows")
    trusted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # 30 days from trust
    last_used_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    mfa_settings = relationship("MFASettings", back_populates="trusted_devices")


class MFABackupCode(Base):
    """Backup codes for MFA recovery (8 codes per user)"""
    __tablename__ = "mfa_backup_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String, nullable=False, index=True)  # SHA-256 hash of the code
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    user = relationship("User")


# Minimal stubs for admin metrics
class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


# Community and social features models
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    interests = Column(JSON, nullable=True)
    privacy_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String, default="text")
    media_url = Column(String, nullable=True)
    chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True)
    tags = Column(JSON, nullable=True)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    chart = relationship("Chart")


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("post_comments.id"), nullable=True)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = relationship("CommunityPost")
    user = relationship("User")


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("CommunityPost")
    user = relationship("User")


class CommentLike(Base):
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("post_comments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    comment = relationship("PostComment")
    user = relationship("User")


class UserFollow(Base):
    __tablename__ = "user_follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    follower = relationship("User", foreign_keys=[follower_id])
    following = relationship("User", foreign_keys=[following_id])


class CommunityEvent(Base):
    __tablename__ = "community_events"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    location = Column(String, nullable=True)
    is_online = Column(Boolean, default=False)
    meeting_link = Column(String, nullable=True)
    max_participants = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organizer = relationship("User")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("community_events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="registered")
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("CommunityEvent")
    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("guru_bookings.id"), nullable=False)
    guru_id = Column(Integer, ForeignKey("gurus.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    remedies = Column(JSON, nullable=False)
    notes = Column(Text, nullable=True)
    digital_signature = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking = relationship("GuruBooking")
    guru = relationship("Guru")
    user = relationship("User")


class PrescriptionReminder(Base):
    __tablename__ = "prescription_reminders"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reminder_date = Column(DateTime, nullable=False)
    reminder_type = Column(String, default="follow_up")
    message = Column(Text, nullable=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    prescription = relationship("Prescription")
    user = relationship("User")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="email_verification_tokens")
    
    def is_valid(self) -> bool:
        """Check if the token is still valid (not expired and not used)."""
        from datetime import datetime
        return bool(self.used_at is None and self.expires_at > datetime.utcnow())
    
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        from datetime import datetime
        return bool(self.expires_at <= datetime.utcnow())
    
    def is_used(self) -> bool:
        """Check if the token has been used."""
        return bool(self.used_at is not None)
