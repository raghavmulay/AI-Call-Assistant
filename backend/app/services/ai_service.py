"""
services/ai_service.py — AI Service Wrapper for Orchestrator
Bridges the FastAPI backend with the central AI Orchestrator.
"""

import uuid
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Import the orchestrator entry point
from backend.app.ai.orchestrator.orchestrator import process_query

async def handle_chat_query(
    student_id: uuid.UUID,
    message: str,
    db: AsyncSession,
) -> dict:
    """
    Main AI text chat handler using the Central Orchestrator.
    """
    # Build user context for personalized retrieval
    user_context = {"student_id": student_id}
    
    # We use student_id as the session_id for persistence
    session_id = str(student_id)
    
    # Delegate everything to the Orchestrator
    return await process_query(
        user_input=message,
        session_id=session_id,
        user_context=user_context,
        db=db
    )


async def handle_voice_query(
    student_id: uuid.UUID,
    audio_base64: str,
    db: AsyncSession,
) -> dict:
    """
    Voice query handler using the Central Orchestrator.
    """
    import base64
    import tempfile
    import os
    from backend.app.ai.stt.whisper_stt import SpeechToText

    # 1. Decode base64 audio
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception:
        return {"error": "Invalid base64 audio data.", "success": False}

    # 2. Transcribe using STT module
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        stt = SpeechToText(model_size="base")
        transcribed_text = stt.transcribe(tmp_path)
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {"error": f"STT failed: {str(e)}", "success": False}

    if not transcribed_text:
        return {"error": "Could not transcribe audio.", "success": False}

    # 3. Process the transcribed text through the Orchestrator
    result = await handle_chat_query(student_id, transcribed_text, db)
    result["transcribed_text"] = transcribed_text
    return result


async def handle_rag_query(
    student_id: uuid.UUID,
    query: str,
    db: AsyncSession,
) -> dict:
    """
    Direct RAG document query using the Central Orchestrator.
    """
    return await handle_chat_query(student_id, query, db)

