"""
stream_logger.py — Structured logger for real-time audio/WebSocket events.
"""
import logging
import time

_log = logging.getLogger("realtime.stream")


class StreamLogger:
    """Thin wrapper that emits structured log lines for every stream event."""

    def _emit(self, level: int, event: str, **kwargs):
        parts = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        _log.log(level, f"[{event}] {parts} ts={time.time():.4f}")

    # ── Connection lifecycle ──────────────────────────────────────────────────

    def log_connect(self, session_id: str, client: str):
        self._emit(logging.INFO, "WS_CONNECT", session_id=session_id, client=client)

    def log_disconnect(self, session_id: str, reason: str = "normal"):
        self._emit(logging.INFO, "WS_DISCONNECT", session_id=session_id, reason=reason)

    def log_reconnect(self, session_id: str):
        self._emit(logging.WARNING, "WS_RECONNECT", session_id=session_id)

    def log_session_timeout(self, session_id: str):
        self._emit(logging.WARNING, "SESSION_TIMEOUT", session_id=session_id)

    # ── Packet events ─────────────────────────────────────────────────────────

    def log_packet_received(self, session_id: str, chunk_id: int, latency_ms: float):
        self._emit(logging.DEBUG, "PACKET_RECV", session_id=session_id, chunk_id=chunk_id, latency_ms=f"{latency_ms:.2f}")

    def log_packet_dropped(self, session_id: str, chunk_id: int, reason: str):
        self._emit(logging.WARNING, "PACKET_DROP", session_id=session_id, chunk_id=chunk_id, reason=reason)

    # ── Buffer events ─────────────────────────────────────────────────────────

    def log_buffer_size(self, session_id: str, size: int):
        self._emit(logging.DEBUG, "BUFFER_SIZE", session_id=session_id, size=size)

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    def log_heartbeat(self, session_id: str, direction: str):
        self._emit(logging.DEBUG, "HEARTBEAT", session_id=session_id, direction=direction)


stream_logger = StreamLogger()
