"""
Tests for guru booking API endpoints
"""

import pytest
from datetime import datetime, timedelta
from models.database import Guru, GuruAvailability


@pytest.fixture
def test_guru(db_session):
    """Create a test guru"""
    guru = Guru(
        name="Pandit Rajesh Kumar",
        title="Vedic Astrology Expert",
        bio="20+ years experience in Vedic astrology and Kundli analysis",
        avatar_url="https://example.com/avatar.jpg",
        specializations=["Vedic Astrology", "Career Guidance", "Marriage Matching"],
        languages=["Hindi", "English", "Sanskrit"],
        experience_years=20,
        rating=5,
        total_sessions=150,
        price_per_hour=3000,
        availability_schedule={
            "monday": ["09:00-10:00", "10:00-11:00", "14:00-15:00"],
            "tuesday": ["09:00-10:00", "10:00-11:00", "14:00-15:00"],
            "wednesday": ["09:00-10:00", "10:00-11:00", "14:00-15:00"]
        },
        is_active=True,
        personality_tags=["empathetic", "analytical"]
    )
    db_session.add(guru)
    db_session.commit()
    db_session.refresh(guru)
    return guru


@pytest.fixture
def admin_user(db_session):
    """Create an admin user"""
    from models.database import User
    from modules.auth import get_password_hash
    
    user = User(
        username="adminuser",
        email="admin@yatinveda.com",
        password_hash=get_password_hash("AdminPass123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Generate JWT token for admin user"""
    from modules.auth import create_access_token
    return create_access_token(data={
        "sub": admin_user.username, 
        "user_id": admin_user.id,
        "is_admin": True
    })


@pytest.fixture
def admin_headers(admin_token):
    """Create authorization headers for admin"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestGuruDiscovery:
    """Test guru listing and discovery endpoints"""
    
    def test_get_all_gurus(self, client, test_guru):
        """Test getting all active gurus"""
        response = client.get("/api/v1/guru-booking/gurus")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Pandit Rajesh Kumar"
        assert data[0]["price_per_hour"] == 3000
    
    def test_get_guru_details(self, client, test_guru):
        """Test getting specific guru details"""
        response = client.get(f"/api/v1/guru-booking/gurus/{test_guru.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pandit Rajesh Kumar"
        assert data["experience_years"] == 20
        assert "Vedic Astrology" in data["specializations"]
    
    def test_get_nonexistent_guru(self, client):
        """Test getting details for non-existent guru"""
        response = client.get("/api/v1/guru-booking/gurus/99999")
        assert response.status_code == 404


class TestQuizMatching:
    """Test quiz-based guru matching"""
    
    def test_get_quiz_questions(self, client):
        """Test retrieving quiz questions"""
        response = client.get("/api/v1/guru-booking/quiz")
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) > 0
    
    def test_match_gurus_from_quiz(self, client, test_guru, auth_headers):
        """Test guru matching based on quiz responses"""
        quiz_data = {
            "responses": [
                {"question_id": 1, "answer": "career"},
                {"question_id": 2, "answer": "traditional"},
                {"question_id": 4, "answer": "mid"},
                {"question_id": 5, "answer": "empathetic"}
            ]
        }
        response = client.post(
            "/api/v1/guru-booking/match",
            json=quiz_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "match_score" in data[0]
        assert data[0]["id"] == test_guru.id


class TestAvailability:
    """Test guru availability management"""
    
    def test_get_guru_availability_from_schedule(self, client, test_guru):
        """Test getting availability from guru's schedule"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = client.get(
            f"/api/v1/guru-booking/gurus/{test_guru.id}/availability",
            params={"date": tomorrow, "days": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert "availability" in data
        assert len(data["availability"]) == 1
    
    def test_set_guru_availability_requires_admin(self, client, test_guru, auth_headers):
        """Test that setting availability requires admin privileges"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        availability_data = {
            "date": tomorrow,
            "slots": ["09:00-10:00", "10:00-11:00"],
            "overwrite": False
        }
        response = client.post(
            f"/api/v1/guru-booking/gurus/{test_guru.id}/availability",
            json=availability_data,
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()
    
    def test_set_guru_availability_as_admin(self, client, test_guru, admin_headers, db_session):
        """Test admin can set guru availability"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        availability_data = {
            "date": tomorrow,
            "slots": ["09:00-10:00", "10:00-11:00"],
            "overwrite": False
        }
        response = client.post(
            f"/api/v1/guru-booking/gurus/{test_guru.id}/availability",
            json=availability_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "created_slots" in data
        assert len(data["created_slots"]) == 2
        
        # Verify in database
        target_date = datetime.strptime(tomorrow, "%Y-%m-%d")
        rows = db_session.query(GuruAvailability).filter(
            GuruAvailability.guru_id == test_guru.id,
            GuruAvailability.date == target_date
        ).all()
        assert len(rows) == 2


class TestBookingCreation:
    """Test booking creation and availability linkage"""
    
    def test_create_booking_success(self, client, test_guru, test_user, auth_headers, db_session):
        """Test successful booking creation"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "09:00-10:00",
            "duration_minutes": 60,
            "session_type": "video_call",
            "notes": "Looking for career guidance"
        }
        
        response = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["guru_id"] == test_guru.id
        assert data["time_slot"] == "09:00-10:00"
        assert data["status"] == "pending"
        assert data["payment_status"] == "pending"
        assert data["payment_amount"] == 3000  # 60 min * (3000/60)
    
    def test_create_booking_with_persisted_availability(
        self, client, test_guru, test_user, admin_headers, auth_headers, db_session
    ):
        """Test booking creation links to persisted availability row"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # First, set availability as admin
        availability_data = {
            "date": tomorrow,
            "slots": ["14:00-15:00"],
            "overwrite": False
        }
        client.post(
            f"/api/v1/guru-booking/gurus/{test_guru.id}/availability",
            json=availability_data,
            headers=admin_headers
        )
        
        # Now create booking
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "14:00-15:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        
        response = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        booking_id = response.json()["id"]
        
        # Verify availability row is now marked as booked
        target_date = datetime.strptime(tomorrow, "%Y-%m-%d")
        av_row = db_session.query(GuruAvailability).filter(
            GuruAvailability.guru_id == test_guru.id,
            GuruAvailability.date == target_date,
            GuruAvailability.time_slot == "14:00-15:00"
        ).first()
        
        assert av_row is not None
        assert av_row.is_available is False
        assert av_row.booking_id == booking_id
    
    def test_create_booking_duplicate_slot(self, client, test_guru, test_user, auth_headers):
        """Test cannot book the same slot twice"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "10:00-11:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        
        # First booking
        response1 = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # Second booking (should fail)
        response2 = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already booked" in response2.json()["detail"].lower()


class TestBookingCancellation:
    """Test booking cancellation and availability release"""
    
    def test_cancel_booking_releases_availability(
        self, client, test_guru, test_user, admin_headers, auth_headers, db_session
    ):
        """Test cancelling booking releases the availability slot"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Set availability
        availability_data = {
            "date": tomorrow,
            "slots": ["15:00-16:00"],
            "overwrite": False
        }
        client.post(
            f"/api/v1/guru-booking/gurus/{test_guru.id}/availability",
            json=availability_data,
            headers=admin_headers
        )
        
        # Create booking
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "15:00-16:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        create_response = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        booking_id = create_response.json()["id"]
        
        # Cancel booking
        cancel_response = client.patch(
            f"/api/v1/guru-booking/bookings/{booking_id}/cancel",
            headers=auth_headers
        )
        assert cancel_response.status_code == 200
        
        # Verify availability is released
        target_date = datetime.strptime(tomorrow, "%Y-%m-%d")
        av_row = db_session.query(GuruAvailability).filter(
            GuruAvailability.guru_id == test_guru.id,
            GuruAvailability.date == target_date,
            GuruAvailability.time_slot == "15:00-16:00"
        ).first()
        
        assert av_row is not None
        assert av_row.is_available is True
        assert av_row.booking_id is None
    
    def test_cancel_booking_not_owned(self, client, test_guru, test_user, second_test_user, auth_headers, second_auth_headers):
        """Test cannot cancel another user's booking"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create booking as first user
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "16:00-17:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        create_response = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        booking_id = create_response.json()["id"]
        
        # Try to cancel as second user
        cancel_response = client.patch(
            f"/api/v1/guru-booking/bookings/{booking_id}/cancel",
            headers=second_auth_headers
        )
        assert cancel_response.status_code == 404


class TestBookingReschedule:
    """Test booking reschedule functionality"""
    
    def test_reschedule_booking_success(
        self, client, test_guru, test_user, admin_headers, auth_headers, db_session
    ):
        """Test successful booking reschedule"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Set availability for both days
        for date in [tomorrow, day_after]:
            availability_data = {
                "date": date,
                "slots": ["11:00-12:00"],
                "overwrite": False
            }
            client.post(
                f"/api/v1/guru-booking/gurus/{test_guru.id}/availability",
                json=availability_data,
                headers=admin_headers
            )
        
        # Create booking
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "11:00-12:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        create_response = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        booking_id = create_response.json()["id"]
        
        # Reschedule booking
        reschedule_data = {
            "new_date": day_after,
            "new_time_slot": "11:00-12:00"
        }
        reschedule_response = client.patch(
            f"/api/v1/guru-booking/bookings/{booking_id}/reschedule",
            json=reschedule_data,
            headers=auth_headers
        )
        assert reschedule_response.status_code == 200
        data = reschedule_response.json()
        assert data["time_slot"] == "11:00-12:00"
        
        # Verify old slot is released
        old_date = datetime.strptime(tomorrow, "%Y-%m-%d")
        old_av = db_session.query(GuruAvailability).filter(
            GuruAvailability.guru_id == test_guru.id,
            GuruAvailability.date == old_date,
            GuruAvailability.time_slot == "11:00-12:00"
        ).first()
        assert old_av.is_available is True
        assert old_av.booking_id is None
        
        # Verify new slot is booked
        new_date = datetime.strptime(day_after, "%Y-%m-%d")
        new_av = db_session.query(GuruAvailability).filter(
            GuruAvailability.guru_id == test_guru.id,
            GuruAvailability.date == new_date,
            GuruAvailability.time_slot == "11:00-12:00"
        ).first()
        assert new_av.is_available is False
        assert new_av.booking_id == booking_id
    
    def test_reschedule_to_conflicting_slot(
        self, client, test_guru, test_user, second_test_user, auth_headers, second_auth_headers
    ):
        """Test cannot reschedule to already booked slot"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create two bookings
        booking_data_1 = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "13:00-14:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        booking_data_2 = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "14:00-15:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        
        response1 = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data_1,
            headers=auth_headers
        )
        booking_id_1 = response1.json()["id"]
        
        client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data_2,
            headers=second_auth_headers
        )
        
        # Try to reschedule first booking to second slot
        reschedule_data = {
            "new_date": tomorrow,
            "new_time_slot": "14:00-15:00"
        }
        reschedule_response = client.patch(
            f"/api/v1/guru-booking/bookings/{booking_id_1}/reschedule",
            json=reschedule_data,
            headers=auth_headers
        )
        assert reschedule_response.status_code == 400
        assert "already booked" in reschedule_response.json()["detail"].lower()


class TestBookingRetrieval:
    """Test booking listing and retrieval"""
    
    def test_get_user_bookings(self, client, test_guru, test_user, auth_headers):
        """Test getting user's bookings"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create booking
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "17:00-18:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        
        # Get bookings
        response = client.get(
            "/api/v1/guru-booking/bookings",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["guru_name"] == "Pandit Rajesh Kumar"
    
    def test_get_booking_details(self, client, test_guru, test_user, auth_headers):
        """Test getting specific booking details"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create booking
        booking_data = {
            "guru_id": test_guru.id,
            "booking_date": tomorrow,
            "time_slot": "18:00-19:00",
            "duration_minutes": 60,
            "session_type": "video_call"
        }
        create_response = client.post(
            "/api/v1/guru-booking/bookings",
            json=booking_data,
            headers=auth_headers
        )
        booking_id = create_response.json()["id"]
        
        # Get details
        detail_response = client.get(
            f"/api/v1/guru-booking/bookings/{booking_id}",
            headers=auth_headers
        )
        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["id"] == booking_id
        assert data["time_slot"] == "18:00-19:00"
