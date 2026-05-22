"""
test_barge_in.py — Barge-in / interruption handling tests.
"""
import pytest
import asyncio
from backend.app.realtime.conversation.conversation_state import (
    ConversationStateRegistry, VoiceState,
)


@pytest.fixture
def reg():
    return ConversationStateRegistry()


def test_streaming_response_is_interruptible(reg):
    reg.transition("s1", VoiceState.STREAMING_RESPONSE)
    assert reg.is_interruptible("s1") is True


def test_responding_is_interruptible(reg):
    reg.transition("s1", VoiceState.RESPONDING)
    assert reg.is_interruptible("s1") is True


def test_waiting_for_tts_is_interruptible(reg):
    reg.transition("s1", VoiceState.WAITING_FOR_TTS)
    assert reg.is_interruptible("s1") is True


def test_processing_not_interruptible(reg):
    reg.transition("s1", VoiceState.PROCESSING)
    assert reg.is_interruptible("s1") is False


def test_idle_not_interruptible(reg):
    reg.transition("s1", VoiceState.IDLE)
    assert reg.is_interruptible("s1") is False


def test_interrupt_sets_cancel_event(reg):
    reg.transition("s1", VoiceState.STREAMING_RESPONSE)
    reg.interrupt("s1")
    state = reg.get("s1")
    assert state.is_cancelled is True


def test_interrupt_transitions_to_interrupted(reg):
    reg.transition("s1", VoiceState.STREAMING_RESPONSE)
    reg.interrupt("s1")
    assert reg.get("s1").voice_state == VoiceState.INTERRUPTED


def test_interrupt_increments_counter(reg):
    reg.transition("s1", VoiceState.STREAMING_RESPONSE)
    reg.interrupt("s1")
    reg.transition("s1", VoiceState.STREAMING_RESPONSE)
    reg.interrupt("s1")
    assert reg.get("s1").interrupt_count == 2


def test_clear_interrupt_resets_event(reg):
    reg.transition("s1", VoiceState.STREAMING_RESPONSE)
    reg.interrupt("s1")
    reg.get("s1").clear_interrupt()
    assert reg.get("s1").is_cancelled is False


def test_interrupt_non_interruptible_state_is_safe(reg):
    reg.transition("s1", VoiceState.IDLE)
    reg.interrupt("s1")  # should not raise, should not change state
    assert reg.get("s1").voice_state == VoiceState.IDLE


def test_session_isolation_interrupt(reg):
    reg.transition("a", VoiceState.STREAMING_RESPONSE)
    reg.transition("b", VoiceState.STREAMING_RESPONSE)
    reg.interrupt("a")
    assert reg.get("a").is_cancelled is True
    assert reg.get("b").is_cancelled is False
