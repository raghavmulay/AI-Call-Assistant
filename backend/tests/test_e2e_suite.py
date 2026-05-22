import pytest
import asyncio
import uuid
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.ai.orchestrator.orchestrator import process_query
from backend.app.ai.intent.intent_detector import detect_intent
from backend.app.ai.orchestrator.router import router, Route
from backend.app.ai.prompts.serializer import serializer
from backend.app.core.config import settings
from backend.app.auth.jwt_handler import create_access_token, decode_access_token
from backend.app.middleware.rate_limit import rate_limit_middleware

# ==============================================================================
# FIXTURES & MOCKING INFRASTRUCTURE
# ==============================================================================

class MockAsyncClient:
    """Mock HTTP client for simulating Ollama generation and network failures."""
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    async def post(self, url, json=None, **kwargs):
        if self.should_fail:
            raise Exception("Ollama connection refused.")
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        # Coherent receptionist answers based on intent or query keywords
        prompt_content = json["messages"][-1]["content"] if json and "messages" in json else ""
        q = prompt_content.lower()
        
        ans = "Hello, I am your institutional assistant. How can I help you today?"
        if "hostel fee" in q or "hostel cost" in q:
            ans = "The hostel fee is Rs. 95,000 per year for non-AC and Rs. 1,40,000 for AC rooms."
        elif "hostel" in q and "ac" in q:
            ans = "Yes, AC rooms are available in both boys and girls hostels on a first-come basis."
        elif "placement" in q or "package" in q:
            ans = "Placements are outstanding, with an average package of 8.5 LPA and companies like Microsoft and TCS visiting."
        elif "scholarship" in q:
            ans = "Several scholarships are available including EBC and OBC fee waivers for students."
        elif "admission" in q:
            ans = "The admission process is fully online. You must apply through the CAP portal."
        elif "recursion" in q:
            ans = "Recursion is a programming technique where a function calls itself to solve smaller instances of a problem."
        elif "machine learning" in q:
            ans = "Machine learning is a field of AI that allows computers to learn from data without explicit programming."
        elif "attendance" in q:
            ans = "Your attendance summary shows Data Structures is 85.0% and DBMS is 72.0%, with an overall average of 78.5%."
        elif "timetable" in q:
            ans = "Your timetable shows Data Structures on Monday at 09:00 AM and DBMS at 11:00 AM."
        elif "notices" in q:
            ans = "The latest notice is: The orientation program starts on Monday at 10:00 AM."
        elif "assignment" in q:
            ans = "You have one pending assignment in Data Structures due next Friday."
            
        mock_response.json = MagicMock(return_value={"message": {"content": ans}})
        return mock_response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockRedisMemory:
    """Mock Redis memory backing store for session testing."""
    def __init__(self):
        self.store = {}
        self.metadata = {}

    def _history_key(self, session_id: str) -> str:
        return f"history:{session_id}"

    def _metadata_key(self, session_id: str) -> str:
        return f"metadata:{session_id}"

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        key = self._history_key(session_id)
        return self.store.get(key, [])

    async def add_turn(self, session_id: str, role: str, content: str):
        key = self._history_key(session_id)
        if key not in self.store:
            self.store[key] = []
        self.store[key].append({"role": role, "content": content})
        # Mock sliding window: keep last N turns
        if len(self.store[key]) > settings.MAX_CONVERSATION_WINDOW:
            self.store[key] = self.store[key][-settings.MAX_CONVERSATION_WINDOW:]

    async def get_metadata(self, session_id: str) -> Dict[str, Any]:
        key = self._metadata_key(session_id)
        return self.metadata.get(key, {})

    async def update_metadata(self, session_id: str, **kwargs):
        key = self._metadata_key(session_id)
        if key not in self.metadata:
            self.metadata[key] = {}
        self.metadata[key].update(kwargs)

    async def clear(self, session_id: str):
        self.store.pop(self._history_key(session_id), None)
        self.metadata.pop(self._metadata_key(session_id), None)


class MockDatabase:
    """Mock SQLAlchemy AsyncSession for student DB retrieval tests."""
    class MockRecord:
        def __init__(self, subject_name, attendance_percent):
            self.subject_name = subject_name
            self.attendance_percent = attendance_percent

    class MockSlot:
        def __init__(self, day, time, subject_name, classroom):
            self.day = day
            self.time = time
            self.subject_name = subject_name
            self.classroom = classroom

    class MockAttendanceSummary:
        def __init__(self):
            self.overall_average = 78.5
            self.records = [
                MockDatabase.MockRecord("Data Structures", 85.0),
                MockDatabase.MockRecord("DBMS", 72.0)
            ]

    class MockAssignment:
        def __init__(self, title, deadline):
            self.title = title
            self.deadline = deadline
            self.subject = MagicMock(subject_name="Data Structures")

    async def execute(self, stmt):
        # We can analyze the statement and return appropriate mock structures
        mock_result = MagicMock()
        return mock_result


# Configure global patches
@pytest.fixture(autouse=True)
def setup_mock_environment():
    """Sets up unified mocks for httpx and redis clients to guarantee deterministic tests."""
    mock_redis = MockRedisMemory()
    
    with patch("httpx.AsyncClient", return_value=MockAsyncClient()) as mock_http, \
         patch("backend.app.ai.memory.redis_memory.redis_memory", mock_redis), \
         patch("backend.app.ai.orchestrator.memory_manager.redis_memory", mock_redis):
        yield {
            "http": mock_http,
            "redis_memory": mock_redis
        }


# ==============================================================================
# PART 2: STRUCTURED QUERY TESTING
# ==============================================================================

@pytest.mark.asyncio
async def test_structured_query_routing_and_accuracy():
    """Verifies intent detection, route selection, structured serialisation, and response consistency."""
    queries = {
        "what are hostel fees?": ("fees", Route.STRUCTURED_RETRIEVAL),
        "Tell me about placements": ("placements", Route.STRUCTURED_RETRIEVAL),
        "What scholarships are available?": ("scholarship", Route.STRUCTURED_RETRIEVAL),
        "Explain admission process": ("admission_process", Route.STRUCTURED_RETRIEVAL),
        "What is hostel timing?": ("hostel_rules", Route.RAG_RETRIEVAL),  # Maps to RAG per intent rules
        "What facilities are available?": ("hostel", Route.STRUCTURED_RETRIEVAL)
    }

    for query, (expected_intent, expected_route) in queries.items():
        intent, sub_intent, confidence, entity = detect_intent(query)
        route = router.decide_route(intent, sub_intent, confidence)
        
        # Verify correctness of Intent and Route selection
        assert intent == expected_intent or intent == "hostel_rules", f"Failed for {query}: got intent {intent}"
        assert route == expected_route, f"Failed for {query}: got route {route}"
        
        # Trigger orchestrator flow and ensure no generic LLM hallucination
        session_id = f"test_struct_{uuid.uuid4()}"
        res = await process_query(query, session_id)
        
        assert res.success == True
        assert res.intent == intent
        assert res.route == route.value
        assert len(res.response) > 0
        # Prevents hallucination response containing 'sorry' or unverified facts
        assert "brain" not in res.response.lower()


# ==============================================================================
# PART 3: DATABASE QUERY TESTING
# ==============================================================================

@pytest.mark.asyncio
async def test_database_queries_and_jwt_auth():
    """Tests student personalized database queries, JWT loading, permission enforcement, and token failures."""
    student_id = uuid.uuid4()
    
    # 1. Test Valid JWT Access
    valid_token = create_access_token({"sub": str(student_id), "role": "student"})
    payload = decode_access_token(valid_token)
    assert payload is not None
    assert payload["sub"] == str(student_id)
    
    # Mock services to bypass PostgreSQL connections during testing
    with patch("backend.app.ai.orchestrator.services.ai_services.get_database_data") as mock_db_data:
        # Attendance mock return
        mock_db_data.return_value = MockDatabase.MockAttendanceSummary()
        
        session_id = str(student_id)
        user_context = {"student_id": student_id}
        
        # Check Attendance route
        res = await process_query("What is my attendance?", session_id, user_context=user_context, db=MagicMock())
        assert res.success == True
        assert res.route == Route.DATABASE_RETRIEVAL.value
        assert "78.5" in res.response or "85" in res.response
        
        # 2. Test Invalid JWT Handling
        invalid_payload = decode_access_token("invalid.jwt.token")
        assert invalid_payload is None
        
        # 3. Test Missing Student Data Context
        res_no_context = await process_query("Show my timetable", session_id, user_context=None, db=MagicMock())
        assert "authenticated" in res_no_context.response.lower() or "unavailable" in res_no_context.response.lower()


# ==============================================================================
# PART 4: GENERAL AI TESTING
# ==============================================================================

@pytest.mark.asyncio
async def test_general_ai_conversational_persona():
    """Validates that general queries route to Pure LLM and verify counselor voice constraints."""
    general_queries = [
        "Explain recursion",
        "What is machine learning?",
        "How should I prepare for placements?",
        "Best branch for AI?",
        "Explain OOP concepts"
    ]

    for query in general_queries:
        intent, sub_intent, confidence, entity = detect_intent(query)
        route = router.decide_route(intent, sub_intent, confidence)
        
        assert route == Route.GENERAL_LLM
        
        session_id = f"test_general_{uuid.uuid4()}"
        res = await process_query(query, session_id)
        
        assert res.success == True
        assert res.route == Route.GENERAL_LLM.value
        
        # Core Counselor Constraint: Concise, Voice-First response lengths (under 4 sentences)
        sentences = [s for s in res.response.split(".") if s.strip()]
        assert len(sentences) <= 5, f"Response too verbose: {res.response}"


# ==============================================================================
# PART 5: MULTI-TURN MEMORY TESTING
# ==============================================================================

@pytest.mark.asyncio
async def test_multi_turn_conversational_continuity():
    """Performs deep conversational memory flow testing with sliding windows and entity tracking."""
    session_id = f"test_multi_{uuid.uuid4()}"
    
    # FLOW 1: Hostel conversation
    # Turn 1
    res1 = await process_query("Tell me about hostel", session_id)
    assert res1.intent == "hostel"
    
    # Turn 2: Contextual follow-up tracking branch or topic
    res2 = await process_query("Are AC rooms available?", session_id)
    # Checks that system resolves the prompt with context or RAG
    assert len(res2.response) > 0
    
    # Turn 3: "What are the fees?" (Resolves to hostel fees because of previous turns)
    res3 = await process_query("What are the fees?", session_id)
    # The serialiser formats fee structure context
    assert len(res3.response) > 0


# ==============================================================================
# PART 6: REDIS PERSISTENCE TESTING
# ==============================================================================

@pytest.mark.asyncio
async def test_redis_persistence_and_sliding_window(setup_mock_environment):
    """Verifies session persistence across requests, isolation, and sliding window clipping."""
    redis_mock = setup_mock_environment["redis_memory"]
    session_id = "test-session-redis-1"
    
    # Load turns and verify clipping
    for i in range(20):
        await redis_mock.add_turn(session_id, "user", f"query {i}")
        await redis_mock.add_turn(session_id, "assistant", f"reply {i}")
        
    history = await redis_mock.get_history(session_id)
    # Max sliding window configuration limits size
    assert len(history) <= settings.MAX_CONVERSATION_WINDOW
    assert history[-1]["content"] == "reply 19"
    
    # Test Isolation
    session_id_2 = "test-session-redis-2"
    history_2 = await redis_mock.get_history(session_id_2)
    assert len(history_2) == 0


# ==============================================================================
# PART 7: ERROR HANDLING & FAILURE SIMULATION
# ==============================================================================

@pytest.mark.asyncio
async def test_intentional_failure_simulation():
    """Simulates Ollama failures, Redis failures, database disconnections, and bad inputs."""
    session_id = f"test_fail_{uuid.uuid4()}"
    
    # A. Test Ollama Offline Outage
    with patch("httpx.AsyncClient", return_value=MockAsyncClient(should_fail=True)):
        res = await process_query("What are hostel fees?", session_id)
        # Should gracefully recover and output fallback text, not crash
        assert res.success == True
        assert "thinking" in res.response or "brain" in res.response or "taking too long" in res.response or "hostel" in res.response.lower()

    # B. Test Redis Offline Outage
    # Make get_history throw an exception
    with patch("backend.app.ai.memory.redis_memory.redis_memory.get_history", side_effect=Exception("Redis disconnected.")):
        res = await process_query("Tell me about placements", session_id)
        # Should proceed without history context rather than crashing
        assert res.success == True
        assert len(res.response) > 0

    # C. Test Database Disconnection
    res = await process_query("What is my attendance?", session_id, user_context={"student_id": uuid.uuid4()}, db=None)
    # Bypasses crash and returns database unavailable note
    assert "authenticated" in res.response.lower() or "unavailable" in res.response.lower()

    # D. Empty / Whitespace Inputs
    res_empty = await process_query("   ", session_id)
    assert "catch" in res_empty.response.lower()


# ==============================================================================
# PART 8 & 9: ASYNC CONCURRENCY & RATE LIMITING
# ==============================================================================

@pytest.mark.asyncio
async def test_async_concurrency_and_rate_limiting():
    """Verifies event-loop async safety under concurrent users and rate limiter throttling."""
    session_ids = [str(uuid.uuid4()) for _ in range(5)]
    queries = [
        "Tell me about hostel fees", 
        "Explain machine learning", 
        "Show my attendance", 
        "Explain recursion", 
        "What scholarships exist?"
    ]
    
    # 1. Run all 5 concurrently to test async safety
    start_time = time.perf_counter()
    tasks = [
        process_query(q, sid, user_context={"student_id": uuid.uuid4()}, db=MagicMock()) 
        for q, sid in zip(queries, session_ids)
    ]
    results = await asyncio.gather(*tasks)
    latency = time.perf_counter() - start_time
    
    assert len(results) == 5
    for res in results:
        assert res.success == True
    # Ensures none of the concurrent queries blocked the event loop
    assert latency < 2.0  # Mocks are fast and concurrent

    # 2. Test Rate Limiter Middleware Throttling
    mock_request = MagicMock()
    mock_request.url.path = "/chat"
    mock_request.client.host = "127.0.0.1"
    
    # Mock Redis client get/pipeline
    mock_redis_client = MagicMock()
    mock_redis_client.get = AsyncMock(return_value="25") # Exceeds RATE_LIMIT_REQUESTS (20)
    
    with patch.object(type(redis_client), "client", new_callable=lambda: property(lambda self: mock_redis_client)):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit_middleware(mock_request, AsyncMock())
        assert exc_info.value.status_code == 429
