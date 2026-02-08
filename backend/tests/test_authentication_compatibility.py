"""
Property-based tests for authentication compatibility in dual user registration system.
Tests that authentication works regardless of user role.
Feature: dual-user-registration
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
import json

from main import app
from database import get_db
from models.database import User, Guru
from services.user_service import UserService
from schemas.dual_registration import UserRegistrationData, PractitionerRegistrationData


class TestAuthenticationCompatibility:
    """Property tests for authentication compatibility across user roles."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
        self.db = next(get_db())
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db.close()
    
    @given(
        role=st.sampled_from(["user", "practitioner"]),
        verification_status=st.sampled_from(["active", "pending_verification", "verified", "rejected"])
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=8, deadline=None)
    def test_authentication_works_regardless_of_user_role(self, role, verification_status):
        """
        Property 13: Authentication works regardless of user role
        For any user with valid credentials, authentication should succeed and return
        appropriate tokens and user information, regardless of their role or verification status.
        
        Feature: dual-user-registration, Property 13: Authentication works regardless of user role
        Validates: Requirements 6.1
        """
        user_service = UserService(self.db)
        
        # Create unique test data
        unique_suffix = str(datetime.now().microsecond)
        username = f"testuser_{unique_suffix}"
        email = f"test_{unique_suffix}@example.com"
        password = "TestPassword123"
        
        try:
            # Create user based on role
            if role == "user":
                user_data = UserRegistrationData(
                    username=username,
                    email=email,
                    password=password,
                    full_name="Test User",
                    role="user"
                )
                user = user_service.create_user(user_data)
                guru = None
            else:  # practitioner
                practitioner_data = PractitionerRegistrationData(
                    username=username,
                    email=email,
                    password=password,
                    full_name="Test Practitioner",
                    role="practitioner",
                    professional_title="Test Astrologer",
                    bio="Experienced astrologer with years of practice in various forms of divination and guidance.",
                    specializations=["vedic_astrology"],
                    experience_years=5,
                    certification_details={
                        "certification_type": "diploma",
                        "issuing_authority": "Test Institute"
                    },
                    languages=["english"],
                    price_per_hour=1500
                )
                user, guru = user_service.create_practitioner(practitioner_data)
            
            # Set the desired verification status
            user.verification_status = verification_status
            self.db.commit()
            self.db.refresh(user)
            
            # Test authentication via login endpoint
            login_payload = {
                "username": username,
                "password": password
            }
            
            response = self.client.post("/api/v1/auth/login", json=login_payload)
            
            # Authentication should succeed regardless of role or verification status
            assert response.status_code == 200
            
            login_data = response.json()
            
            # Verify response structure
            assert "access_token" in login_data
            assert "token_type" in login_data
            assert "expires_in" in login_data
            assert login_data["token_type"] == "bearer"
            assert isinstance(login_data["expires_in"], int)
            assert login_data["expires_in"] > 0
            
            # Verify token contains role information by using it to access profile
            headers = {"Authorization": f"Bearer {login_data['access_token']}"}
            profile_response = self.client.get("/api/v1/auth/profile", headers=headers)
            
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            
            # Verify profile contains correct role and verification status
            assert profile_data["username"] == username
            assert profile_data["email"] == email
            assert profile_data["role"] == role
            assert profile_data["verification_status"] == verification_status
            
            # Verify role-specific profile data
            if role == "practitioner" and guru:
                assert "practitioner_profile" in profile_data
                if profile_data["practitioner_profile"]:
                    assert profile_data["practitioner_profile"]["guru_id"] == guru.id
                    assert profile_data["practitioner_profile"]["professional_title"] == guru.title
            else:
                # Regular users should not have practitioner profile
                if "practitioner_profile" in profile_data:
                    assert profile_data["practitioner_profile"] is None
            
            # Test authentication with email instead of username
            email_login_payload = {
                "username": email,  # Using email in username field
                "password": password
            }
            
            email_response = self.client.post("/api/v1/auth/login", json=email_login_payload)
            assert email_response.status_code == 200
            
            email_login_data = email_response.json()
            assert "access_token" in email_login_data
            
            # Clean up
            if guru:
                self.db.delete(guru)
            self.db.delete(user)
            self.db.commit()
            
        except Exception as e:
            # Clean up on error
            try:
                if 'guru' in locals() and guru:
                    self.db.delete(guru)
                if 'user' in locals() and user:
                    self.db.delete(user)
                self.db.commit()
            except:
                self.db.rollback()
            raise e
    
    def test_authentication_with_invalid_credentials_fails_consistently(self):
        """
        Test that authentication fails consistently for invalid credentials
        regardless of user role.
        """
        # Test with non-existent user
        invalid_login = {
            "username": "nonexistent_user",
            "password": "WrongPassword123"
        }
        
        response = self.client.post("/api/v1/auth/login", json=invalid_login)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_token_contains_role_information(self):
        """
        Test that JWT tokens contain role and verification status information
        for both user types.
        """
        user_service = UserService(self.db)
        
        # Test with regular user
        unique_suffix = str(datetime.now().microsecond)
        user_data = UserRegistrationData(
            username=f"user_{unique_suffix}",
            email=f"user_{unique_suffix}@example.com",
            password="TestPassword123",
            full_name="Test User",
            role="user"
        )
        
        try:
            user = user_service.create_user(user_data)
            
            # Login and get token
            login_payload = {
                "username": user.username,
                "password": "TestPassword123"
            }
            
            response = self.client.post("/api/v1/auth/login", json=login_payload)
            assert response.status_code == 200
            
            token = response.json()["access_token"]
            
            # Use token to access protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = self.client.get("/api/v1/auth/profile", headers=headers)
            
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            
            # Verify token contains correct role information
            assert profile_data["role"] == "user"
            assert profile_data["verification_status"] == "active"
            
            # Clean up
            self.db.delete(user)
            self.db.commit()
            
        except Exception as e:
            try:
                if 'user' in locals() and user:
                    self.db.delete(user)
                self.db.commit()
            except:
                self.db.rollback()
            raise e
    
    def test_legacy_registration_compatibility(self):
        """
        Test that legacy registration endpoint still works and creates
        users with correct default role.
        """
        unique_suffix = str(datetime.now().microsecond)
        legacy_user_data = {
            "username": f"legacy_{unique_suffix}",
            "email": f"legacy_{unique_suffix}@example.com",
            "password": "TestPassword123",
            "full_name": "Legacy User"
        }
        
        try:
            # Use legacy registration endpoint
            response = self.client.post("/api/v1/auth/register/legacy", json=legacy_user_data)
            assert response.status_code == 200
            
            registration_data = response.json()
            assert "access_token" in registration_data
            assert "user_id" in registration_data
            
            # Verify user was created with correct default role
            user = self.db.query(User).filter(User.id == registration_data["user_id"]).first()
            assert user is not None
            assert user.role == "user"
            assert user.verification_status == "active"
            
            # Test login with legacy user
            login_payload = {
                "username": legacy_user_data["username"],
                "password": legacy_user_data["password"]
            }
            
            login_response = self.client.post("/api/v1/auth/login", json=login_payload)
            assert login_response.status_code == 200
            
            # Clean up
            self.db.delete(user)
            self.db.commit()
            
        except Exception as e:
            try:
                if 'user' in locals() and user:
                    self.db.delete(user)
                self.db.commit()
            except:
                self.db.rollback()
            raise e


if __name__ == "__main__":
    pytest.main([__file__, "-v"])