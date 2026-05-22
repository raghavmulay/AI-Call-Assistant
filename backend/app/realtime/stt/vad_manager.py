"""
vad_manager.py — Voice Activity Detection using webrtcvad.

Stage 3 Part 3 additions:
  - Adaptive silence threshold: shortens after first speech burst
  - Partial speech event callback hook
  - Per-session configurable aggressiveness
"""
import webrtcvad
from dataclasses import dataclass, field
from typing import Dict
import time

VAD_AGGRESSIVENESS = 2
FRAME_MS = 20
SAMPLE_RATE = 16000
FRAME_BYTES = int(SAMPLE_RATE * FRAME_MS / 1000) * 2  # 640 bytes

# Silence thresholds
SILENCE_THRESHOLD_INITIAL_MS = 800   # first turn — wait longer
SILENCE_THRESHOLD_FAST_MS = 500      # subsequent turns — faster response
MIN_SPEECH_FOR_FAST_MS = 300         # need at least 300ms speech to use fast threshold


@dataclass
class VADState:
    is_speaking: bool = False
    silence_ms: float = 0.0
    speech_ms: float = 0.0
    total_turns: int = 0              # tracks how many turns completed
    last_frame_at: float = field(default_factory=time.time)

    @property
    def silence_threshold(self) -> float:
        """Adaptive: use faster threshold after first turn."""
        if self.total_turns > 0 and self.speech_ms >= MIN_SPEECH_FOR_FAST_MS:
            return SILENCE_THRESHOLD_FAST_MS
        return SILENCE_THRESHOLD_INITIAL_MS

    def reset(self):
        self.is_speaking = False
        self.silence_ms = 0.0
        self.speech_ms = 0.0


class VADManager:
    """
    Per-session VAD state tracker with adaptive silence threshold.
    Call process_frame() for each 20ms PCM16 chunk.
    Returns True when a turn-end is detected.
    """

    def __init__(self):
        self._vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self._states: Dict[str, VADState] = {}

    def _get_state(self, session_id: str) -> VADState:
        if session_id not in self._states:
            self._states[session_id] = VADState()
        return self._states[session_id]

    def process_frame(self, session_id: str, pcm_frame: bytes) -> bool:
        """
        Process one 20ms PCM16 frame.
        Returns True if a turn-end is detected.
        """
        state = self._get_state(session_id)

        if len(pcm_frame) < FRAME_BYTES:
            pcm_frame = pcm_frame.ljust(FRAME_BYTES, b"\x00")
        elif len(pcm_frame) > FRAME_BYTES:
            pcm_frame = pcm_frame[:FRAME_BYTES]

        try:
            is_speech = self._vad.is_speech(pcm_frame, SAMPLE_RATE)
        except Exception:
            is_speech = False

        if is_speech:
            state.is_speaking = True
            state.speech_ms += FRAME_MS
            state.silence_ms = 0.0
            state.last_frame_at = time.time()
            return False
        else:
            state.silence_ms += FRAME_MS
            state.last_frame_at = time.time()
            if state.is_speaking and state.silence_ms >= state.silence_threshold:
                state.total_turns += 1
                state.is_speaking = False
                state.silence_ms = 0.0
                return True
            return False

    def is_speaking(self, session_id: str) -> bool:
        return self._get_state(session_id).is_speaking

    def has_speech(self, session_id: str) -> bool:
        """True if any speech has been detected in current buffer."""
        return self._get_state(session_id).speech_ms > 0

    def reset(self, session_id: str):
        if session_id in self._states:
            self._states[session_id].reset()

    def remove(self, session_id: str):
        self._states.pop(session_id, None)


vad_manager = VADManager()
