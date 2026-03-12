"""Tests for remedies endpoints."""
import pytest


class TestRemedyCategories:
    def test_no_auth_rejected(self, client):
        resp = client.get("/api/v1/remedies/categories")
        assert resp.status_code in (401, 403)

    def test_returns_categories(self, client, auth_headers):
        resp = client.get("/api/v1/remedies/categories", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "value" in data[0]


class TestPlanetRemedies:
    def test_no_auth_rejected(self, client):
        resp = client.get("/api/v1/remedies/planets/sun")
        assert resp.status_code in (401, 403)

    def test_get_sun_remedies(self, client, auth_headers):
        resp = client.get("/api/v1/remedies/planets/sun", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["planet"] == "Sun"
        assert "remedies" in data
        assert data["total"] >= 1

    def test_get_moon_remedies(self, client, auth_headers):
        resp = client.get("/api/v1/remedies/planets/moon", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["planet"] == "Moon"

    def test_nonexistent_planet(self, client, auth_headers):
        resp = client.get("/api/v1/remedies/planets/pluto", headers=auth_headers)
        assert resp.status_code == 404


class TestRecommendRemedies:
    def test_no_auth_rejected(self, client):
        resp = client.post("/api/v1/remedies/recommend", json={})
        assert resp.status_code in (401, 403)

    def test_no_chart_data(self, client, auth_headers):
        """Should fail when no chart has planet data."""
        resp = client.post(
            "/api/v1/remedies/recommend",
            json={"concerns": ["career"]},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_chart_not_found(self, client, auth_headers):
        resp = client.post(
            "/api/v1/remedies/recommend",
            json={"chart_id": 99999},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestTrackingPlan:
    def test_no_auth_rejected(self, client):
        resp = client.post("/api/v1/remedies/tracking-plan", json={"remedies": []})
        assert resp.status_code in (401, 403)

    def test_create_plan(self, client, auth_headers):
        resp = client.post(
            "/api/v1/remedies/tracking-plan",
            json={
                "remedies": [{"title": "Feed crows", "name": "Feed crows", "category": "lal_kitab", "planet": "Saturn", "duration": "21 days", "description": "Feed crows on Saturdays"}],
                "start_date": "2024-06-01",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "tracking_plan" in data

    def test_invalid_date_format(self, client, auth_headers):
        resp = client.post(
            "/api/v1/remedies/tracking-plan",
            json={"remedies": [{"name": "test"}], "start_date": "not-a-date"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
