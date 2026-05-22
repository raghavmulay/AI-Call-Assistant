"""
core/websocket_manager.py — Scalable WebSocket connection manager.

Tracks connections per session_id (guest or user).
Supports:
  - personal messages (transcript chunks, AI responses)
  - broadcast (system-wide events)
  - typed message envelopes for the client to parse
"""

import json
from typing import Dict
from fastapi import WebSocket
from backend.core.logger import get_logger

logger = get_logger("websocket_manager")


class WebSocketManager:
    def __init__(self):
        # session_id → WebSocket
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[session_id] = ws
        logger.info("WS connected: %s  (total=%d)", session_id, len(self._connections))

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)
        logger.info("WS disconnected: %s", session_id)

    async def send(self, session_id: str, msg_type: str, data):
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_text(json.dumps({"type": msg_type, "data": data}))
            except Exception as e:
                logger.warning("WS send failed for %s: %s", session_id, e)
                self.disconnect(session_id)

    async def broadcast(self, msg_type: str, data):
        dead = []
        for sid, ws in self._connections.items():
            try:
                await ws.send_text(json.dumps({"type": msg_type, "data": data}))
            except Exception:
                dead.append(sid)
        for sid in dead:
            self.disconnect(sid)

    def is_connected(self, session_id: str) -> bool:
        return session_id in self._connections


# Singleton — imported everywhere
ws_manager = WebSocketManager()
