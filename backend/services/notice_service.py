"""
services/notice_service.py — Notice CRUD Business Logic
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.notice import Notice
from backend.schemas.notice import NoticeCreateRequest, NoticeResponse


async def create_notice(
    data: NoticeCreateRequest,
    uploaded_by: uuid.UUID,
    db: AsyncSession,
) -> NoticeResponse:
    """Create a new notice. uploaded_by is the faculty's UUID from JWT."""
    notice = Notice(
        title=data.title,
        description=data.description,
        uploaded_by=uploaded_by,
    )
    db.add(notice)
    await db.flush()   # Get the generated ID without committing yet
    await db.refresh(notice)
    return NoticeResponse.model_validate(notice)


async def get_all_notices(db: AsyncSession) -> list[NoticeResponse]:
    """Return all notices ordered by newest first."""
    result = await db.execute(
        select(Notice).order_by(Notice.created_at.desc())
    )
    notices = result.scalars().all()
    return [NoticeResponse.model_validate(n) for n in notices]
