"""database/models/timetable.py"""

import uuid, enum, datetime
from sqlalchemy import String, ForeignKey, Time, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database.connection import Base


class DayOfWeek(str, enum.Enum):
    monday = "monday"; tuesday = "tuesday"; wednesday = "wednesday"
    thursday = "thursday"; friday = "friday"; saturday = "saturday"


class Timetable(Base):
    __tablename__ = "timetable"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    day: Mapped[str] = mapped_column(SAEnum(DayOfWeek, name="day_of_week_enum"), nullable=False)
    time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    classroom: Mapped[str] = mapped_column(String(50), nullable=True)

    subject = relationship("Subject", back_populates="timetable_slots")
