"""
schemas/assignment.py — Assignment Pydantic Schemas
"""

import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class AssignmentCreateRequest(BaseModel):
    subject_id: uuid.UUID
    title: str
    description: Optional[str] = None
    deadline: datetime


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    description: Optional[str]
    deadline: datetime
    uploaded_by: Optional[uuid.UUID]
    created_at: datetime

    model_config = {"from_attributes": True}
