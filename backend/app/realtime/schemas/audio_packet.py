"""
audio_packet.py — Pydantic schemas for audio chunk packets.

Defines the canonical AudioPacket exchanged over WebSocket and the
server-side acknowledgement schema.  Supports both JSON (base64) and
binary (raw PCM16) transport — discriminated by `encoding`.
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal, Optional
import time


class PacketType(str, Enum):
    AUDIO = "audio"
    CONTROL = "control"


class AudioPacket(BaseModel):
    """A single chunk of streamed audio."""
    session_id: str
    chunk_id: int = Field(ge=0, description="Monotonically increasing sequence number")
    timestamp: float = Field(default_factory=time.time)
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    channels: int = Field(default=1, ge=1, le=2)
    encoding: Literal["pcm16", "base64"] = "base64"
    audio_data: str = Field(
        default="",
        description="Base64-encoded PCM16 bytes (empty when binary transport is used)",
    )
    byte_length: int = Field(
        default=0,
        ge=0,
        description="Length of decoded audio in bytes — filled by server on binary receive",
    )


class AudioPacketAck(BaseModel):
    """Server acknowledgement for a received audio packet."""
    session_id: str
    chunk_id: int
    received_at: float = Field(default_factory=time.time)
    status: Literal["ok", "dropped", "invalid"] = "ok"
    latency_ms: Optional[float] = None
