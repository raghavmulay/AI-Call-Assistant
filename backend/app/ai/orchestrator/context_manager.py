"""
context_manager.py — Context Management for AI Orchestrator
Builds enriched prompts by combining history, retrieved data, and system prompts.
"""

from typing import List, Optional
from backend.app.ai.prompts.system_prompts import SYSTEM_PROMPT, RAG_PROMPT

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
        """
        
        # 1. Base System Prompt
        full_prompt = f"System Instruction: {SYSTEM_PROMPT}\n\n"
        
        # 2. Metadata (Entity Awareness)
        if metadata.get("branch"):
            full_prompt += f"[Context: Student/Query belongs to {metadata['branch']} branch]\n"
        if metadata.get("last_intent"):
            full_prompt += f"[Context: Previous topic was about {metadata['last_intent']}]\n"

        # 3. History — only last 2 turns to keep prompt short for small models
        if history:
            full_prompt += "--- RECENT CONVERSATION ---\n"
            for turn in history[-2:]:
                full_prompt += f"{turn['role'].upper()}: {turn['content']}\n"
            full_prompt += "----------------------------\n\n"

        # 4. Context Data (Retrieval results)
        if use_rag:
            full_prompt += RAG_PROMPT.format(context=context_data, query=query)
        elif context_data:
            full_prompt += f"Retrieved Data / Background: {context_data}\n\n"
            full_prompt += f"Current User Query: {query}\n"
        else:
            full_prompt += f"Current User Query: {query}\n"

        return full_prompt

context_manager = ContextManager()
