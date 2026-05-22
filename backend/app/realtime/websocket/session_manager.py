"""
session_manager.py — Real-time voice session lifecycle manager.

Distinct from Redis memory manager — this tracks LIVE connection state only.
"""
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SessionState(str, Enum):
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    CLOSED = "closed"


@dataclass
class VoiceSession:
    session_id: str
    state: SessionState = SessionState.IDLE
    created_at: float = field(default_factory=time.time)
    last_activity_at: float = field(default_factory=time.time)  # covers both idle + audio
    last_audio_at: float = 0.0
    chunks_received: int = 0
    reconnect_count: int = 0

    def mark_audio(self):
        now = time.time()
        self.last_audio_at = now
        self.last_activity_at = now
        self.chunks_received += 1
        self.state = SessionState.STREAMING

    def mark_activity(self):
        """Called on any WebSocket message (heartbeat, control) to reset idle timer."""
        self.last_activity_at = time.time()

    def mark_reconnect(self):
        self.reconnect_count += 1
        self.last_activity_at = time.time()
        self.state = SessionState.STREAMING

    def mark_paused(self):
        self.state = SessionState.PAUSED

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "state": self.state,
            "created_at": self.created_at,
            "last_activity_at": self.last_activity_at,
            "last_audio_at": self.last_audio_at,
            "chunks_received": self.chunks_received,
            "reconnect_count": self.reconnect_count,
        }


class SessionManager:
    """
    Manages live voice session state.
    SESSION_TIMEOUT applies to last_activity_at — covers both idle and streaming sessions.
    """

    SESSION_TIMEOUT = 60  # seconds of inactivity before cleanup

    def __init__(self):
        self._sessions: Dict[str, VoiceSession] = {}
        self._lock = asyncio.Lock()

    async def create(self, session_id: str) -> VoiceSession:
        async with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].mark_reconnect()
                return self._sessions[session_id]
            session = VoiceSession(session_id=session_id)
            self._sessions[session_id] = session
            return session

    async def get(self, session_id: str) -> Optional[VoiceSession]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def mark_audio(self, session_id: str):
        async with self._lock:
            s = self._sessions.get(session_id)
            if s:
                s.mark_audio()

    async def mark_activity(self, session_id: str):
        async with self._lock:
            s = self._sessions.get(session_id)
            if s:
                s.mark_activity()

    async def close(self, session_id: str):
        async with self._lock:
            s = self._sessions.pop(session_id, None)
            if s:
                s.state = SessionState.CLOSED

    async def cleanup_stale(self) -> List[str]:
        """Remove sessions inactive beyond SESSION_TIMEOUT."""
        cutoff = time.time() - self.SESSION_TIMEOUT
        async with self._lock:
            stale = [
                sid for sid, s in self._sessions.items()
                if s.last_activity_at < cutoff
            ]
            for sid in stale:
                self._sessions.pop(sid)
        return stale

    async def active_count(self) -> int:
        async with self._lock:
            return len(self._sessions)

    async def all_sessions(self) -> List[dict]:
        async with self._lock:
            return [s.to_dict() for s in self._sessions.values()]


session_manager = SessionManager()


async def run_session_cleanup(interval: float = 30.0):
    """Background task: periodically purge stale sessions."""
    from backend.app.realtime.monitoring.stream_logger import stream_logger
    from backend.app.realtime.audio.chunk_buffer import buffer_registry

    while True:
        await asyncio.sleep(interval)
        stale = await session_manager.cleanup_stale()
        for sid in stale:
            await buffer_registry.remove(sid)
            stream_logger.log_session_timeout(sid)
