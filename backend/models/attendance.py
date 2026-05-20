"""
models/attendance.py — Attendance ORM Model
Maps to the `attendance` table in PostgreSQL.
Stores per-student, per-subject attendance percentage.
"""

import uuid
from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    # ── Composite uniqueness: one record per (student, subject) ───────────────
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", name="uq_attendance_student_subject"),
    )

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Foreign Keys ─────────────────────────────────────────────────────────
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Attendance Data ───────────────────────────────────────────────────────
    attendance_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Relationships ─────────────────────────────────────────────────────────
    student: Mapped["Student"] = relationship("Student", back_populates="attendance_records")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="attendance_records")

    def __repr__(self) -> str:
        return (
            f"<Attendance student={self.student_id} "
            f"subject={self.subject_id} pct={self.attendance_percent}>"
        )
