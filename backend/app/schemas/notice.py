"""
schemas/notice.py — Notice Pydantic Schemas
"""

import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class NoticeCreateRequest(BaseModel):
    title: str
    description: str


class NoticeResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    uploaded_by: Optional[uuid.UUID]
    created_at: datetime

    model_config = {"from_attributes": True}
