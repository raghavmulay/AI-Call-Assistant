"""
services/assignment_service.py — Assignment CRUD Business Logic
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.assignment import Assignment
from backend.schemas.assignment import AssignmentCreateRequest, AssignmentResponse


async def create_assignment(
    data: AssignmentCreateRequest,
    uploaded_by: uuid.UUID,
    db: AsyncSession,
) -> AssignmentResponse:
    """Create a new assignment."""
    assignment = Assignment(
        subject_id=data.subject_id,
        title=data.title,
        description=data.description,
        deadline=data.deadline,
        uploaded_by=uploaded_by,
    )
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    return AssignmentResponse.model_validate(assignment)
