"""
test_transcript_manager.py — TranscriptManager unit tests.
"""
import pytest
from backend.app.realtime.stt.transcript_manager import TranscriptManager


@pytest.fixture
def tm():
    return TranscriptManager()


def test_update_partial(tm):
    tm.update_partial("s1", "hello world")
    assert tm.get_partial("s1") == "hello world"


def test_finalize_returns_text(tm):
    tm.update_partial("s1", "what are the fees")
    result = tm.finalize("s1")
    assert result == "what are the fees"


def test_finalize_clears_partial(tm):
    tm.update_partial("s1", "test")
    tm.finalize("s1")
    assert tm.get_partial("s1") == ""


def test_finalize_archives_to_history(tm):
    tm.update_partial("s1", "turn one")
    tm.finalize("s1")
    tm.update_partial("s1", "turn two")
    tm.finalize("s1")
    state = tm.get_or_create("s1")
    assert len(state.history) == 2
    assert state.history[0] == "turn one"
    assert state.history[1] == "turn two"


def test_finalize_empty_partial_returns_empty(tm):
    result = tm.finalize("s1")
    assert result == ""


def test_clear_resets_state(tm):
    tm.update_partial("s1", "something")
    tm.finalize("s1")
    tm.clear("s1")
    assert tm.get_partial("s1") == ""
    assert tm.get_final("s1") == ""


def test_session_isolation(tm):
    tm.update_partial("a", "session a text")
    tm.update_partial("b", "session b text")
    assert tm.get_partial("a") == "session a text"
    assert tm.get_partial("b") == "session b text"


def test_remove(tm):
    tm.update_partial("s1", "data")
    tm.remove("s1")
    assert "s1" not in tm._states
