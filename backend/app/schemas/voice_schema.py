"""schemas/voice_schema.py — Voice request/response."""

from pydantic import BaseModel
from typing import Optional


class VoiceRequest(BaseModel):
    audio_b64: str    # base64-encoded WAV/MP3
    session_id: str
    return_audio: bool = True


class VoiceResponse(BaseModel):
    session_id: str
    transcript: Optional[str]
    text: str
    audio_b64: Optional[str] = None   # base64 TTS audio
    intent: str
    sub_intent: Optional[str] = None
    requires_auth: bool = False
