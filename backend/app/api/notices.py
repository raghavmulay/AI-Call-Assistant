"""
routes/notices.py — Notice Endpoints
GET /notices — Public endpoint, returns all notices ordered by date
"""

from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.database import get_db
from backend.app.schemas.notice import NoticeResponse
from backend.app.services.notice_service import get_all_notices

router = APIRouter(prefix="", tags=["Notices"])


@router.get(
    "/notices",
    response_model=List[NoticeResponse],
    summary="Get all campus notices",
)
async def list_notices(db: AsyncSession = Depends(get_db)):
    """
    Return all notices ordered by newest first.
    This endpoint is public — no authentication required.
    """
    return await get_all_notices(db)
