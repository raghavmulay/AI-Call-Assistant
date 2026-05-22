"""database/models/student.py"""

import uuid, enum
from datetime import datetime
from sqlalchemy import String, Float, Integer, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database.connection import Base


class Role(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    admin   = "admin"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    division: Mapped[str] = mapped_column(String(10), nullable=True)
    cgpa: Mapped[float] = mapped_column(Float, nullable=True)
    role: Mapped[str] = mapped_column(SAEnum(Role, name="role_enum"), default=Role.student, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    chat_histories     = relationship("ChatHistory", back_populates="student", cascade="all, delete-orphan")
