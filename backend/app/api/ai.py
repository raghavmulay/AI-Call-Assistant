"""
routes/ai.py — AI Integration Endpoints
POST /chat        — Text-based AI assistant
POST /voice-query — Voice (audio) based AI assistant
POST /rag-query   — Direct RAG document query
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.database import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.chat import (
    ChatRequest,
    VoiceQueryRequest,
    RAGQueryRequest,
    ChatResponse,
)
from backend.app.services import ai_service
from datetime import datetime, timezone

router = APIRouter(prefix="", tags=["AI Assistant"])


@router.post(
    "/chat",
    summary="Send a text message to the AI campus assistant",
)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Text chat with the AI campus assistant.

    The AI will:
    1. Fetch the student's attendance and timetable as context
    2. Query the RAG pipeline with the enriched prompt
    3. Save the conversation to chat_history
    4. Return the AI response
    """
    result = await ai_service.handle_chat_query(data.student_id, data.message, db)
    return {
        "student_id": data.student_id,
        "user_message": data.message,
        "ai_response": result["ai_response"],
        "created_at": datetime.now(timezone.utc),
    }


@router.post(
    "/voice-query",
    summary="Send a voice message (base64 audio) to the AI assistant",
)
async def voice_query(
    data: VoiceQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Voice-based AI query.

    - Send base64-encoded WAV audio in the request body.
    - The backend transcribes it with Whisper STT, then processes as a chat query.
    """
    result = await ai_service.handle_voice_query(data.student_id, data.audio_base64, db)
    return result


@router.post(
    "/rag-query",
    summary="Query the RAG document pipeline directly",
)
async def rag_query(
    data: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Direct RAG query — skips student context enrichment.
    Best for questions about college documents, syllabi, exam schedules, etc.
    """
    result = await ai_service.handle_rag_query(data.student_id, data.query, db)
    return result
