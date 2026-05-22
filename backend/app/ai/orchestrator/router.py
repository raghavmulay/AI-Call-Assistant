"""
router.py — Intelligent Routing for AI Orchestrator
Decides which retrieval layer or logic to use based on intent.
"""

from enum import Enum
from typing import Optional

class Route(Enum):
    STRUCTURED_RETRIEVAL = "structured"  # JSON data (fees, dates, etc.)
    DATABASE_RETRIEVAL   = "database"    # PostgreSQL (attendance, grades)
    RAG_RETRIEVAL        = "rag"         # PDF documents
    GENERAL_LLM          = "llm"         # General conversation

class Router:
    @staticmethod
    def decide_route(intent: str, sub_intent: Optional[str] = None, confidence: float = 1.0) -> Route:
        """
        Determines the appropriate routing logic based on the detected intent and confidence.
        """

        # ── 0. Confidence Check ────────────────────────────────────
        if confidence < 0.3:
            return Route.GENERAL_LLM

        # ── 1. Structured Retrieval (JSON) ─────────────────────────
        structured_intents = {
            "fees", "admission_dates", "admission_process",
            "branches", "placements", "scholarship",
            "hostel", "hostel_rules", "contact", "office_timing", "office_location",
            "cutoff", "eligibility", "documents",
            "campus_life", "counseling", "academics",
        }
        if intent in structured_intents:
            return Route.STRUCTURED_RETRIEVAL

        # ── 2. Database Retrieval (SQL) ───────────────────────────
        database_intents = {
            "attendance", "grades", "timetable", "assignments", "notices", "profile"
        }
        if intent in database_intents:
            if confidence < 0.4:
                return Route.GENERAL_LLM
            return Route.DATABASE_RETRIEVAL

        # ── 3. Default to General LLM ────────────────────────────
        return Route.GENERAL_LLM

router = Router()
