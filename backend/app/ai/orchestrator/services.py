"""
services/ — Service Abstractions for AI Orchestrator
Wraps specific implementations into a clean interface.
"""

import os
import json
from typing import Any, Dict, List, Optional
from backend.app.services.student_service import get_attendance_for_student, get_timetable_for_student
from backend.app.ai.llm.async_llm import async_llm

from backend.app.core.logger import logger

class AIServices:
    @staticmethod
    async def get_structured_data(intent: str, sub_intent: Optional[str], entity: Optional[str]) -> Any:
        try:
            import aiofiles
            # Absolute path to knowledge directory
            _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            KNOWLEDGE_DIR = os.path.join(_BASE, "knowledge")

            # Map every intent to its JSON file
            file_map = {
                # Root-level files
                "fees":             os.path.join(KNOWLEDGE_DIR, "fees.json"),
                "admission_dates":  os.path.join(KNOWLEDGE_DIR, "admission_dates.json"),
                "documents":        os.path.join(KNOWLEDGE_DIR, "admission", "dates.json"),
                "faq":              os.path.join(KNOWLEDGE_DIR, "faq.json"),
                # Sub-folder files
                "hostel":           os.path.join(KNOWLEDGE_DIR, "hostel", "hostel.json"),
                "hostel_rules":     os.path.join(KNOWLEDGE_DIR, "hostel", "hostel.json"),
                "placements":       os.path.join(KNOWLEDGE_DIR, "placements", "placements.json"),
                "scholarship":      os.path.join(KNOWLEDGE_DIR, "placements", "placements.json"),
                "branches":         os.path.join(KNOWLEDGE_DIR, "admission", "dates.json"),
                "admission_process":os.path.join(KNOWLEDGE_DIR, "admission", "dates.json"),
                "eligibility":      os.path.join(KNOWLEDGE_DIR, "admission", "dates.json"),
                "cutoff":           os.path.join(KNOWLEDGE_DIR, "admission", "dates.json"),
                "contact":          os.path.join(KNOWLEDGE_DIR, "office", "office.json"),
                "office_timing":    os.path.join(KNOWLEDGE_DIR, "office", "office.json"),
                "office_location":  os.path.join(KNOWLEDGE_DIR, "office", "office.json"),
            }

            path = file_map.get(intent)
            if not path or not os.path.exists(path):
                logger.warning(f"No knowledge file for intent: {intent}")
                return None

            async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)

            # For intents that share a file, extract the relevant section
            section_map = {
                "scholarship":  "scholarship",
                "branches":     "branches",
                "documents":    "documents",
                "eligibility":  "eligibility",
                "cutoff":       "cutoff",
                "admission_process": "process",
                "admission_dates":   "schedule",
            }
            section = section_map.get(intent)
            if section and section in data:
                return data[section]
            if sub_intent and sub_intent in data:
                return data[sub_intent]
            return data

        except Exception as e:
            logger.error(f"Error retrieving structured data: {str(e)}")
            return None

    @staticmethod
    async def get_database_data(intent: str, student_id: str, db: Any) -> Any:
        try:
            if intent == "attendance":
                return await get_attendance_for_student(student_id, db)
            if intent == "timetable":
                return await get_timetable_for_student(student_id, db)
            if intent == "notices":
                # In a real app, this might be a more generic service
                return "Latest college notices: Orientation starts Monday."
            return None
        except Exception as e:
            logger.error(f"Database service error: {str(e)}")
            return "Database currently unavailable."

    @staticmethod
    async def get_rag_data(query: str) -> str:
        # RAG temporarily disabled — returns empty, LLM will answer from general knowledge
        return ""

    @staticmethod
    async def get_llm_response(prompt: str) -> str:
        try:
            # Collect streamed tokens into full response
            chunks = []
            async for token in async_llm.stream_generate(prompt, "You are a campus assistant. Answer ONLY using the provided data. Be concise (1-2 sentences max). Never add extra information. Never start your reply with 'Assistant:' or 'User:'."):
                chunks.append(token)
            return "".join(chunks).strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            return "I'm having trouble thinking clearly right now. Please try in a moment."

ai_services = AIServices()
