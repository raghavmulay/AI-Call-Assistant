"""
test_memory.py — MemoryManager tests with mocked Redis.
"""
import pytest
from unittest.mock import patch, AsyncMock
from backend.app.ai.orchestrator.memory_manager import MemoryManager


def make_mock_redis():
    """In-memory Redis mock that stores data in a dict."""
    store = {}
    meta = {}

    mock = AsyncMock()
    mock.lrange = AsyncMock(side_effect=lambda k, s, e: store.get(k, []))
    mock.rpush = AsyncMock(side_effect=lambda k, v: store.setdefault(k, []).append(v))
    mock.ltrim = AsyncMock()
    mock.hgetall = AsyncMock(side_effect=lambda k: meta.get(k, {}))
    mock.hset = AsyncMock(side_effect=lambda k, mapping: meta.update({k: {**meta.get(k, {}), **mapping}}))
    mock.expire = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture(autouse=True)
def mock_redis_client():
    mock = make_mock_redis()
    with patch("backend.app.ai.memory.redis_memory.redis_client") as rc:
        rc.client = mock
        yield rc


@pytest.mark.asyncio
async def test_session_persistence():
    mm = MemoryManager()
    session_id = "test-123"
    await mm.add_turn(session_id, "user", "hello")
    await mm.add_turn(session_id, "assistant", "hi there")

    history = await mm.get_history(session_id)
    assert len(history) == 2
    assert history[0]["content"] == "hello"


@pytest.mark.asyncio
async def test_entity_tracking():
    mm = MemoryManager()
    session_id = "test-456"
    await mm.update_metadata(session_id, branch="IT", last_intent="fees")

    meta = await mm.get_metadata(session_id)
    assert meta["branch"] == "IT"
    assert meta["last_intent"] == "fees"


@pytest.mark.asyncio
async def test_history_window_limit():
    mm = MemoryManager()
    session_id = "test-limit"
    for i in range(10):
        await mm.add_turn(session_id, "user", f"msg {i}")

    history = await mm.get_history(session_id)
    assert len(history) <= 20
    assert history[-1]["content"] == "msg 9"
