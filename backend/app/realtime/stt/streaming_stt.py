"""
streaming_stt.py — Buffered streaming Whisper transcription.

Stage 3 Part 3 additions:
  - Partial transcript events during speech (every PARTIAL_INTERVAL_MS)
  - Partial transcription runs on a rolling window without clearing the buffer
  - Callback hook for partial updates
"""
import asyncio
import io
import time
import wave
from typing import Callable, Dict, Optional

from faster_whisper import WhisperModel

from backend.app.realtime.stt.vad_manager import vad_manager, FRAME_BYTES
from backend.app.realtime.stt.transcript_manager import transcript_manager
from backend.app.realtime.monitoring.voice_pipeline_logger import voice_logger

_MODEL: Optional[WhisperModel] = None

WHISPER_MODEL_SIZE = "tiny"
SAMPLE_RATE = 16000
MIN_AUDIO_MS = 300
PARTIAL_INTERVAL_MS = 2000   # emit partial transcript every 2s during speech


def _get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="float32")
    return _MODEL


# Pre-warm the model at import time so first transcription has no cold-start delay
def _warmup_model():
    import threading
    def _warm():
        try:
            import numpy as np
            silence = np.zeros(SAMPLE_RATE, dtype=np.int16).tobytes()
            _transcribe_pcm(silence)
        except Exception:
            pass
    threading.Thread(target=_warm, daemon=True).start()


def _pcm_to_wav_bytes(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


def _transcribe_pcm(pcm: bytes) -> str:
    if len(pcm) < int(SAMPLE_RATE * MIN_AUDIO_MS / 1000) * 2:
        return ""
    buf = io.BytesIO(_pcm_to_wav_bytes(pcm))
    model = _get_model()
    segments, _ = model.transcribe(
        buf,
        language="en",
        beam_size=1,
        vad_filter=False,
    )
    return " ".join(s.text.strip() for s in segments).strip()


class StreamingSTT:
    """
    Per-session rolling PCM16 buffer + VAD-triggered Whisper transcription.
    Emits partial transcripts during speech for real-time display.
    """

    def __init__(self):
        self._buffers: Dict[str, bytearray] = {}       # unprocessed incoming chunks
        self._speech_buffers: Dict[str, bytearray] = {} # accumulated speech audio
        self._last_partial_at: Dict[str, float] = {}
        self._partial_callbacks: Dict[str, Callable] = {}

    def set_partial_callback(self, session_id: str, callback: Callable):
        self._partial_callbacks[session_id] = callback

    def _get_buffer(self, session_id: str) -> bytearray:
        if session_id not in self._buffers:
            self._buffers[session_id] = bytearray()
            self._speech_buffers[session_id] = bytearray()
            self._last_partial_at[session_id] = time.time()
        return self._buffers[session_id]

    async def ingest(self, session_id: str, pcm_chunk: bytes) -> bool:
        if not pcm_chunk:
            return False

        buf = self._get_buffer(session_id)
        speech_buf = self._speech_buffers[session_id]
        buf.extend(pcm_chunk)

        turn_ended = False
        while len(buf) >= FRAME_BYTES:
            frame = bytes(buf[:FRAME_BYTES])
            del buf[:FRAME_BYTES]
            turn_ended = vad_manager.process_frame(session_id, frame)
            # Always accumulate frames into speech buffer
            speech_buf.extend(frame)
            if turn_ended:
                break

        # ── Partial transcript during active speech ───────────────────────────
        if not turn_ended and vad_manager.is_speaking(session_id):
            now = time.time()
            last = self._last_partial_at.get(session_id, 0)
            if (now - last) * 1000 >= PARTIAL_INTERVAL_MS and len(speech_buf) > 0:
                self._last_partial_at[session_id] = now
                snapshot = bytes(speech_buf)
                loop = asyncio.get_running_loop()
                partial_text = await loop.run_in_executor(None, _transcribe_pcm, snapshot)
                if partial_text:
                    transcript_manager.update_partial(session_id, partial_text)
                    cb = self._partial_callbacks.get(session_id)
                    if cb:
                        await cb(session_id, partial_text)

        # ── Final transcription on turn-end ───────────────────────────────────
        if turn_ended:
            t0 = time.perf_counter()
            loop = asyncio.get_running_loop()
            audio_snapshot = bytes(speech_buf)
            speech_buf.clear()
            buf.clear()
            self._last_partial_at[session_id] = time.time()

            text = await loop.run_in_executor(None, _transcribe_pcm, audio_snapshot)
            latency_ms = (time.perf_counter() - t0) * 1000

            transcript_manager.update_partial(session_id, text)
            voice_logger.log_stt(session_id, text, latency_ms)
            vad_manager.reset(session_id)
            return True

        return False

    def remove(self, session_id: str):
        self._buffers.pop(session_id, None)
        self._speech_buffers.pop(session_id, None)
        self._last_partial_at.pop(session_id, None)
        self._partial_callbacks.pop(session_id, None)
        vad_manager.remove(session_id)
        transcript_manager.remove(session_id)


streaming_stt = StreamingSTT()
_warmup_model()
