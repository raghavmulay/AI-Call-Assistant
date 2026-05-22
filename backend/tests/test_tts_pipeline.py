"""
test_tts_pipeline.py — TTS engine and audio_response tests (network mocked).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.realtime.tts.tts_engine import TTSEngine
from backend.app.realtime.tts.audio_response import send_audio_response


FAKE_MP3 = b"\xFF\xFB\x90\x00" + b"\x00" * 100  # minimal fake MP3 header


@pytest.fixture(autouse=True)
def mock_voice_logger():
    with patch("backend.app.realtime.tts.tts_engine.voice_logger") as m:
        yield m


@pytest.mark.asyncio
async def test_synthesize_returns_bytes():
    engine = TTSEngine()
    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", return_value=FAKE_MP3):
        result = await engine.synthesize("Hello world", "s1")
    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_synthesize_empty_text_returns_empty():
    engine = TTSEngine()
    result = await engine.synthesize("", "s1")
    assert result == b""


@pytest.mark.asyncio
async def test_synthesize_whitespace_returns_empty():
    engine = TTSEngine()
    result = await engine.synthesize("   ", "s1")
    assert result == b""


@pytest.mark.asyncio
async def test_edge_tts_failure_falls_back_to_pyttsx3():
    engine = TTSEngine()
    fake_wav = b"RIFF" + b"\x00" * 40

    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", side_effect=Exception("network error")), \
         patch("backend.app.realtime.tts.tts_engine._synthesize_pyttsx3", return_value=fake_wav):
        result = await engine.synthesize("Fallback test", "s1")

    assert result == fake_wav


@pytest.mark.asyncio
async def test_both_engines_fail_returns_empty():
    engine = TTSEngine()
    with patch("backend.app.realtime.tts.tts_engine._synthesize_edge", side_effect=Exception("fail")), \
         patch("backend.app.realtime.tts.tts_engine._synthesize_pyttsx3", side_effect=Exception("fail")):
        result = await engine.synthesize("test", "s1")
    assert result == b""


@pytest.mark.asyncio
async def test_send_audio_response_sends_header_and_bytes():
    ws = MagicMock()
    ws.send_json = AsyncMock()
    ws.send_bytes = AsyncMock()

    await send_audio_response(ws, "s1", FAKE_MP3, text="Hello", encoding="mp3")

    assert ws.send_json.call_count == 2  # tts_start + tts_end
    ws.send_bytes.assert_called_once_with(FAKE_MP3)

    start_payload = ws.send_json.call_args_list[0][0][0]
    assert start_payload["type"] == "tts_start"
    assert start_payload["length"] == len(FAKE_MP3)
    assert start_payload["text"] == "Hello"


@pytest.mark.asyncio
async def test_send_audio_response_empty_bytes_skipped():
    ws = MagicMock()
    ws.send_json = AsyncMock()
    ws.send_bytes = AsyncMock()

    await send_audio_response(ws, "s1", b"")
    ws.send_json.assert_not_called()
    ws.send_bytes.assert_not_called()
