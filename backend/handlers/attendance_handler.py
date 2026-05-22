"""
handlers/attendance_handler.py — Attendance DB tool.
Returns a plain-text summary consumed by the LLM as context.
"""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.attendance import Attendance
from backend.database.models.subject import Subject


async def get_attendance_summary(user_id: str, db: AsyncSession) -> Optional[str]:
    try:
        result = await db.execute(
            select(Subject.name, func.count(Attendance.id).label("total"),
                   func.sum(Attendance.is_present.cast(int)).label("present"))
            .join(Subject, Attendance.subject_id == Subject.id)
            .where(Attendance.student_id == user_id)
            .group_by(Subject.name)
        )
        rows = result.all()
        if not rows:
            return None
        lines = []
        for name, total, present in rows:
            pct = round((present / total) * 100, 1) if total else 0
            lines.append(f"{name}: {present}/{total} ({pct}%)")
        return ", ".join(lines)
    except Exception:
        return None
