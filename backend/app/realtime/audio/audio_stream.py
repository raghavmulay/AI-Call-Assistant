"""
audio_stream.py — Async generator interface over a session's chunk buffer.

Stage 3 Part 2 STT hook: replace the `yield` body with Whisper ingestion.
"""
import asyncio
from typing import AsyncGenerator, List
from backend.app.realtime.audio.chunk_buffer import buffer_registry, BufferedChunk


async def stream_session_audio(
    session_id: str,
    poll_interval: float = 0.02,
) -> AsyncGenerator[List[BufferedChunk], None]:
    """
    Continuously yields batches of buffered chunks for a session.
    Stops when the session buffer is removed (session ended).
    """
    while True:
        buf = await buffer_registry.get(session_id)
        if buf is None:
            break
        chunks = await buf.drain()
        if chunks:
            yield chunks
        await asyncio.sleep(poll_interval)
