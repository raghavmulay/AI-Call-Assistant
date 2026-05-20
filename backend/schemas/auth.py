"""
schemas/auth.py — Authentication Pydantic Schemas
Used for signup and login request/response validation.
"""

import uuid
from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal


# ── Signup ────────────────────────────────────────────────────────────────────

class StudentSignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    branch: str
    year: int
    division: str | None = None
    cgpa: float | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v

    @field_validator("year")
    @classmethod
    def year_range(cls, v: int) -> int:
        if v not in (1, 2, 3, 4):
            raise ValueError("Year must be between 1 and 4.")
        return v


class FacultySignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    department: str
    role: Literal["faculty", "admin"] = "faculty"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "faculty", "admin"]


# ── Responses ─────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: uuid.UUID

    model_config = {"from_attributes": True}
