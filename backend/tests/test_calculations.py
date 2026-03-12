"""Tests for astrology calculation endpoints."""
import pytest


CHART_REQ = {
    "birth_date": "1990-01-15",
    "birth_time": "14:30",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone_offset": 5.5,
}


class TestChartCalculation:
    def test_calculate_chart_success(self, client, auth_headers):
        resp = client.post("/api/v1/calculations/chart", json=CHART_REQ, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "ascendant" in data
        assert "planets" in data
        assert "houses" in data
        assert "dashas" in data
        assert data["calculation_method"] == "simplified"

    def test_calculate_chart_invalid_date(self, client, auth_headers):
        bad = {**CHART_REQ, "birth_date": "invalid-date"}
        resp = client.post("/api/v1/calculations/chart", json=bad, headers=auth_headers)
        assert resp.status_code == 400

    def test_calculate_chart_invalid_time(self, client, auth_headers):
        bad = {**CHART_REQ, "birth_time": "99:99"}
        resp = client.post("/api/v1/calculations/chart", json=bad, headers=auth_headers)
        assert resp.status_code == 400

    def test_calculate_chart_no_auth(self, client):
        resp = client.post("/api/v1/calculations/chart", json=CHART_REQ)
        assert resp.status_code in (401, 403)

    def test_calculate_chart_validates_latitude(self, client, auth_headers):
        bad = {**CHART_REQ, "latitude": 100}
        resp = client.post("/api/v1/calculations/chart", json=bad, headers=auth_headers)
        assert resp.status_code == 422

    def test_calculate_chart_validates_longitude(self, client, auth_headers):
        bad = {**CHART_REQ, "longitude": 200}
        resp = client.post("/api/v1/calculations/chart", json=bad, headers=auth_headers)
        assert resp.status_code == 422


class TestCompatibility:
    def test_compatibility_success(self, client, auth_headers):
        payload = {"person1": CHART_REQ, "person2": {**CHART_REQ, "birth_date": "1992-06-20", "birth_time": "08:15"}}
        resp = client.post("/api/v1/calculations/compatibility", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "person1_chart" in data
        assert "person2_chart" in data
        assert "compatibility" in data

    def test_compatibility_invalid_date(self, client, auth_headers):
        payload = {"person1": CHART_REQ, "person2": {**CHART_REQ, "birth_date": "bad"}}
        resp = client.post("/api/v1/calculations/compatibility", json=payload, headers=auth_headers)
        assert resp.status_code == 400

    def test_compatibility_no_auth(self, client):
        payload = {"person1": CHART_REQ, "person2": CHART_REQ}
        resp = client.post("/api/v1/calculations/compatibility", json=payload)
        assert resp.status_code in (401, 403)


class TestDasha:
    def test_dasha_success(self, client, auth_headers):
        resp = client.post("/api/v1/calculations/dasha", json=CHART_REQ, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "dashas" in data
        assert isinstance(data["dashas"], list)
        assert "calculation_method" in data

    def test_dasha_invalid_date(self, client, auth_headers):
        bad = {**CHART_REQ, "birth_date": "not-a-date"}
        resp = client.post("/api/v1/calculations/dasha", json=bad, headers=auth_headers)
        assert resp.status_code == 400

    def test_dasha_no_auth(self, client):
        resp = client.post("/api/v1/calculations/dasha", json=CHART_REQ)
        assert resp.status_code in (401, 403)
