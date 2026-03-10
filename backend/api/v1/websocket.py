"""WebSocket endpoints for real-time notifications and live updates."""

from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from modules.auth import verify_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        if user_id not in self._connections:
            return
        self._connections[user_id] = [ws for ws in self._connections[user_id] if ws != websocket]
        if not self._connections[user_id]:
            del self._connections[user_id]

    async def send_personal(self, user_id: int, message: dict) -> None:
        for ws in self._connections.get(user_id, []):
            await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/connect")
async def ws_connect(websocket: WebSocket, token: str = Query(...)):
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    user_id = payload.get("user_id")
    if user_id is None:
        await websocket.close(code=1008)
        return

    await manager.connect(int(user_id), websocket)

    try:
        await manager.send_personal(int(user_id), {"type": "connection", "message": "connected"})
        while True:
            raw = await websocket.receive_text()
            await manager.send_personal(int(user_id), {"type": "echo", "message": raw})
    except WebSocketDisconnect:
        manager.disconnect(int(user_id), websocket)


@router.post("/notify/{user_id}")
async def notify_user(user_id: int, payload: dict):
    # Lightweight server-side push endpoint for internal workflows.
    await manager.send_personal(user_id, payload)
    return {"ok": True}
