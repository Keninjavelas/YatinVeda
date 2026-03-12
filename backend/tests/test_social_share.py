"""Tests for social share endpoints."""
import pytest
from models.database import Chart, CommunityPost, CommunityEvent
from datetime import datetime


@pytest.fixture
def sample_chart(db_session, test_user):
    chart = Chart(
        user_id=test_user.id,
        chart_name="Test Chart",
        chart_type="natal",
        birth_details={"date": "1990-01-01", "place": "Delhi"},
        chart_data={"ascendant": "Aries"},
    )
    db_session.add(chart)
    db_session.commit()
    db_session.refresh(chart)
    return chart


@pytest.fixture
def sample_post(db_session, test_user):
    post = CommunityPost(
        user_id=test_user.id,
        title="Test Post",
        content="Post content",
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


@pytest.fixture
def sample_event(db_session, test_user):
    event = CommunityEvent(
        title="Test Event",
        description="Event desc",
        created_by=test_user.id,
        event_type="webinar",
        event_date=datetime(2025, 6, 1, 10, 0),
        location="Online",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


class TestListPlatforms:
    def test_returns_platforms(self, client):
        resp = client.get("/api/v1/share/platforms")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(p["id"] == "twitter" for p in data)
        assert any(p["id"] == "whatsapp" for p in data)


class TestGenerateShareLink:
    def test_no_auth_rejected(self, client):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "chart", "content_id": 1, "platform": "twitter"
        })
        assert resp.status_code in (401, 403)

    def test_share_chart(self, client, auth_headers, sample_chart):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "chart",
            "content_id": sample_chart.id,
            "platform": "twitter",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "twitter.com" in data["share_url"]
        assert data["platform"] == "twitter"

    def test_share_post(self, client, auth_headers, sample_post):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "post",
            "content_id": sample_post.id,
            "platform": "facebook",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert "facebook.com" in resp.json()["share_url"]

    def test_share_event(self, client, auth_headers, sample_event):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "event",
            "content_id": sample_event.id,
            "platform": "whatsapp",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert "wa.me" in resp.json()["share_url"]

    def test_share_insight(self, client, auth_headers):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "insight",
            "content_id": 0,
            "platform": "linkedin",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert "linkedin.com" in resp.json()["share_url"]

    def test_share_with_custom_message(self, client, auth_headers, sample_chart):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "chart",
            "content_id": sample_chart.id,
            "platform": "copy",
            "custom_message": "Look at my chart!",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["preview_text"] == "Look at my chart!"

    def test_invalid_platform(self, client, auth_headers):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "chart",
            "content_id": 1,
            "platform": "invalid_platform",
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_invalid_content_type(self, client, auth_headers):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "bad_type",
            "content_id": 1,
            "platform": "twitter",
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_chart_not_found(self, client, auth_headers):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "chart",
            "content_id": 99999,
            "platform": "twitter",
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_post_not_found(self, client, auth_headers):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "post",
            "content_id": 99999,
            "platform": "twitter",
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_event_not_found(self, client, auth_headers):
        resp = client.post("/api/v1/share/generate", json={
            "content_type": "event",
            "content_id": 99999,
            "platform": "twitter",
        }, headers=auth_headers)
        assert resp.status_code == 404
