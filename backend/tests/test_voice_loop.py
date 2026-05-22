"""
test_voice_loop.py — End-to-end voice pipeline integration tests.

All external dependencies (Whisper, Ollama, edge-tts) are mocked.
Tests verify the pipeline wiring: STT → Orchestrator → TTS → WebSocket.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.realtime.conversation.conversation_coordinator import handle_turn
from backend.app.realtime.conversation.conversation_state import (
    ConversationStateRegistry, VoiceState,
)
from backend.app.realtime.stt.transcript_manager import TranscriptManager
from backend.app.realtime.tts.tts_engine import TTSEngine


FAKE_MP3 = b"\xFF\xFB\x90\x00" + b"\x00" * 200


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
async def test_handle_turn_full_pipeline():
    """Full pipeline: transcript → orchestrator → TTS → WebSocket."""
    session_id = "loop-test-1"
    ws = make_mock_ws()

    tm = TranscriptManager()
    tm.update_partial(session_id, "What are the hostel fees?")

    mock_ai_result = MagicMock()
    mock_ai_result.response = "The hostel fee is Rs. 60,000 per year."

    with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
         patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
               AsyncMock(return_value=mock_ai_result)), \
         patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
         patch("backend.app.realtime.conversation.conversation_coordinator.send_audio_response",
               AsyncMock()) as mock_send:

        mock_tts.synthesize = AsyncMock(return_value=FAKE_MP3)
        await handle_turn(session_id, ws)

    # Transcript frame sent
    json_calls = [c[0][0] for c in ws.send_json.call_args_list]
    transcript_frames = [c for c in json_calls if c.get("type") == "transcript"]
    assert len(transcript_frames) == 1
    assert transcript_frames[0]["text"] == "What are the hostel fees?"

    # TTS called with AI response
    mock_tts.synthesize.assert_called_once_with(
        "The hostel fee is Rs. 60,000 per year.", session_id
    )

    # Audio response sent
    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_handle_turn_empty_transcript_skips_pipeline():
    """Empty transcript must not call orchestrator or TTS."""
    session_id = "loop-test-2"
    ws = make_mock_ws()
    tm = TranscriptManager()  # no partial set → finalize returns ""

    with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
         patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
               AsyncMock()) as mock_orch:
        await handle_turn(session_id, ws)

    mock_orch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_turn_state_returns_to_idle():
    """Conversation state must return to IDLE after turn completes."""
    session_id = "loop-test-3"
    ws = make_mock_ws()
    tm = TranscriptManager()
    tm.update_partial(session_id, "Hello")

    mock_ai = MagicMock()
    mock_ai.response = "Hi there!"
    reg = ConversationStateRegistry()

    with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
         patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
         patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
               AsyncMock(return_value=mock_ai)), \
         patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
         patch("backend.app.realtime.conversation.conversation_coordinator.send_audio_response",
               AsyncMock()):
        mock_tts.synthesize = AsyncMock(return_value=FAKE_MP3)
        await handle_turn(session_id, ws)

    assert reg.get_or_create(session_id).voice_state == VoiceState.IDLE


@pytest.mark.asyncio
async def test_handle_turn_increments_turn_count():
    session_id = "loop-test-4"
    ws = make_mock_ws()
    tm = TranscriptManager()
    mock_ai = MagicMock()
    mock_ai.response = "Response"
    reg = ConversationStateRegistry()

    async def run_turn():
        tm.update_partial(session_id, "query")
        with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
             patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
             patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
                   AsyncMock(return_value=mock_ai)), \
             patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
             patch("backend.app.realtime.conversation.conversation_coordinator.send_audio_response",
                   AsyncMock()):
            mock_tts.synthesize = AsyncMock(return_value=FAKE_MP3)
            await handle_turn(session_id, ws)

    await run_turn()
    await run_turn()
    assert reg.get_or_create(session_id).turn_count == 2


@pytest.mark.asyncio
async def test_concurrent_voice_turns_different_sessions():
    """Two sessions running turns concurrently must not interfere."""
    sessions = ["concurrent-1", "concurrent-2"]
    results = {}

    async def run(sid: str):
        ws = make_mock_ws()
        tm = TranscriptManager()
        tm.update_partial(sid, f"query from {sid}")
        mock_ai = MagicMock()
        mock_ai.response = f"response for {sid}"

        with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
             patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
                   AsyncMock(return_value=mock_ai)), \
             patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
             patch("backend.app.realtime.conversation.conversation_coordinator.send_audio_response",
                   AsyncMock()):
            mock_tts.synthesize = AsyncMock(return_value=FAKE_MP3)
            await handle_turn(sid, ws)
            results[sid] = mock_ai.response

    await asyncio.gather(*[run(s) for s in sessions])
    assert results["concurrent-1"] == "response for concurrent-1"
    assert results["concurrent-2"] == "response for concurrent-2"
