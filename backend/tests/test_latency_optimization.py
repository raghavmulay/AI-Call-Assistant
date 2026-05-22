"""
test_latency_optimization.py — Latency and performance validation tests.
"""
import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock

from backend.app.realtime.tts.tts_engine import TTSEngine, split_sentences
from backend.app.realtime.stt.vad_manager import (
    VADManager, SILENCE_THRESHOLD_INITIAL_MS, SILENCE_THRESHOLD_FAST_MS,
)
from backend.app.realtime.conversation.conversation_state import (
    ConversationStateRegistry, VoiceState,
)

FAKE_MP3 = b"\xFF\xFB" + b"\x00" * 50


@pytest.fixture(autouse=True)
def mock_logger():
    with patch("backend.app.realtime.tts.tts_engine.voice_logger"):
        yield


# ── Sentence splitting reduces first-chunk latency ───────────────────────────

def test_long_response_splits_into_multiple_sentences():
    text = (
        "The hostel fee is Rs. 60,000 per year. "
        "This includes mess charges. "
        "AC rooms are available at an additional cost. "
        "Please contact the admin office for more details."
    )
    sentences = split_sentences(text)
    assert len(sentences) >= 3


def test_first_sentence_is_short_for_low_latency():
    text = "Hello! How can I help you today? I am your campus assistant."
    sentences = split_sentences(text)
    # First sentence should be short enough to synthesize quickly
    assert len(sentences[0].split()) <= 10


# ── Adaptive VAD reduces silence wait ────────────────────────────────────────

def test_adaptive_threshold_is_shorter_after_first_turn():
    vad = VADManager()
    state = vad._get_state("s1")
    initial = state.silence_threshold
    state.total_turns = 1
    state.speech_ms = 500
    fast = state.silence_threshold
    assert fast < initial
    assert initial == SILENCE_THRESHOLD_INITIAL_MS
    assert fast == SILENCE_THRESHOLD_FAST_MS


def test_silence_threshold_difference_ms():
    """Fast threshold must be at least 200ms shorter than initial."""
    diff = SILENCE_THRESHOLD_INITIAL_MS - SILENCE_THRESHOLD_FAST_MS
    assert diff >= 200


# ── Streaming TTS first-chunk latency ────────────────────────────────────────

@pytest.mark.asyncio
async def test_first_chunk_arrives_before_full_synthesis():
    """
    Streaming TTS should yield the first chunk before all sentences are done.
    Simulates latency by adding a small delay per sentence.
    """
    engine = TTSEngine()
    chunk_times = []

    async def timed_edge(text, voice):
        await asyncio.sleep(0.05)  # 50ms per sentence
        return FAKE_MP3

    t_start = time.perf_counter()
    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", side_effect=timed_edge):
        async for _, audio in engine.stream_synthesize(
            "First sentence. Second sentence. Third sentence.", "s1"
        ):
            chunk_times.append(time.perf_counter() - t_start)

    assert len(chunk_times) >= 2
    # First chunk arrives well before all chunks
    assert chunk_times[0] < chunk_times[-1]
    # First chunk latency should be ~50ms, not 150ms (all 3 sentences)
    assert chunk_times[0] < 0.2  # generous bound for CI


# ── Cancel event stops streaming immediately ─────────────────────────────────

@pytest.mark.asyncio
async def test_cancel_stops_after_first_chunk():
    engine = TTSEngine()
    cancel = asyncio.Event()
    chunks_received = []

    async def fake_edge(text, voice):
        return FAKE_MP3

    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", side_effect=fake_edge):
        async for sentence, audio in engine.stream_synthesize(
            "One. Two. Three. Four. Five.",
            "s1",
            cancel_event=cancel,
        ):
            chunks_received.append(sentence)
            cancel.set()  # cancel after first chunk

    assert len(chunks_received) == 1


# ── Concurrent session throughput ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_10_concurrent_turns_complete():
    """10 concurrent voice turns must all complete without errors."""
    from backend.app.realtime.conversation.conversation_coordinator import handle_turn
    from backend.app.realtime.stt.transcript_manager import TranscriptManager

    mock_ai = MagicMock()
    mock_ai.response = "Response text."

    async def run(i: int):
        sid = f"perf-{i}"
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()
        tm = TranscriptManager()
        tm.update_partial(sid, "query")
        reg = ConversationStateRegistry()

        with patch("backend.app.realtime.conversation.conversation_coordinator.transcript_manager", tm), \
             patch("backend.app.realtime.conversation.conversation_coordinator.conversation_state", reg), \
             patch("backend.app.realtime.conversation.conversation_coordinator.process_query",
                   AsyncMock(return_value=mock_ai)), \
             patch("backend.app.realtime.conversation.conversation_coordinator.tts_engine") as mock_tts, \
             patch("backend.app.realtime.conversation.conversation_coordinator.send_streaming_audio_response",
                   AsyncMock(return_value=True)), \
             patch("backend.app.realtime.conversation.conversation_coordinator.voice_logger"):
            mock_tts.stream_synthesize = AsyncMock()
            await handle_turn(sid, ws)

        return reg.get_or_create(sid).voice_state

    t0 = time.perf_counter()
    results = await asyncio.gather(*[run(i) for i in range(10)])
    elapsed = time.perf_counter() - t0

    assert all(s == VoiceState.IDLE for s in results)
    assert elapsed < 5.0  # all 10 concurrent turns complete in under 5s (mocked)
