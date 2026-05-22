"""
orchestrator.py — Central AI Orchestration Controller
The SINGLE entry point for all AI processing in the system.
"""

import uuid
from typing import Any, Dict, Optional

from backend.app.ai.intent.intent_detector import detect_intent
from backend.app.ai.orchestrator.router import router, Route
from backend.app.ai.orchestrator.memory_manager import memory_manager
from backend.app.ai.orchestrator.context_manager import context_manager
from backend.app.ai.orchestrator.response_builder import response_builder
from backend.app.ai.orchestrator.services import ai_services
from backend.app.ai.prompts.serializer import serializer

from backend.app.core.logger import logger

async def process_query(
    user_input: str,
    session_id: str,
    user_context: Dict[str, Any] = None,
    db: Any = None
) -> Dict[str, Any]:
    """
    Main orchestration flow.
    """
    # ── Normalize Input ──────────────────────────────────────────────────────
    query = user_input.strip()
    if not query:
        return response_builder.format_final_response(
            response_text="I didn't quite catch that. Could you please repeat?",
            intent="empty",
            route="none",
            session_id=session_id
        )

    logger.info(f"Processing query: {query!r} | session: {session_id}")

    import time
    import os
    from backend.app.core.config import settings
    
    DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() in ("true", "1") or settings.DEBUG
    total_start = time.perf_counter()
    latencies = {}

    try:
        # STEP 1: Load conversation memory
        step1_start = time.perf_counter()
        history = await memory_manager.get_history(session_id)
        metadata = await memory_manager.get_metadata(session_id)
        latencies["memory_load"] = time.perf_counter() - step1_start
        
        # STEP 2: Run intent detection
        step2_start = time.perf_counter()
        intent, sub_intent, confidence, entity = detect_intent(query)
        latencies["intent_detect"] = time.perf_counter() - step2_start
        logger.info(f"Detected intent: {intent} (conf: {confidence}) | entity: {entity}")
        
        # STEP 3: Route query intelligently
        step3_start = time.perf_counter()
        route = router.decide_route(intent, sub_intent, confidence=confidence)
        latencies["routing"] = time.perf_counter() - step3_start
        logger.info(f"Selected route: {route.value}")

        # STEP 4: Retrieve required data
        step4_start = time.perf_counter()
        context_data = ""
        sources = []
        direct_response = None  # skip LLM if set

        if route == Route.STRUCTURED_RETRIEVAL:
            data = await ai_services.get_structured_data(intent, sub_intent, entity)
            direct_response = serializer.serialize(intent, data, sub_intent=sub_intent, entity=entity)
            context_data = direct_response
            sources = [f"JSON:{intent}"]

        elif route == Route.GENERAL_LLM and intent in ("greeting", "thanks", "farewell"):
            _quick = {
                "greeting": "Hello! I'm Aria, your AI admission counselor at VIT Pune. How can I help you today?",
                "thanks": "You're welcome! Feel free to ask if you have any more questions about admissions, fees, hostel, or anything else.",
                "farewell": "Goodbye! Best of luck with your admission. Feel free to call back anytime you need help!"
            }
            direct_response = _quick[intent]
            context_data = direct_response
            sources = []
            
        elif route == Route.DATABASE_RETRIEVAL:
            student_id = user_context.get("student_id") if user_context else None
            if student_id and db:
                data = await ai_services.get_database_data(intent, str(student_id), db)
                context_data = serializer.serialize(intent, data)
                sources = [f"DB:{intent}"]
            else:
                context_data = "Student not authenticated or database unavailable."
                sources = ["DB:error"]

        elif route == Route.RAG_RETRIEVAL:
            context_data = await ai_services.get_rag_data(query)
            sources = ["ChromaDB/PDF"]

        latencies["retrieval"] = time.perf_counter() - step4_start

        # STEP 5 & 6: Skip LLM for structured — use direct response
        step5_start = time.perf_counter()
        if direct_response:
            ai_response = direct_response
            full_prompt = "[DIRECT — LLM skipped]"
            latencies["prompt_gen"] = 0
            latencies["llm_gen"] = 0
        else:
            full_prompt = context_manager.build_prompt(
                query=query,
                history=history,
                context_data=context_data,
                metadata=metadata,
                use_rag=(route == Route.RAG_RETRIEVAL)
            )
            latencies["prompt_gen"] = time.perf_counter() - step5_start
            step6_start = time.perf_counter()
            ai_response = await ai_services.get_llm_response(full_prompt)
            latencies["llm_gen"] = time.perf_counter() - step6_start

        # STEP 7: Build final conversational response
        step7_start = time.perf_counter()
        final_response = response_builder.format_final_response(
            response_text=ai_response,
            intent=intent,
            route=route.value,
            session_id=session_id,
            sources=sources
        )
        latencies["formatting"] = time.perf_counter() - step7_start

        # STEP 8: Update memory
        step8_start = time.perf_counter()
        await memory_manager.add_turn(session_id, "user", query)
        await memory_manager.add_turn(session_id, "assistant", ai_response)
        meta = {"intent": intent}
        if entity is not None:
            meta["branch"] = entity
        # Preserve branch across turns if not detected in current query
        elif metadata.get("branch") and intent not in ("greeting", "thanks", "farewell", "general_chat"):
            meta["branch"] = metadata["branch"]
        await memory_manager.update_metadata(session_id, **meta)
        latencies["memory_update"] = time.perf_counter() - step8_start

        total_latency = time.perf_counter() - total_start

        if DEBUG_MODE:
            trace_log = (
                f"\n"
                f"========================================================================\n"
                f"                     AI ORCHESTRATION FLOW TRACE                        \n"
                f"========================================================================\n"
                f" [Query]             : {query!r}\n"
                f" [Session ID]        : {session_id}\n"
                f"------------------------------------------------------------------------\n"
                f" 1. MEMORY STATE\n"
                f"    - History Size   : {len(history)} messages\n"
                f"    - Active Branch  : {metadata.get('branch', 'None')}\n"
                f"    - Last Intent    : {metadata.get('last_intent', 'None')}\n"
                f"    - Load Latency   : {latencies['memory_load'] * 1000:.2f}ms\n"
                f"------------------------------------------------------------------------\n"
                f" 2. INTENT DETECTION\n"
                f"    - Intent         : {intent}\n"
                f"    - Sub-Intent     : {sub_intent}\n"
                f"    - Confidence     : {confidence:.2f}\n"
                f"    - Extracted Entity: {entity}\n"
                f"    - Latency        : {latencies['intent_detect'] * 1000:.2f}ms\n"
                f"------------------------------------------------------------------------\n"
                f" 3. ROUTE SELECTION\n"
                f"    - Selected Route : {route.value}\n"
                f"    - Latency        : {latencies['routing'] * 1000:.2f}ms\n"
                f"------------------------------------------------------------------------\n"
                f" 4. DATA RETRIEVAL\n"
                f"    - Source         : {sources}\n"
                f"    - Has Data       : {bool(context_data)}\n"
                f"    - Context Length : {len(context_data)} chars\n"
                f"    - Latency        : {latencies['retrieval'] * 1000:.2f}ms\n"
                f"------------------------------------------------------------------------\n"
                f" 5. PROMPT GENERATION\n"
                f"    - Latency        : {latencies['prompt_gen'] * 1000:.2f}ms\n"
                f"    - Generated Prompt:\n"
                f"\"\"\"\n{full_prompt}\n\"\"\"\n"
                f"------------------------------------------------------------------------\n"
                f" 6. LLM GENERATION\n"
                f"    - LLM Response   : {ai_response!r}\n"
                f"    - Latency        : {latencies['llm_gen']:.4f}s\n"
                f"------------------------------------------------------------------------\n"
                f" 7. RESPONSE FORMATTING\n"
                f"    - Final Response : {final_response.response!r}\n"
                f"    - Latency        : {latencies['formatting'] * 1000:.2f}ms\n"
                f"------------------------------------------------------------------------\n"
                f" 8. MEMORY UPDATE\n"
                f"    - Latency        : {latencies['memory_update'] * 1000:.2f}ms\n"
                f"------------------------------------------------------------------------\n"
                f" [TOTAL LATENCY]     : {total_latency:.4f}s\n"
                f"========================================================================\n"
            )
            logger.info(trace_log)

        return final_response

    except Exception as e:
        logger.exception(f"Orchestration failure: {str(e)}")
        return response_builder.format_final_response(
            response_text="I'm sorry, I'm having a technical issue. Please try again.",
            intent="error",
            route="error",
            session_id=session_id,
            success=False
        )
