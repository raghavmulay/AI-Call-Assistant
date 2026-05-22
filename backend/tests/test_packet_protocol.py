"""
test_packet_protocol.py — Audio protocol framing and parsing tests.
"""
import pytest
import struct
import json
import time
from unittest.mock import AsyncMock
from backend.app.realtime.websocket.audio_protocol import receive_packet, send_ack, send_pong, send_error
from backend.app.realtime.schemas.audio_packet import AudioPacket
from backend.app.realtime.audio.audio_utils import encode_audio


def make_binary_frame(chunk_id: int, pcm_bytes: bytes) -> bytes:
    return struct.pack("<I", chunk_id) + pcm_bytes


def make_ws_with_message(message: dict):
    ws = AsyncMock()
    ws.receive = AsyncMock(return_value=message)
    return ws


@pytest.mark.asyncio
async def test_receive_binary_frame():
    pcm = b"\x00\x01" * 320
    frame = make_binary_frame(42, pcm)
    ws = make_ws_with_message({"type": "websocket.receive", "bytes": frame, "text": None})
    packet = await receive_packet(ws, "s1")
    assert isinstance(packet, AudioPacket)
    assert packet.chunk_id == 42
    assert packet.session_id == "s1"


@pytest.mark.asyncio
async def test_receive_json_audio_frame():
    raw = b"\x00\x01" * 320
    payload = json.dumps({
        "type": "audio",
        "session_id": "s1",
        "chunk_id": 7,
        "timestamp": time.time(),
        "audio_data": encode_audio(raw),
    })
    ws = make_ws_with_message({"type": "websocket.receive", "bytes": None, "text": payload})
    packet = await receive_packet(ws, "s1")
    assert isinstance(packet, AudioPacket)
    assert packet.chunk_id == 7


@pytest.mark.asyncio
async def test_json_type_field_stripped():
    """'type' field in JSON audio frame must not cause Pydantic validation error."""
    raw = b"\x00\x01" * 320
    payload = json.dumps({
        "type": "audio",
        "chunk_id": 99,
        "audio_data": encode_audio(raw),
    })
    ws = make_ws_with_message({"type": "websocket.receive", "bytes": None, "text": payload})
    packet = await receive_packet(ws, "s1")
    assert isinstance(packet, AudioPacket)
    assert packet.chunk_id == 99
    assert packet.session_id == "s1"  # always overridden from URL


@pytest.mark.asyncio
async def test_receive_control_message():
    payload = json.dumps({"type": "ping", "session_id": "s1"})
    ws = make_ws_with_message({"type": "websocket.receive", "bytes": None, "text": payload})
    result = await receive_packet(ws, "s1")
    assert isinstance(result, dict)
    assert result["type"] == "ping"


@pytest.mark.asyncio
async def test_receive_disconnect_returns_none():
    ws = make_ws_with_message({"type": "websocket.disconnect"})
    result = await receive_packet(ws, "s1")
    assert result is None


@pytest.mark.asyncio
async def test_receive_empty_binary_returns_none():
    """Binary frame shorter than 4 bytes must return None."""
    ws = make_ws_with_message({"type": "websocket.receive", "bytes": b"\x00\x01", "text": None})
    result = await receive_packet(ws, "s1")
    assert result is None


@pytest.mark.asyncio
async def test_receive_malformed_json_returns_none():
    ws = make_ws_with_message({"type": "websocket.receive", "bytes": None, "text": "{not valid json"})
    result = await receive_packet(ws, "s1")
    assert result is None


@pytest.mark.asyncio
async def test_receive_exception_returns_none():
    ws = AsyncMock()
    ws.receive = AsyncMock(side_effect=Exception("connection reset"))
    result = await receive_packet(ws, "s1")
    assert result is None


@pytest.mark.asyncio
async def test_send_ack():
    ws = AsyncMock()
    await send_ack(ws, "s1", 5, "ok")
    ws.send_json.assert_called_once()
    call_args = ws.send_json.call_args[0][0]
    assert call_args["chunk_id"] == 5
    assert call_args["status"] == "ok"


@pytest.mark.asyncio
async def test_send_pong():
    ws = AsyncMock()
    await send_pong(ws, "s1")
    ws.send_json.assert_called_once()
    assert ws.send_json.call_args[0][0]["type"] == "pong"


@pytest.mark.asyncio
async def test_send_error():
    ws = AsyncMock()
    await send_error(ws, "s1", "idle_timeout", "Connection closed due to inactivity.")
    ws.send_json.assert_called_once()
    payload = ws.send_json.call_args[0][0]
    assert payload["type"] == "error"
    assert payload["code"] == "idle_timeout"
