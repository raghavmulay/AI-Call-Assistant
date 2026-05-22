"""
connection_manager.py — Async-safe WebSocket connection registry.
"""
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
from fastapi import WebSocket


class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


@dataclass
class ConnectionRecord:
    session_id: str
    websocket: WebSocket
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    def touch(self):
        self.last_activity = time.time()


class ConnectionManager:
    """
    Manages all active WebSocket connections.
    Async-safe via asyncio.Lock — supports concurrent sessions.
    """

    def __init__(self):
        self._connections: Dict[str, ConnectionRecord] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> ConnectionRecord:
        await websocket.accept()
        async with self._lock:
            record = ConnectionRecord(
                session_id=session_id,
                websocket=websocket,
                state=ConnectionState.ACTIVE,
            )
            self._connections[session_id] = record
        return record

    async def disconnect(self, session_id: str):
        async with self._lock:
            record = self._connections.pop(session_id, None)
            if record:
                record.state = ConnectionState.CLOSED

    async def get(self, session_id: str) -> Optional[ConnectionRecord]:
        async with self._lock:
            return self._connections.get(session_id)

    async def touch(self, session_id: str):
        async with self._lock:
            record = self._connections.get(session_id)
            if record:
                record.touch()

    async def send_json(self, session_id: str, data: dict):
        record = await self.get(session_id)
        if record and record.state == ConnectionState.ACTIVE:
            await record.websocket.send_json(data)

    async def send_bytes(self, session_id: str, data: bytes):
        """Binary send — reserved for Stage 3 Part 2 TTS audio responses."""
        record = await self.get(session_id)
        if record and record.state == ConnectionState.ACTIVE:
            await record.websocket.send_bytes(data)

    async def broadcast_json(self, data: dict):
        async with self._lock:
            sessions = list(self._connections.values())
        for record in sessions:
            if record.state == ConnectionState.ACTIVE:
                try:
                    await record.websocket.send_json(data)
                except Exception:
                    pass

    async def active_count(self) -> int:
        async with self._lock:
            return len(self._connections)

    async def active_sessions(self) -> list:
        async with self._lock:
            return list(self._connections.keys())


connection_manager = ConnectionManager()
