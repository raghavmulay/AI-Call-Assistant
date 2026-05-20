"""
schemas/timetable.py — Timetable Pydantic Schemas
"""

import uuid
import datetime as dt
from pydantic import BaseModel


class TimetableSlotResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    subject_name: str           # Joined from Subject in service
    day: str
    time: dt.time
    classroom: str | None

    model_config = {"from_attributes": True}
