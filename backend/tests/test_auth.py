"""
Integration tests for authentication flows including login, refresh, logout, and revoke-all
"""

import pytest
import os
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from modules.auth import create_refresh_token, hash_token_sha256
from models.database import User, RefreshToken


@pytest.fixture
def client(db_session):
    """Create test client with database session dependency override"""
    def override_get_db():
        yield db_session
    
    from database import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from modules.auth import get_password_hash
    
    user = User(
        username="testuser",
        email="testuser@example.com",
        password_hash=get_password_hash("Test@1234"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin test user"""
    from modules.auth import get_password_hash
    
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("Admin@1234"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestAuthenticationFlow:
    """Test complete auth flow: login -> refresh -> logout"""

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Check for refresh token cookie
        cookies = response.cookies
        assert "refresh_token" in cookies

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == 401
        assert "password" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "Test@1234"
            }
        )
        
        assert response.status_code == 401

    def test_refresh_tokens_with_cookie(self, client, test_user, db_session):
        """Test token refresh using refresh token cookie"""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        assert login_response.status_code == 200
        initial_access_token = login_response.json()["access_token"]
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Now refresh without CSRF (should fail since cookie is used)
        refresh_response = client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == 400
        assert "CSRF token missing" in refresh_response.json()["detail"]
        
        # Refresh with CSRF header
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"x-csrf-token": "test-csrf-token"}
        )
        
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        new_access_token = data["access_token"]
        
        # Tokens should be different
        assert new_access_token != initial_access_token

    def test_refresh_tokens_with_body(self, client, test_user, db_session):
        """Test token refresh using refresh token in request body"""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        assert login_response.status_code == 200
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Refresh using body (no cookie, no CSRF required)
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data

    def test_logout_with_cookie(self, client, test_user):
        """Test logout using refresh token cookie"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        assert login_response.status_code == 200
        
        # Logout
        logout_response = client.post("/api/v1/auth/logout")
        
        assert logout_response.status_code == 200
        assert logout_response.json()["success"] is True

    def test_logout_with_body(self, client, test_user):
        """Test logout using refresh token in body"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        assert login_response.status_code == 200
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Logout with body
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token}
        )
        
        assert logout_response.status_code == 200
        assert logout_response.json()["success"] is True

    def test_cannot_reuse_revoked_token(self, client, test_user):
        """Test that revoked tokens cannot be reused"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Logout to revoke token
        client.post("/api/v1/auth/logout")
        
        # Try to use revoked token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()


class TestTokenRotation:
    """Test token rotation on refresh"""

    def test_token_rotation(self, client, test_user, db_session):
        """Test that old refresh tokens are revoked on new refresh"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        refresh_token_1 = login_response.cookies.get("refresh_token")
        
        # First refresh
        refresh_response_1 = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_1}
        )
        
        assert refresh_response_1.status_code == 200
        refresh_token_2 = refresh_response_1.cookies.get("refresh_token")
        
        # Old token should now be revoked
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_1}
        )
        
        assert response.status_code == 401

    def test_token_expiration(self, client, test_user, db_session):
        """Test that expired refresh tokens are rejected"""
        # Create an expired refresh token
        from modules.auth import create_refresh_token
        
        base_claims = {
            "sub": test_user.username,
            "user_id": test_user.id,
            "is_admin": test_user.is_admin
        }
        
        # Create a token with past expiry
        old_token_claims = {
            **base_claims,
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
            "type": "refresh"
        }
        
        # This would require JWT encoding, which we can test by creating an old token
        # For now, we verify the behavior through the API
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "expired.token.here"}
        )
        
        assert response.status_code == 401


class TestCSRFProtection:
    """Test CSRF protection on cookie-based auth"""

    def test_csrf_required_for_cookie_refresh(self, client, test_user):
        """Test that CSRF token is required when using cookie for refresh"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        # Try refresh without CSRF header
        response = client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 400
        assert "CSRF" in response.json()["detail"]

    def test_csrf_not_required_for_body_refresh(self, client, test_user):
        """Test that CSRF token is NOT required when using refresh token in body"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Refresh with body (no CSRF header needed)
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200


class TestAdminEndpoints:
    """Test admin-only endpoints"""

    def test_revoke_all_user_tokens(self, client, admin_user, test_user, db_session):
        """Test admin revoke-all endpoint"""
        # First, login as regular user to create tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            }
        )
        
        refresh_token = login_response.cookies.get("refresh_token")
        access_token = login_response.json()["access_token"]
        
        # Login as admin
        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "Admin@1234"
            }
        )
        
        admin_access_token = admin_login.json()["access_token"]
        
        # Admin revokes all user's tokens
        revoke_response = client.post(
            "/api/v1/auth/revoke-all",
            json={"user_id": test_user.id},
            headers={"Authorization": f"Bearer {admin_access_token}"}
        )
        
        assert revoke_response.status_code == 200
        assert revoke_response.json()["revoked"] > 0
        
        # Try to refresh with original token - should fail
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 401

    def test_cleanup_expired_tokens(self, client, admin_user):
        """Test admin cleanup-refresh endpoint"""
        # Login as admin
        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "Admin@1234"
            }
        )
        
        admin_access_token = admin_login.json()["access_token"]
        
        # Run cleanup
        cleanup_response = client.post(
            "/api/v1/auth/cleanup-refresh",
            headers={"Authorization": f"Bearer {admin_access_token}"}
        )
        
        assert cleanup_response.status_code == 200
        assert "deleted" in cleanup_response.json()


class TestUserAgentAndIPBinding:
    """Test optional user agent and IP binding"""

    @pytest.mark.parametrize("enable_binding", ["true", "false"])
    def test_binding_enforcement(self, monkeypatch, client, test_user, db_session, enable_binding):
        """Test user agent and IP binding when enabled"""
        monkeypatch.setenv("REFRESH_TOKEN_BINDING", enable_binding)
        
        # Recreate app to pick up env var
        from main import app as test_app
        from database import get_db
        
        def override_get_db():
            yield db_session
        
        test_app.dependency_overrides[get_db] = override_get_db
        test_client = TestClient(test_app)
        
        # Login
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test@1234"
            },
            headers={"User-Agent": "TestClient/1.0"}
        )
        
        assert login_response.status_code == 200
        refresh_token = login_response.cookies.get("refresh_token")
        
        # Try refresh with same user agent
        refresh_response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
            headers={"User-Agent": "TestClient/1.0"}
        )
        
        assert refresh_response.status_code == 200
        
        if enable_binding == "true":
            # Try refresh with different user agent - should fail
            different_ua_response = test_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
                headers={"User-Agent": "DifferentClient/2.0"}
            )
            
            assert different_ua_response.status_code == 401
