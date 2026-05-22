"""
test_playback_interruptions.py — PlaybackManager interruption tests.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from backend.app.realtime.playback.playback_manager import PlaybackManager
from backend.app.realtime.tts.audio_response import send_streaming_audio_response


FAKE_MP3 = b"\xFF\xFB" + b"\x00" * 50


def test_interrupt_sets_stop_flag():
    pm = PlaybackManager()
    pm.interrupt()
    assert pm._stop_flag[0] is True


def test_resume_clears_stop_flag():
    pm = PlaybackManager()
    pm.interrupt()
    pm.resume()
    assert pm._stop_flag[0] is False


def test_clear_flushes_queue():
    pm = PlaybackManager()
    # Manually put items in queue
    pm._queue.put_nowait((FAKE_MP3, "mp3"))
    pm._queue.put_nowait((FAKE_MP3, "mp3"))
    pm.clear()
    assert pm._queue.empty()


@pytest.mark.asyncio
async def test_enqueue_adds_to_queue():
    pm = PlaybackManager()
    await pm.enqueue(FAKE_MP3, "mp3")
    assert pm._queue.qsize() == 1


@pytest.mark.asyncio
async def test_enqueue_empty_bytes_skipped():
    pm = PlaybackManager()
    await pm.enqueue(b"")
    assert pm._queue.empty()


@pytest.mark.asyncio
async def test_interrupt_clears_pending_queue():
    pm = PlaybackManager()
    await pm.enqueue(FAKE_MP3)
    await pm.enqueue(FAKE_MP3)
    pm.interrupt()
    assert pm._queue.empty()
    assert pm._stop_flag[0] is True


# ── send_streaming_audio_response ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_streaming_response_sends_all_chunks():
    from unittest.mock import AsyncMock
    ws = MagicMock()
    ws.send_json = AsyncMock()
    ws.send_bytes = AsyncMock()

    async def fake_stream():
        yield "Hello.", FAKE_MP3
        yield "How are you?", FAKE_MP3

    completed = await send_streaming_audio_response(ws, "s1", fake_stream())
    assert completed is True
    assert ws.send_bytes.call_count == 2
    # tts_stream_start + 2×tts_chunk + tts_stream_end = 4
    assert ws.send_json.call_count == 4


@pytest.mark.asyncio
async def test_streaming_response_stops_on_cancel():
    from unittest.mock import AsyncMock
    ws = MagicMock()
    ws.send_json = AsyncMock()
    ws.send_bytes = AsyncMock()

    cancel = asyncio.Event()

    async def fake_stream():
        yield "First.", FAKE_MP3
        cancel.set()
        yield "Second.", FAKE_MP3

    completed = await send_streaming_audio_response(ws, "s1", fake_stream(), cancel_event=cancel)
    assert completed is False
    # Only first chunk sent
    assert ws.send_bytes.call_count == 1
    # End frame should be tts_stream_interrupted
    last_json = ws.send_json.call_args_list[-1][0][0]
    assert last_json["type"] == "tts_stream_interrupted"


@pytest.mark.asyncio
async def test_streaming_response_empty_audio_skipped():
    from unittest.mock import AsyncMock
    ws = MagicMock()
    ws.send_json = AsyncMock()
    ws.send_bytes = AsyncMock()

    async def fake_stream():
        yield "Hello.", b""  # empty — should be skipped
        yield "World.", FAKE_MP3

    await send_streaming_audio_response(ws, "s1", fake_stream())
    assert ws.send_bytes.call_count == 1
