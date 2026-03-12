"""Tests for prescription endpoints."""
import pytest
from datetime import datetime
from models.database import User, Guru, GuruBooking, Prescription
from modules.auth import get_password_hash


@pytest.fixture
def guru_setup(db_session, test_user):
    """Create a guru user with a completed booking."""
    # Create guru user
    guru_user = User(
        username="guruji",
        email="guru@example.com",
        password_hash=get_password_hash("GuruPass123"),
        full_name="Guru Ji",
        is_active=True,
    )
    db_session.add(guru_user)
    db_session.commit()
    db_session.refresh(guru_user)

    # Create guru profile (only use columns that exist on the Guru model)
    guru = Guru(
        user_id=guru_user.id,
        name="Guru Ji",
        experience_years=10,
        is_active=True,
    )
    db_session.add(guru)
    db_session.commit()
    db_session.refresh(guru)

    # Create completed booking between guru and test_user (patient)
    booking = GuruBooking(
        user_id=test_user.id,
        guru_id=guru.id,
        booking_date=datetime(2024, 6, 1, 10, 0),
        time_slot="10:00",
        status="completed",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    return {"guru_user": guru_user, "guru": guru, "booking": booking}


@pytest.fixture
def guru_headers(guru_setup):
    from modules.auth import create_access_token
    token = create_access_token(data={"sub": guru_setup["guru_user"].username, "user_id": guru_setup["guru_user"].id})
    return {"Authorization": f"Bearer {token}"}


def _prescription_payload(booking_id: int):
    return {
        "booking_id": booking_id,
        "title": "Vedic Remedies",
        "diagnosis": "Weak Saturn in 7th house",
        "remedies": [
            {
                "category": "lal_kitab",
                "description": "Feed crows on Saturdays",
                "duration": "21 days",
                "frequency": "Weekly",
            }
        ],
        "notes": "Follow strictly for best results.",
    }


class TestCreatePrescription:
    def test_create_success(self, client, guru_headers, guru_setup):
        payload = _prescription_payload(guru_setup["booking"].id)
        resp = client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["prescription_id"] is not None
        assert data["verification_code"] is not None

    def test_create_not_guru(self, client, auth_headers, guru_setup):
        """Regular users cannot create prescriptions."""
        payload = _prescription_payload(guru_setup["booking"].id)
        resp = client.post("/api/v1/prescriptions/create", json=payload, headers=auth_headers)
        assert resp.status_code == 403

    def test_create_booking_not_completed(self, client, guru_headers, guru_setup, db_session):
        """Can only create prescription for completed bookings."""
        booking = guru_setup["booking"]
        booking.status = "pending"
        db_session.commit()
        payload = _prescription_payload(booking.id)
        resp = client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        assert resp.status_code == 400

    def test_create_no_auth(self, client, guru_setup):
        payload = _prescription_payload(guru_setup["booking"].id)
        resp = client.post("/api/v1/prescriptions/create", json=payload)
        assert resp.status_code in (401, 403)

    def test_create_nonexistent_booking(self, client, guru_headers):
        payload = _prescription_payload(99999)
        resp = client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        assert resp.status_code == 404


class TestGetPrescription:
    def _create(self, client, guru_headers, booking_id):
        payload = _prescription_payload(booking_id)
        resp = client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        return resp.json()["prescription_id"]

    def test_get_as_patient(self, client, auth_headers, guru_headers, guru_setup):
        pid = self._create(client, guru_headers, guru_setup["booking"].id)
        resp = client.get(f"/api/v1/prescriptions/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Vedic Remedies"

    def test_get_as_guru(self, client, guru_headers, guru_setup):
        pid = self._create(client, guru_headers, guru_setup["booking"].id)
        resp = client.get(f"/api/v1/prescriptions/{pid}", headers=guru_headers)
        assert resp.status_code == 200

    def test_get_unauthorized(self, client, second_auth_headers, guru_headers, guru_setup, second_test_user):
        pid = self._create(client, guru_headers, guru_setup["booking"].id)
        resp = client.get(f"/api/v1/prescriptions/{pid}", headers=second_auth_headers)
        assert resp.status_code == 403

    def test_get_not_found(self, client, auth_headers):
        resp = client.get("/api/v1/prescriptions/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestMyPrescriptions:
    def test_get_user_prescriptions(self, client, auth_headers, guru_headers, guru_setup):
        payload = _prescription_payload(guru_setup["booking"].id)
        client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        resp = client.get("/api/v1/prescriptions/user/my-prescriptions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_get_guru_prescriptions(self, client, guru_headers, guru_setup):
        payload = _prescription_payload(guru_setup["booking"].id)
        client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        resp = client.get("/api/v1/prescriptions/guru/my-created-prescriptions", headers=guru_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_get_guru_prescriptions_not_guru(self, client, auth_headers):
        resp = client.get("/api/v1/prescriptions/guru/my-created-prescriptions", headers=auth_headers)
        assert resp.status_code == 403


class TestUpdatePrescription:
    def _create(self, client, guru_headers, booking_id):
        payload = _prescription_payload(booking_id)
        resp = client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        return resp.json()["prescription_id"]

    def test_update(self, client, guru_headers, guru_setup):
        pid = self._create(client, guru_headers, guru_setup["booking"].id)
        resp = client.put(
            f"/api/v1/prescriptions/{pid}",
            json={"title": "Updated Remedies", "notes": "Updated notes"},
            headers=guru_headers,
        )
        assert resp.status_code == 200

    def test_update_not_guru(self, client, auth_headers, guru_headers, guru_setup):
        pid = self._create(client, guru_headers, guru_setup["booking"].id)
        resp = client.put(
            f"/api/v1/prescriptions/{pid}",
            json={"title": "Hack"},
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestVerifyPrescription:
    def test_verify_valid(self, client, guru_headers, guru_setup):
        payload = _prescription_payload(guru_setup["booking"].id)
        create_resp = client.post("/api/v1/prescriptions/create", json=payload, headers=guru_headers)
        code = create_resp.json()["verification_code"]
        resp = client.get(f"/api/v1/prescriptions/verify/{code}")
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

    def test_verify_invalid(self, client):
        resp = client.get("/api/v1/prescriptions/verify/FAKE-CODE-12345")
        assert resp.status_code == 200
        assert resp.json()["verified"] is False
