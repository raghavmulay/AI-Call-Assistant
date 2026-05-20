"""
services/student_service.py — Student Business Logic
All database queries for student-related operations live here.
Routes call these service functions — keeping route handlers thin.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from backend.models.student import Student
from backend.models.attendance import Attendance
from backend.models.timetable import Timetable
from backend.models.assignment import Assignment
from backend.models.subject import Subject
from backend.schemas.attendance import AttendanceResponse, AttendanceSummary
from backend.schemas.timetable import TimetableSlotResponse
from backend.schemas.assignment import AssignmentResponse


async def get_student_by_id(student_id: uuid.UUID, db: AsyncSession) -> Student:
    """Fetch a single student by UUID. Raises 404 if not found."""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found.",
        )
    return student


async def get_student_by_email(email: str, db: AsyncSession) -> Student | None:
    """Fetch a student by email. Returns None if not found."""
    result = await db.execute(select(Student).where(Student.email == email))
    return result.scalar_one_or_none()


async def get_attendance_for_student(
    student_id: uuid.UUID, db: AsyncSession
) -> AttendanceSummary:
    """
    Fetch all attendance records for a student, joined with subject names.
    Also computes the overall attendance average.
    """
    # Verify student exists first
    await get_student_by_id(student_id, db)

    # Join attendance with subjects to get subject names
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
        sum(r.attendance_percent for r in records) / len(records) if records else 0.0
    )

    return AttendanceSummary(
        student_id=student_id,
        records=records,
        overall_average=round(overall_average, 2),
    )


async def get_timetable_for_student(
    student_id: uuid.UUID, db: AsyncSession
) -> list[TimetableSlotResponse]:
    """
    Fetch timetable slots for a student, matched by branch + year.
    Joins timetable → subject → filters by student's branch.
    """
    student = await get_student_by_id(student_id, db)

    # Semester = year * 2 - 1 or year * 2 (approximate — use odd sem)
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
    student_id: uuid.UUID, db: AsyncSession
) -> list[AssignmentResponse]:
    """
    Return all assignments for subjects matching the student's branch.
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
        AssignmentResponse.model_validate(a) for a in assignments
    ]
