"""
routes/chat_history.py — Chat History Endpoints
GET /chat-history/{student_id}
"""

import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.schemas.chat import ChatHistoryResponse
from backend.services.chat_service import get_chat_history

router = APIRouter(prefix="", tags=["Chat History"])


@router.get(
    "/chat-history/{student_id}",
    response_model=list[ChatHistoryResponse],
    summary="Get AI chat history for a student",
)
async def fetch_chat_history(
    student_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve the AI conversation history for a student.

    - **Students** can only access their own history.
    - **Faculty / Admin** can access any student's history.
    - Results are ordered newest first.
    - Use the `limit` query param to control how many records are returned.
    """
    if current_user.role.value == "student" and str(current_user.id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own chat history.",
        )
    return await get_chat_history(student_id, db, limit=limit)
