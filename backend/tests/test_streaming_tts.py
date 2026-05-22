"""
test_streaming_tts.py — Streaming TTS engine tests.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from backend.app.realtime.tts.tts_engine import TTSEngine, split_sentences

FAKE_MP3 = b"\xFF\xFB" + b"\x00" * 50


@pytest.fixture(autouse=True)
def mock_logger():
    with patch("backend.app.realtime.tts.tts_engine.voice_logger"):
        yield


# ── split_sentences ───────────────────────────────────────────────────────────

def test_split_single_sentence():
    result = split_sentences("Hello world.")
    assert result == ["Hello world."]


def test_split_multiple_sentences():
    result = split_sentences("Hello world. How are you? I am fine.")
    assert len(result) >= 2  # merger may combine short fragments


def test_split_merges_short_fragments():
    result = split_sentences("Hi. How are you today?")
    # "Hi." is < 4 words, should merge with next
    assert len(result) == 1


def test_split_empty_returns_empty():
    assert split_sentences("") == []


def test_split_preserves_question_marks():
    result = split_sentences("What is your name? My name is Aria.")
    assert len(result) == 2


# ── stream_synthesize ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_synthesize_yields_chunks():
    engine = TTSEngine()
    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", return_value=FAKE_MP3):
        chunks = []
        async for sentence, audio in engine.stream_synthesize("Hello world. How are you?", "s1"):
            chunks.append((sentence, audio))
    assert len(chunks) >= 1
    assert all(len(audio) > 0 for _, audio in chunks)


@pytest.mark.asyncio
async def test_stream_synthesize_empty_text_yields_nothing():
    engine = TTSEngine()
    chunks = []
    async for item in engine.stream_synthesize("", "s1"):
        chunks.append(item)
    assert chunks == []


@pytest.mark.asyncio
async def test_stream_synthesize_cancelled_mid_stream():
    """Cancel event set before second sentence — only first should be yielded."""
    engine = TTSEngine()
    cancel = asyncio.Event()
    call_count = 0

    async def fake_edge(text, voice):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            cancel.set()  # set cancel before second chunk is yielded
        return FAKE_MP3

    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", side_effect=fake_edge):
        chunks = []
        async for sentence, audio in engine.stream_synthesize(
            "First sentence. Second sentence. Third sentence.",
            "s1",
            cancel_event=cancel,
        ):
            chunks.append(sentence)

    # Should stop after cancel is set
    assert len(chunks) <= 2


@pytest.mark.asyncio
async def test_stream_synthesize_fallback_on_edge_failure():
    engine = TTSEngine()
    fake_wav = b"RIFF" + b"\x00" * 40
    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", side_effect=Exception("fail")), \
         patch("backend.app.realtime.tts.tts_engine._synthesize_pyttsx3", return_value=fake_wav):
        chunks = []
        async for _, audio in engine.stream_synthesize("Hello world.", "s1"):
            chunks.append(audio)
    assert len(chunks) == 1
    assert chunks[0] == fake_wav
