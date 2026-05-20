"""
services/faculty_service.py — Faculty Business Logic
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from backend.models.faculty import Faculty
from backend.models.student import Student
from backend.schemas.student import StudentSummary


async def get_faculty_by_email(email: str, db: AsyncSession) -> Faculty | None:
    """Fetch a faculty member by email."""
    result = await db.execute(select(Faculty).where(Faculty.email == email))
    return result.scalar_one_or_none()


async def get_faculty_by_id(faculty_id: uuid.UUID, db: AsyncSession) -> Faculty:
    """Fetch faculty by UUID. Raises 404 if not found."""
    result = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    faculty = result.scalar_one_or_none()
    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faculty with id {faculty_id} not found.",
        )
    return faculty


async def get_all_students(db: AsyncSession) -> list[StudentSummary]:
    """Return lightweight summaries of all students (for faculty dashboard)."""
    result = await db.execute(select(Student).order_by(Student.name))
    students = result.scalars().all()
    return [StudentSummary.model_validate(s) for s in students]
