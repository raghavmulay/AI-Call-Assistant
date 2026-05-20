"""
schemas/student.py — Student Pydantic Schemas
Request and response models for student-related endpoints.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class StudentProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    branch: str
    year: int
    division: str | None
    cgpa: float | None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentSummary(BaseModel):
    """Lightweight student summary used in faculty views."""
    id: uuid.UUID
    name: str
    email: EmailStr
    branch: str
    year: int

    model_config = {"from_attributes": True}
