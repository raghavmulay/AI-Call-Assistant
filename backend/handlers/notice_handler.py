"""handlers/notice_handler.py — Notice DB tool."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.notice import Notice


async def get_notice_summary(user_id: str, db: AsyncSession) -> Optional[str]:
    try:
        result = await db.execute(
            select(Notice.title, Notice.description)
            .order_by(Notice.created_at.desc())
            .limit(3)
        )
        rows = result.all()
        if not rows:
            return None
        return " | ".join(f"{t}: {d[:80]}" for t, d in rows)
    except Exception:
        return None
