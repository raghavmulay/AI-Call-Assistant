"""
test_streaming_stt.py — StreamingSTT pipeline tests (Whisper mocked).
"""
import pytest
import struct
import math
from unittest.mock import patch, MagicMock
from backend.app.realtime.stt.streaming_stt import StreamingSTT
from backend.app.realtime.stt.transcript_manager import TranscriptManager
from backend.app.realtime.stt.vad_manager import SAMPLE_RATE


def make_tone_pcm(ms: int = 20, freq: int = 440) -> bytes:
    samples = int(SAMPLE_RATE * ms / 1000)
    result = bytearray()
    for i in range(samples):
        val = int(32767 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE))
        result += struct.pack("<h", val)
    return bytes(result)


def make_silence_pcm(ms: int = 20) -> bytes:
    return b"\x00\x00" * int(SAMPLE_RATE * ms / 1000)


@pytest.fixture(autouse=True)
def mock_whisper():
    """Mock _transcribe_pcm to avoid loading the Whisper model in tests."""
    with patch("backend.app.realtime.stt.streaming_stt._transcribe_pcm", return_value="test transcript") as m:
        yield m


@pytest.mark.asyncio
async def test_ingest_silence_no_turn_end():
    stt = StreamingSTT()
    for _ in range(20):
        result = await stt.ingest("s1", make_silence_pcm(20))
    assert result is False


@pytest.mark.asyncio
async def test_ingest_speech_then_silence_triggers_turn():
    stt = StreamingSTT()
    tm = TranscriptManager()

    with patch("backend.app.realtime.stt.streaming_stt.transcript_manager", tm):
        # Feed speech
        for _ in range(25):
            await stt.ingest("s1", make_tone_pcm(20))
        # Feed silence until turn ends
        turn_ended = False
        for _ in range(60):
            result = await stt.ingest("s1", make_silence_pcm(20))
            if result:
                turn_ended = True
                break

    assert turn_ended
    assert tm.get_partial("s1") == "test transcript"


@pytest.mark.asyncio
async def test_session_isolation():
    stt = StreamingSTT()
    # Feed speech to s1 only
    for _ in range(25):
        await stt.ingest("s1", make_tone_pcm(20))
    # s2 buffer should be empty
    assert "s2" not in stt._buffers or len(stt._buffers.get("s2", b"")) == 0


@pytest.mark.asyncio
async def test_remove_cleans_up():
    stt = StreamingSTT()
    await stt.ingest("s1", make_silence_pcm(20))
    stt.remove("s1")
    assert "s1" not in stt._buffers


@pytest.mark.asyncio
async def test_empty_chunk_handled():
    stt = StreamingSTT()
    result = await stt.ingest("s1", b"")
    assert result is False
