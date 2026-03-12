"""Tests for cookie consent management endpoints."""

import pytest
from models.database import CookiePreference, LegalConsent as LegalConsentModel


class TestGetCookiePreferences:
    """Tests for GET /api/v1/cookies/preferences"""

    def test_anonymous_returns_defaults(self, client):
        response = client.get("/api/v1/cookies/preferences")
        assert response.status_code == 200
        data = response.json()
        assert data["essential_cookies"] is True
        assert data["is_configured"] is False

    def test_authenticated_no_prefs_returns_defaults(self, client, test_user, auth_headers):
        response = client.get("/api/v1/cookies/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False

    def test_authenticated_with_prefs(self, client, test_user, auth_headers, db_session):
        pref = CookiePreference(
            user_id=test_user.id,
            essential=True,
            functional=True,
            analytics=False,
            marketing=False,
        )
        db_session.add(pref)
        db_session.commit()

        response = client.get("/api/v1/cookies/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is True
        assert data["essential_cookies"] is True
        assert data["functional_cookies"] is True
        assert data["analytics_cookies"] is False


class TestUpdateCookiePreferences:
    """Tests for POST /api/v1/cookies/preferences"""

    def test_anonymous_returns_client_side_note(self, client):
        response = client.post(
            "/api/v1/cookies/preferences",
            json={
                "essential_cookies": True,
                "functional_cookies": True,
                "analytics_cookies": False,
                "marketing_cookies": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "browser" in data.get("note", "").lower() or "client" in data.get("note", "").lower()

    def test_authenticated_creates_prefs(self, client, test_user, auth_headers, db_session):
        response = client.post(
            "/api/v1/cookies/preferences",
            headers=auth_headers,
            json={
                "essential_cookies": True,
                "functional_cookies": True,
                "analytics_cookies": True,
                "marketing_cookies": False,
            },
        )
        assert response.status_code == 200

        pref = db_session.query(CookiePreference).filter_by(user_id=test_user.id).first()
        assert pref is not None
        assert pref.functional is True
        assert pref.analytics is True
        assert pref.marketing is False

    def test_authenticated_updates_existing_prefs(self, client, test_user, auth_headers, db_session):
        pref = CookiePreference(
            user_id=test_user.id,
            essential=True,
            functional=False,
            analytics=False,
            marketing=False,
        )
        db_session.add(pref)
        db_session.commit()

        response = client.post(
            "/api/v1/cookies/preferences",
            headers=auth_headers,
            json={
                "essential_cookies": True,
                "functional_cookies": True,
                "analytics_cookies": True,
                "marketing_cookies": True,
            },
        )
        assert response.status_code == 200

        db_session.refresh(pref)
        assert pref.functional is True
        assert pref.analytics is True
        assert pref.marketing is True

    def test_essential_cookies_forced_true(self, client):
        response = client.post(
            "/api/v1/cookies/preferences",
            json={
                "essential_cookies": False,
                "functional_cookies": False,
                "analytics_cookies": False,
                "marketing_cookies": False,
            },
        )
        assert response.status_code == 200
        # Essential should be forced to True regardless of input
        data = response.json()
        assert data["preferences"]["essential_cookies"] is True


class TestRecordConsent:
    """Tests for POST /api/v1/cookies/consent"""

    def test_record_terms_consent(self, client, test_user, auth_headers):
        response = client.post(
            "/api/v1/cookies/consent",
            headers=auth_headers,
            json={"consent_type": "terms", "consent_version": "1.0.0"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "consent_id" in data

    def test_invalid_consent_type(self, client, test_user, auth_headers):
        response = client.post(
            "/api/v1/cookies/consent",
            headers=auth_headers,
            json={"consent_type": "invalid_type", "consent_version": "1.0.0"},
        )
        assert response.status_code == 400
        assert "Invalid consent type" in response.json()["detail"]

    def test_record_consent_unauthenticated(self, client):
        response = client.post(
            "/api/v1/cookies/consent",
            json={"consent_type": "terms", "consent_version": "1.0.0"},
        )
        assert response.status_code in (401, 403)


class TestConsentHistory:
    """Tests for GET /api/v1/cookies/consent/history"""

    def test_empty_history(self, client, test_user, auth_headers):
        response = client.get("/api/v1/cookies/consent/history", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["consents"] == []

    def test_history_with_consents(self, client, test_user, auth_headers, db_session):
        consent = LegalConsentModel(
            user_id=test_user.id,
            consent_type="privacy",
            consent_version="2.0.0",
        )
        db_session.add(consent)
        db_session.commit()

        response = client.get("/api/v1/cookies/consent/history", headers=auth_headers)
        assert response.status_code == 200
        consents = response.json()["consents"]
        assert len(consents) >= 1
        assert consents[0]["consent_type"] == "privacy"
        assert consents[0]["is_active"] is True

    def test_consent_history_unauthenticated(self, client):
        response = client.get("/api/v1/cookies/consent/history")
        assert response.status_code in (401, 403)


class TestWithdrawConsent:
    """Tests for POST /api/v1/cookies/consent/{consent_type}/withdraw"""

    def test_withdraw_existing_consent(self, client, test_user, auth_headers, db_session):
        consent = LegalConsentModel(
            user_id=test_user.id,
            consent_type="marketing",
            consent_version="1.0.0",
        )
        db_session.add(consent)
        db_session.commit()

        response = client.post(
            "/api/v1/cookies/consent/marketing/withdraw",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["withdrawn_at"] is not None

    def test_withdraw_nonexistent_consent(self, client, test_user, auth_headers):
        response = client.post(
            "/api/v1/cookies/consent/terms/withdraw",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_withdraw_returns_warning_for_terms(self, client, test_user, auth_headers, db_session):
        consent = LegalConsentModel(
            user_id=test_user.id,
            consent_type="terms",
            consent_version="1.0.0",
        )
        db_session.add(consent)
        db_session.commit()

        response = client.post(
            "/api/v1/cookies/consent/terms/withdraw",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["warning"] is not None

    def test_withdraw_unauthenticated(self, client):
        response = client.post("/api/v1/cookies/consent/marketing/withdraw")
        assert response.status_code in (401, 403)
