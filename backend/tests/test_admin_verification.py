"""
Integration tests for admin verification endpoints.
Tests the complete admin verification workflow.
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
from services.user_service import UserService
from schemas.dual_registration import PractitionerRegistrationData


class TestAdminVerificationEndpoints:
    """Integration tests for admin verification endpoints."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.client = TestClient(app)
        self.db = next(get_db())
        
        # Create admin user
        self.admin_user = User(
            username="admin_test",
            email="admin@test.com",
            password_hash="test_hash",
            full_name="Admin User",
            role="user",
            verification_status="active",
            is_admin=True,
            created_at=datetime.utcnow()
        )
        self.db.add(self.admin_user)
        self.db.commit()
        self.db.refresh(self.admin_user)
        
        # Create admin access token
        self.admin_token = create_access_token(
            data={
                "sub": self.admin_user.username,
                "user_id": self.admin_user.id,
                "is_admin": True,
                "role": self.admin_user.role,
                "verification_status": self.admin_user.verification_status
            }
        )
        
        # Create test practitioner
        user_service = UserService(self.db)
        practitioner_data = PractitionerRegistrationData(
            username="test_practitioner",
            email="practitioner@test.com",
            password="TestPassword123",
            full_name="Test Practitioner",
            role="practitioner",
            professional_title="Vedic Astrologer",
            bio="Experienced astrologer with 10 years of practice in Vedic astrology and horoscope reading.",
            specializations=["vedic_astrology", "horoscope_matching"],
            experience_years=10,
            certification_details={
                "certification_type": "diploma",
                "issuing_authority": "Indian Astrology Institute"
            },
            languages=["english", "hindi"],
            price_per_hour=2000
        )
        
        self.test_user, self.test_guru = user_service.create_practitioner(practitioner_data)
        
    def teardown_method(self):
        """Clean up test data after each test."""
        try:
            # Clean up in reverse order of creation
            if hasattr(self, 'test_guru') and self.test_guru:
                self.db.delete(self.test_guru)
            if hasattr(self, 'test_user') and self.test_user:
                self.db.delete(self.test_user)
            if hasattr(self, 'admin_user') and self.admin_user:
                self.db.delete(self.admin_user)
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()
    
    def test_get_pending_verifications_success(self):
        """Test successful retrieval of pending verifications."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = self.client.get("/api/v1/admin/pending-verifications", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check the test practitioner is in the list
        practitioner = next((p for p in data if p["guru_id"] == self.test_guru.id), None)
        assert practitioner is not None
        assert practitioner["username"] == "test_practitioner"
        assert practitioner["verification_status"] == "pending_verification"
        assert practitioner["is_ready_for_verification"] is True
    
    def test_get_pending_verifications_unauthorized(self):
        """Test that non-admin users cannot access pending verifications."""
        # Create regular user token
        regular_token = create_access_token(
            data={
                "sub": self.test_user.username,
                "user_id": self.test_user.id,
                "is_admin": False,
                "role": self.test_user.role,
                "verification_status": self.test_user.verification_status
            }
        )
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        response = self.client.get("/api/v1/admin/pending-verifications", headers=headers)
        
        assert response.status_code == 403
        assert "admin privileges" in response.json()["detail"].lower()
    
    def test_verify_practitioner_success(self):
        """Test successful practitioner verification."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {"notes": "Approved after reviewing credentials"}
        
        response = self.client.post(
            f"/api/v1/admin/verify/{self.test_guru.id}",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Practitioner approved successfully"
        assert data["guru_id"] == self.test_guru.id
        assert data["user_id"] == self.test_user.id
        assert data["verification_status"] == "verified"
        assert data["verified_at"] is not None
        assert data["verified_by"] == self.admin_user.id
        
        # Verify database was updated
        self.db.refresh(self.test_user)
        self.db.refresh(self.test_guru)
        assert self.test_user.verification_status == "verified"
        assert self.test_guru.verified_at is not None
        assert self.test_guru.verified_by == self.admin_user.id
    
    def test_verify_practitioner_not_found(self):
        """Test verification of non-existent practitioner."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {"notes": "Test"}
        
        response = self.client.post(
            "/api/v1/admin/verify/99999",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_verify_already_verified_practitioner(self):
        """Test verification of already verified practitioner."""
        # First verify the practitioner
        self.test_user.verification_status = "verified"
        self.test_guru.verified_at = datetime.utcnow()
        self.test_guru.verified_by = self.admin_user.id
        self.db.commit()
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {"notes": "Test"}
        
        response = self.client.post(
            f"/api/v1/admin/verify/{self.test_guru.id}",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()
    
    def test_reject_practitioner_success(self):
        """Test successful practitioner rejection."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {
            "reason": "Insufficient experience documentation",
            "notes": "Please provide more detailed experience certificates"
        }
        
        response = self.client.post(
            f"/api/v1/admin/reject/{self.test_guru.id}",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Practitioner rejected"
        assert data["guru_id"] == self.test_guru.id
        assert data["user_id"] == self.test_user.id
        assert data["verification_status"] == "rejected"
        
        # Verify database was updated
        self.db.refresh(self.test_user)
        self.db.refresh(self.test_guru)
        assert self.test_user.verification_status == "rejected"
        assert "rejection_info" in self.test_guru.verification_documents
        assert self.test_guru.verification_documents["rejection_info"]["rejection_reason"] == payload["reason"]
    
    def test_reject_practitioner_without_reason(self):
        """Test rejection without providing reason."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {"reason": ""}  # Empty reason
        
        response = self.client.post(
            f"/api/v1/admin/reject/{self.test_guru.id}",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 400
        assert "reason is required" in response.json()["detail"].lower()
    
    def test_reject_verified_practitioner(self):
        """Test rejection of already verified practitioner."""
        # First verify the practitioner
        self.test_user.verification_status = "verified"
        self.test_guru.verified_at = datetime.utcnow()
        self.test_guru.verified_by = self.admin_user.id
        self.db.commit()
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        payload = {"reason": "Test rejection"}
        
        response = self.client.post(
            f"/api/v1/admin/reject/{self.test_guru.id}",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 400
        assert "cannot reject" in response.json()["detail"].lower()
    
    def test_get_verification_statistics(self):
        """Test retrieval of verification statistics."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = self.client.get("/api/v1/admin/verification-stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            "total_practitioners", "pending_verification", "verified", 
            "rejected", "recent_verifications_30_days", "verification_rate"
        ]
        for field in required_fields:
            assert field in data
            assert isinstance(data[field], (int, float))
        
        # Should have at least our test practitioner
        assert data["total_practitioners"] >= 1
        assert data["pending_verification"] >= 1
    
    def test_admin_endpoints_require_authentication(self):
        """Test that admin endpoints require authentication."""
        endpoints = [
            "/api/v1/admin/pending-verifications",
            "/api/v1/admin/verification-stats"
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Admin endpoints return 403 (Forbidden) when accessed without authentication
            # because they require admin privileges
            assert response.status_code == 403
    
    def test_incomplete_practitioner_not_ready_for_verification(self):
        """Test that incomplete practitioner profiles are marked as not ready."""
        # Create incomplete practitioner
        incomplete_user = User(
            username="incomplete_practitioner",
            email="incomplete@test.com",
            password_hash="test_hash",
            full_name="Incomplete Practitioner",
            role="practitioner",
            verification_status="pending_verification",
            created_at=datetime.utcnow()
        )
        self.db.add(incomplete_user)
        self.db.commit()
        self.db.refresh(incomplete_user)
        
        # Create incomplete guru profile (missing required fields)
        incomplete_guru = Guru(
            user_id=incomplete_user.id,
            name=incomplete_user.full_name,
            title="Test",  # Too short bio will make it incomplete
            bio="Short bio",  # Less than 50 characters
            specializations=[],  # Empty specializations
            experience_years=5,
            price_per_hour=1000
        )
        self.db.add(incomplete_guru)
        self.db.commit()
        self.db.refresh(incomplete_guru)
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = self.client.get("/api/v1/admin/pending-verifications", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            
            # Find the incomplete practitioner
            incomplete = next((p for p in data if p["guru_id"] == incomplete_guru.id), None)
            assert incomplete is not None
            assert incomplete["is_ready_for_verification"] is False
            
        finally:
            # Clean up
            self.db.delete(incomplete_guru)
            self.db.delete(incomplete_user)
            self.db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])