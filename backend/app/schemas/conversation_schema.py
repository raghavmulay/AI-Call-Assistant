"""schemas/conversation_schema.py — Text conversation request/response."""

from pydantic import BaseModel
from typing import Optional


class ConversationRequest(BaseModel):
    message: str
    session_id: str  # client-generated UUID string


class ConversationResponse(BaseModel):
    session_id: str
    transcript: Optional[str] = None   # populated for voice turns
    text: str                           # AI response text
    intent: str
    sub_intent: Optional[str] = None
    requires_auth: bool = False
