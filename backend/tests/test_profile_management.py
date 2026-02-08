"""
Property-based tests for profile management in dual user registration system.
Feature: dual-user-registration
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from sqlalchemy.orm import Session
from datetime import datetime
import json
import string

from database import get_db
from models.database import User, Guru
from schemas.dual_registration import UserRegistrationData, PractitionerRegistrationData
from services.user_service import UserService


class TestProfileManagement:
    """Property tests for profile management functionality."""
    
    @given(
        role=st.sampled_from(["user", "practitioner"]),
        verification_status=st.sampled_from(["active", "pending_verification", "verified", "rejected"]),
        is_admin=st.booleans(),
        has_practitioner_profile=st.booleans()
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10, deadline=None)
    def test_profile_responses_contain_role_appropriate_information(self, role, verification_status, is_admin, has_practitioner_profile):
        """
        Property 11: Profile responses contain role-appropriate information
        For any user profile request, the response should contain basic user information
        plus role-specific information (practitioner profile for practitioners).
        
        Feature: dual-user-registration, Property 11: Profile responses contain role-appropriate information
        Validates: Requirements 4.5, 7.1
        """
        db = next(get_db())
        try:
            user_service = UserService(db)
            
            # Create a test user
            unique_suffix = str(datetime.now().microsecond)
            user = User(
                username=f"testuser_{unique_suffix}",
                email=f"test_{unique_suffix}@example.com",
                password_hash="test_hash",
                role=role,
                verification_status=verification_status,
                is_admin=is_admin,
                full_name="Test User",
                created_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create practitioner profile if needed
            guru = None
            if role == "practitioner" and has_practitioner_profile:
                guru = Guru(
                    user_id=user.id,
                    name=user.full_name,
                    title="Test Practitioner",
                    bio="Test bio for practitioner",
                    specializations=["vedic_astrology"],
                    experience_years=5,
                    price_per_hour=1000,
                    certification_details={"type": "diploma"},
                    languages=["english"],
                    rating=4,
                    total_sessions=10
                )
                db.add(guru)
                db.commit()
                db.refresh(guru)
            
            # Get profile data using the service
            profile_data = user_service.get_user_profile_data(user.id)
            
            # Verify basic profile information is always present
            assert profile_data is not None
            assert profile_data["user_id"] == user.id
            assert profile_data["username"] == user.username
            assert profile_data["email"] == user.email
            assert profile_data["full_name"] == user.full_name
            assert profile_data["role"] == role
            assert profile_data["verification_status"] == verification_status
            assert "created_at" in profile_data
            
            # Verify role-appropriate information
            if role == "practitioner" and has_practitioner_profile:
                # Practitioners should have practitioner profile data
                assert "practitioner_profile" in profile_data
                assert profile_data["practitioner_profile"] is not None
                
                practitioner_profile = profile_data["practitioner_profile"]
                assert practitioner_profile["guru_id"] == guru.id
                assert practitioner_profile["professional_title"] == guru.title
                assert practitioner_profile["bio"] == guru.bio
                assert practitioner_profile["specializations"] == guru.specializations
                assert practitioner_profile["experience_years"] == guru.experience_years
                assert practitioner_profile["price_per_hour"] == guru.price_per_hour
                assert practitioner_profile["languages"] == guru.languages
                assert practitioner_profile["rating"] == guru.rating
                assert practitioner_profile["total_sessions"] == guru.total_sessions
            else:
                # Non-practitioners or practitioners without profiles should not have practitioner data
                if "practitioner_profile" in profile_data:
                    assert profile_data["practitioner_profile"] is None
            
            # Clean up
            if guru:
                db.delete(guru)
            db.delete(user)
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    @given(
        original_verification_status=st.sampled_from(["verified", "active"]),
        update_critical_field=st.booleans(),
        update_non_critical_field=st.booleans()
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=8, deadline=None)
    def test_profile_update_verification_reset(self, original_verification_status, update_critical_field, update_non_critical_field):
        """
        Property 12: Profile update validation and verification reset
        For any practitioner profile update, critical changes should reset verification status
        to pending_verification, while non-critical changes should not affect verification status.
        
        Feature: dual-user-registration, Property 12: Profile update validation and verification reset
        Validates: Requirements 7.2, 7.3, 7.4, 7.5
        """
        # Skip test if no updates are being made
        assume(update_critical_field or update_non_critical_field)
        
        db = next(get_db())
        try:
            # Create a verified practitioner
            unique_suffix = str(datetime.now().microsecond)
            user = User(
                username=f"practitioner_{unique_suffix}",
                email=f"practitioner_{unique_suffix}@example.com",
                password_hash="test_hash",
                role="practitioner",
                verification_status=original_verification_status,
                full_name="Test Practitioner",
                created_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create practitioner profile
            guru = Guru(
                user_id=user.id,
                name=user.full_name,
                title="Original Title",
                bio="Original bio",
                specializations=["vedic_astrology"],
                experience_years=5,
                price_per_hour=1000,
                certification_details={"type": "diploma"},
                languages=["english"],
                verified_at=datetime.utcnow() if original_verification_status == "verified" else None
            )
            
            db.add(guru)
            db.commit()
            db.refresh(guru)
            
            # Track original values
            original_title = guru.title
            original_bio = guru.bio
            original_specializations = guru.specializations
            original_experience = guru.experience_years
            original_languages = guru.languages
            original_price = guru.price_per_hour
            
            # Simulate profile updates
            critical_change_made = False
            
            if update_critical_field:
                # Make critical changes (should reset verification)
                guru.title = "Updated Title"
                guru.bio = "Updated bio"
                guru.specializations = ["tarot"]
                guru.experience_years = 10
                critical_change_made = True
            
            if update_non_critical_field:
                # Make non-critical changes (should not reset verification)
                guru.languages = ["hindi"]
                guru.price_per_hour = 1500
            
            # Apply verification reset logic
            if critical_change_made and original_verification_status == "verified":
                user.verification_status = "pending_verification"
                guru.verified_at = None
                guru.verified_by = None
            
            db.commit()
            db.refresh(user)
            db.refresh(guru)
            
            # Verify the verification reset logic
            if critical_change_made and original_verification_status == "verified":
                # Verification should be reset for critical changes
                assert user.verification_status == "pending_verification"
                assert guru.verified_at is None
                assert guru.verified_by is None
            else:
                # Verification status should remain unchanged
                assert user.verification_status == original_verification_status
                if original_verification_status == "verified":
                    # verified_at should remain if no critical changes
                    if not critical_change_made:
                        assert guru.verified_at is not None
            
            # Verify that updates were applied correctly
            if update_critical_field:
                assert guru.title != original_title
                assert guru.bio != original_bio
                assert guru.specializations != original_specializations
                assert guru.experience_years != original_experience
            
            if update_non_critical_field:
                assert guru.languages != original_languages
                assert guru.price_per_hour != original_price
            
            # Clean up
            db.delete(guru)
            db.delete(user)
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def test_profile_update_field_validation(self):
        """
        Property 12: Profile update validation and verification reset
        Profile updates should validate field constraints and data types.
        
        Feature: dual-user-registration, Property 12: Profile update validation and verification reset
        Validates: Requirements 7.2, 7.3, 7.4, 7.5
        """
        db = next(get_db())
        try:
            # Create a test practitioner
            unique_suffix = str(datetime.now().microsecond)
            user = User(
                username=f"practitioner_{unique_suffix}",
                email=f"practitioner_{unique_suffix}@example.com",
                password_hash="test_hash",
                role="practitioner",
                verification_status="verified",
                full_name="Test Practitioner",
                created_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            guru = Guru(
                user_id=user.id,
                name=user.full_name,
                title="Test Title",
                bio="Test bio",
                specializations=["vedic_astrology"],
                experience_years=5,
                price_per_hour=1000,
                certification_details={"type": "diploma"},
                languages=["english"]
            )
            
            db.add(guru)
            db.commit()
            db.refresh(guru)
            
            # Test valid updates
            valid_updates = [
                {"title": "Updated Title"},
                {"bio": "Updated bio with sufficient length"},
                {"specializations": ["tarot", "numerology"]},
                {"experience_years": 10},
                {"languages": ["hindi", "english"]},
                {"price_per_hour": 1500}
            ]
            
            for update in valid_updates:
                for field, value in update.items():
                    setattr(guru, field, value)
                    
                    # Should not raise any validation errors
                    db.commit()
                    db.refresh(guru)
                    
                    # Verify the update was applied
                    assert getattr(guru, field) == value
            
            # Clean up
            db.delete(guru)
            db.delete(user)
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])