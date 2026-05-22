"""
utils/responses.py — Standardized JSON Response Helpers
Provides consistent response shapes across all endpoints.
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse


def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200,
) -> JSONResponse:
    """
    Wrap any data in a standard success envelope.

    Shape:
        {
            "success": true,
            "message": "...",
            "data": <your data>
        }
    """
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def error_response(
    message: str,
    status_code: int = 400,
    details: Optional[Any] = None,
) -> JSONResponse:
    """
    Wrap an error in a standard error envelope.

    Shape:
        {
            "success": false,
            "message": "...",
            "details": <optional extra info>
        }
    """
    body: dict = {"success": False, "message": message}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)
