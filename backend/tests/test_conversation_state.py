"""
test_conversation_state.py — ConversationState and registry tests.
"""
import pytest
from backend.app.realtime.conversation.conversation_state import (
    ConversationStateRegistry, VoiceState,
)


@pytest.fixture
def reg():
    return ConversationStateRegistry()


def test_initial_state_is_idle(reg):
    state = reg.get_or_create("s1")
    assert state.voice_state == VoiceState.IDLE


def test_transition_changes_state(reg):
    reg.transition("s1", VoiceState.LISTENING)
    assert reg.get("s1").voice_state == VoiceState.LISTENING


def test_is_busy_when_processing(reg):
    reg.transition("s1", VoiceState.PROCESSING)
    assert reg.is_busy("s1") is True


def test_is_busy_when_responding(reg):
    reg.transition("s1", VoiceState.RESPONDING)
    assert reg.is_busy("s1") is True


def test_not_busy_when_idle(reg):
    reg.transition("s1", VoiceState.IDLE)
    assert reg.is_busy("s1") is False


def test_not_busy_when_listening(reg):
    reg.transition("s1", VoiceState.LISTENING)
    assert reg.is_busy("s1") is False


def test_unknown_session_not_busy(reg):
    assert reg.is_busy("nonexistent") is False


def test_session_isolation(reg):
    reg.transition("a", VoiceState.PROCESSING)
    reg.transition("b", VoiceState.IDLE)
    assert reg.is_busy("a") is True
    assert reg.is_busy("b") is False


def test_remove_cleans_up(reg):
    reg.get_or_create("s1")
    reg.remove("s1")
    assert reg.get("s1") is None


def test_to_dict_contains_required_keys(reg):
    state = reg.get_or_create("s1")
    d = state.to_dict()
    for key in ("session_id", "voice_state", "turn_count", "active_transcript", "active_response"):
        assert key in d
