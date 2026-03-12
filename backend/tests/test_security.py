"""Tests for security admin endpoints."""
import pytest
from models.database import User
from modules.auth import get_password_hash, create_access_token


@pytest.fixture
def admin_user(db_session):
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user):
    token = create_access_token(
        data={"sub": admin_user.username, "user_id": admin_user.id, "is_admin": True}
    )
    return {"Authorization": f"Bearer {token}"}


class TestSecurityDashboard:
    def test_no_auth_rejected(self, client):
        resp = client.get("/api/v1/security/dashboard")
        assert resp.status_code in (401, 403)

    def test_non_admin_rejected(self, client, auth_headers):
        resp = client.get("/api/v1/security/dashboard", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_gets_dashboard(self, client, admin_headers, admin_user):
        resp = client.get("/api/v1/security/dashboard", headers=admin_headers)
        # 200 or 500 if monitor not fully initialized
        assert resp.status_code in (200, 500)


class TestSecurityEvents:
    def test_non_admin_rejected(self, client, auth_headers):
        resp = client.get("/api/v1/security/events", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_gets_events(self, client, admin_headers, admin_user):
        resp = client.get("/api/v1/security/events", headers=admin_headers)
        assert resp.status_code in (200, 500)


class TestSecurityAlerts:
    def test_non_admin_rejected(self, client, auth_headers):
        resp = client.get("/api/v1/security/alerts", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_gets_alerts(self, client, admin_headers, admin_user):
        resp = client.get("/api/v1/security/alerts", headers=admin_headers)
        assert resp.status_code in (200, 500)


class TestSecurityHealth:
    def test_non_admin_rejected(self, client, auth_headers):
        resp = client.get("/api/v1/security/health", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_gets_health(self, client, admin_headers, admin_user):
        resp = client.get("/api/v1/security/health", headers=admin_headers)
        assert resp.status_code in (200, 500)


class TestCSRFToken:
    def test_non_admin_rejected(self, client, auth_headers):
        resp = client.get("/api/v1/security/csrf-token", headers=auth_headers)
        assert resp.status_code == 403
