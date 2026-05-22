"""
models/assignment.py — Assignment ORM Model
Maps to the `assignments` table in PostgreSQL.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Foreign Keys ─────────────────────────────────────────────────────────
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("faculty.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Assignment Details ────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    subject: Mapped["Subject"] = relationship("Subject", back_populates="assignments")
    uploader: Mapped["Faculty"] = relationship("Faculty", back_populates="assignments")

    def __repr__(self) -> str:
        return f"<Assignment id={self.id} title={self.title} deadline={self.deadline}>"
