import json
from typing import Any, Dict, List, Optional
from backend.app.core.redis import redis_client
from backend.app.core.config import settings

class RedisMemory:
    def __init__(self):
        self.ttl = settings.MEMORY_TTL
        self.max_window = settings.MAX_CONVERSATION_WINDOW

    def _history_key(self, session_id: str) -> str:
        return f"history:{session_id}"

    def _metadata_key(self, session_id: str) -> str:
        return f"metadata:{session_id}"

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history from Redis list."""
        key = self._history_key(session_id)
        data = await redis_client.client.lrange(key, 0, -1)
        return [json.loads(turn) for turn in data]

    async def add_turn(self, session_id: str, role: str, content: str):
        """Append a turn to the Redis list and clip the window."""
        key = self._history_key(session_id)
        turn = {"role": role, "content": content}
        
        # Add to list
        await redis_client.client.rpush(key, json.dumps(turn))
        # Set expiration
        await redis_client.client.expire(key, self.ttl)
        # Clip window (keep last N items)
        await redis_client.client.ltrim(key, -self.max_window, -1)

    async def get_metadata(self, session_id: str) -> Dict[str, Any]:
        """Retrieve session metadata from Redis."""
        key = self._metadata_key(session_id)
        raw = await redis_client.client.get(key)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {}

    async def update_metadata(self, session_id: str, **kwargs):
        """Update session metadata in Redis as a JSON string."""
        if not kwargs:
            return
        key = self._metadata_key(session_id)
        existing = await self.get_metadata(session_id)
        existing.update({k: v for k, v in kwargs.items() if v is not None})
        await redis_client.client.set(key, json.dumps(existing), ex=self.ttl)

    async def clear(self, session_id: str):
        """Delete session data from Redis."""
        await redis_client.client.delete(self._history_key(session_id))
        await redis_client.client.delete(self._metadata_key(session_id))

redis_memory = RedisMemory()
