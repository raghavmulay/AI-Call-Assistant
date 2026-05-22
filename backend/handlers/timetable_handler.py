"""handlers/timetable_handler.py — Timetable DB tool."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.timetable import Timetable
from backend.database.models.subject import Subject


async def get_timetable_summary(user_id: str, db: AsyncSession) -> Optional[str]:
    try:
        result = await db.execute(
            select(Subject.name, Timetable.day, Timetable.time, Timetable.classroom)
            .join(Subject, Timetable.subject_id == Subject.id)
            .where(Timetable.student_id == user_id)
            .order_by(Timetable.day, Timetable.time)
            .limit(10)
        )
        rows = result.all()
        if not rows:
            return None
        return ", ".join(f"{name} on {day} at {time} in {room}" for name, day, time, room in rows)
    except Exception:
        return None
