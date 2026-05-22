"""
websocket_router.py — FastAPI WebSocket endpoint for real-time audio streaming.

Stage 3 Part 3:
  - Barge-in: speech during AI response triggers immediate interruption
  - Partial transcript events forwarded to client
  - INTERRUPTED state recovery
"""
import asyncio
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.realtime.websocket.connection_manager import connection_manager
from backend.app.realtime.websocket.session_manager import session_manager
from backend.app.realtime.websocket.audio_protocol import (
    receive_packet, send_ack, send_pong, send_error,
)
from backend.app.realtime.audio.packet_processor import process_audio_packet
from backend.app.realtime.audio.audio_utils import decode_audio
from backend.app.realtime.audio.chunk_buffer import buffer_registry
from backend.app.realtime.monitoring.stream_logger import stream_logger
from backend.app.realtime.monitoring.latency_tracker import latency_tracker
from backend.app.realtime.monitoring.voice_pipeline_logger import voice_logger

from backend.app.realtime.stt.streaming_stt import streaming_stt
from backend.app.realtime.stt.vad_manager import vad_manager
from backend.app.realtime.conversation.conversation_state import (
    conversation_state, VoiceState,
)
from backend.app.realtime.conversation.conversation_coordinator import handle_turn

router = APIRouter(prefix="/ws", tags=["WebSocket Audio"])

HEARTBEAT_INTERVAL = 15
IDLE_TIMEOUT = 60


@router.websocket("/audio/{session_id}")
async def audio_stream_endpoint(websocket: WebSocket, session_id: str):
    # ── Connect ───────────────────────────────────────────────────────────────
    await connection_manager.connect(session_id, websocket)
    await session_manager.create(session_id)
    await buffer_registry.get_or_create(session_id)
    state = conversation_state.get_or_create(session_id)
    stream_logger.log_connect(session_id, str(websocket.client))

    # Register partial transcript callback → forward to client
    async def _on_partial(sid: str, partial_text: str):
        try:
            await websocket.send_json({
                "type": "partial_transcript",
                "session_id": sid,
                "text": partial_text,
            })
            voice_logger.log_partial_transcript(sid, partial_text)
        except Exception:
            pass

    streaming_stt.set_partial_callback(session_id, _on_partial)

    heartbeat_task = asyncio.create_task(_heartbeat(websocket, session_id))
    idle_task = asyncio.create_task(_idle_watchdog(websocket, session_id))

    try:
        while True:
            packet = await receive_packet(websocket, session_id)
            if packet is None:
                break

            await connection_manager.touch(session_id)
            await session_manager.mark_activity(session_id)

            # ── Control messages ──────────────────────────────────────────────
            if isinstance(packet, dict):
                msg_type = packet.get("type")
                if msg_type == "ping":
                    stream_logger.log_heartbeat(session_id, "ping_recv")
                    await send_pong(websocket, session_id)
                elif msg_type == "disconnect":
                    break
                continue

            # ── Audio packet ──────────────────────────────────────────────────
            accepted = await process_audio_packet(packet)
            await session_manager.mark_audio(session_id)
            await send_ack(websocket, session_id, packet.chunk_id, "ok" if accepted else "dropped")

            if not accepted:
                continue

            raw_pcm = decode_audio(packet.audio_data)

            # ── Barge-in detection ────────────────────────────────────────────
            if conversation_state.is_interruptible(session_id):
                # Grace period: don't allow barge-in within 2s of TTS starting
                state = conversation_state.get_or_create(session_id)
                time_in_state = time.time() - state.state_changed_at
                if time_in_state > 2.0 and vad_manager.is_speaking(session_id):
                    voice_logger.log_barge_in(session_id)
                    conversation_state.interrupt(session_id)
                    try:
                        await websocket.send_json({
                            "type": "barge_in",
                            "session_id": session_id,
                            "timestamp": time.time(),
                        })
                    except Exception:
                        pass
                continue  # don't process STT while TTS is playing

            # Skip if AI is processing (not yet interruptible)
            if state.voice_state == VoiceState.PROCESSING:
                continue

            # ── STT pipeline ──────────────────────────────────────────────────
            conversation_state.transition(session_id, VoiceState.LISTENING)
            turn_ended = await streaming_stt.ingest(session_id, raw_pcm)

            if turn_ended:
                asyncio.create_task(_run_voice_turn(websocket, session_id))

    except WebSocketDisconnect:
        stream_logger.log_disconnect(session_id, "websocket_disconnect")
    except Exception as exc:
        stream_logger.log_disconnect(session_id, f"error:{exc}")
    finally:
        heartbeat_task.cancel()
        idle_task.cancel()
        await asyncio.gather(heartbeat_task, idle_task, return_exceptions=True)
        await connection_manager.disconnect(session_id)
        await session_manager.close(session_id)
        await buffer_registry.remove(session_id)
        latency_tracker.remove(session_id)
        streaming_stt.remove(session_id)
        conversation_state.remove(session_id)
        stream_logger.log_disconnect(session_id, "cleanup_complete")


async def _run_voice_turn(websocket: WebSocket, session_id: str):
    try:
        record = await connection_manager.get(session_id)
        if record is None:
            return  # connection already closed
        await handle_turn(session_id=session_id, websocket=websocket)
    except Exception as exc:
        stream_logger.log_disconnect(session_id, f"turn_error:{exc}")
        conversation_state.transition(session_id, VoiceState.IDLE)


async def _heartbeat(websocket: WebSocket, session_id: str):
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await websocket.send_json({
                "type": "ping",
                "session_id": session_id,
                "timestamp": time.time(),
            })
            stream_logger.log_heartbeat(session_id, "ping_sent")
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


async def _idle_watchdog(websocket: WebSocket, session_id: str):
    try:
        while True:
            await asyncio.sleep(IDLE_TIMEOUT)
            session = await session_manager.get(session_id)
            if session is None:
                break
            if time.time() - session.last_activity_at >= IDLE_TIMEOUT:
                stream_logger.log_session_timeout(session_id)
                await send_error(websocket, session_id, "idle_timeout", "Closed due to inactivity.")
                await websocket.close(code=1000)
                break
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
