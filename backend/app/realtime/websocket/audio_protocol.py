"""
audio_protocol.py — WebSocket message framing and packet parsing.

Supports two transport modes:
  - JSON text frames  ({"type": "audio", ...AudioPacket fields})
  - Binary frames     (raw PCM16 with chunk_id prepended as 4-byte little-endian int)
"""
import json
import struct
import time
from typing import Union
from fastapi import WebSocket
from backend.app.realtime.schemas.audio_packet import AudioPacket
from backend.app.realtime.audio.audio_utils import encode_audio

PROTOCOL_VERSION = "1.0"

# Fields that belong to AudioPacket schema
_AUDIO_PACKET_FIELDS = {"session_id", "chunk_id", "timestamp", "sample_rate", "channels", "encoding", "audio_data"}


async def receive_packet(websocket: WebSocket, session_id: str) -> Union[AudioPacket, dict, None]:
    """
    Receive one frame from the WebSocket and parse it.

    Returns:
      - AudioPacket  for audio frames
      - dict         for control messages (ping, disconnect, etc.)
      - None         on close / unrecognised frame
    """
    try:
        message = await websocket.receive()
    except Exception:
        return None

    if message["type"] == "websocket.disconnect":
        return None

    # ── Binary frame: [4-byte chunk_id LE][PCM16 bytes] ──────────────────────
    raw_bytes = message.get("bytes")
    if raw_bytes:
        if len(raw_bytes) < 4:
            return None
        chunk_id = struct.unpack_from("<I", raw_bytes, 0)[0]
        audio_bytes = raw_bytes[4:]
        return AudioPacket(
            session_id=session_id,
            chunk_id=chunk_id,
            timestamp=time.time(),
            audio_data=encode_audio(audio_bytes),
        )

    # ── Text / JSON frame ─────────────────────────────────────────────────────
    text = message.get("text")
    if text:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None

        msg_type = data.get("type", "audio")
        if msg_type == "audio":
            # Strip control fields before constructing AudioPacket
            packet_data = {k: v for k, v in data.items() if k in _AUDIO_PACKET_FIELDS}
            # Ensure session_id is always from the URL path (authoritative)
            packet_data["session_id"] = session_id
            try:
                return AudioPacket(**packet_data)
            except Exception:
                return None
        return data  # control message (ping, disconnect, etc.)

    return None


async def send_ack(websocket: WebSocket, session_id: str, chunk_id: int, status: str = "ok"):
    await websocket.send_json({
        "type": "ack",
        "session_id": session_id,
        "chunk_id": chunk_id,
        "status": status,
        "ts": time.time(),
    })


async def send_pong(websocket: WebSocket, session_id: str):
    await websocket.send_json({"type": "pong", "session_id": session_id, "timestamp": time.time()})


async def send_error(websocket: WebSocket, session_id: str, code: str, message: str):
    await websocket.send_json({
        "type": "error",
        "session_id": session_id,
        "code": code,
        "message": message,
        "ts": time.time(),
    })
