"""
models/student.py — Student ORM Model
Maps to the `students` table in PostgreSQL.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database import Base
import enum


class Role(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    admin = "admin"


class Student(Base):
    __tablename__ = "students"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Personal Info ────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Academic Info ────────────────────────────────────────────────────────
    branch: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    division: Mapped[str] = mapped_column(String(10), nullable=True)
    cgpa: Mapped[float] = mapped_column(Float, nullable=True)

    # ── Role ─────────────────────────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        SAEnum(Role, name="role_enum"), default=Role.student, nullable=False
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )
    chat_histories: Mapped[list["ChatHistory"]] = relationship(
        "ChatHistory", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} name={self.name} email={self.email}>"
