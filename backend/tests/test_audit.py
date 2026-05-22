import pytest
import uuid
from backend.app.ai.orchestrator.orchestrator import process_query
from backend.app.ai.intent.intent_detector import detect_intent
from backend.app.ai.orchestrator.router import router, Route


@pytest.mark.asyncio
async def test_intelligence_ambiguity():
    """Test how the system handles ambiguous or conflicting intents."""
    query = "How much attendance is needed for placements?"
    intent, sub_intent, confidence, entity = detect_intent(query)
    # Query touches attendance, placements, or fees — any is acceptable
    assert intent in ["attendance", "placements", "fees", "general_chat"]


@pytest.mark.asyncio
async def test_memory_multi_turn_flow():
    """Test deep multi-turn conversational flow."""
    session_id = str(uuid.uuid4())

    resp1 = await process_query("Tell me about hostel", session_id)
    assert resp1.intent == "hostel"

    resp2 = await process_query("Are AC rooms available?", session_id)
    assert resp2.route in ["rag", "llm", "structured"]

    resp3 = await process_query("What are the fees?", session_id)
    assert resp3.intent == "fees"


@pytest.mark.asyncio
async def test_failure_db_outage():
    """Simulate DB failure during orchestration."""
    session_id = str(uuid.uuid4())
    resp = await process_query("show my attendance", session_id, db=None)
    assert resp.success == True
    assert "authenticated" in resp.response.lower() or "unavailable" in resp.response.lower()


@pytest.mark.asyncio
async def test_empty_malformed_input():
    """Test robust handling of bad input."""
    session_id = str(uuid.uuid4())
    resp1 = await process_query("", session_id)
    assert len(resp1.response) > 0

    resp2 = await process_query("   ", session_id)
    assert len(resp2.response) > 0
