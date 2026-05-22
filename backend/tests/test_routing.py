import pytest
from backend.app.ai.intent.intent_detector import detect_intent
from backend.app.ai.orchestrator.router import router, Route

def test_structured_routing():
    queries = ["what are the hostel fees?", "admission process 2025", "placements in it branch"]
    for q in queries:
        intent, sub_intent, confidence, entity = detect_intent(q)
        route = router.decide_route(intent, sub_intent, confidence)
        assert route == Route.STRUCTURED_RETRIEVAL

def test_database_routing():
    queries = ["show my attendance", "what is my timetable?", "any new notices?"]
    for q in queries:
        intent, sub_intent, confidence, entity = detect_intent(q)
        route = router.decide_route(intent, sub_intent, confidence)
        assert route == Route.DATABASE_RETRIEVAL

def test_rag_routing():
    queries = ["what is the hostel policy for visitors?", "show me the syllabus", "college regulations"]
    for q in queries:
        intent, sub_intent, confidence, entity = detect_intent(q)
        route = router.decide_route(intent, sub_intent, confidence)
        assert route == Route.RAG_RETRIEVAL

def test_low_confidence_fallback():
    query = "xyz random gibberish"
    intent, sub_intent, confidence, entity = detect_intent(query)
    route = router.decide_route(intent, sub_intent, confidence)
    assert route == Route.GENERAL_LLM
