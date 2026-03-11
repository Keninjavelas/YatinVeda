"""
WebRTC signaling module for peer-to-peer video consultations.

Provides signaling via WebSocket for establishing WebRTC connections between
practitioner and client. Uses STUN/TURN servers for NAT traversal.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import BaseModel

from modules.auth import verify_token

router = APIRouter(prefix="/video", tags=["Video Consultations"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# STUN/TURN Configuration
# ---------------------------------------------------------------------------

def get_ice_servers() -> list:
    """Return ICE server configuration for WebRTC connections."""
    import os
    turn_url = os.getenv("TURN_SERVER_URL")
    turn_user = os.getenv("TURN_SERVER_USERNAME")
    turn_credential = os.getenv("TURN_SERVER_CREDENTIAL")

    servers = [
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun1.l.google.com:19302"},
    ]

    if turn_url and turn_user and turn_credential:
        servers.append({
            "urls": turn_url,
            "username": turn_user,
            "credential": turn_credential,
        })

    return servers


# ---------------------------------------------------------------------------
# Room Management
# ---------------------------------------------------------------------------

class VideoRoom:
    """Represents a video consultation room between two parties."""

    def __init__(self, room_id: str):
        self.room_id = room_id
        self.participants: Dict[int, WebSocket] = {}
        self.created_at = datetime.utcnow()

    def is_full(self) -> bool:
        return len(self.participants) >= 2

    async def broadcast(self, sender_id: int, message: dict) -> None:
        dead = []
        for uid, ws in self.participants.items():
            if uid != sender_id:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(uid)
        for uid in dead:
            self.participants.pop(uid, None)


class VideoRoomManager:
    """Manages active video consultation rooms."""

    def __init__(self) -> None:
        self._rooms: Dict[str, VideoRoom] = {}

    def get_or_create(self, room_id: str) -> VideoRoom:
        if room_id not in self._rooms:
            self._rooms[room_id] = VideoRoom(room_id)
        return self._rooms[room_id]

    def remove_participant(self, room_id: str, user_id: int) -> None:
        room = self._rooms.get(room_id)
        if room:
            room.participants.pop(user_id, None)
            if not room.participants:
                del self._rooms[room_id]

    def get_room(self, room_id: str) -> Optional[VideoRoom]:
        return self._rooms.get(room_id)

    @property
    def active_rooms(self) -> int:
        return len(self._rooms)


video_manager = VideoRoomManager()


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

class RoomInfoResponse(BaseModel):
    room_id: str
    participant_count: int
    is_full: bool
    ice_servers: list


@router.get("/ice-servers")
async def get_ice_configuration():
    """Return ICE server configuration for WebRTC clients."""
    return {"ice_servers": get_ice_servers()}


@router.get("/room/{room_id}")
async def get_room_info(room_id: str):
    """Get information about a video room."""
    room = video_manager.get_room(room_id)
    if not room:
        return {
            "room_id": room_id,
            "participant_count": 0,
            "is_full": False,
            "ice_servers": get_ice_servers(),
        }
    return {
        "room_id": room_id,
        "participant_count": len(room.participants),
        "is_full": room.is_full(),
        "ice_servers": get_ice_servers(),
    }


@router.get("/active-rooms")
async def get_active_rooms():
    """Return count of active video rooms."""
    return {"active_rooms": video_manager.active_rooms}


# ---------------------------------------------------------------------------
# WebSocket Signaling Endpoint
# ---------------------------------------------------------------------------

@router.websocket("/signal/{room_id}")
async def video_signaling(websocket: WebSocket, room_id: str, token: str = Query(...)):
    """
    WebRTC signaling endpoint for video consultations.

    Message types:
    - offer: SDP offer from caller
    - answer: SDP answer from callee
    - ice-candidate: ICE candidate exchange
    - chat: In-call text chat
    - mute-toggle: Audio/video mute notification
    - end-call: Call termination signal
    """
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    user_id = payload.get("user_id")
    if user_id is None:
        await websocket.close(code=1008)
        return

    uid = int(user_id)
    room = video_manager.get_or_create(room_id)

    if room.is_full() and uid not in room.participants:
        await websocket.close(code=1013, reason="Room is full")
        return

    await websocket.accept()
    room.participants[uid] = websocket

    try:
        # Notify existing participant that someone joined
        await room.broadcast(uid, {
            "type": "peer-joined",
            "user_id": uid,
            "participant_count": len(room.participants),
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Send room info to the joiner
        await websocket.send_json({
            "type": "room-info",
            "room_id": room_id,
            "participant_count": len(room.participants),
            "ice_servers": get_ice_servers(),
            "timestamp": datetime.utcnow().isoformat(),
        })

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "")

            if msg_type in ("offer", "answer", "ice-candidate"):
                # Forward WebRTC signaling directly to the other participant
                await room.broadcast(uid, {
                    "type": msg_type,
                    "from_user_id": uid,
                    "data": data.get("data"),
                    "timestamp": datetime.utcnow().isoformat(),
                })

            elif msg_type == "chat":
                await room.broadcast(uid, {
                    "type": "chat",
                    "from_user_id": uid,
                    "content": data.get("content", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                })

            elif msg_type == "mute-toggle":
                await room.broadcast(uid, {
                    "type": "mute-toggle",
                    "from_user_id": uid,
                    "audio_muted": data.get("audio_muted", False),
                    "video_muted": data.get("video_muted", False),
                    "timestamp": datetime.utcnow().isoformat(),
                })

            elif msg_type == "end-call":
                await room.broadcast(uid, {
                    "type": "call-ended",
                    "from_user_id": uid,
                    "reason": data.get("reason", "user_ended"),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                break

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        video_manager.remove_participant(room_id, uid)
        # Notify remaining participant
        remaining_room = video_manager.get_room(room_id)
        if remaining_room:
            await remaining_room.broadcast(uid, {
                "type": "peer-left",
                "user_id": uid,
                "timestamp": datetime.utcnow().isoformat(),
            })
