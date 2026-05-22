"""
transcript_manager.py — Per-session transcript state.

Accumulates partial transcripts from STT, finalizes on turn-end.
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TranscriptState:
    session_id: str
    partial: str = ""
    final: str = ""
    started_at: float = field(default_factory=time.time)
    finalized_at: Optional[float] = None
    history: List[str] = field(default_factory=list)  # past finalized turns

    def update_partial(self, text: str):
        self.partial = text.strip()

    def finalize(self) -> str:
        """Commit partial as final, archive it, return the final text."""
        text = self.partial.strip()
        if text:
            self.final = text
            self.history.append(text)
            self.finalized_at = time.time()
        self.partial = ""
        return text

    def clear(self):
        """Reset for next turn."""
        self.partial = ""
        self.final = ""
        self.started_at = time.time()
        self.finalized_at = None


class TranscriptManager:
    """Registry of per-session transcript states."""

    def __init__(self):
        self._states: Dict[str, TranscriptState] = {}

    def get_or_create(self, session_id: str) -> TranscriptState:
        if session_id not in self._states:
            self._states[session_id] = TranscriptState(session_id=session_id)
        return self._states[session_id]

    def update_partial(self, session_id: str, text: str):
        self.get_or_create(session_id).update_partial(text)

    def finalize(self, session_id: str) -> str:
        return self.get_or_create(session_id).finalize()

    def clear(self, session_id: str):
        self.get_or_create(session_id).clear()

    def get_final(self, session_id: str) -> str:
        return self.get_or_create(session_id).final

    def get_partial(self, session_id: str) -> str:
        return self.get_or_create(session_id).partial

    def remove(self, session_id: str):
        self._states.pop(session_id, None)


transcript_manager = TranscriptManager()
