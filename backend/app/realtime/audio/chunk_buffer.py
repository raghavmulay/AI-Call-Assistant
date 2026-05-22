"""
chunk_buffer.py — Async per-session audio chunk buffer.

Maintains ordered PCM16 chunks per session.
Designed as the handoff point for STT integration in Stage 3 Part 2.
"""
import asyncio
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional
import time


@dataclass
class BufferedChunk:
    chunk_id: int
    audio_bytes: bytes
    received_at: float = field(default_factory=time.time)


class SessionChunkBuffer:
    """Async-safe buffer for a single session's audio stream."""

    def __init__(self, max_chunks: int = 200):
        self._queue: Deque[BufferedChunk] = deque(maxlen=max_chunks)
        self._lock = asyncio.Lock()
        self._next_expected: int = 0
        self.dropped: int = 0

    async def push(self, chunk_id: int, audio_bytes: bytes) -> bool:
        """Add a chunk. Returns False if dropped (out-of-order or overflow)."""
        async with self._lock:
            if chunk_id < self._next_expected:
                self.dropped += 1
                return False
            self._queue.append(BufferedChunk(chunk_id=chunk_id, audio_bytes=audio_bytes))
            self._next_expected = chunk_id + 1
            return True

    async def drain(self) -> List[BufferedChunk]:
        """Drain and return all buffered chunks in order."""
        async with self._lock:
            chunks = list(self._queue)
            self._queue.clear()
            return chunks

    async def peek_size(self) -> int:
        async with self._lock:
            return len(self._queue)

    async def reset(self):
        """Async-safe full reset — clears buffer and resets sequence counter."""
        async with self._lock:
            self._queue.clear()
            self._next_expected = 0
            self.dropped = 0

    def reset_sync(self):
        """Sync reset for use in test fixtures only (single-threaded context)."""
        self._queue.clear()
        self._next_expected = 0
        self.dropped = 0


class ChunkBufferRegistry:
    """Registry of per-session buffers. Async-safe for concurrent sessions."""

    def __init__(self):
        self._buffers: Dict[str, SessionChunkBuffer] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, session_id: str) -> SessionChunkBuffer:
        async with self._lock:
            if session_id not in self._buffers:
                self._buffers[session_id] = SessionChunkBuffer()
            return self._buffers[session_id]

    async def remove(self, session_id: str):
        async with self._lock:
            self._buffers.pop(session_id, None)

    async def get(self, session_id: str) -> Optional[SessionChunkBuffer]:
        async with self._lock:
            return self._buffers.get(session_id)

    async def active_sessions(self) -> List[str]:
        async with self._lock:
            return list(self._buffers.keys())

    async def active_count(self) -> int:
        async with self._lock:
            return len(self._buffers)


# Module-level singleton
buffer_registry = ChunkBufferRegistry()
