"""
memory_manager.py — Abstracted Conversation Memory Manager
Now uses Redis for persistent session storage.
"""

from typing import Any, Dict, List, Optional
from backend.app.ai.memory.redis_memory import redis_memory
from backend.app.core.logger import logger

class MemoryManager:
    """
    Coordinates session memory retrieval and updates.
    Current backend: Redis
    """

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history for the given session."""
        try:
            return await redis_memory.get_history(session_id)
        except Exception as e:
            logger.error(f"Failed to retrieve history from Redis: {str(e)}")
            return []

    async def get_metadata(self, session_id: str) -> Dict[str, Any]:
        """Retrieve session-specific metadata (branch, etc.)."""
        try:
            return await redis_memory.get_metadata(session_id)
        except Exception as e:
            logger.error(f"Failed to retrieve metadata from Redis: {str(e)}")
            return {}

    async def add_turn(self, session_id: str, role: str, content: str):
        """Record a new turn in the conversation."""
        try:
            await redis_memory.add_turn(session_id, role, content)
        except Exception as e:
            logger.error(f"Failed to add turn to Redis: {str(e)}")

    async def update_metadata(self, session_id: str, **kwargs):
        """Persist session metadata."""
        try:
            await redis_memory.update_metadata(session_id, **kwargs)
        except Exception as e:
            logger.error(f"Failed to update metadata in Redis: {str(e)}")

    async def clear_session(self, session_id: str):
        """Remove all data associated with a session."""
        try:
            await redis_memory.clear(session_id)
        except Exception as e:
            logger.error(f"Failed to clear session in Redis: {str(e)}")

memory_manager = MemoryManager()
