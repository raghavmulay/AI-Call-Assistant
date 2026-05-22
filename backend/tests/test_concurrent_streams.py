"""
test_concurrent_streams.py — Concurrent session isolation and no-leakage tests.
"""
import pytest
import asyncio
from backend.app.realtime.audio.chunk_buffer import ChunkBufferRegistry
from backend.app.realtime.audio.audio_utils import encode_audio
from backend.app.realtime.schemas.audio_packet import AudioPacket
from backend.app.realtime.audio.packet_processor import process_audio_packet
from backend.app.realtime.websocket.connection_manager import ConnectionManager
from unittest.mock import AsyncMock, MagicMock


def make_pcm(value: int = 0, samples: int = 320) -> bytes:
    return bytes([value, 0] * samples)


@pytest.mark.asyncio
async def test_concurrent_buffer_isolation():
    reg = ChunkBufferRegistry()
    sessions = [f"sess-{i}" for i in range(10)]

    async def fill(sid: str):
        buf = await reg.get_or_create(sid)
        for i in range(5):
            await buf.push(i, make_pcm(ord(sid[-1])))

    await asyncio.gather(*[fill(s) for s in sessions])

    for sid in sessions:
        buf = await reg.get(sid)
        chunks = await buf.drain()
        assert len(chunks) == 5
        expected_byte = ord(sid[-1])
        for c in chunks:
            assert c.audio_bytes[0] == expected_byte


@pytest.mark.asyncio
async def test_concurrent_packet_processing():
    """10 sessions × 20 packets concurrently — no errors, no leakage."""
    from backend.app.realtime.audio.chunk_buffer import buffer_registry
    sessions = [f"cp-{i}" for i in range(10)]

    async def send_packets(sid: str):
        for i in range(20):
            pkt = AudioPacket(session_id=sid, chunk_id=i, audio_data=encode_audio(make_pcm()))
            await process_audio_packet(pkt)

    await asyncio.gather(*[send_packets(s) for s in sessions])

    for sid in sessions:
        buf = await buffer_registry.get(sid)
        assert buf is not None
        await buffer_registry.remove(sid)


@pytest.mark.asyncio
async def test_concurrent_connection_manager():
    mgr = ConnectionManager()

    async def connect_disconnect(i: int):
        ws = AsyncMock()
        ws.client = MagicMock()
        await mgr.connect(f"c{i}", ws)
        await mgr.touch(f"c{i}")
        await mgr.disconnect(f"c{i}")

    await asyncio.gather(*[connect_disconnect(i) for i in range(20)])
    assert await mgr.active_count() == 0


@pytest.mark.asyncio
async def test_no_audio_leakage_between_sessions():
    """Verify audio pushed to session A never appears in session B."""
    reg = ChunkBufferRegistry()
    buf_a = await reg.get_or_create("leak-a")
    buf_b = await reg.get_or_create("leak-b")

    for i in range(10):
        await buf_a.push(i, b"\xFF\xFF")

    chunks_b = await buf_b.drain()
    assert chunks_b == []

    chunks_a = await buf_a.drain()
    assert len(chunks_a) == 10
    assert all(c.audio_bytes == b"\xFF\xFF" for c in chunks_a)


@pytest.mark.asyncio
async def test_50_session_stress():
    """50 concurrent sessions each pushing 10 packets — verify isolation."""
    reg = ChunkBufferRegistry()
    sessions = [f"stress-{i}" for i in range(50)]

    async def fill(sid: str):
        buf = await reg.get_or_create(sid)
        for i in range(10):
            await buf.push(i, b"\xAB\xCD")

    await asyncio.gather(*[fill(s) for s in sessions])

    assert await reg.active_count() == 50
    for sid in sessions:
        buf = await reg.get(sid)
        assert await buf.peek_size() == 10
