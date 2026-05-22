"""
schemas/ai_response.py — Unified AI Response Schemas
Ensures all AI outputs follow the same structural contract.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class AIResponse(BaseModel):
    """
    Standard response schema for all AI queries.
    """
    response: str = Field(..., description="The conversational AI response")
    intent: str = Field(..., description="The detected intent of the user query")
    route: str = Field(..., description="The routing path used (structured, db, rag, or llm)")
    success: bool = Field(default=True, description="Whether the operation was successful")
    sources: List[str] = Field(default_factory=list, description="List of retrieval sources or references")
    session_id: str = Field(..., description="The active conversation session ID")

class VoiceQueryAIResponse(AIResponse):
    """
    Response schema for voice queries, including transcription.
    """
    transcribed_text: Optional[str] = Field(None, description="The text transcribed from audio")
