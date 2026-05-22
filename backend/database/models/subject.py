"""database/models/subject.py"""

import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database.connection import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    branch: Mapped[str] = mapped_column(String(50), nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)

    faculty          = relationship("Faculty",    back_populates="subjects")
    attendance_records = relationship("Attendance", back_populates="subject", cascade="all, delete-orphan")
    timetable_slots  = relationship("Timetable",  back_populates="subject", cascade="all, delete-orphan")
    assignments      = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")
