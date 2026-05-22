"""
schemas/attendance.py — Attendance Pydantic Schemas
"""

import uuid
from pydantic import BaseModel, Field
from typing import List


class AttendanceResponse(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    subject_name: str           # Joined from Subject table in service layer
    attendance_percent: float

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    """Used by the AI service to summarize a student's attendance."""
    student_id: uuid.UUID
    records: List[AttendanceResponse]
    overall_average: float = Field(description="Mean attendance % across all subjects")
