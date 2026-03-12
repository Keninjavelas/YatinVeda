"""Tests for WebSocket endpoints and ConnectionManager."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from api.v1.websocket import ConnectionManager


# ── ConnectionManager unit tests ──────────────────────────────────

class TestConnectionManager:

    @pytest.fixture(autouse=True)
    def fresh_manager(self):
        self.mgr = ConnectionManager()

    def _mock_ws(self):
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.anyio
    async def test_connect_and_online(self):
        ws = self._mock_ws()
        await self.mgr.connect(1, ws)
        assert self.mgr.is_online(1)
        assert self.mgr.total_connections == 1
        ws.accept.assert_awaited_once()

    @pytest.mark.anyio
    async def test_disconnect(self):
        ws = self._mock_ws()
        await self.mgr.connect(1, ws)
        self.mgr.disconnect(1, ws)
        assert not self.mgr.is_online(1)
        assert self.mgr.total_connections == 0

    @pytest.mark.anyio
    async def test_send_personal(self):
        ws = self._mock_ws()
        await self.mgr.connect(1, ws)
        await self.mgr.send_personal(1, {"type": "test"})
        ws.send_json.assert_awaited_once_with({"type": "test"})

    @pytest.mark.anyio
    async def test_broadcast(self):
        ws1 = self._mock_ws()
        ws2 = self._mock_ws()
        await self.mgr.connect(1, ws1)
        await self.mgr.connect(2, ws2)
        await self.mgr.broadcast({"type": "hi"}, exclude_user=1)
        ws1.send_json.assert_not_awaited()
        ws2.send_json.assert_awaited_once()

    @pytest.mark.anyio
    async def test_room_join_and_send(self):
        ws1 = self._mock_ws()
        ws2 = self._mock_ws()
        await self.mgr.connect(1, ws1)
        await self.mgr.connect(2, ws2)
        self.mgr.join_room(1, "astro")
        self.mgr.join_room(2, "astro")
        await self.mgr.send_to_room("astro", {"type": "msg"}, exclude_user=2)
        ws1.send_json.assert_awaited_once_with({"type": "msg"})
        ws2.send_json.assert_not_awaited()

    @pytest.mark.anyio
    async def test_leave_room(self):
        ws = self._mock_ws()
        await self.mgr.connect(1, ws)
        self.mgr.join_room(1, "room1")
        self.mgr.leave_room(1, "room1")
        # Room should be cleaned up
        assert "room1" not in self.mgr._rooms

    @pytest.mark.anyio
    async def test_multiple_connections_same_user(self):
        ws1 = self._mock_ws()
        ws2 = self._mock_ws()
        await self.mgr.connect(1, ws1)
        await self.mgr.connect(1, ws2)
        assert self.mgr.total_connections == 2
        await self.mgr.send_personal(1, {"type": "test"})
        assert ws1.send_json.await_count == 1
        assert ws2.send_json.await_count == 1

    @pytest.mark.anyio
    async def test_disconnect_cleans_rooms(self):
        ws = self._mock_ws()
        await self.mgr.connect(1, ws)
        self.mgr.join_room(1, "room_a")
        self.mgr.disconnect(1, ws)
        assert "room_a" not in self.mgr._rooms


# ── WebSocket endpoint integration tests ──────────────────────────

class TestWebSocketEndpoint:

    def test_ws_rejects_invalid_token(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws/connect?token=badtoken"):
                pass

    def test_ws_connect_and_ping(self, client, test_user, test_user_token):
        with client.websocket_connect(f"/api/v1/ws/connect?token={test_user_token}") as ws:
            # Should receive connection confirmation
            data = ws.receive_json()
            assert data["type"] == "connection"
            assert data["message"] == "connected"

            # Send ping, expect pong
            ws.send_text(json.dumps({"type": "ping"}))
            pong = ws.receive_json()
            assert pong["type"] == "pong"

    def test_ws_invalid_json(self, client, test_user, test_user_token):
        with client.websocket_connect(f"/api/v1/ws/connect?token={test_user_token}") as ws:
            ws.receive_json()  # connection msg
            ws.send_text("not json at all")
            err = ws.receive_json()
            assert err["type"] == "error"
            assert "Invalid JSON" in err["message"]

    def test_ws_join_room(self, client, test_user, test_user_token):
        with client.websocket_connect(f"/api/v1/ws/connect?token={test_user_token}") as ws:
            ws.receive_json()  # connection msg
            ws.send_text(json.dumps({"type": "join_room", "room": "lobby"}))
            resp = ws.receive_json()
            assert resp["type"] == "room_joined"
            assert resp["room"] == "lobby"


# ── REST endpoints in websocket module ────────────────────────────

class TestWebSocketRestEndpoints:

    def test_online_users_endpoint(self, client):
        response = client.get("/api/v1/ws/online")
        assert response.status_code == 200
        data = response.json()
        assert "online_users" in data
        assert "count" in data

    def test_notify_user_endpoint(self, client):
        response = client.post(
            "/api/v1/ws/notify/999",
            json={"message": "hello"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["online"] is False

    def test_broadcast_endpoint(self, client):
        response = client.post(
            "/api/v1/ws/broadcast",
            json={"message": "system announcement"},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
