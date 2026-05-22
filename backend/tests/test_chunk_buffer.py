"""
test_chunk_buffer.py — SessionChunkBuffer and ChunkBufferRegistry tests.
"""
import pytest
import asyncio
from backend.app.realtime.audio.chunk_buffer import SessionChunkBuffer, ChunkBufferRegistry


@pytest.fixture
def buf():
    return SessionChunkBuffer(max_chunks=10)


@pytest.mark.asyncio
async def test_push_and_drain(buf):
    await buf.push(0, b"\x00\x01")
    await buf.push(1, b"\x02\x03")
    chunks = await buf.drain()
    assert len(chunks) == 2
    assert chunks[0].chunk_id == 0
    assert chunks[1].chunk_id == 1


@pytest.mark.asyncio
async def test_drain_clears_buffer(buf):
    await buf.push(0, b"\x00\x01")
    await buf.drain()
    assert await buf.peek_size() == 0


@pytest.mark.asyncio
async def test_out_of_order_dropped(buf):
    await buf.push(5, b"\x00\x01")
    accepted = await buf.push(3, b"\x02\x03")
    assert accepted is False
    assert buf.dropped == 1


@pytest.mark.asyncio
async def test_max_chunks_overflow(buf):
    for i in range(10):
        await buf.push(i, b"\x00\x01")
    await buf.push(10, b"\x00\x01")
    assert await buf.peek_size() == 10


@pytest.mark.asyncio
async def test_async_reset(buf):
    await buf.push(0, b"\x00\x01")
    await buf.reset()
    assert await buf.peek_size() == 0
    assert buf.dropped == 0
    # After reset, chunk_id 0 should be accepted again
    accepted = await buf.push(0, b"\x00\x01")
    assert accepted is True


@pytest.mark.asyncio
async def test_registry_isolation():
    reg = ChunkBufferRegistry()
    buf_a = await reg.get_or_create("a")
    buf_b = await reg.get_or_create("b")
    await buf_a.push(0, b"\xAA\xBB")
    chunks_b = await buf_b.drain()
    assert chunks_b == []


@pytest.mark.asyncio
async def test_registry_remove():
    reg = ChunkBufferRegistry()
    await reg.get_or_create("x")
    await reg.remove("x")
    assert await reg.get("x") is None


@pytest.mark.asyncio
async def test_registry_active_count():
    reg = ChunkBufferRegistry()
    await reg.get_or_create("c1")
    await reg.get_or_create("c2")
    assert await reg.active_count() == 2
    await reg.remove("c1")
    assert await reg.active_count() == 1


@pytest.mark.asyncio
async def test_concurrent_pushes(buf):
    await buf.reset()
    tasks = [buf.push(i, b"\x00\x01") for i in range(10)]
    results = await asyncio.gather(*tasks)
    assert all(results)


@pytest.mark.asyncio
async def test_high_throughput_stress():
    """500 sequential packets — verify none dropped and ordering preserved."""
    buf = SessionChunkBuffer(max_chunks=500)
    for i in range(500):
        accepted = await buf.push(i, b"\x00\x01")
        assert accepted is True
    chunks = await buf.drain()
    assert len(chunks) == 500
    for i, c in enumerate(chunks):
        assert c.chunk_id == i


@pytest.mark.asyncio
async def test_packet_drop_simulation():
    """Simulate out-of-order arrival — only forward-progressing chunks accepted."""
    buf = SessionChunkBuffer(max_chunks=100)
    await buf.push(0, b"\x00\x01")
    await buf.push(2, b"\x00\x01")  # gap — accepted (future chunk)
    await buf.push(1, b"\x00\x01")  # late — dropped
    assert buf.dropped == 1
    chunks = await buf.drain()
    assert len(chunks) == 2
