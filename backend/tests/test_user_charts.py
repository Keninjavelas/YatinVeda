"""
Tests for User Charts CRUD endpoints (/api/v1/charts)
"""

import pytest
from datetime import datetime


# ── helpers ──────────────────────────────────────────────────

SAMPLE_BIRTH = {"date": "1990-01-15", "time": "14:30", "place": "Delhi"}
SAMPLE_DATA = {"ascendant": "Aries", "moon_sign": "Cancer", "planets": []}


def _create_chart(client, headers, **overrides):
    payload = {
        "chart_name": overrides.get("chart_name", "My Chart"),
        "birth_details": SAMPLE_BIRTH,
        "chart_data": SAMPLE_DATA,
        "chart_type": overrides.get("chart_type", "D1"),
        "is_public": overrides.get("is_public", False),
    }
    return client.post("/api/v1/charts/", json=payload, headers=headers)


# ── Create ───────────────────────────────────────────────────

class TestCreateChart:
    def test_create_success(self, client, auth_headers):
        r = _create_chart(client, auth_headers)
        assert r.status_code == 201
        body = r.json()
        assert body["chart_name"] == "My Chart"
        assert body["birth_details"] == SAMPLE_BIRTH
        assert body["chart_data"] == SAMPLE_DATA
        assert body["chart_type"] == "D1"
        assert body["is_public"] is False
        assert "id" in body

    def test_create_public_chart(self, client, auth_headers):
        r = _create_chart(client, auth_headers, is_public=True)
        assert r.status_code == 201
        assert r.json()["is_public"] is True

    def test_create_unauthenticated(self, client):
        r = client.post("/api/v1/charts/", json={
            "chart_name": "X", "birth_details": SAMPLE_BIRTH,
            "chart_data": SAMPLE_DATA,
        })
        assert r.status_code in (401, 403)


# ── List ─────────────────────────────────────────────────────

class TestListCharts:
    def test_empty_list(self, client, auth_headers):
        r = client.get("/api/v1/charts/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_own_charts(self, client, auth_headers):
        _create_chart(client, auth_headers, chart_name="A")
        _create_chart(client, auth_headers, chart_name="B")
        r = client.get("/api/v1/charts/", headers=auth_headers)
        assert r.status_code == 200
        names = [c["chart_name"] for c in r.json()]
        assert "A" in names and "B" in names

    def test_list_does_not_show_other_user(self, client, auth_headers, second_auth_headers):
        _create_chart(client, auth_headers, chart_name="Owner Chart")
        r = client.get("/api/v1/charts/", headers=second_auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 0


# ── Get single ───────────────────────────────────────────────

class TestGetChart:
    def test_get_own_chart(self, client, auth_headers):
        create = _create_chart(client, auth_headers)
        chart_id = create.json()["id"]
        r = client.get(f"/api/v1/charts/{chart_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == chart_id

    def test_get_nonexistent(self, client, auth_headers):
        r = client.get("/api/v1/charts/99999", headers=auth_headers)
        assert r.status_code == 404

    def test_get_private_chart_other_user_forbidden(self, client, auth_headers, second_auth_headers):
        chart_id = _create_chart(client, auth_headers).json()["id"]
        r = client.get(f"/api/v1/charts/{chart_id}", headers=second_auth_headers)
        assert r.status_code == 403

    def test_get_public_chart_other_user_allowed(self, client, auth_headers, second_auth_headers):
        chart_id = _create_chart(client, auth_headers, is_public=True).json()["id"]
        r = client.get(f"/api/v1/charts/{chart_id}", headers=second_auth_headers)
        assert r.status_code == 200


# ── Update ───────────────────────────────────────────────────

class TestUpdateChart:
    def test_update_name(self, client, auth_headers):
        chart_id = _create_chart(client, auth_headers).json()["id"]
        r = client.put(
            f"/api/v1/charts/{chart_id}",
            json={"chart_name": "Renamed"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["chart_name"] == "Renamed"

    def test_update_privacy(self, client, auth_headers):
        chart_id = _create_chart(client, auth_headers).json()["id"]
        r = client.put(
            f"/api/v1/charts/{chart_id}",
            json={"is_public": True},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_public"] is True

    def test_update_other_user_forbidden(self, client, auth_headers, second_auth_headers):
        chart_id = _create_chart(client, auth_headers).json()["id"]
        r = client.put(
            f"/api/v1/charts/{chart_id}",
            json={"chart_name": "Hacked"},
            headers=second_auth_headers,
        )
        assert r.status_code == 403

    def test_update_nonexistent(self, client, auth_headers):
        r = client.put(
            "/api/v1/charts/99999",
            json={"chart_name": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 404


# ── Delete ───────────────────────────────────────────────────

class TestDeleteChart:
    def test_delete_own_chart(self, client, auth_headers):
        chart_id = _create_chart(client, auth_headers).json()["id"]
        r = client.delete(f"/api/v1/charts/{chart_id}", headers=auth_headers)
        assert r.status_code == 204
        # confirm gone
        r2 = client.get(f"/api/v1/charts/{chart_id}", headers=auth_headers)
        assert r2.status_code == 404

    def test_delete_other_user_forbidden(self, client, auth_headers, second_auth_headers):
        chart_id = _create_chart(client, auth_headers).json()["id"]
        r = client.delete(f"/api/v1/charts/{chart_id}", headers=second_auth_headers)
        assert r.status_code == 403

    def test_delete_nonexistent(self, client, auth_headers):
        r = client.delete("/api/v1/charts/99999", headers=auth_headers)
        assert r.status_code == 404
