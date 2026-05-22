"""
test_websocket_connection.py — WebSocket connect/disconnect/reconnect/heartbeat tests.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.app.realtime.websocket.connection_manager import ConnectionManager, ConnectionState


@pytest.fixture
def manager():
    return ConnectionManager()


def make_ws():
    ws = AsyncMock()
    ws.client = MagicMock()
    ws.client.__str__ = lambda self: "127.0.0.1:9999"
    return ws


@pytest.mark.asyncio
async def test_connect_registers_session(manager):
    ws = make_ws()
    record = await manager.connect("s1", ws)
    assert record.session_id == "s1"
    assert record.state == ConnectionState.ACTIVE
    assert await manager.active_count() == 1


@pytest.mark.asyncio
async def test_disconnect_removes_session(manager):
    ws = make_ws()
    await manager.connect("s1", ws)
    await manager.disconnect("s1")
    assert await manager.active_count() == 0
    assert await manager.get("s1") is None


@pytest.mark.asyncio
async def test_multiple_concurrent_sessions(manager):
    for i in range(5):
        await manager.connect(f"s{i}", make_ws())
    assert await manager.active_count() == 5
    assert set(await manager.active_sessions()) == {f"s{i}" for i in range(5)}


@pytest.mark.asyncio
async def test_reconnect_replaces_connection(manager):
    ws1, ws2 = make_ws(), make_ws()
    await manager.connect("s1", ws1)
    await manager.connect("s1", ws2)
    record = await manager.get("s1")
    assert record.websocket is ws2
    assert record.state == ConnectionState.ACTIVE


@pytest.mark.asyncio
async def test_touch_updates_activity(manager):
    ws = make_ws()
    record = await manager.connect("s1", ws)
    old_ts = record.last_activity
    await asyncio.sleep(0.01)
    await manager.touch("s1")
    assert record.last_activity > old_ts


@pytest.mark.asyncio
async def test_send_json_calls_websocket(manager):
    ws = make_ws()
    await manager.connect("s1", ws)
    await manager.send_json("s1", {"type": "ping"})
    ws.send_json.assert_called_once_with({"type": "ping"})


@pytest.mark.asyncio
async def test_send_bytes_calls_websocket(manager):
    ws = make_ws()
    await manager.connect("s1", ws)
    await manager.send_bytes("s1", b"\x00\x01\x02")
    ws.send_bytes.assert_called_once_with(b"\x00\x01\x02")


@pytest.mark.asyncio
async def test_disconnect_unknown_session_is_safe(manager):
    await manager.disconnect("nonexistent")  # must not raise


@pytest.mark.asyncio
async def test_rapid_connect_disconnect(manager):
    """Rapid connect/disconnect cycle must not corrupt state."""
    for i in range(50):
        ws = make_ws()
        await manager.connect(f"rapid-{i}", ws)
        await manager.disconnect(f"rapid-{i}")
    assert await manager.active_count() == 0


@pytest.mark.asyncio
async def test_broadcast_json(manager):
    ws1, ws2 = make_ws(), make_ws()
    await manager.connect("b1", ws1)
    await manager.connect("b2", ws2)
    await manager.broadcast_json({"type": "notice"})
    ws1.send_json.assert_called_once()
    ws2.send_json.assert_called_once()
