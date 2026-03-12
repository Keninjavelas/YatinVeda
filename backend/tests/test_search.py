"""Tests for search endpoints."""
import pytest
from models.database import User, Guru, CommunityPost
from modules.auth import get_password_hash


@pytest.fixture
def search_data(db_session, test_user):
    """Create searchable data."""
    # A community post by test_user
    post = CommunityPost(
        user_id=test_user.id,
        title="Vedic Moon Transit",
        content="The moon transits through Rohini nakshatra today.",
    )
    db_session.add(post)

    # A verified guru
    guru_user = User(
        username="searchguru",
        email="searchguru@example.com",
        password_hash=get_password_hash("Pass1234"),
        full_name="Search Guru Ji",
        is_active=True,
        verification_status="verified",
    )
    db_session.add(guru_user)
    db_session.commit()
    db_session.refresh(guru_user)

    guru = Guru(
        user_id=guru_user.id,
        name="Search Guru Ji",
        title="Senior Astrologer",
        bio="Expert in Vedic astrology",
        experience_years=15,
        is_active=True,
    )
    db_session.add(guru)
    db_session.commit()

    return {"post": post, "guru_user": guru_user, "guru": guru}


class TestGlobalSearch:
    def test_no_auth_rejected(self, client):
        resp = client.get("/api/v1/search/global?q=moon")
        assert resp.status_code in (401, 403)

    def test_search_all(self, client, auth_headers, search_data):
        resp = client.get("/api/v1/search/global?q=moon", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Should have at least one category populated
        assert any(k in data for k in ("users", "posts", "practitioners"))

    def test_search_posts(self, client, auth_headers, search_data):
        resp = client.get("/api/v1/search/global?q=Vedic&category=posts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "posts" in data
        assert data["posts"]["total"] >= 1

    def test_search_users(self, client, auth_headers, search_data):
        resp = client.get("/api/v1/search/global?q=testuser&category=users", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data

    def test_search_practitioners(self, client, auth_headers, search_data):
        resp = client.get(
            "/api/v1/search/global?q=Guru&category=practitioners",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "practitioners" in data

    def test_search_empty_query_rejected(self, client, auth_headers):
        resp = client.get("/api/v1/search/global?q=", headers=auth_headers)
        assert resp.status_code == 422

    def test_search_invalid_category(self, client, auth_headers):
        resp = client.get("/api/v1/search/global?q=test&category=bad", headers=auth_headers)
        assert resp.status_code == 422


class TestAutocomplete:
    def test_no_auth_rejected(self, client):
        resp = client.get("/api/v1/search/autocomplete?q=te")
        assert resp.status_code in (401, 403)

    def test_autocomplete_returns_list(self, client, auth_headers):
        resp = client.get("/api/v1/search/autocomplete?q=te", headers=auth_headers)
        assert resp.status_code == 200
        # Without Elasticsearch it returns []
        assert isinstance(resp.json(), list)
