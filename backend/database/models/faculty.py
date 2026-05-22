"""database/models/faculty.py"""

import uuid, enum
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database.connection import Base


class FacultyRole(str, enum.Enum):
    faculty = "faculty"
    admin   = "admin"


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(SAEnum(FacultyRole, name="faculty_role_enum"), default=FacultyRole.faculty, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subjects    = relationship("Subject",    back_populates="faculty")
    notices     = relationship("Notice",     back_populates="uploader")
    assignments = relationship("Assignment", back_populates="uploader")
