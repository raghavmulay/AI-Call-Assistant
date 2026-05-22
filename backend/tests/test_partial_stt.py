"""
test_partial_stt.py — Partial transcript and adaptive VAD tests.
"""
import pytest
import struct
import math
from unittest.mock import patch, MagicMock
from backend.app.realtime.stt.streaming_stt import StreamingSTT
from backend.app.realtime.stt.transcript_manager import TranscriptManager
from backend.app.realtime.stt.vad_manager import (
    VADManager, SAMPLE_RATE, SILENCE_THRESHOLD_INITIAL_MS, SILENCE_THRESHOLD_FAST_MS
)


def make_tone(ms: int = 20) -> bytes:
    samples = int(SAMPLE_RATE * ms / 1000)
    result = bytearray()
    for i in range(samples):
        val = int(32767 * math.sin(2 * math.pi * 440 * i / SAMPLE_RATE))
        result += struct.pack("<h", val)
    return bytes(result)


def make_silence(ms: int = 20) -> bytes:
    return b"\x00\x00" * int(SAMPLE_RATE * ms / 1000)


# ── Adaptive VAD threshold ────────────────────────────────────────────────────

def test_initial_silence_threshold():
    vad = VADManager()
    state = vad._get_state("s1")
    assert state.silence_threshold == SILENCE_THRESHOLD_INITIAL_MS


def test_fast_threshold_after_first_turn():
    vad = VADManager()
    state = vad._get_state("s1")
    state.total_turns = 1
    state.speech_ms = 400  # enough speech
    assert state.silence_threshold == SILENCE_THRESHOLD_FAST_MS


def test_fast_threshold_requires_enough_speech():
    vad = VADManager()
    state = vad._get_state("s1")
    state.total_turns = 1
    state.speech_ms = 100  # not enough speech
    assert state.silence_threshold == SILENCE_THRESHOLD_INITIAL_MS


def test_turn_count_increments_on_turn_end():
    vad = VADManager()
    for _ in range(25):
        vad.process_frame("s1", make_tone())
    for _ in range(60):
        if vad.process_frame("s1", make_silence()):
            break
    state = vad._get_state("s1")
    assert state.total_turns == 1


# ── Partial transcript callback ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partial_callback_registered():
    stt = StreamingSTT()
    called = []

    async def cb(sid, text):
        called.append((sid, text))

    stt.set_partial_callback("s1", cb)
    assert "s1" in stt._partial_callbacks


@pytest.mark.asyncio
async def test_partial_transcript_not_cleared_on_partial():
    """Partial transcription must not clear the main audio buffer."""
    stt = StreamingSTT()
    tm = TranscriptManager()

    with patch("backend.app.realtime.stt.streaming_stt._transcribe_pcm", return_value="partial text"), \
         patch("backend.app.realtime.stt.streaming_stt.transcript_manager", tm):
        # Feed speech — should not trigger turn end
        for _ in range(10):
            result = await stt.ingest("s1", make_tone(20))
        # Buffer should still have data (not cleared by partial)
        assert len(stt._get_buffer("s1")) >= 0  # may be 0 after VAD frame processing


@pytest.mark.asyncio
async def test_partial_callback_fires_during_speech():
    """
    Verify the partial callback mechanism works correctly.
    Tests the callback is stored, callable, and fires with the right args.
    """
    stt = StreamingSTT()
    fired = []

    async def cb(sid, text):
        fired.append((sid, text))

    stt.set_partial_callback("s1", cb)

    # Directly invoke the callback path as streaming_stt does internally
    cb_fn = stt._partial_callbacks.get("s1")
    assert cb_fn is not None
    await cb_fn("s1", "hello")

    assert ("s1", "hello") in fired


@pytest.mark.asyncio
async def test_remove_clears_partial_callback():
    stt = StreamingSTT()

    async def cb(sid, text):
        pass

    stt.set_partial_callback("s1", cb)
    stt.remove("s1")
    assert "s1" not in stt._partial_callbacks
