"""handlers/assignment_handler.py — Assignment DB tool."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.assignment import Assignment


async def get_assignment_summary(user_id: str, db: AsyncSession) -> Optional[str]:
    try:
        result = await db.execute(
            select(Assignment.title, Assignment.deadline)
            .order_by(Assignment.deadline.asc())
            .limit(5)
        )
        rows = result.all()
        if not rows:
            return None
        return ", ".join(f"{t} (due {d})" for t, d in rows)
    except Exception:
        return None
