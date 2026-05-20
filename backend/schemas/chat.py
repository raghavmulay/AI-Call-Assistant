"""
schemas/chat.py — AI Chat Pydantic Schemas
Request and response schemas for all AI interaction endpoints.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel


# ── Request Schemas ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    student_id: uuid.UUID


class VoiceQueryRequest(BaseModel):
    """Base64-encoded audio blob sent from the client."""
    audio_base64: str
    student_id: uuid.UUID


class RAGQueryRequest(BaseModel):
    query: str
    student_id: uuid.UUID


# ── Response Schemas ──────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    student_id: uuid.UUID
    user_message: str
    ai_response: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    user_message: str
    ai_response: str
    created_at: datetime

    model_config = {"from_attributes": True}
