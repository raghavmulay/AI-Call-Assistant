"""
models/subject.py — Subject ORM Model
Maps to the `subjects` table in PostgreSQL.
"""

import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Subject Details ───────────────────────────────────────────────────────
    subject_name: Mapped[str] = mapped_column(String(150), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    branch: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── Foreign Key ───────────────────────────────────────────────────────────
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="subjects")
    attendance_records: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="subject", cascade="all, delete-orphan"
    )
    timetable_slots: Mapped[List["Timetable"]] = relationship(
        "Timetable", back_populates="subject", cascade="all, delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subject id={self.id} name={self.subject_name} semester={self.semester}>"
