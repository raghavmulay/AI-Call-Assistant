"""
services/chat_service.py — Chat History Business Logic
Saves and retrieves AI conversation turns for a student.
"""

import uuid
from typing import List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.chat_history import ChatHistory
from backend.app.schemas.chat import ChatHistoryResponse


async def save_chat(
    student_id: uuid.UUID,
    user_message: str,
    ai_response: str,
    db: AsyncSession,
) -> ChatHistory:
    """Persist one conversation turn to the database."""
    entry = ChatHistory(
        student_id=student_id,
        user_message=user_message,
        ai_response=ai_response,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def get_chat_history(
    student_id: uuid.UUID, db: AsyncSession, limit: int = 50
) -> List[ChatHistoryResponse]:
    """Return the last `limit` conversation turns for a student, newest first."""
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.student_id == student_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return [ChatHistoryResponse.model_validate(r) for r in records]
