"""
test_conversation_flow.py — End-to-end conversation flow with Part 3 features.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.realtime.conversation.conversation_coordinator import handle_turn
from backend.app.realtime.conversation.conversation_state import (
    ConversationStateRegistry, VoiceState,
)
from backend.app.realtime.stt.transcript_manager import TranscriptManager

FAKE_MP3 = b"\xFF\xFB" + b"\x00" * 50


def make_mock_ws():
    ws = MagicMock()
    ws.send_json = AsyncMock()
    ws.send_bytes = AsyncMock()
    return ws


@pytest.fixture(autouse=True)
def mock_logger():
    with patch("backend.app.realtime.conversation.conversation_coordinator.voice_logger"):
        yield


@pytest.mark.asyncio
async def test_full_streaming_turn():
    """Complete turn: transcript → orchestrator → streaming TTS → IDLE."""
    sid = "flow-1"
    ws = make_mock_ws()
    tm = TranscriptManager()
    tm.update_partial(sid, "What are the fees?")
    reg = ConversationStateRegistry()

    mock_ai = MagicMock()
    mock_ai.response = "The fee is Rs. 60,000 per year. Please contact admin for details."

    async def fake_stream(text, session_id, cancel_event=None):
        yield "The fee is Rs. 60,000 per year.", FAKE_MP3
        yield "Please contact admin for details.", FAKE_MP3

    with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
         patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
         patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
               AsyncMock(return_value=mock_ai)), \
         patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
         patch("backend.app.realtime.conversation.conversation_coordinator.send_streaming_audio_response",
               AsyncMock(return_value=True)):
        mock_tts.stream_synthesize = fake_stream
        await handle_turn(sid, ws)

    assert reg.get_or_create(sid).voice_state == VoiceState.IDLE
    assert reg.get_or_create(sid).turn_count == 1


@pytest.mark.asyncio
async def test_barge_in_during_tts_stops_pipeline():
    """Barge-in during TTS streaming → state returns to LISTENING."""
    sid = "flow-2"
    ws = make_mock_ws()
    tm = TranscriptManager()
    tm.update_partial(sid, "Tell me about hostel.")
    reg = ConversationStateRegistry()

    mock_ai = MagicMock()
    mock_ai.response = "The hostel fee is Rs. 60,000. AC rooms are available on request."

    with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
         patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
         patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
               AsyncMock(return_value=mock_ai)), \
         patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
         patch("backend.app.realtime.conversation.conversation_coordinator.send_streaming_audio_response",
               AsyncMock(return_value=False)):  # False = interrupted
        mock_tts.stream_synthesize = AsyncMock()
        await handle_turn(sid, ws)

    assert reg.get_or_create(sid).voice_state == VoiceState.LISTENING


@pytest.mark.asyncio
async def test_barge_in_during_orchestrator():
    """Cancel event set during orchestrator → pipeline aborts before TTS."""
    sid = "flow-3"
    ws = make_mock_ws()
    tm = TranscriptManager()
    tm.update_partial(sid, "Hello")
    reg = ConversationStateRegistry()

    mock_ai = MagicMock()
    mock_ai.response = "Hello there!"

    async def slow_orchestrator(*args, **kwargs):
        # Simulate barge-in happening during orchestrator
        state = reg.get_or_create(sid)
        state.request_interrupt()
        return mock_ai

    with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
         patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
         patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
               slow_orchestrator), \
         patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
         patch("backend.app.realtime.conversation.conversation_coordinator.send_streaming_audio_response",
               AsyncMock()) as mock_send:
        mock_tts.stream_synthesize = AsyncMock()
        await handle_turn(sid, ws)

    # TTS should never have been called
    mock_send.assert_not_called()
    assert reg.get_or_create(sid).voice_state == VoiceState.LISTENING


@pytest.mark.asyncio
async def test_empty_transcript_skips_pipeline():
    sid = "flow-4"
    ws = make_mock_ws()
    tm = TranscriptManager()  # no partial set
    reg = ConversationStateRegistry()

    with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
         patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
         patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
               AsyncMock()) as mock_orch:
        await handle_turn(sid, ws)

    mock_orch.assert_not_called()
    assert reg.get_or_create(sid).voice_state == VoiceState.IDLE


@pytest.mark.asyncio
async def test_multiple_turns_increment_count():
    sid = "flow-5"
    ws = make_mock_ws()
    reg = ConversationStateRegistry()
    mock_ai = MagicMock()
    mock_ai.response = "Response."

    async def run_turn():
        tm = TranscriptManager()
        tm.update_partial(sid, "query")
        with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
             patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
             patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
                   AsyncMock(return_value=mock_ai)), \
             patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
             patch("backend.app.realtime.conversation.conversation_coordinator.send_streaming_audio_response",
                   AsyncMock(return_value=True)):
            mock_tts.stream_synthesize = AsyncMock()
            await handle_turn(sid, ws)

    await run_turn()
    await run_turn()
    await run_turn()
    assert reg.get_or_create(sid).turn_count == 3


@pytest.mark.asyncio
async def test_concurrent_sessions_isolated():
    """Two sessions running turns concurrently must not share state."""
    sessions = ["iso-1", "iso-2"]
    results = {}

    async def run(sid: str):
        ws = make_mock_ws()
        tm = TranscriptManager()
        tm.update_partial(sid, f"query from {sid}")
        reg = ConversationStateRegistry()
        mock_ai = MagicMock()
        mock_ai.response = f"response for {sid}"

        with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
             patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
             patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
                   AsyncMock(return_value=mock_ai)), \
             patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
             patch("backend.app.realtime.conversation.conversation_coordinator.send_streaming_audio_response",
                   AsyncMock(return_value=True)):
            mock_tts.stream_synthesize = AsyncMock()
            await handle_turn(sid, ws)
            results[sid] = reg.get_or_create(sid).active_response

    await asyncio.gather(*[run(s) for s in sessions])
    assert results["iso-1"] == "response for iso-1"
    assert results["iso-2"] == "response for iso-2"
