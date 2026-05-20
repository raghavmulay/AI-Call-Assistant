"""
websocket/notification_ws.py — Real-Time Notification WebSocket
Clients connect to ws://host/ws/notifications and receive push events.

Usage example (client-side JavaScript):
    const ws = new WebSocket("ws://localhost:8000/ws/notifications?token=<JWT>");
    ws.onmessage = (e) => console.log(JSON.parse(e.data));
"""

import json
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from backend.auth.jwt_handler import decode_access_token

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages all active WebSocket connections and broadcasts messages."""

    def __init__(self):
        # Maps user_id → WebSocket
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def send_personal(self, message: dict, user_id: str):
        """Send a message to a specific user."""
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        """Broadcast a message to ALL connected clients."""
        disconnected = []
        for uid, ws in self.active_connections.items():
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(uid)
        for uid in disconnected:
            self.disconnect(uid)


# Global manager instance (shared across the app)
manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def notification_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
):
    """
    WebSocket endpoint for real-time notifications.

    Authentication:
        Pass ?token=<JWT> as a query parameter when connecting.

    Events you may receive:
        {"type": "notice", "data": {"title": "...", "description": "..."}}
        {"type": "assignment", "data": {"title": "...", "deadline": "..."}}
        {"type": "ping", "data": "pong"}
    """
    # ── Authenticate via JWT token ────────────────────────────────────────────
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id: str = payload.get("sub", "unknown")

    # ── Accept connection ─────────────────────────────────────────────────────
    await manager.connect(websocket, user_id)
    await manager.send_personal(
        {"type": "connected", "data": f"Welcome! You are connected as {user_id}"},
        user_id,
    )

    try:
        while True:
            # Keep alive — clients can send "ping" and get "pong"
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await manager.send_personal({"type": "pong", "data": "pong"}, user_id)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(user_id)
