"""
voice_pipeline_logger.py — Structured logger for the voice processing pipeline.

Stage 3 Part 3 additions:
  - log_interrupt()
  - log_tts_chunk()
  - log_partial_transcript()
  - log_barge_in()
"""
import logging
import time

_log = logging.getLogger("realtime.voice")


class VoicePipelineLogger:

    def _emit(self, level: int, event: str, **kwargs):
        parts = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        _log.log(level, f"[{event}] {parts} ts={time.time():.4f}")

    def log_stt(self, session_id: str, transcript: str, latency_ms: float):
        self._emit(logging.INFO, "STT_COMPLETE",
                   session_id=session_id,
                   transcript=repr(transcript[:80]),
                   latency_ms=f"{latency_ms:.1f}")

    def log_stt_error(self, session_id: str, error: str):
        self._emit(logging.ERROR, "STT_ERROR", session_id=session_id, error=error)

    def log_partial_transcript(self, session_id: str, partial: str):
        self._emit(logging.DEBUG, "STT_PARTIAL",
                   session_id=session_id,
                   partial=repr(partial[:60]))

    def log_vad_turn_end(self, session_id: str):
        self._emit(logging.DEBUG, "VAD_TURN_END", session_id=session_id)

    def log_turn_start(self, session_id: str, transcript: str, turn: int):
        self._emit(logging.INFO, "TURN_START",
                   session_id=session_id,
                   turn=turn,
                   transcript=repr(transcript[:80]))

    def log_orchestrator(self, session_id: str, response: str, latency_ms: float):
        self._emit(logging.INFO, "ORCHESTRATOR_COMPLETE",
                   session_id=session_id,
                   response=repr(response[:80]),
                   latency_ms=f"{latency_ms:.1f}")

    def log_tts(self, session_id: str, audio_bytes: int, latency_ms: float, engine: str):
        self._emit(logging.INFO, "TTS_COMPLETE",
                   session_id=session_id,
                   bytes=audio_bytes,
                   latency_ms=f"{latency_ms:.1f}",
                   engine=engine)

    def log_tts_chunk(self, session_id: str, index: int, audio_bytes: int,
                      latency_ms: float, engine: str):
        self._emit(logging.DEBUG, "TTS_CHUNK",
                   session_id=session_id,
                   index=index,
                   bytes=audio_bytes,
                   latency_ms=f"{latency_ms:.1f}",
                   engine=engine)

    def log_tts_error(self, session_id: str, error: str):
        self._emit(logging.ERROR, "TTS_ERROR", session_id=session_id, error=error)

    def log_interrupt(self, session_id: str, stage: str):
        self._emit(logging.WARNING, "BARGE_IN",
                   session_id=session_id,
                   stage=stage)

    def log_barge_in(self, session_id: str):
        self._emit(logging.WARNING, "BARGE_IN_DETECTED", session_id=session_id)

    def log_turn_complete(self, session_id: str, total_ms: float):
        self._emit(logging.INFO, "TURN_COMPLETE",
                   session_id=session_id,
                   total_ms=f"{total_ms:.1f}")

    def log_pipeline_error(self, session_id: str, stage: str, error: str):
        self._emit(logging.ERROR, "PIPELINE_ERROR",
                   session_id=session_id,
                   stage=stage,
                   error=error)


voice_logger = VoicePipelineLogger()
