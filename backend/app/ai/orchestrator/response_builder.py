"""
response_builder.py — Final Response Formatter for AI Orchestrator
Ensures outputs are conversational and properly structured.
"""

from typing import Any, Dict, List, Optional

from backend.app.schemas.ai_response import AIResponse

class ResponseBuilder:
    @staticmethod
    def format_final_response(
        response_text: str,
        intent: str,
        route: str,
        session_id: str,
        sources: List[str] = [],
        success: bool = True
    ) -> AIResponse:
        """
        Wraps the AI output into the standard structured format.
        """
        return AIResponse(
            response=response_text,
            intent=intent,
            route=route,
            sources=sources,
            session_id=session_id,
            success=success
        )

    @staticmethod
    def make_conversational(raw_data: Any, query: str) -> str:
        """
        (Optional) High-level formatting for structured data before LLM sees it,
        or if LLM isn't needed for simple data.
        """
        # For now, it could just be a string conversion
        return str(raw_data)

response_builder = ResponseBuilder()
