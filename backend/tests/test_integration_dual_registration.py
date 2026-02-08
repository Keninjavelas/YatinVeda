"""
End-to-end integration tests for dual user registration system.
Tests complete user journeys from registration to dashboard access.
Feature: dual-user-registration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
import json

from main import app
from database import get_db
from models.database import User, Guru
from modules.auth import create_access_token


class TestDualRegistrationIntegration:
    """End-to-end integration tests for dual user registration system."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
        self.db = next(get_db())
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db.close()
    
    def test_complete_user_registration_to_dashboard_flow(self):
        """
        Test complete user journey from registration to dashboard access.
        Validates the entire flow for regular users.
        """
        unique_suffix = str(datetime.now().microsecond)
        
        # Step 1: Register as regular user
        registration_data = {
            "username": f"testuser_{unique_suffix}",
            "email": f"testuser_{unique_suffix}@example.com",
            "password": "TestPassword123",
            "full_name": "Test User",
            "role": "user"
        }
        
        try:
            # Register user
            register_response = self.client.post("/api/v1/auth/register", json=registration_data)
            assert register_response.status_code == 200
            
            register_data = register_response.json()
            assert register_data["role"] == "user"
            assert register_data["verification_status"] == "active"
            assert register_data["requires_verification"] is False
            assert "access_token" in register_data
            
            user_id = register_data["user_id"]
            access_token = register_data["access_token"]
            
            # Step 2: Login with credentials
            login_response = self.client.post("/api/v1/auth/login", json={
                "username": registration_data["email"],
                "password": registration_data["password"]
            })
            assert login_response.status_code == 200
            
            login_data = login_response.json()
            assert "access_token" in login_data
            
            # Step 3: Access profile with token
            headers = {"Authorization": f"Bearer {login_data['access_token']}"}
            profile_response = self.client.get("/api/v1/auth/profile", headers=headers)
            assert profile_response.status_code == 200
            
            profile_data = profile_response.json()
            assert profile_data["username"] == registration_data["username"]
            assert profile_data["email"] == registration_data["email"]
            assert profile_data["role"] == "user"
            assert profile_data["verification_status"] == "active"
            assert profile_data["practitioner_profile"] is None
            
            # Step 4: Test role-based access control
            # Regular users should not be able to access admin endpoints
            admin_response = self.client.get("/api/v1/admin/pending-verifications", headers=headers)
            assert admin_response.status_code == 403
            
            # Clean up
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                self.db.delete(user)
                self.db.commit()
                
        except Exception as e:
            # Clean up on error
            try:
                user = self.db.query(User).filter(User.email == registration_data["email"]).first()
                if user:
                    self.db.delete(user)
                    self.db.commit()
            except:
                self.db.rollback()
            raise e
    
    def test_complete_practitioner_registration_to_verification_flow(self):
        """
        Test complete practitioner journey from registration to verification.
        Validates the entire flow for practitioners including admin verification.
        """
        unique_suffix = str(datetime.now().microsecond)
        
        # Step 1: Register as practitioner
        practitioner_data = {
            "username": f"practitioner_{unique_suffix}",
            "email": f"practitioner_{unique_suffix}@example.com",
            "password": "TestPassword123",
            "full_name": "Test Practitioner",
            "role": "practitioner",
            "professional_title": "Vedic Astrologer",
            "bio": "Experienced astrologer with 10 years of practice in Vedic astrology and horoscope reading. Specializing in birth chart analysis and future predictions.",
            "specializations": ["vedic_astrology", "horoscope_matching"],
            "experience_years": 10,
            "certification_details": {
                "certification_type": "diploma",
                "issuing_authority": "Indian Astrology Institute"
            },
            "languages": ["english", "hindi"],
            "price_per_hour": 2000
        }
        
        try:
            # Register practitioner
            register_response = self.client.post("/api/v1/auth/register", json=practitioner_data)
            assert register_response.status_code == 200
            
            register_data = register_response.json()
            assert register_data["role"] == "practitioner"
            assert register_data["verification_status"] == "pending_verification"
            assert register_data["requires_verification"] is True
            assert "access_token" in register_data
            
            user_id = register_data["user_id"]
            
            # Step 2: Login as practitioner
            login_response = self.client.post("/api/v1/auth/login", json={
                "username": practitioner_data["email"],
                "password": practitioner_data["password"]
            })
            assert login_response.status_code == 200
            
            login_data = login_response.json()
            practitioner_token = login_data["access_token"]
            
            # Step 3: Check practitioner profile
            headers = {"Authorization": f"Bearer {practitioner_token}"}
            profile_response = self.client.get("/api/v1/auth/profile", headers=headers)
            assert profile_response.status_code == 200
            
            profile_data = profile_response.json()
            assert profile_data["role"] == "practitioner"
            assert profile_data["verification_status"] == "pending_verification"
            assert profile_data["practitioner_profile"] is not None
            
            practitioner_profile = profile_data["practitioner_profile"]
            assert practitioner_profile["professional_title"] == practitioner_data["professional_title"]
            assert practitioner_profile["bio"] == practitioner_data["bio"]
            assert practitioner_profile["specializations"] == practitioner_data["specializations"]
            assert practitioner_profile["experience_years"] == practitioner_data["experience_years"]
            
            # Step 4: Create admin user for verification
            admin_user = User(
                username="admin_test",
                email="admin@test.com",
                password_hash="test_hash",
                full_name="Admin User",
                role="user",
                verification_status="active",
                is_admin=True,
                created_at=datetime.utcnow()
            )
            self.db.add(admin_user)
            self.db.commit()
            self.db.refresh(admin_user)
            
            admin_token = create_access_token(
                data={
                    "sub": admin_user.username,
                    "user_id": admin_user.id,
                    "is_admin": True,
                    "role": admin_user.role,
                    "verification_status": admin_user.verification_status
                }
            )
            
            # Step 5: Admin checks pending verifications
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            pending_response = self.client.get("/api/v1/admin/pending-verifications", headers=admin_headers)
            assert pending_response.status_code == 200
            
            pending_data = pending_response.json()
            assert len(pending_data) >= 1
            
            # Find our practitioner in the list
            our_practitioner = next((p for p in pending_data if p["user_id"] == user_id), None)
            assert our_practitioner is not None
            assert our_practitioner["is_ready_for_verification"] is True
            
            guru_id = our_practitioner["guru_id"]
            
            # Step 6: Admin approves practitioner
            verify_response = self.client.post(
                f"/api/v1/admin/verify/{guru_id}",
                headers=admin_headers,
                json={"notes": "Approved after reviewing credentials"}
            )
            assert verify_response.status_code == 200
            
            verify_data = verify_response.json()
            assert verify_data["success"] is True
            assert verify_data["verification_status"] == "verified"
            
            # Step 7: Check practitioner profile after verification
            profile_response = self.client.get("/api/v1/auth/profile", headers=headers)
            assert profile_response.status_code == 200
            
            updated_profile = profile_response.json()
            assert updated_profile["verification_status"] == "verified"
            
            # Step 8: Verify practitioner no longer appears in pending list
            pending_response = self.client.get("/api/v1/admin/pending-verifications", headers=admin_headers)
            assert pending_response.status_code == 200
            
            updated_pending = pending_response.json()
            our_practitioner_still_pending = next((p for p in updated_pending if p["user_id"] == user_id), None)
            assert our_practitioner_still_pending is None
            
            # Clean up
            guru = self.db.query(Guru).filter(Guru.user_id == user_id).first()
            user = self.db.query(User).filter(User.id == user_id).first()
            if guru:
                self.db.delete(guru)
            if user:
                self.db.delete(user)
            self.db.delete(admin_user)
            self.db.commit()
            
        except Exception as e:
            # Clean up on error
            try:
                guru = self.db.query(Guru).filter(Guru.user_id == user_id).first()
                user = self.db.query(User).filter(User.email == practitioner_data["email"]).first()
                admin_user = self.db.query(User).filter(User.email == "admin@test.com").first()
                if guru:
                    self.db.delete(guru)
                if user:
                    self.db.delete(user)
                if admin_user:
                    self.db.delete(admin_user)
                self.db.commit()
            except:
                self.db.rollback()
            raise e
    
    def test_admin_verification_workflow_end_to_end(self):
        """
        Test complete admin verification workflow from practitioner registration to rejection.
        """
        unique_suffix = str(datetime.now().microsecond)
        
        # Create practitioner
        practitioner_data = {
            "username": f"reject_test_{unique_suffix}",
            "email": f"reject_test_{unique_suffix}@example.com",
            "password": "TestPassword123",
            "full_name": "Reject Test Practitioner",
            "role": "practitioner",
            "professional_title": "Tarot Reader",
            "bio": "New tarot reader with basic experience in card reading and spiritual guidance for personal growth.",
            "specializations": ["tarot"],
            "experience_years": 2,
            "certification_details": {
                "certification_type": "certificate",
                "issuing_authority": "Local Tarot School"
            },
            "languages": ["english"],
            "price_per_hour": 1000
        }
        
        try:
            # Register practitioner
            register_response = self.client.post("/api/v1/auth/register", json=practitioner_data)
            assert register_response.status_code == 200
            
            user_id = register_response.json()["user_id"]
            
            # Create admin
            admin_user = User(
                username="admin_reject_test",
                email="admin_reject@test.com",
                password_hash="test_hash",
                full_name="Admin User",
                role="user",
                verification_status="active",
                is_admin=True,
                created_at=datetime.utcnow()
            )
            self.db.add(admin_user)
            self.db.commit()
            self.db.refresh(admin_user)
            
            admin_token = create_access_token(
                data={
                    "sub": admin_user.username,
                    "user_id": admin_user.id,
                    "is_admin": True,
                    "role": admin_user.role,
                    "verification_status": admin_user.verification_status
                }
            )
            
            # Get pending verifications
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            pending_response = self.client.get("/api/v1/admin/pending-verifications", headers=admin_headers)
            assert pending_response.status_code == 200
            
            pending_data = pending_response.json()
            our_practitioner = next((p for p in pending_data if p["user_id"] == user_id), None)
            assert our_practitioner is not None
            
            guru_id = our_practitioner["guru_id"]
            
            # Reject practitioner
            reject_response = self.client.post(
                f"/api/v1/admin/reject/{guru_id}",
                headers=admin_headers,
                json={
                    "reason": "Insufficient experience for platform requirements",
                    "notes": "Please gain more experience and reapply"
                }
            )
            assert reject_response.status_code == 200
            
            reject_data = reject_response.json()
            assert reject_data["success"] is True
            assert reject_data["verification_status"] == "rejected"
            
            # Verify practitioner status is updated
            user = self.db.query(User).filter(User.id == user_id).first()
            assert user.verification_status == "rejected"
            
            # Verify rejection info is stored
            guru = self.db.query(Guru).filter(Guru.user_id == user_id).first()
            assert "rejection_info" in guru.verification_documents
            rejection_info = guru.verification_documents["rejection_info"]
            assert rejection_info["rejection_reason"] == "Insufficient experience for platform requirements"
            assert rejection_info["rejection_notes"] == "Please gain more experience and reapply"
            
            # Clean up
            self.db.delete(guru)
            self.db.delete(user)
            self.db.delete(admin_user)
            self.db.commit()
            
        except Exception as e:
            # Clean up on error
            try:
                guru = self.db.query(Guru).filter(Guru.user_id == user_id).first()
                user = self.db.query(User).filter(User.email == practitioner_data["email"]).first()
                admin_user = self.db.query(User).filter(User.email == "admin_reject@test.com").first()
                if guru:
                    self.db.delete(guru)
                if user:
                    self.db.delete(user)
                if admin_user:
                    self.db.delete(admin_user)
                self.db.commit()
            except:
                self.db.rollback()
            raise e
    
    def test_role_based_access_control_across_all_endpoints(self):
        """
        Test role-based access control across all endpoints to ensure proper permissions.
        """
        unique_suffix = str(datetime.now().microsecond)
        
        # Create users of different types
        regular_user_data = {
            "username": f"regular_{unique_suffix}",
            "email": f"regular_{unique_suffix}@example.com",
            "password": "TestPassword123",
            "full_name": "Regular User",
            "role": "user"
        }
        
        practitioner_data = {
            "username": f"practitioner_{unique_suffix}",
            "email": f"practitioner_{unique_suffix}@example.com",
            "password": "TestPassword123",
            "full_name": "Test Practitioner",
            "role": "practitioner",
            "professional_title": "Astrologer",
            "bio": "Professional astrologer with extensive experience in birth chart analysis and predictive astrology.",
            "specializations": ["vedic_astrology"],
            "experience_years": 5,
            "certification_details": {
                "certification_type": "diploma",
                "issuing_authority": "Astrology Institute"
            },
            "languages": ["english"],
            "price_per_hour": 1500
        }
        
        try:
            # Register users
            regular_response = self.client.post("/api/v1/auth/register", json=regular_user_data)
            assert regular_response.status_code == 200
            regular_user_id = regular_response.json()["user_id"]
            regular_token = regular_response.json()["access_token"]
            
            practitioner_response = self.client.post("/api/v1/auth/register", json=practitioner_data)
            assert practitioner_response.status_code == 200
            practitioner_user_id = practitioner_response.json()["user_id"]
            practitioner_token = practitioner_response.json()["access_token"]
            
            # Create admin
            admin_user = User(
                username="admin_rbac_test",
                email="admin_rbac@test.com",
                password_hash="test_hash",
                full_name="Admin User",
                role="user",
                verification_status="active",
                is_admin=True,
                created_at=datetime.utcnow()
            )
            self.db.add(admin_user)
            self.db.commit()
            self.db.refresh(admin_user)
            
            admin_token = create_access_token(
                data={
                    "sub": admin_user.username,
                    "user_id": admin_user.id,
                    "is_admin": True,
                    "role": admin_user.role,
                    "verification_status": admin_user.verification_status
                }
            )
            
            # Test access control
            regular_headers = {"Authorization": f"Bearer {regular_token}"}
            practitioner_headers = {"Authorization": f"Bearer {practitioner_token}"}
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Regular user should access profile but not admin endpoints
            profile_response = self.client.get("/api/v1/auth/profile", headers=regular_headers)
            assert profile_response.status_code == 200
            
            admin_response = self.client.get("/api/v1/admin/pending-verifications", headers=regular_headers)
            assert admin_response.status_code == 403
            
            # Practitioner should access profile but not admin endpoints
            practitioner_profile_response = self.client.get("/api/v1/auth/profile", headers=practitioner_headers)
            assert practitioner_profile_response.status_code == 200
            
            practitioner_admin_response = self.client.get("/api/v1/admin/pending-verifications", headers=practitioner_headers)
            assert practitioner_admin_response.status_code == 403
            
            # Admin should access all endpoints
            admin_profile_response = self.client.get("/api/v1/auth/profile", headers=admin_headers)
            assert admin_profile_response.status_code == 200
            
            admin_pending_response = self.client.get("/api/v1/admin/pending-verifications", headers=admin_headers)
            assert admin_pending_response.status_code == 200
            
            admin_stats_response = self.client.get("/api/v1/admin/verification-stats", headers=admin_headers)
            assert admin_stats_response.status_code == 200
            
            # Clean up
            guru = self.db.query(Guru).filter(Guru.user_id == practitioner_user_id).first()
            regular_user = self.db.query(User).filter(User.id == regular_user_id).first()
            practitioner_user = self.db.query(User).filter(User.id == practitioner_user_id).first()
            
            if guru:
                self.db.delete(guru)
            if regular_user:
                self.db.delete(regular_user)
            if practitioner_user:
                self.db.delete(practitioner_user)
            self.db.delete(admin_user)
            self.db.commit()
            
        except Exception as e:
            # Clean up on error
            try:
                guru = self.db.query(Guru).filter(Guru.user_id == practitioner_user_id).first()
                regular_user = self.db.query(User).filter(User.email == regular_user_data["email"]).first()
                practitioner_user = self.db.query(User).filter(User.email == practitioner_data["email"]).first()
                admin_user = self.db.query(User).filter(User.email == "admin_rbac@test.com").first()
                
                if guru:
                    self.db.delete(guru)
                if regular_user:
                    self.db.delete(regular_user)
                if practitioner_user:
                    self.db.delete(practitioner_user)
                if admin_user:
                    self.db.delete(admin_user)
                self.db.commit()
            except:
                self.db.rollback()
            raise e
    
    def test_backward_compatibility_with_existing_functionality(self):
        """
        Test that existing functionality still works after dual registration implementation.
        """
        unique_suffix = str(datetime.now().microsecond)
        
        # Test legacy registration endpoint
        legacy_user_data = {
            "username": f"legacy_{unique_suffix}",
            "email": f"legacy_{unique_suffix}@example.com",
            "password": "TestPassword123",
            "full_name": "Legacy User"
        }
        
        try:
            # Use legacy registration endpoint
            legacy_response = self.client.post("/api/v1/auth/register/legacy", json=legacy_user_data)
            assert legacy_response.status_code == 200
            
            legacy_data = legacy_response.json()
            assert "access_token" in legacy_data
            assert "user_id" in legacy_data
            
            user_id = legacy_data["user_id"]
            
            # Verify user was created with correct defaults
            user = self.db.query(User).filter(User.id == user_id).first()
            assert user is not None
            assert user.role == "user"
            assert user.verification_status == "active"
            
            # Test login with legacy user
            login_response = self.client.post("/api/v1/auth/login", json={
                "username": legacy_user_data["username"],
                "password": legacy_user_data["password"]
            })
            assert login_response.status_code == 200
            
            # Test profile access
            login_data = login_response.json()
            headers = {"Authorization": f"Bearer {login_data['access_token']}"}
            profile_response = self.client.get("/api/v1/auth/profile", headers=headers)
            assert profile_response.status_code == 200
            
            profile_data = profile_response.json()
            assert profile_data["role"] == "user"
            assert profile_data["verification_status"] == "active"
            
            # Clean up
            self.db.delete(user)
            self.db.commit()
            
        except Exception as e:
            # Clean up on error
            try:
                user = self.db.query(User).filter(User.email == legacy_user_data["email"]).first()
                if user:
                    self.db.delete(user)
                    self.db.commit()
            except:
                self.db.rollback()
            raise e


if __name__ == "__main__":
    pytest.main([__file__, "-v"])