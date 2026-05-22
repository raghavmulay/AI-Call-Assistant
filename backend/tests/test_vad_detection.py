"""
test_vad_detection.py — VAD manager unit tests.
"""
import pytest
from backend.app.realtime.stt.vad_manager import VADManager, FRAME_BYTES, SAMPLE_RATE


def make_silence(ms: int = 20) -> bytes:
    samples = int(SAMPLE_RATE * ms / 1000)
    return b"\x00\x00" * samples


def make_tone(ms: int = 20, freq: int = 440) -> bytes:
    """Generate a simple sine-wave tone as PCM16."""
    import struct, math
    samples = int(SAMPLE_RATE * ms / 1000)
    result = bytearray()
    for i in range(samples):
        val = int(32767 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE))
        result += struct.pack("<h", val)
    return bytes(result)


def test_silence_does_not_trigger_turn_end():
    vad = VADManager()
    for _ in range(50):  # 1 second of silence
        result = vad.process_frame("s1", make_silence())
    assert not vad.is_speaking("s1")


def test_speech_sets_speaking_flag():
    vad = VADManager()
    # Feed enough speech frames to trigger VAD
    for _ in range(10):
        vad.process_frame("s1", make_tone())
    assert vad.is_speaking("s1")


def test_turn_end_after_speech_then_silence():
    vad = VADManager()
    # Speak for 500ms
    for _ in range(25):
        vad.process_frame("s1", make_tone())
    # Silence for 1 second (> SILENCE_THRESHOLD_MS=800ms)
    turn_ended = False
    for _ in range(50):
        if vad.process_frame("s1", make_silence()):
            turn_ended = True
            break
    assert turn_ended


def test_short_frame_padded_safely():
    """Frames shorter than FRAME_BYTES must not raise."""
    vad = VADManager()
    short = b"\x00\x00" * 10  # too short
    result = vad.process_frame("s1", short)
    assert isinstance(result, bool)


def test_session_isolation():
    vad = VADManager()
    for _ in range(10):
        vad.process_frame("a", make_tone())
    assert not vad.is_speaking("b")


def test_reset_clears_state():
    vad = VADManager()
    for _ in range(10):
        vad.process_frame("s1", make_tone())
    vad.reset("s1")
    assert not vad.is_speaking("s1")


def test_remove_cleans_up():
    vad = VADManager()
    vad.process_frame("s1", make_silence())
    vad.remove("s1")
    assert "s1" not in vad._states
