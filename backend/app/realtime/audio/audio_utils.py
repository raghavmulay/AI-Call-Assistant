"""
audio_utils.py — Lightweight audio helpers for PCM16 / base64 transport.
"""
import base64


def encode_audio(raw_bytes: bytes) -> str:
    """Encode raw PCM16 bytes to base64 string for WebSocket transport."""
    return base64.b64encode(raw_bytes).decode("utf-8")


def decode_audio(b64_str: str) -> bytes:
    """Decode base64 string back to raw PCM16 bytes."""
    return base64.b64decode(b64_str)


def is_valid_pcm16(data: bytes) -> bool:
    """PCM16 frames are 2 bytes each — total length must be even."""
    return len(data) % 2 == 0


def chunk_duration_ms(num_bytes: int, sample_rate: int = 16000, channels: int = 1) -> float:
    """Return duration in milliseconds for a PCM16 byte chunk."""
    bytes_per_sample = 2  # 16-bit
    total_samples = num_bytes / (bytes_per_sample * channels)
    return (total_samples / sample_rate) * 1000
