"""
services/voice_service.py — End-to-end voice pipeline.

audio bytes → STT → conversation_manager → TTS → audio bytes
"""

import base64
from typing import Optional, Optional
from backend.app.ai.stt.whisper_engine import whisper_engine
from backend.app.ai.tts.speech_engine import synthesize
from backend.app.ai.conversation.conversation_manager import process
from backend.app.core.logger import get_logger

logger = get_logger("voice_service")


async def handle_voice(
    audio_bytes: bytes,
    session_id: str,
    user_id: Optional[str] = None,
    get_personal_context=None,
    return_audio: bool = True,
) -> dict:
    """
    Full voice round-trip.

    Returns:
        {
            "transcript": str,
            "text": str,
            "audio_b64": Optional[str],   # base64 MP3/WAV, if return_audio=True
            "intent": str,
            "requires_auth": bool,
        }
    """
    # 1. STT
    transcript = await whisper_engine.transcribe_bytes(audio_bytes)
    if not transcript:
        return {"error": "Could not transcribe audio.", "transcript": None}

    logger.info("Transcript [%s]: %s", session_id, transcript)

    # 2. Conversation
    result = await process(transcript, user_id=user_id, get_personal_context=get_personal_context)

    # 3. TTS
    audio_b64 = None
    if return_audio:
        audio_bytes_out = await synthesize(result["text"])
        if audio_bytes_out:
            audio_b64 = base64.b64encode(audio_bytes_out).decode()

    return {
        "transcript": transcript,
        "text": result["text"],
        "audio_b64": audio_b64,
        "intent": result["intent"],
        "sub_intent": result.get("sub_intent"),
        "requires_auth": result.get("requires_auth", False),
    }


async def handle_voice_b64(
    audio_b64: str,
    session_id: str,
    user_id: Optional[str] = None,
    get_personal_context=None,
) -> dict:
    """Convenience wrapper that accepts base64-encoded audio."""
    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        return {"error": "Invalid base64 audio."}
    return await handle_voice(audio_bytes, session_id, user_id, get_personal_context)
