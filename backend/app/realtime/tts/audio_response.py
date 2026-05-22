"""
audio_response.py — WebSocket audio delivery.

Stage 3 Part 3:
  send_audio_response()         — full response (Part 2 compat)
  send_streaming_audio_response() — sentence-chunk streaming with barge-in support
"""
import asyncio
import time
from typing import Optional, AsyncGenerator, Tuple
from fastapi import WebSocket


async def send_audio_response(
    websocket: WebSocket,
    session_id: str,
    audio_bytes: bytes,
    text: str = "",
    encoding: str = "mp3",
):
    """Send complete TTS audio (Part 2 compatible)."""
    if not audio_bytes:
        return
    await websocket.send_json({
        "type": "tts_start",
        "session_id": session_id,
        "text": text,
        "encoding": encoding,
        "length": len(audio_bytes),
        "timestamp": time.time(),
    })
    await websocket.send_bytes(audio_bytes)
    await websocket.send_json({
        "type": "tts_end",
        "session_id": session_id,
        "timestamp": time.time(),
    })


async def send_streaming_audio_response(
    websocket: WebSocket,
    session_id: str,
    audio_stream: AsyncGenerator[Tuple[str, bytes], None],
    cancel_event: Optional[asyncio.Event] = None,
    encoding: str = "mp3",
) -> bool:
    """
    Stream sentence-level TTS chunks to the client.

    Sends each sentence as:
      1. tts_chunk JSON header
      2. binary audio bytes

    Returns True if completed fully, False if interrupted.
    """
    chunk_index = 0
    interrupted = False

    try:
        await websocket.send_json({
            "type": "tts_stream_start",
            "session_id": session_id,
            "timestamp": time.time(),
        })
    except Exception:
        return False

    async for sentence, audio_bytes in audio_stream:
        if cancel_event and cancel_event.is_set():
            interrupted = True
            break
        if not audio_bytes:
            continue
        try:
            await websocket.send_json({
                "type": "tts_chunk",
                "session_id": session_id,
                "index": chunk_index,
                "text": sentence,
                "encoding": encoding,
                "length": len(audio_bytes),
                "timestamp": time.time(),
            })
            await websocket.send_bytes(audio_bytes)
        except Exception:
            interrupted = True
            break
        chunk_index += 1

    try:
        end_type = "tts_stream_interrupted" if interrupted else "tts_stream_end"
        await websocket.send_json({
            "type": end_type,
            "session_id": session_id,
            "chunks_sent": chunk_index,
            "timestamp": time.time(),
        })
    except Exception:
        pass

    return not interrupted
