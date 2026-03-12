"""Tests for rate limit endpoints."""
import pytest


class TestListTiers:
    def test_returns_tiers(self, client):
        resp = client.get("/api/v1/rate-limits/tiers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_tier_has_info(self, client):
        resp = client.get("/api/v1/rate-limits/tiers")
        tier = resp.json()[0]
        assert "name" in tier or "tier" in tier


class TestCurrentTier:
    def test_no_auth_rejected(self, client):
        resp = client.get("/api/v1/rate-limits/current")
        assert resp.status_code in (401, 403)

    def test_returns_tier_for_user(self, client, auth_headers):
        resp = client.get("/api/v1/rate-limits/current", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "tier" in data
        assert "user_id" in data
