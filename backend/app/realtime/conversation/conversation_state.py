"""
conversation_state.py — Live per-session voice conversation state.

Stage 3 Part 3 additions:
  - INTERRUPTED, STREAMING_RESPONSE, WAITING_FOR_TTS, PARTIAL_LISTENING states
  - Per-session cancellation Event for barge-in support
  - Adaptive silence threshold tracking
"""
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class VoiceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"               # user speaking / audio arriving
    PARTIAL_LISTENING = "partial_listening"  # partial transcript available
    PROCESSING = "processing"             # STT + orchestrator running
    WAITING_FOR_TTS = "waiting_for_tts"   # orchestrator done, TTS not started
    STREAMING_RESPONSE = "streaming_response"  # streaming TTS chunks to client
    RESPONDING = "responding"             # full TTS playing (Part 2 compat)
    INTERRUPTED = "interrupted"           # user barged in during response
    ERROR = "error"

    @property
    def is_busy(self) -> bool:
        return self in (
            VoiceState.PROCESSING,
            VoiceState.WAITING_FOR_TTS,
            VoiceState.STREAMING_RESPONSE,
            VoiceState.RESPONDING,
        )

    @property
    def is_interruptible(self) -> bool:
        return self in (
            VoiceState.STREAMING_RESPONSE,
            VoiceState.RESPONDING,
            VoiceState.WAITING_FOR_TTS,
        )


@dataclass
class ConversationState:
    session_id: str
    voice_state: VoiceState = VoiceState.IDLE
    active_transcript: str = ""
    active_response: str = ""
    turn_count: int = 0
    interrupt_count: int = 0
    last_activity: float = field(default_factory=time.time)
    state_changed_at: float = field(default_factory=time.time)

    # Cancellation token — set this to interrupt active TTS streaming
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    def transition(self, new_state: VoiceState):
        self.voice_state = new_state
        self.state_changed_at = time.time()
        self.last_activity = time.time()

    def request_interrupt(self):
        """Signal active TTS streaming to stop immediately."""
        self.cancel_event.set()
        self.interrupt_count += 1

    def clear_interrupt(self):
        """Reset cancellation token for next turn."""
        self.cancel_event.clear()

    @property
    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "voice_state": self.voice_state,
            "turn_count": self.turn_count,
            "interrupt_count": self.interrupt_count,
            "active_transcript": self.active_transcript,
            "active_response": self.active_response,
            "last_activity": self.last_activity,
        }


class ConversationStateRegistry:
    """Registry of live conversation states per session."""

    def __init__(self):
        self._states: Dict[str, ConversationState] = {}

    def get_or_create(self, session_id: str) -> ConversationState:
        if session_id not in self._states:
            self._states[session_id] = ConversationState(session_id=session_id)
        return self._states[session_id]

    def get(self, session_id: str) -> Optional[ConversationState]:
        return self._states.get(session_id)

    def remove(self, session_id: str):
        self._states.pop(session_id, None)

    def transition(self, session_id: str, new_state: VoiceState):
        self.get_or_create(session_id).transition(new_state)

    def is_busy(self, session_id: str) -> bool:
        state = self.get(session_id)
        return state is not None and state.voice_state.is_busy

    def is_interruptible(self, session_id: str) -> bool:
        state = self.get(session_id)
        return state is not None and state.voice_state.is_interruptible

    def interrupt(self, session_id: str):
        """Trigger barge-in: cancel active response and transition to INTERRUPTED."""
        state = self.get(session_id)
        if state and state.voice_state.is_interruptible:
            state.request_interrupt()
            state.transition(VoiceState.INTERRUPTED)


conversation_state = ConversationStateRegistry()
