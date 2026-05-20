"""
services/ai_service.py — AI Integration Service Layer
Bridges the FastAPI backend with the existing RAG/LLM pipeline modules.

FIXES APPLIED:
- FIX #3: rag_pipeline.py has no get_rag_answer(). Replaced with
          direct calls to retrieve() + generate_response().
- FIX #4: SpeechToText has no transcribe_file(). Correct method is transcribe(path).
- Added RAG_DIR to sys.path so relative imports inside app/rag/ work.
"""

import sys
import os
import uuid
import base64
import tempfile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.student_service import get_attendance_for_student, get_timetable_for_student
from backend.services.chat_service import save_chat

# ── Path setup ────────────────────────────────────────────────────────────────
# PROJECT_ROOT = AI-Call-Assistant/  (two levels up from backend/services/)
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Also add app/rag/ so that retriever.py's own relative imports work correctly
RAG_DIR = os.path.join(PROJECT_ROOT, "app", "rag")
if RAG_DIR not in sys.path:
    sys.path.insert(0, RAG_DIR)


# ── AI Pipeline Helpers ───────────────────────────────────────────────────────

def _get_rag_answer(query: str) -> str:
    """
    FIX #3: rag_pipeline.py only has run_rag_pipeline() (interactive CLI).
    There is no get_rag_answer() function — it was a wrong assumption.

    Correct approach: call retrieve() from retriever.py to get document context,
    then pass context + query to generate_response() from ollama_llm.py.

    Gracefully returns an error message if ollama or chromadb is unavailable.
    """
    try:
        from app.rag.retriever import retrieve
        from app.llm.ollama_llm import generate_response

        results = retrieve(query, top_k=3)
        # Extract top matching document chunks
        docs = results.get("documents", [[]])[0]
        context = "\n".join(docs) if docs else ""
        prompt = f"Context:\n{context}\n\nQuestion: {query}" if context else query
        return generate_response(prompt)
    except Exception as e:
        # Graceful degradation — return error in response, don't crash the API
        return f"AI service unavailable: {str(e)}"


def _import_stt_class():
    """
    FIX #4: Verify SpeechToText import works.
    Returns the class or raises RuntimeError.
    """
    try:
        from app.stt.whisper_stt import SpeechToText  # noqa: F401
        return SpeechToText
    except ImportError as e:
        raise RuntimeError(f"STT module not available: {e}")


# ── Service Functions ─────────────────────────────────────────────────────────

async def handle_chat_query(
    student_id: uuid.UUID,
    message: str,
    db: AsyncSession,
) -> dict:
    """
    Main AI text chat handler.
    1. Fetch student attendance + timetable from DB as context.
    2. Enrich the user query with this context.
    3. Call the RAG+LLM pipeline.
    4. Persist the conversation to chat_history.
    5. Return the response.
    """
    # ── Build student context string ────────────────────────────────────────
    context_str = ""
    try:
        attendance_summary = await get_attendance_for_student(student_id, db)
        timetable = await get_timetable_for_student(student_id, db)

        attendance_text = ", ".join(
            f"{r.subject_name}: {r.attendance_percent}%"
            for r in attendance_summary.records
        )
        timetable_text = ", ".join(
            f"{slot.subject_name} at {slot.time} in {slot.classroom}"
            for slot in timetable[:5]
        )
        context_str = (
            f"Student data — Attendance average: {attendance_summary.overall_average}%. "
            f"Subjects: {attendance_text}. "
            f"Today's classes: {timetable_text}."
        )
    except Exception:
        # Student may not have DB data yet — proceed without context
        pass

    # ── Call RAG + LLM ──────────────────────────────────────────────────────
    enriched_query = (
        f"{context_str}\n\nStudent question: {message}" if context_str else message
    )
    ai_response: str = _get_rag_answer(enriched_query)

    # ── Save conversation turn ──────────────────────────────────────────────
    await save_chat(student_id, message, ai_response, db)

    return {"user_message": message, "ai_response": ai_response}


async def handle_voice_query(
    student_id: uuid.UUID,
    audio_base64: str,
    db: AsyncSession,
) -> dict:
    """
    Voice query handler.
    1. Decode base64 WAV audio from client.
    2. Transcribe using Whisper STT — calls stt.transcribe(path) [FIX #4].
       Note: SpeechToText.transcribe() auto-deletes the temp file.
    3. Forward transcription to handle_chat_query.
    """
    # Decode base64 → bytes → temp WAV file
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception:
        return {"error": "Invalid base64 audio data.", "ai_response": None}

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        SpeechToText = _import_stt_class()
        stt = SpeechToText(model_size="base")
        # FIX #4: correct method name is .transcribe(path), NOT .transcribe_file(path)
        transcribed_text = stt.transcribe(tmp_path)
        # Note: stt.transcribe() internally deletes tmp_path on success

    except RuntimeError as e:
        # STT import failed
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {"error": f"STT unavailable: {str(e)}", "ai_response": None}
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {"error": f"STT failed: {str(e)}", "ai_response": None}

    if not transcribed_text:
        return {"error": "Could not transcribe audio — empty result.", "ai_response": None}

    return await handle_chat_query(student_id, transcribed_text, db)


async def handle_rag_query(
    student_id: uuid.UUID,
    query: str,
    db: AsyncSession,
) -> dict:
    """
    Direct RAG document query — no student context enrichment.
    Best for syllabus, exam schedule, or policy questions.
    """
    ai_response: str = _get_rag_answer(query)
    await save_chat(student_id, query, ai_response, db)
    return {"query": query, "ai_response": ai_response}
