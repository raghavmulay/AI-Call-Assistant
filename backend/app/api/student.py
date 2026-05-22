"""
routes/student.py — Student Endpoints
GET /student/profile/{id}
GET /student/attendance/{id}
GET /student/timetable/{id}
GET /student/assignments/{id}

FIX: current_user.role is a Role enum — must use .value for string comparisons.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.database import get_db
from backend.app.auth.dependencies import get_current_user, require_role
from backend.app.schemas.student import StudentProfileResponse
from backend.app.schemas.attendance import AttendanceSummary
from backend.app.schemas.timetable import TimetableSlotResponse
from backend.app.schemas.assignment import AssignmentResponse
from backend.app.services import student_service

router = APIRouter(prefix="/student", tags=["Student"])


@router.get(
    "/profile/{student_id}",
    response_model=StudentProfileResponse,
    summary="Get student profile by ID",
)
async def get_profile(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve a student's profile.

    - **Students** can only view their own profile.
    - **Faculty / Admin** can view any student's profile.
    """
    # FIX: use .value to compare enum to string literal
    if current_user.role.value == "student" and str(current_user.id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile.",
        )
    student = await student_service.get_student_by_id(student_id, db)
    return StudentProfileResponse.model_validate(student)


@router.get(
    "/attendance/{student_id}",
    response_model=AttendanceSummary,
    summary="Get attendance summary for a student",
)
async def get_attendance(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Fetch all subject attendance percentages and overall average.
    Students can only view their own attendance.
    """
    if current_user.role.value == "student" and str(current_user.id) != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return await student_service.get_attendance_for_student(student_id, db)


@router.get(
    "/timetable/{student_id}",
    response_model=List[TimetableSlotResponse],
    summary="Get the weekly timetable for a student",
)
async def get_timetable(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch all timetable slots for the student's branch, ordered by day and time."""
    if current_user.role.value == "student" and str(current_user.id) != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return await student_service.get_timetable_for_student(student_id, db)


@router.get(
    "/assignments/{student_id}",
    response_model=List[AssignmentResponse],
    summary="Get all assignments for a student",
)
async def get_assignments(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch all assignments for the student's branch, ordered by deadline."""
    if current_user.role.value == "student" and str(current_user.id) != str(student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return await student_service.get_assignments_for_student(student_id, db)
