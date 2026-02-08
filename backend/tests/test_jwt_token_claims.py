"""
Property-based tests for JWT token claims in dual user registration system.
Feature: dual-user-registration
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import string
from jose import jwt

from database import get_db
from models.database import User, Guru
from schemas.dual_registration import UserRegistrationData, PractitionerRegistrationData
from services.user_service import UserService
from modules.auth import create_access_token, verify_token, SECRET_KEY, ALGORITHM


class TestJWTTokenClaims:
    """Property tests for JWT token claims with role and verification status."""
    
    @given(
        username=st.text(min_size=3, max_size=15, alphabet=string.ascii_lowercase + string.digits),
        email_local=st.text(min_size=1, max_size=10, alphabet=string.ascii_lowercase),
        email_domain=st.text(min_size=1, max_size=10, alphabet=string.ascii_lowercase),
        password=st.just("TestPass123"),  # Use a fixed valid password
        full_name=st.one_of(st.none(), st.text(min_size=2, max_size=20, alphabet=string.ascii_letters + " ")),
        is_admin=st.booleans()
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=5, deadline=None)
    def test_jwt_token_contains_correct_user_claims(self, username, email_local, email_domain, password, full_name, is_admin):
        """
        Property 10: JWT token contains correct role and verification status
        For any user registration, the generated JWT token should contain the correct
        user_id, username, role, verification_status, and is_admin claims.
        
        Feature: dual-user-registration, Property 10: JWT token contains correct role and verification status
        Validates: Requirements 6.2, 6.3
        """
        # Skip reserved usernames
        assume(username.lower() not in ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp'])
        
        # Make username and email unique by adding timestamp
        unique_suffix = str(datetime.now().microsecond)
        unique_username = f"{username}_{unique_suffix}"
        unique_email = f"{email_local}_{unique_suffix}@{email_domain}.com"
        
        db = next(get_db())
        try:
            user_service = UserService(db)
            
            # Create user registration data
            registration_data = UserRegistrationData(
                username=unique_username,
                email=unique_email,
                password=password,
                full_name=full_name,
                role="user"
            )
            
            # Create user
            user = user_service.create_user(registration_data)
            
            # Set admin status if needed
            if is_admin:
                user.is_admin = True
                db.commit()
                db.refresh(user)
            
            # Create JWT token with user claims
            token_data = {
                "sub": user.username,
                "user_id": user.id,
                "is_admin": user.is_admin,
                "role": user.role,
                "verification_status": user.verification_status
            }
            
            access_token = create_access_token(data=token_data)
            
            # Verify token and extract claims
            payload = verify_token(access_token)
            assert payload is not None, "Token verification failed"
            
            # Verify all required claims are present and correct
            assert payload.get("sub") == user.username, f"Username claim mismatch: {payload.get('sub')} != {user.username}"
            assert payload.get("user_id") == user.id, f"User ID claim mismatch: {payload.get('user_id')} != {user.id}"
            assert payload.get("is_admin") == user.is_admin, f"Admin claim mismatch: {payload.get('is_admin')} != {user.is_admin}"
            assert payload.get("role") == user.role, f"Role claim mismatch: {payload.get('role')} != {user.role}"
            assert payload.get("verification_status") == user.verification_status, f"Verification status claim mismatch: {payload.get('verification_status')} != {user.verification_status}"
            
            # Verify standard JWT claims are present
            assert "iat" in payload, "Missing issued-at claim"
            assert "nbf" in payload, "Missing not-before claim"
            assert "exp" in payload, "Missing expiration claim"
            
            # Verify token can be decoded directly with jose
            direct_payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            assert direct_payload.get("sub") == user.username, "Direct JWT decode failed"
            
            # Clean up
            db.delete(user)
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    @given(
        username=st.text(min_size=3, max_size=15, alphabet=string.ascii_lowercase + string.digits),
        email_local=st.text(min_size=1, max_size=10, alphabet=string.ascii_lowercase),
        email_domain=st.text(min_size=1, max_size=10, alphabet=string.ascii_lowercase),
        password=st.just("TestPass123"),  # Use a fixed valid password
        full_name=st.one_of(st.none(), st.text(min_size=2, max_size=20, alphabet=string.ascii_letters + " ")),
        professional_title=st.text(min_size=2, max_size=20, alphabet=string.ascii_letters + " "),
        bio=st.just("This is a test bio with more than fifty characters to meet the minimum requirement for testing."),
        specializations=st.just(["vedic_astrology"]),  # Use fixed specializations
        experience_years=st.integers(min_value=0, max_value=20),
        price_per_hour=st.one_of(st.none(), st.integers(min_value=100, max_value=2000))
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=5, deadline=None)
    def test_jwt_token_contains_correct_practitioner_claims(self, username, email_local, email_domain, password, 
                                                          full_name, professional_title, bio, specializations, 
                                                          experience_years, price_per_hour):
        """
        Property 10: JWT token contains correct role and verification status
        For any practitioner registration, the generated JWT token should contain the correct
        user_id, username, role="practitioner", verification_status="pending_verification", and is_admin=False claims.
        
        Feature: dual-user-registration, Property 10: JWT token contains correct role and verification status
        Validates: Requirements 6.2, 6.3
        """
        # Skip reserved usernames
        assume(username.lower() not in ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp'])
        
        # Make username and email unique by adding timestamp
        unique_suffix = str(datetime.now().microsecond)
        unique_username = f"{username}_{unique_suffix}"
        unique_email = f"{email_local}_{unique_suffix}@{email_domain}.com"
        
        db = next(get_db())
        try:
            user_service = UserService(db)
            
            # Create practitioner registration data
            registration_data = PractitionerRegistrationData(
                username=unique_username,
                email=unique_email,
                password=password,
                full_name=full_name,
                role="practitioner",
                professional_title=professional_title,
                bio=bio,
                specializations=specializations,
                experience_years=experience_years,
                certification_details={
                    "certification_type": "diploma",
                    "issuing_authority": "Test Authority"
                },
                price_per_hour=price_per_hour
            )
            
            # Create practitioner
            user, guru = user_service.create_practitioner(registration_data)
            
            # Create JWT token with practitioner claims
            token_data = {
                "sub": user.username,
                "user_id": user.id,
                "is_admin": user.is_admin,
                "role": user.role,
                "verification_status": user.verification_status
            }
            
            access_token = create_access_token(data=token_data)
            
            # Verify token and extract claims
            payload = verify_token(access_token)
            assert payload is not None, "Token verification failed"
            
            # Verify practitioner-specific claims
            assert payload.get("sub") == user.username, f"Username claim mismatch: {payload.get('sub')} != {user.username}"
            assert payload.get("user_id") == user.id, f"User ID claim mismatch: {payload.get('user_id')} != {user.id}"
            assert payload.get("is_admin") == False, f"Admin claim should be False for practitioners: {payload.get('is_admin')}"
            assert payload.get("role") == "practitioner", f"Role claim should be 'practitioner': {payload.get('role')}"
            assert payload.get("verification_status") == "pending_verification", f"Verification status should be 'pending_verification': {payload.get('verification_status')}"
            
            # Verify standard JWT claims are present
            assert "iat" in payload, "Missing issued-at claim"
            assert "nbf" in payload, "Missing not-before claim"
            assert "exp" in payload, "Missing expiration claim"
            
            # Verify token expiration is reasonable (should be in the future)
            import time
            current_time = int(time.time())
            exp_time = payload.get("exp")
            assert exp_time > current_time, f"Token should not be expired: exp={exp_time}, now={current_time}"
            
            # Clean up
            db.delete(guru)
            db.delete(user)
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    @given(
        role=st.sampled_from(["user", "practitioner"]),
        verification_status=st.sampled_from(["active", "pending_verification", "verified", "rejected"]),
        is_admin=st.booleans()
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10, deadline=None)
    def test_jwt_token_claims_consistency(self, role, verification_status, is_admin):
        """
        Property 10: JWT token contains correct role and verification status
        For any combination of role, verification_status, and is_admin values,
        the JWT token should accurately reflect these values in its claims.
        
        Feature: dual-user-registration, Property 10: JWT token contains correct role and verification status
        Validates: Requirements 6.2, 6.3
        """
        # Create token data with the given properties
        token_data = {
            "sub": "testuser",
            "user_id": 12345,
            "is_admin": is_admin,
            "role": role,
            "verification_status": verification_status
        }
        
        # Create and verify token
        access_token = create_access_token(data=token_data)
        payload = verify_token(access_token)
        
        assert payload is not None, "Token verification failed"
        
        # Verify all claims match exactly
        assert payload.get("sub") == "testuser", "Username claim mismatch"
        assert payload.get("user_id") == 12345, "User ID claim mismatch"
        assert payload.get("is_admin") == is_admin, f"Admin claim mismatch: expected {is_admin}, got {payload.get('is_admin')}"
        assert payload.get("role") == role, f"Role claim mismatch: expected {role}, got {payload.get('role')}"
        assert payload.get("verification_status") == verification_status, f"Verification status claim mismatch: expected {verification_status}, got {payload.get('verification_status')}"
    
    def test_jwt_token_backward_compatibility(self):
        """
        Property 10: JWT token contains correct role and verification status
        JWT tokens should maintain backward compatibility - tokens without role/verification claims
        should still be valid, and new tokens should include all required claims.
        
        Feature: dual-user-registration, Property 10: JWT token contains correct role and verification status
        Validates: Requirements 6.2, 6.3
        """
        # Test old-style token (without role/verification claims)
        old_token_data = {
            "sub": "olduser",
            "user_id": 999
        }
        
        old_token = create_access_token(data=old_token_data)
        old_payload = verify_token(old_token)
        
        assert old_payload is not None, "Old token format should still be valid"
        assert old_payload.get("sub") == "olduser", "Old token username should be preserved"
        assert old_payload.get("user_id") == 999, "Old token user_id should be preserved"
        # Role and verification_status should be None for old tokens
        assert old_payload.get("role") is None, "Old tokens should not have role claim"
        assert old_payload.get("verification_status") is None, "Old tokens should not have verification_status claim"
        
        # Test new-style token (with all claims)
        new_token_data = {
            "sub": "newuser",
            "user_id": 1000,
            "is_admin": True,
            "role": "practitioner",
            "verification_status": "verified"
        }
        
        new_token = create_access_token(data=new_token_data)
        new_payload = verify_token(new_token)
        
        assert new_payload is not None, "New token format should be valid"
        assert new_payload.get("sub") == "newuser", "New token username should be preserved"
        assert new_payload.get("user_id") == 1000, "New token user_id should be preserved"
        assert new_payload.get("is_admin") == True, "New token should have is_admin claim"
        assert new_payload.get("role") == "practitioner", "New token should have role claim"
        assert new_payload.get("verification_status") == "verified", "New token should have verification_status claim"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])