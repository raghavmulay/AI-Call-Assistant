"""schemas/response_schema.py — Unified API response envelope."""

from pydantic import BaseModel
from typing import Any, Optional


class APIResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None

    @classmethod
    def ok(cls, data=None, message="OK"):
        return cls(success=True, message=message, data=data)

    @classmethod
    def error(cls, message: str):
        return cls(success=False, message=message)
