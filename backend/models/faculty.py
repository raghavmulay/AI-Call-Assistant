"""
models/faculty.py — Faculty ORM Model
Maps to the `faculty` table in PostgreSQL.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database import Base
import enum


class FacultyRole(str, enum.Enum):
    faculty = "faculty"
    admin = "admin"


class Faculty(Base):
    __tablename__ = "faculty"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Personal Info ────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Department ────────────────────────────────────────────────────────────
    department: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Role ──────────────────────────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        SAEnum(FacultyRole, name="faculty_role_enum"),
        default=FacultyRole.faculty,
        nullable=False,
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    subjects: Mapped[list["Subject"]] = relationship(
        "Subject", back_populates="faculty"
    )
    notices: Mapped[list["Notice"]] = relationship(
        "Notice", back_populates="uploader"
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment", back_populates="uploader"
    )

    def __repr__(self) -> str:
        return f"<Faculty id={self.id} name={self.name} department={self.department}>"
