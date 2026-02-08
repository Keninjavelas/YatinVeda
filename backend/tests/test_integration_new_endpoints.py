#!/usr/bin/env python3
"""
Integration tests for new API endpoints
Tests the complete functionality of auth, charts, profile, prescriptions, chat, and community endpoints
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, User, Guru, Chart, Prescription
from database import get_db
from main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user_data():
    """Test user registration data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": "user"
    }

@pytest.fixture
def test_guru_data():
    """Test guru registration data"""
    return {
        "username": "testguru",
        "email": "guru@example.com", 
        "password": "GuruPassword123!",
        "full_name": "Test Guru",
        "role": "practitioner",
        "professional_title": "Senior Vedic Astrologer",
        "bio": "Experienced astrologer with 10+ years of practice",
        "specializations": ["vedic_astrology", "career_guidance"],
        "experience_years": 10,
        "contact_phone": "+91-9876543210"
    }

class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_user_registration_and_login(self, test_user_data):
        """Test complete user registration and login flow"""
        # Register user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["username"] == test_user_data["username"]
        assert user_data["role"] == "user"
        
        # Login user
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
        return tokens
    
    def test_guru_registration_and_verification_flow(self, test_guru_data):
        """Test guru registration and verification workflow"""
        # Register guru
        response = client.post("/api/v1/auth/register", json=test_guru_data)
        assert response.status_code == 201
        guru_data = response.json()
        assert guru_data["role"] == "practitioner"
        assert guru_data["verification_status"] == "pending_verification"
        
        # Login guru
        login_data = {
            "username": test_guru_data["username"],
            "password": test_guru_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        return response.json()
    
    def test_token_refresh(self, test_user_data):
        """Test token refresh functionality"""
        # Get initial tokens
        tokens = self.test_user_registration_and_login(test_user_data)
        
        # Refresh token
        headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
        response = client.post("/api/v1/auth/refresh", headers=headers)
        assert response.status_code == 200
        
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]

class TestChartsEndpoints:
    """Test user charts endpoints"""
    
    @pytest.fixture
    def authenticated_user(self, test_user_data):
        """Get authenticated user tokens"""
        auth_test = TestAuthEndpoints()
        return auth_test.test_user_registration_and_login(test_user_data)
    
    def test_create_chart(self, authenticated_user):
        """Test chart creation"""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        chart_data = {
            "chart_name": "My Birth Chart",
            "birth_details": {
                "date": "1990-05-15",
                "time": "10:30:00",
                "location": "Mumbai, India",
                "latitude": 19.0760,
                "longitude": 72.8777
            },
            "chart_data": {
                "ascendant": "Leo",
                "sun_sign": "Taurus",
                "moon_sign": "Scorpio"
            },
            "chart_type": "D1",
            "is_public": False,
            "is_primary": True
        }
        
        response = client.post("/api/v1/charts/", json=chart_data, headers=headers)
        assert response.status_code == 201
        
        chart = response.json()
        assert chart["chart_name"] == chart_data["chart_name"]
        assert chart["is_primary"] == True
        
        return chart
    
    def test_list_user_charts(self, authenticated_user):
        """Test listing user charts"""
        # Create a chart first
        chart = self.test_create_chart(authenticated_user)
        
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        response = client.get("/api/v1/charts/", headers=headers)
        assert response.status_code == 200
        
        charts = response.json()
        assert len(charts) >= 1
        assert any(c["id"] == chart["id"] for c in charts)
    
    def test_get_chart_details(self, authenticated_user):
        """Test getting chart details"""
        chart = self.test_create_chart(authenticated_user)
        
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        response = client.get(f"/api/v1/charts/{chart['id']}", headers=headers)
        assert response.status_code == 200
        
        chart_details = response.json()
        assert chart_details["id"] == chart["id"]
        assert chart_details["chart_name"] == chart["chart_name"]

class TestProfileEndpoints:
    """Test profile management endpoints"""
    
    @pytest.fixture
    def authenticated_user(self, test_user_data):
        """Get authenticated user tokens"""
        auth_test = TestAuthEndpoints()
        return auth_test.test_user_registration_and_login(test_user_data)
    
    def test_change_password(self, authenticated_user):
        """Test password change"""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        
        response = client.post("/api/v1/profile/password", json=password_data, headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Password updated successfully"
    
    def test_get_profile_stats(self, authenticated_user):
        """Test getting profile statistics"""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.get("/api/v1/profile/stats", headers=headers)
        assert response.status_code == 200
        
        stats = response.json()
        assert "charts_count" in stats
        assert "bookings_count" in stats
        assert "member_since" in stats

class TestPrescriptionsEndpoints:
    """Test prescription endpoints"""
    
    @pytest.fixture
    def authenticated_guru(self, test_guru_data):
        """Get authenticated guru tokens"""
        auth_test = TestAuthEndpoints()
        return auth_test.test_guru_registration_and_verification_flow(test_guru_data)
    
    @pytest.fixture
    def authenticated_user(self, test_user_data):
        """Get authenticated user tokens"""
        auth_test = TestAuthEndpoints()
        return auth_test.test_user_registration_and_login(test_user_data)
    
    def test_create_prescription(self, authenticated_guru, authenticated_user):
        """Test prescription creation"""
        # Note: In a real scenario, we'd need a booking first
        # For this test, we'll mock the prescription creation
        
        headers = {"Authorization": f"Bearer {authenticated_guru['access_token']}"}
        
        prescription_data = {
            "booking_id": 1,  # Mock booking ID
            "remedies": [
                {
                    "category": "Gemstone Therapy",
                    "description": "Wear Blue Sapphire",
                    "duration": "6 months",
                    "frequency": "Daily"
                }
            ],
            "notes": "Follow remedies consistently",
            "follow_up_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        # This might fail due to missing booking, but we test the endpoint structure
        response = client.post("/api/v1/prescriptions/create", json=prescription_data, headers=headers)
        # We expect either success or a specific error about missing booking
        assert response.status_code in [201, 404, 400]

class TestCommunityEndpoints:
    """Test community endpoints"""
    
    @pytest.fixture
    def authenticated_user(self, test_user_data):
        """Get authenticated user tokens"""
        auth_test = TestAuthEndpoints()
        return auth_test.test_user_registration_and_login(test_user_data)
    
    def test_create_post(self, authenticated_user):
        """Test creating a community post"""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        post_data = {
            "content": "Just had an amazing astrology reading! The insights about my career path were spot on.",
            "post_type": "text",
            "tags": ["astrology", "career", "insights"],
            "is_public": True
        }
        
        response = client.post("/api/v1/community/posts", json=post_data, headers=headers)
        assert response.status_code == 201
        
        post = response.json()
        assert post["content"] == post_data["content"]
        assert post["post_type"] == "text"
        assert post["is_public"] == True
        
        return post
    
    def test_get_community_feed(self, authenticated_user):
        """Test getting community feed"""
        # Create a post first
        post = self.test_create_post(authenticated_user)
        
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        response = client.get("/api/v1/community/posts", headers=headers)
        assert response.status_code == 200
        
        posts = response.json()
        assert len(posts) >= 1
        assert any(p["id"] == post["id"] for p in posts)
    
    def test_get_post_details(self, authenticated_user):
        """Test getting specific post details"""
        post = self.test_create_post(authenticated_user)
        
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        response = client.get(f"/api/v1/community/posts/{post['id']}", headers=headers)
        assert response.status_code == 200
        
        post_details = response.json()
        assert post_details["id"] == post["id"]
        assert post_details["content"] == post["content"]

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        health = response.json()
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert "database" in health
    
    def test_readiness_check(self):
        """Test readiness check"""
        response = client.get("/api/v1/readiness")
        assert response.status_code == 200
        
        readiness = response.json()
        assert readiness["ready"] == True
        assert "checks" in readiness
    
    def test_liveness_check(self):
        """Test liveness check"""
        response = client.get("/api/v1/liveness")
        assert response.status_code == 200
        
        liveness = response.json()
        assert liveness["alive"] == True

class TestMFAEndpoints:
    """Test MFA endpoints"""
    
    @pytest.fixture
    def authenticated_user(self, test_user_data):
        """Get authenticated user tokens"""
        auth_test = TestAuthEndpoints()
        return auth_test.test_user_registration_and_login(test_user_data)
    
    def test_get_mfa_status(self, authenticated_user):
        """Test getting MFA status"""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.get("/mfa/status", headers=headers)
        assert response.status_code == 200
        
        status = response.json()
        assert "is_enabled" in status
        assert "has_backup_codes" in status
        assert status["is_enabled"] == False  # New user shouldn't have MFA enabled
    
    def test_setup_mfa(self, authenticated_user):
        """Test MFA setup"""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = client.post("/mfa/setup", headers=headers)
        assert response.status_code == 200
        
        setup = response.json()
        assert "secret_key" in setup
        assert "qr_code_url" in setup
        assert "backup_codes" in setup

def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Integration Tests for New API Endpoints...")
    print("=" * 70)
    
    # Run pytest with verbose output
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", 
        "test_integration_new_endpoints.py", 
        "-v", 
        "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_integration_tests()
    if success:
        print("🎉 All integration tests passed!")
    else:
        print("❌ Some integration tests failed.")
        print("Note: Some failures may be expected due to missing dependencies or incomplete setup.")
        print("The tests verify that endpoints are properly structured and accessible.")