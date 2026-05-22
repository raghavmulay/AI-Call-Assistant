"""
conversation_coordinator.py — End-to-end voice turn pipeline.

Stage 3 Part 3:
  - Streaming TTS via stream_synthesize()
  - Barge-in safe: checks cancel_event between TTS chunks
  - INTERRUPTED state recovery
  - Partial transcript notification to client
"""
import time
from fastapi import WebSocket

from backend.app.realtime.stt.transcript_manager import transcript_manager
from backend.app.realtime.tts.tts_engine import tts_engine
from backend.app.realtime.tts.audio_response import send_streaming_audio_response
from backend.app.realtime.conversation.conversation_state import (
    conversation_state, VoiceState,
)
from backend.app.realtime.monitoring.voice_pipeline_logger import voice_logger
from backend.app.ai.orchestrator.orchestrator import process_query


async def handle_turn(
    session_id: str,
    websocket: WebSocket,
    user_context: dict = None,
    db=None,
):
    """
    Execute one complete voice turn with streaming TTS and barge-in support.

    Flow:
      1. Finalize transcript
      2. Notify client of transcript
      3. Run orchestrator
      4. Stream TTS sentence-by-sentence
      5. Handle interruption if barge-in detected
      6. Reset state for next turn
    """
    # ── 1. Finalize transcript ────────────────────────────────────────────────
    transcript = transcript_manager.finalize(session_id)
    if not transcript:
        conversation_state.transition(session_id, VoiceState.IDLE)
        return

    state = conversation_state.get_or_create(session_id)
    state.clear_interrupt()
    state.active_transcript = transcript
    state.turn_count += 1
    conversation_state.transition(session_id, VoiceState.PROCESSING)

    voice_logger.log_turn_start(session_id, transcript, state.turn_count)
    t_total = time.perf_counter()

    # ── 2. Notify client: transcript ready ───────────────────────────────────
    await websocket.send_json({
        "type": "transcript",
        "session_id": session_id,
        "text": transcript,
        "turn": state.turn_count,
    })

    # ── 3. Orchestrator ───────────────────────────────────────────────────────
    conversation_state.transition(session_id, VoiceState.WAITING_FOR_TTS)
    t_orch = time.perf_counter()
    ai_result = await process_query(
        user_input=transcript,
        session_id=session_id,
        user_context=user_context,
        db=db,
    )
    orch_ms = (time.perf_counter() - t_orch) * 1000
    response_text = ai_result.response
    state.active_response = response_text
    voice_logger.log_orchestrator(session_id, response_text, orch_ms)

    # Check for barge-in that happened during orchestrator processing
    if state.is_cancelled:
        voice_logger.log_interrupt(session_id, "during_orchestrator")
        conversation_state.transition(session_id, VoiceState.LISTENING)
        transcript_manager.clear(session_id)
        return

    # ── 4. Streaming TTS ──────────────────────────────────────────────────────
    conversation_state.transition(session_id, VoiceState.STREAMING_RESPONSE)

    audio_stream = tts_engine.stream_synthesize(
        text=response_text,
        session_id=session_id,
        cancel_event=state.cancel_event,
    )

    completed = await send_streaming_audio_response(
        websocket=websocket,
        session_id=session_id,
        audio_stream=audio_stream,
        cancel_event=state.cancel_event,
    )

    total_ms = (time.perf_counter() - t_total) * 1000

    # ── 5. Handle interruption ────────────────────────────────────────────────
    if not completed:
        voice_logger.log_interrupt(session_id, "during_tts_streaming")
        transcript_manager.clear(session_id)
        state.clear_interrupt()
        conversation_state.transition(session_id, VoiceState.LISTENING)
        return

    voice_logger.log_turn_complete(session_id, total_ms)

    # ── 6. Reset for next turn ────────────────────────────────────────────────
    transcript_manager.clear(session_id)
    state.clear_interrupt()
    conversation_state.transition(session_id, VoiceState.IDLE)


conversation_coordinator = handle_turn
