"""WebSocket endpoints for real-time notifications, chat, and live updates."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import BaseModel
from modules.auth import verify_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manages WebSocket connections with room/channel support."""

    def __init__(self) -> None:
        # user_id → list of WebSocket connections
        self._connections: Dict[int, List[WebSocket]] = {}
        # room_name → set of user_ids
        self._rooms: Dict[str, Set[int]] = {}
        # Track online users
        self._online_users: Set[int] = set()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)
        self._online_users.add(user_id)
        logger.info("WebSocket connected: user_id=%s (total connections: %d)",
                     user_id, self.total_connections)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        if user_id not in self._connections:
            return
        self._connections[user_id] = [ws for ws in self._connections[user_id] if ws != websocket]
        if not self._connections[user_id]:
            del self._connections[user_id]
            self._online_users.discard(user_id)
            # Remove from all rooms
            for room in list(self._rooms.keys()):
                self._rooms[room].discard(user_id)
                if not self._rooms[room]:
                    del self._rooms[room]
        logger.info("WebSocket disconnected: user_id=%s", user_id)

    async def send_personal(self, user_id: int, message: dict) -> None:
        dead: List[WebSocket] = []
        for ws in self._connections.get(user_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        # Cleanup dead connections
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict, exclude_user: Optional[int] = None) -> None:
        """Broadcast a message to all connected users."""
        for uid in list(self._connections.keys()):
            if uid != exclude_user:
                await self.send_personal(uid, message)

    async def send_to_room(self, room: str, message: dict, exclude_user: Optional[int] = None) -> None:
        """Send a message to all users in a room/channel."""
        for uid in self._rooms.get(room, set()):
            if uid != exclude_user:
                await self.send_personal(uid, message)

    def join_room(self, user_id: int, room: str) -> None:
        self._rooms.setdefault(room, set()).add(user_id)
        logger.debug("User %s joined room %s", user_id, room)

    def leave_room(self, user_id: int, room: str) -> None:
        if room in self._rooms:
            self._rooms[room].discard(user_id)
            if not self._rooms[room]:
                del self._rooms[room]

    @property
    def online_users(self) -> Set[int]:
        return self._online_users.copy()

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())

    def is_online(self, user_id: int) -> bool:
        return user_id in self._online_users


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket Endpoints
# ---------------------------------------------------------------------------

@router.websocket("/connect")
async def ws_connect(websocket: WebSocket, token: str = Query(...)):
    """Main WebSocket connection endpoint with full message handling."""
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    user_id = payload.get("user_id")
    if user_id is None:
        await websocket.close(code=1008)
        return

    uid = int(user_id)
    await manager.connect(uid, websocket)

    try:
        # Send connection confirmation with online count
        await manager.send_personal(uid, {
            "type": "connection",
            "message": "connected",
            "online_count": len(manager.online_users),
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Notify others that user came online
        await manager.broadcast({
            "type": "user_online",
            "user_id": uid,
            "online_count": len(manager.online_users),
            "timestamp": datetime.utcnow().isoformat(),
        }, exclude_user=uid)

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal(uid, {"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "")

            if msg_type == "chat":
                # Direct message to another user
                target_id = data.get("target_user_id")
                content = data.get("content", "")
                if target_id and content:
                    chat_msg = {
                        "type": "chat",
                        "from_user_id": uid,
                        "content": content,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    await manager.send_personal(int(target_id), chat_msg)
                    # Echo back to sender as confirmation
                    await manager.send_personal(uid, {
                        **chat_msg,
                        "type": "chat_sent",
                        "target_user_id": target_id,
                    })

            elif msg_type == "join_room":
                room = data.get("room", "")
                if room:
                    manager.join_room(uid, room)
                    await manager.send_personal(uid, {
                        "type": "room_joined",
                        "room": room,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    await manager.send_to_room(room, {
                        "type": "room_user_joined",
                        "user_id": uid,
                        "room": room,
                        "timestamp": datetime.utcnow().isoformat(),
                    }, exclude_user=uid)

            elif msg_type == "leave_room":
                room = data.get("room", "")
                if room:
                    manager.leave_room(uid, room)
                    await manager.send_personal(uid, {"type": "room_left", "room": room})

            elif msg_type == "room_message":
                room = data.get("room", "")
                content = data.get("content", "")
                if room and content:
                    await manager.send_to_room(room, {
                        "type": "room_message",
                        "room": room,
                        "from_user_id": uid,
                        "content": content,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            elif msg_type == "typing":
                target_id = data.get("target_user_id")
                if target_id:
                    await manager.send_personal(int(target_id), {
                        "type": "typing",
                        "from_user_id": uid,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            elif msg_type == "ping":
                await manager.send_personal(uid, {"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            else:
                # Echo unknown message types back
                await manager.send_personal(uid, {"type": "echo", "message": raw})

    except WebSocketDisconnect:
        manager.disconnect(uid, websocket)
        # Notify others that user went offline
        await manager.broadcast({
            "type": "user_offline",
            "user_id": uid,
            "online_count": len(manager.online_users),
            "timestamp": datetime.utcnow().isoformat(),
        })


@router.post("/notify/{user_id}")
async def notify_user(user_id: int, payload: dict):
    """Server-side push notification to a specific user."""
    payload.setdefault("timestamp", datetime.utcnow().isoformat())
    payload.setdefault("type", "notification")
    await manager.send_personal(user_id, payload)
    return {"ok": True, "online": manager.is_online(user_id)}


@router.post("/broadcast")
async def broadcast_message(payload: dict):
    """Broadcast a message to all connected users (admin use)."""
    payload.setdefault("timestamp", datetime.utcnow().isoformat())
    payload.setdefault("type", "broadcast")
    await manager.broadcast(payload)
    return {"ok": True, "recipients": len(manager.online_users)}


@router.get("/online")
async def get_online_users():
    """Return list of currently connected user IDs and count."""
    return {
        "online_users": list(manager.online_users),
        "count": len(manager.online_users),
        "total_connections": manager.total_connections,
    }
