"""
Tests for Health check endpoints (/api/v1/health, /readiness, /liveness)
"""

import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("healthy", "degraded", "unhealthy")
        assert "uptime_seconds" in body
        assert "checks" in body
        assert "database" in body["checks"]
        assert "system" in body["checks"]

    def test_health_database_connected(self, client):
        body = client.get("/api/v1/health").json()
        db_check = body["checks"]["database"]
        assert db_check["connected"] is True
        assert db_check["status"] == "healthy"


class TestReadinessEndpoint:
    def test_readiness_returns_200(self, client):
        r = client.get("/api/v1/readiness")
        assert r.status_code == 200
        body = r.json()
        assert "ready" in body
        assert "checks" in body

    def test_readiness_db_check(self, client):
        body = client.get("/api/v1/readiness").json()
        assert "database" in body["checks"]


class TestLivenessEndpoint:
    def test_liveness_returns_200(self, client):
        r = client.get("/api/v1/liveness")
        assert r.status_code == 200
        body = r.json()
        assert body["alive"] is True
        assert "uptime_seconds" in body
