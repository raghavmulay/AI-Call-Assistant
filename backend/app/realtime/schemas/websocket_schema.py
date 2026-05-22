"""
websocket_schema.py — Pydantic schemas for WebSocket lifecycle control messages.

All non-audio frames (connect, disconnect, heartbeat, error) are modelled here.
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal, Optional
import time


class ControlMessageType(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class StreamStatus(str, Enum):
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    CLOSED = "closed"


# ── Individual message models ────────────────────────────────────────────────


class WSConnectMessage(BaseModel):
    type: Literal["connect"] = "connect"
    session_id: str
    timestamp: float = Field(default_factory=time.time)
    protocol_version: str = "1.0"


class WSDisconnectMessage(BaseModel):
    type: Literal["disconnect"] = "disconnect"
    session_id: str
    reason: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class WSHeartbeat(BaseModel):
    type: Literal["ping", "pong"]
    session_id: str
    timestamp: float = Field(default_factory=time.time)


class WSErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    session_id: str
    code: str
    message: str
    timestamp: float = Field(default_factory=time.time)
