"""Tests for GDPR compliance endpoints (data export, account deletion, download)."""

import pytest
from datetime import datetime, timedelta

from models.database import (
    DataExportRequest, GuruBooking, Wallet, Guru,
)


class TestDataExport:
    """Tests for POST /api/v1/gdpr/export-data"""

    def test_export_data_creates_request(self, client, test_user, auth_headers, db_session):
        response = client.post("/api/v1/gdpr/export-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "request_id" in data

        # Verify DB record
        req = db_session.query(DataExportRequest).filter_by(user_id=test_user.id).first()
        assert req is not None
        assert req.request_type == "export"
        assert req.status in ("pending", "processing", "completed", "failed")

    def test_export_data_duplicate_returns_409(self, client, test_user, auth_headers, db_session):
        # Create a pending export request manually
        existing = DataExportRequest(
            user_id=test_user.id,
            request_type="export",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(existing)
        db_session.commit()

        response = client.post("/api/v1/gdpr/export-data", headers=auth_headers)
        assert response.status_code == 409
        assert "already in progress" in response.json()["detail"]

    def test_export_data_allows_after_completed(self, client, test_user, auth_headers, db_session):
        # Create a completed export — should allow a new one
        completed = DataExportRequest(
            user_id=test_user.id,
            request_type="export",
            status="completed",
        )
        db_session.add(completed)
        db_session.commit()

        response = client.post("/api/v1/gdpr/export-data", headers=auth_headers)
        assert response.status_code == 200

    def test_export_data_unauthenticated(self, client):
        response = client.post("/api/v1/gdpr/export-data")
        assert response.status_code in (401, 403)


class TestAccountDeletion:
    """Tests for DELETE /api/v1/gdpr/delete-account"""

    def test_delete_account_success(self, client, test_user, auth_headers, db_session):
        response = client.delete("/api/v1/gdpr/delete-account", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "deleted_at" in data

    def test_delete_blocked_by_active_booking(self, client, test_user, auth_headers, db_session):
        # Create a guru first (booking requires guru_id FK)
        guru = Guru(name="Test Guru", is_active=True)
        db_session.add(guru)
        db_session.commit()
        db_session.refresh(guru)

        booking = GuruBooking(
            user_id=test_user.id,
            guru_id=guru.id,
            booking_date=datetime.utcnow() + timedelta(days=1),
            time_slot="10:00-11:00",
            status="confirmed",
        )
        db_session.add(booking)
        db_session.commit()

        response = client.delete("/api/v1/gdpr/delete-account", headers=auth_headers)
        assert response.status_code == 400
        assert "active bookings" in response.json()["detail"]

    def test_delete_blocked_by_wallet_balance(self, client, test_user, auth_headers, db_session):
        wallet = Wallet(
            user_id=test_user.id,
            balance=500,  # 500 paise = ₹5
            currency="INR",
        )
        db_session.add(wallet)
        db_session.commit()

        response = client.delete("/api/v1/gdpr/delete-account", headers=auth_headers)
        assert response.status_code == 400
        assert "wallet balance" in response.json()["detail"]

    def test_delete_allowed_with_zero_wallet(self, client, test_user, auth_headers, db_session):
        wallet = Wallet(
            user_id=test_user.id,
            balance=0,
            currency="INR",
        )
        db_session.add(wallet)
        db_session.commit()

        response = client.delete("/api/v1/gdpr/delete-account", headers=auth_headers)
        assert response.status_code == 200

    def test_delete_allowed_with_cancelled_bookings(self, client, test_user, auth_headers, db_session):
        guru = Guru(name="Test Guru", is_active=True)
        db_session.add(guru)
        db_session.commit()
        db_session.refresh(guru)

        booking = GuruBooking(
            user_id=test_user.id,
            guru_id=guru.id,
            booking_date=datetime.utcnow() + timedelta(days=1),
            time_slot="10:00-11:00",
            status="cancelled",
        )
        db_session.add(booking)
        db_session.commit()

        response = client.delete("/api/v1/gdpr/delete-account", headers=auth_headers)
        assert response.status_code == 200

    def test_delete_unauthenticated(self, client):
        response = client.delete("/api/v1/gdpr/delete-account")
        assert response.status_code in (401, 403)


class TestDownloadExport:
    """Tests for GET /api/v1/gdpr/download/{request_id}"""

    def test_download_not_found(self, client, test_user, auth_headers):
        response = client.get("/api/v1/gdpr/download/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_download_not_ready(self, client, test_user, auth_headers, db_session):
        req = DataExportRequest(
            user_id=test_user.id,
            request_type="export",
            status="processing",
        )
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)

        response = client.get(f"/api/v1/gdpr/download/{req.id}", headers=auth_headers)
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"]

    def test_download_expired(self, client, test_user, auth_headers, db_session):
        req = DataExportRequest(
            user_id=test_user.id,
            request_type="export",
            status="completed",
            file_url="/some/path",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)

        response = client.get(f"/api/v1/gdpr/download/{req.id}", headers=auth_headers)
        assert response.status_code == 410

    def test_download_completed_success(self, client, test_user, auth_headers, db_session):
        req = DataExportRequest(
            user_id=test_user.id,
            request_type="export",
            status="completed",
            file_url="/api/v1/gdpr/download/test",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)

        response = client.get(f"/api/v1/gdpr/download/{req.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "file_url" in data

    def test_download_other_users_export_returns_404(self, client, test_user, auth_headers, db_session, second_test_user):
        # Create export for second_test_user
        req = DataExportRequest(
            user_id=second_test_user.id,
            request_type="export",
            status="completed",
            file_url="/some/path",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)

        # First user tries to access — should not find it
        response = client.get(f"/api/v1/gdpr/download/{req.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_download_unauthenticated(self, client):
        response = client.get("/api/v1/gdpr/download/1")
        assert response.status_code in (401, 403)
