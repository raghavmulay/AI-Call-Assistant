"""
context_manager.py — Context Management for AI Orchestrator
Builds enriched prompts combining history, retrieved data, and system prompts.
"""

from typing import List, Optional
from backend.app.ai.prompts.system_prompts import SYSTEM_PROMPT, RAG_PROMPT, GENERAL_CHAT_PROMPT

class ContextManager:
    @staticmethod
    def build_prompt(
        query: str,
        history: List[dict] = [],
        context_data: str = "",
        metadata: dict = {},
        use_rag: bool = False
    ) -> str:
        """
        Constructs the final prompt to be sent to the LLM.
        Includes lightweight context memory for conversational continuity.
        """

        # 1. Base System Prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\n"

        # 2. Context awareness — last topic and branch
        context_hints = []
        if metadata.get("branch"):
            context_hints.append(f"The student is asking about {metadata['branch']} branch.")
        if metadata.get("intent"):
            last_intent = metadata["intent"]
            # Map intent to human-readable topic for context continuity
            topic_map = {
                "hostel": "hostel",
                "fees": "fees",
                "placements": "placements",
                "admission_dates": "admission dates",
                "documents": "required documents",
                "scholarship": "scholarships",
                "branches": "available branches",
                "campus_life": "campus life",
                "counseling": "branch/career guidance",
                "academics": "academics",
            }
            topic = topic_map.get(last_intent, last_intent.replace("_", " "))
            context_hints.append(f"The previous topic was about {topic}.")

        if context_hints:
            full_prompt += f"[Context: {' '.join(context_hints)}]\n\n"

        # 3. Recent conversation history — last 3 turns for continuity
        if history:
            full_prompt += "--- RECENT CONVERSATION ---\n"
            for turn in history[-3:]:
                role = "Student" if turn["role"] == "user" else "Aria"
                full_prompt += f"{role}: {turn['content']}\n"
            full_prompt += "---------------------------\n\n"

        # 4. Retrieved data + query
        if use_rag:
            full_prompt += RAG_PROMPT.format(context=context_data, query=query)
        elif context_data:
            full_prompt += f"Relevant Information: {context_data}\n\n"
            full_prompt += f"Student's Question: {query}\n\n"
            full_prompt += "Answer naturally and helpfully based on the information above:"
        else:
            full_prompt += GENERAL_CHAT_PROMPT.format(query=query)

        return full_prompt

context_manager = ContextManager()
