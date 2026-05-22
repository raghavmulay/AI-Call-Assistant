import time
from fastapi import Request, HTTPException, status
from backend.app.core.redis import redis_client
from backend.app.core.config import settings
from backend.app.core.logger import logger

async def rate_limit_middleware(request: Request, call_next):
    """
    Simple Redis-backed rate limiter.
    Throttles requests based on client IP.
    """
    # Only rate limit AI and WebSocket paths
    path = request.url.path
    if not (path in ["/chat", "/voice-query", "/rag-query"] or path.startswith("/ws") or path.startswith("/api/v1/ai")):
        return await call_next(request)

    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    # Get current count
    count = await redis_client.client.get(key)
    
    if count and int(count) >= settings.RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

    # Increment and set TTL if new
    async with redis_client.client.pipeline(transaction=True) as pipe:
        await pipe.incr(key)
        await pipe.expire(key, settings.RATE_LIMIT_WINDOW, nx=True)
        await pipe.execute()

    return await call_next(request)
