"""
models/notice.py — Notice ORM Model
Maps to the `notices` table in PostgreSQL.
Notices are uploaded by faculty/admin and visible to all students.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database.database import Base


class Notice(Base):
    __tablename__ = "notices"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Foreign Key (faculty who uploaded) ────────────────────────────────────
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("faculty.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    uploader: Mapped["Faculty"] = relationship("Faculty", back_populates="notices")

    def __repr__(self) -> str:
        return f"<Notice id={self.id} title={self.title}>"
