"""
routes/faculty.py — Faculty Endpoints
POST /faculty/upload-notice
POST /faculty/upload-assignment
GET  /faculty/students

FIX #5: Depends() cannot be used as a module-level variable default argument.
         It must be used inside function parameter signatures.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.auth.dependencies import require_role
from backend.schemas.notice import NoticeCreateRequest, NoticeResponse
from backend.schemas.assignment import AssignmentCreateRequest, AssignmentResponse
from backend.schemas.student import StudentSummary
from backend.services import notice_service, assignment_service, faculty_service

router = APIRouter(prefix="/faculty", tags=["Faculty"])

# Store the guard callable — Depends() will be applied per-route below
_faculty_or_admin = require_role("faculty", "admin")


@router.post(
    "/upload-notice",
    response_model=NoticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new notice (faculty/admin only)",
)
async def upload_notice(
    data: NoticeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(_faculty_or_admin),
):
    """
    Create a campus notice.
    Only faculty and admins can post notices.
    """
    return await notice_service.create_notice(data, current_user.id, db)


@router.post(
    "/upload-assignment",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new assignment (faculty/admin only)",
)
async def upload_assignment(
    data: AssignmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(_faculty_or_admin),
):
    """
    Post an assignment for a subject.
    The `subject_id` must match an existing subject in the database.
    """
    return await assignment_service.create_assignment(data, current_user.id, db)


@router.get(
    "/students",
    response_model=list[StudentSummary],
    summary="Get list of all students (faculty/admin only)",
)
async def get_students(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(_faculty_or_admin),
):
    """Return a lightweight list of all registered students."""
    return await faculty_service.get_all_students(db)
