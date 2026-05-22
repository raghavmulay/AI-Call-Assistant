import redis.asyncio as redis
from backend.app.core.config import settings
from backend.app.core.logger import logger

class RedisClient:
    def __init__(self):
        self.url = settings.REDIS_URL
        self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                self.url, 
                encoding="utf-8", 
                decode_responses=True
            )
            logger.info(f"Redis client initialized: {self.url}")
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            logger.info("Redis client closed.")

redis_client = RedisClient()
