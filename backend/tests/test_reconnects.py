"""
test_reconnects.py — WebSocket reconnect recovery and session timeout tests.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from backend.app.realtime.websocket.session_manager import SessionManager, SessionState
from backend.app.realtime.websocket.connection_manager import ConnectionManager, ConnectionState


@pytest.fixture
def sm():
    return SessionManager()


@pytest.fixture
def cm():
    return ConnectionManager()


@pytest.mark.asyncio
async def test_session_created_on_connect(sm):
    s = await sm.create("r1")
    assert s.session_id == "r1"
    assert s.state == SessionState.IDLE


@pytest.mark.asyncio
async def test_reconnect_increments_counter(sm):
    await sm.create("r1")
    s = await sm.create("r1")
    assert s.reconnect_count == 1


@pytest.mark.asyncio
async def test_mark_audio_transitions_state(sm):
    await sm.create("r1")
    await sm.mark_audio("r1")
    s = await sm.get("r1")
    assert s.state == SessionState.STREAMING
    assert s.chunks_received == 1


@pytest.mark.asyncio
async def test_mark_activity_updates_timestamp(sm):
    await sm.create("r1")
    s = await sm.get("r1")
    old_ts = s.last_activity_at
    await asyncio.sleep(0.01)
    await sm.mark_activity("r1")
    assert s.last_activity_at > old_ts


@pytest.mark.asyncio
async def test_close_removes_session(sm):
    await sm.create("r1")
    await sm.close("r1")
    assert await sm.get("r1") is None


@pytest.mark.asyncio
async def test_stale_session_cleanup(sm):
    s = await sm.create("stale")
    s.last_activity_at = time.time() - (sm.SESSION_TIMEOUT + 10)
    stale = await sm.cleanup_stale()
    assert "stale" in stale
    assert await sm.get("stale") is None


@pytest.mark.asyncio
async def test_active_session_not_cleaned(sm):
    await sm.create("active")
    stale = await sm.cleanup_stale()
    assert "active" not in stale


@pytest.mark.asyncio
async def test_connection_manager_reconnect(cm):
    ws1, ws2 = AsyncMock(), AsyncMock()
    ws1.client = ws2.client = MagicMock()
    await cm.connect("r1", ws1)
    await cm.connect("r1", ws2)
    record = await cm.get("r1")
    assert record.websocket is ws2
    assert record.state == ConnectionState.ACTIVE


@pytest.mark.asyncio
async def test_disconnect_unknown_session_is_safe(cm):
    await cm.disconnect("nonexistent")


@pytest.mark.asyncio
async def test_all_sessions_returns_dicts(sm):
    await sm.create("x1")
    await sm.create("x2")
    sessions = await sm.all_sessions()
    assert len(sessions) == 2
    assert all("session_id" in s for s in sessions)


@pytest.mark.asyncio
async def test_rapid_session_create_close(sm):
    """1000 rapid create/close cycles must not leak sessions."""
    for i in range(1000):
        await sm.create(f"rapid-{i}")
        await sm.close(f"rapid-{i}")
    assert await sm.active_count() == 0


@pytest.mark.asyncio
async def test_duplicate_session_id_reconnect(sm):
    """Same session_id connecting twice increments reconnect_count, not creates duplicate."""
    await sm.create("dup")
    await sm.create("dup")
    await sm.create("dup")
    assert await sm.active_count() == 1
    s = await sm.get("dup")
    assert s.reconnect_count == 2
