"""
test_audio_streaming.py — Audio packet processing and encoding tests.
"""
import pytest
import struct
import base64
from backend.app.realtime.audio.audio_utils import encode_audio, decode_audio, is_valid_pcm16, chunk_duration_ms
from backend.app.realtime.schemas.audio_packet import AudioPacket
from backend.app.realtime.audio.packet_processor import process_audio_packet
from backend.app.realtime.audio.chunk_buffer import buffer_registry


def make_pcm16(samples: int = 640) -> bytes:
    """Generate silent PCM16 audio (all zeros)."""
    return b"\x00\x00" * samples


@pytest.mark.asyncio
async def test_process_valid_packet():
    raw = make_pcm16(640)
    packet = AudioPacket(session_id="s1", chunk_id=0, audio_data=encode_audio(raw))
    result = await process_audio_packet(packet)
    assert result is True
    await buffer_registry.remove("s1")


@pytest.mark.asyncio
async def test_process_invalid_base64():
    packet = AudioPacket(session_id="s2", chunk_id=0, audio_data="!!!not_base64!!!")
    result = await process_audio_packet(packet)
    assert result is False


@pytest.mark.asyncio
async def test_process_odd_length_pcm16():
    # 3 bytes — not valid PCM16
    bad = base64.b64encode(b"\x00\x01\x02").decode()
    packet = AudioPacket(session_id="s3", chunk_id=0, audio_data=bad)
    result = await process_audio_packet(packet)
    assert result is False


def test_encode_decode_roundtrip():
    raw = make_pcm16(320)
    assert decode_audio(encode_audio(raw)) == raw


def test_is_valid_pcm16():
    assert is_valid_pcm16(b"\x00\x01\x02\x03") is True
    assert is_valid_pcm16(b"\x00\x01\x02") is False


def test_chunk_duration_ms():
    # 640 samples × 2 bytes = 1280 bytes → 40 ms at 16kHz mono
    assert chunk_duration_ms(1280, 16000, 1) == pytest.approx(40.0)
