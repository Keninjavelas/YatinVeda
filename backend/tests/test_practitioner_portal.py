"""Tests for practitioner portal endpoints."""

from datetime import datetime, timedelta

from modules.auth import create_access_token
from models.database import User, Guru, GuruBooking


def _create_practitioner_with_guru(db_session):
    practitioner = User(
        username="practitioner1",
        email="practitioner1@example.com",
        password_hash="hash",
        full_name="Practitioner One",
        role="practitioner",
        verification_status="verified",
        is_active=True,
    )
    db_session.add(practitioner)
    db_session.commit()
    db_session.refresh(practitioner)

    guru = Guru(
        user_id=practitioner.id,
        name=practitioner.full_name,
        title="Vedic Astrologer",
        bio="Experienced practitioner",
        specializations=["career_guidance"],
        languages=["English", "Hindi"],
        experience_years=8,
        price_per_hour=1500,
        is_active=True,
    )
    db_session.add(guru)
    db_session.commit()
    db_session.refresh(guru)

    token = create_access_token(
        data={
            "sub": practitioner.username,
            "user_id": practitioner.id,
            "role": "practitioner",
        }
    )
    headers = {"Authorization": f"Bearer {token}"}

    return practitioner, guru, headers


def test_get_practitioner_profile(client, db_session):
    _, _, headers = _create_practitioner_with_guru(db_session)

    response = client.get("/api/v1/practitioner/profile", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["professional_title"] == "Vedic Astrologer"
    assert body["verification_status"] == "verified"


def test_get_practitioner_bookings(client, db_session):
    practitioner, guru, headers = _create_practitioner_with_guru(db_session)

    seeker = User(
        username="seeker1",
        email="seeker1@example.com",
        password_hash="hash",
        full_name="Seeker",
        role="user",
        verification_status="active",
        is_active=True,
    )
    db_session.add(seeker)
    db_session.commit()
    db_session.refresh(seeker)

    booking = GuruBooking(
        user_id=seeker.id,
        guru_id=guru.id,
        booking_date=datetime.utcnow() + timedelta(days=1),
        time_slot="10:00",
        duration_minutes=60,
        session_type="video_call",
        status="pending",
        payment_status="pending",
        payment_amount=250000,
    )
    db_session.add(booking)
    db_session.commit()

    response = client.get("/api/v1/practitioner/bookings?period=upcoming", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_name"] == "Seeker"
    assert body[0]["status"] == "pending"
