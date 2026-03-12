"""Tests for video consultation endpoints."""
import pytest


class TestICEServers:
    def test_returns_ice_servers(self, client):
        resp = client.get("/api/v1/video/ice-servers")
        assert resp.status_code == 200
        data = resp.json()
        assert "ice_servers" in data or "servers" in data or isinstance(data, list)

    def test_includes_stun(self, client):
        resp = client.get("/api/v1/video/ice-servers")
        data = resp.json()
        servers = data if isinstance(data, list) else data.get("servers", data.get("ice_servers", []))
        urls = str(servers)
        assert "stun:" in urls


class TestRoomInfo:
    def test_nonexistent_room(self, client):
        resp = client.get("/api/v1/video/room/nonexistent-room-id")
        # May return 404 or an empty room info
        assert resp.status_code in (200, 404)


class TestActiveRooms:
    def test_returns_list(self, client):
        resp = client.get("/api/v1/video/active-rooms")
        assert resp.status_code == 200
        data = resp.json()
        # Expect a list/dict of rooms
        assert isinstance(data, (list, dict))
