"""
services/student_service.py — Student Business Logic

All database queries for student-related operations live here.
Routes call these service functions — keeping route handlers thin.

This service layer acts as the bridge between:
FastAPI Routes ↔ Database Models

WHY THIS FILE EXISTS:
- Keeps route handlers clean
- Centralizes student-related DB logic
- Makes backend scalable and maintainable
- Allows AI handlers and APIs to reuse same logic

HOW IT CONNECTS TO AI:
Later, AI handlers can call backend APIs which internally use
these service functions for personalized retrieval.
"""

import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.assignment import Assignment
from backend.app.models.attendance import Attendance
from backend.app.models.student import Student
from backend.app.models.subject import Subject
from backend.app.models.timetable import Timetable

from backend.app.schemas.assignment import AssignmentResponse
from backend.app.schemas.attendance import (
    AttendanceResponse,
    AttendanceSummary,
)
from backend.app.schemas.timetable import TimetableSlotResponse


async def get_student_by_id(
    student_id: uuid.UUID,
    db: AsyncSession
) -> Student:
    """
    Fetch a single student by UUID.

    Raises:
        HTTPException: If student not found
    """

    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )

    student = result.scalar_one_or_none()

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found.",
        )

    return student


async def get_student_by_email(
    email: str,
    db: AsyncSession
) -> Optional[Student]:
    """
    Fetch a student by email.

    Returns:
        Student | None
    """

    result = await db.execute(
        select(Student).where(Student.email == email)
    )

    return result.scalar_one_or_none()


async def get_attendance_for_student(
    student_id: uuid.UUID,
    db: AsyncSession
) -> AttendanceSummary:
    """
    Fetch attendance records for a student.

    Also computes:
    - overall attendance average
    """

    # Verify student exists
    await get_student_by_id(student_id, db)

    stmt = (
        select(Attendance, Subject.subject_name)
        .join(Subject, Attendance.subject_id == Subject.id)
        .where(Attendance.student_id == student_id)
    )

    result = await db.execute(stmt)

    rows = result.all()

    records = [
        AttendanceResponse(
            id=att.id,
            subject_id=att.subject_id,
            subject_name=subject_name,
            attendance_percent=att.attendance_percent,
        )
        for att, subject_name in rows
    ]

    overall_average = (
        sum(r.attendance_percent for r in records) / len(records)
        if records
        else 0.0
    )

    return AttendanceSummary(
        student_id=student_id,
        records=records,
        overall_average=round(overall_average, 2),
    )


async def get_timetable_for_student(
    student_id: uuid.UUID,
    db: AsyncSession
) -> List[TimetableSlotResponse]:
    """
    Fetch timetable slots for a student.

    Matches:
    - branch
    - year/semester
    """

    student = await get_student_by_id(student_id, db)

    stmt = (
        select(Timetable, Subject.subject_name)
        .join(Subject, Timetable.subject_id == Subject.id)
        .where(Subject.branch == student.branch)
        .order_by(Timetable.day, Timetable.time)
    )

    result = await db.execute(stmt)

    rows = result.all()

    return [
        TimetableSlotResponse(
            id=slot.id,
            subject_id=slot.subject_id,
            subject_name=subject_name,
            day=slot.day,
            time=slot.time,
            classroom=slot.classroom,
        )
        for slot, subject_name in rows
    ]


async def get_assignments_for_student(
    student_id: uuid.UUID,
    db: AsyncSession
) -> List[AssignmentResponse]:
    """
    Fetch assignments for subjects matching
    the student's branch.
    """

    student = await get_student_by_id(student_id, db)

    stmt = (
        select(Assignment)
        .join(Subject, Assignment.subject_id == Subject.id)
        .where(Subject.branch == student.branch)
        .options(selectinload(Assignment.subject))
        .order_by(Assignment.deadline)
    )

    result = await db.execute(stmt)

    assignments = result.scalars().all()

    return [
        AssignmentResponse.model_validate(a)
        for a in assignments
    ]
