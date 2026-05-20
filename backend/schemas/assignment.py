"""
schemas/assignment.py — Assignment Pydantic Schemas
"""

import uuid
from datetime import datetime
from pydantic import BaseModel


class AssignmentCreateRequest(BaseModel):
    subject_id: uuid.UUID
    title: str
    description: str | None = None
    deadline: datetime


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    description: str | None
    deadline: datetime
    uploaded_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
