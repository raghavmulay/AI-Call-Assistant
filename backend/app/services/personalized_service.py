"""
services/personalized_service.py — Fetches student data from PostgreSQL
and formats it as a context string for the LLM.

Used as the `get_personal_context` callable injected into conversation_manager.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.logger import get_logger

logger = get_logger("personalized_service")


async def get_personal_context(
    user_id: str,
    sub_intent: Optional[str],
    db: AsyncSession,
) -> str:
    """
    Returns a plain-text summary of the student's relevant data.
    The LLM uses this as grounding context.
    """
    parts = []

    try:
        if sub_intent in ("attendance", None):
            from backend.app.handlers.attendance_handler import get_attendance_summary
            summary = await get_attendance_summary(user_id, db)
            if summary:
                parts.append(f"Attendance: {summary}")

        if sub_intent in ("timetable", None):
            from backend.app.handlers.timetable_handler import get_timetable_summary
            summary = await get_timetable_summary(user_id, db)
            if summary:
                parts.append(f"Timetable: {summary}")

        if sub_intent in ("assignment", None):
            from backend.app.handlers.assignment_handler import get_assignment_summary
            summary = await get_assignment_summary(user_id, db)
            if summary:
                parts.append(f"Assignments: {summary}")

        if sub_intent in ("notice", None):
            from backend.app.handlers.notice_handler import get_notice_summary
            summary = await get_notice_summary(user_id, db)
            if summary:
                parts.append(f"Notices: {summary}")

    except Exception as e:
        logger.error("Error fetching personal context for %s: %s", user_id, e)

    return "\n".join(parts) if parts else "No personal data found."
