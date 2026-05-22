"""
tts_engine.py — Text-to-Speech synthesis.

Stage 3 Part 3 additions:
  - stream_synthesize(): sentence-level async generator for streaming TTS
  - Interruption-safe: checks cancel_event between sentences
  - split_sentences(): lightweight sentence splitter
"""
import asyncio
import io
import re
import time
import tempfile
import os
from typing import AsyncGenerator, List, Optional, Tuple

import edge_tts

from backend.app.realtime.monitoring.voice_pipeline_logger import voice_logger

DEFAULT_VOICE = "en-US-AriaNeural"


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentence-level chunks for streaming TTS.
    Avoids splitting on decimal points, abbreviations like Rs., Mr., Dr.
    """
    # Protect common abbreviations and currency from being split
    protected = text
    for abbr in ("Rs.", "Mr.", "Mrs.", "Dr.", "Prof.", "St.", "No.", "vs."):
        protected = protected.replace(abbr, abbr.replace(".", "<DOT>"))

    parts = re.split(r'(?<=[.!?])\s+', protected.strip())

    # Restore protected dots
    parts = [p.replace("<DOT>", ".") for p in parts]

    # Merge very short fragments (< 4 words) with the next sentence
    merged = []
    carry = ""
    for i, part in enumerate(parts):
        combined = (carry + " " + part).strip() if carry else part
        if len(combined.split()) < 6 and i < len(parts) - 1:
            carry = combined
        else:
            merged.append(combined)
            carry = ""
    if carry:
        merged.append(carry)
    return [s for s in merged if s.strip()]


async def _synthesize_edge(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def _synthesize_pyttsx3(text: str) -> bytes:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    try:
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        engine.stop()
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


class TTSEngine:
    """
    Async TTS engine with edge-tts primary and pyttsx3 fallback.

    synthesize()        — full response, returns bytes (Part 2 compat)
    stream_synthesize() — sentence-level async generator (Part 3 streaming)
    """

    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice

    async def synthesize(self, text: str, session_id: str = "") -> bytes:
        """Full synthesis — returns complete audio bytes."""
        if not text.strip():
            return b""
        t0 = time.perf_counter()
        engine_used = "edge-tts"
        try:
            audio_bytes = await _synthesize_edge(text, self.voice)
        except Exception:
            engine_used = "pyttsx3"
            try:
                loop = asyncio.get_running_loop()
                audio_bytes = await loop.run_in_executor(None, _synthesize_pyttsx3, text)
            except Exception as e:
                voice_logger.log_tts_error(session_id, str(e))
                return b""
        latency_ms = (time.perf_counter() - t0) * 1000
        voice_logger.log_tts(session_id, len(audio_bytes), latency_ms, engine_used)
        return audio_bytes

    async def stream_synthesize(
        self,
        text: str,
        session_id: str = "",
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[Tuple[str, bytes], None]:
        """
        Sentence-level streaming TTS generator.

        Yields (sentence_text, audio_bytes) for each sentence.
        Stops early if cancel_event is set (barge-in).
        """
        if not text.strip():
            return

        sentences = split_sentences(text)
        for i, sentence in enumerate(sentences):
            if cancel_event and cancel_event.is_set():
                voice_logger.log_tts(session_id, 0, 0.0, "cancelled")
                return

            t0 = time.perf_counter()
            engine_used = "edge-tts"
            try:
                audio_bytes = await _synthesize_edge(sentence, self.voice)
            except Exception:
                engine_used = "pyttsx3"
                try:
                    loop = asyncio.get_running_loop()
                    audio_bytes = await loop.run_in_executor(
                        None, _synthesize_pyttsx3, sentence
                    )
                except Exception as e:
                    voice_logger.log_tts_error(session_id, str(e))
                    continue

            latency_ms = (time.perf_counter() - t0) * 1000
            voice_logger.log_tts_chunk(session_id, i, len(audio_bytes), latency_ms, engine_used)
            yield sentence, audio_bytes


tts_engine = TTSEngine()
