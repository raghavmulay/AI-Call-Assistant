"""
middleware/logging_middleware.py — Request/Response Logging Middleware
Logs method, path, status code, and response time for every request.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("campus_assistant.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that logs HTTP request details.

    Output format:
        [METHOD] /path → STATUS_CODE  (Xms)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        # Process the request
        response: Response = await call_next(request)

        # Calculate elapsed time
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "[%s] %s → %d  (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        # Add server timing header for debugging
        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"

        return response
