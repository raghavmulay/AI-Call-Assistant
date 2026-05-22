"""
models/timetable.py — Timetable ORM Model
Maps to the `timetable` table in PostgreSQL.
Each row represents one class slot: which subject, on which day, at what time.
"""

import uuid
from sqlalchemy import String, ForeignKey, Time, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database.database import Base
import enum
import datetime


class DayOfWeek(str, enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"


class Timetable(Base):
    __tablename__ = "timetable"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Foreign Key ───────────────────────────────────────────────────────────
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Slot Details ──────────────────────────────────────────────────────────
    day: Mapped[str] = mapped_column(
        SAEnum(DayOfWeek, name="day_of_week_enum"), nullable=False
    )
    time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    classroom: Mapped[str] = mapped_column(String(50), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    subject: Mapped["Subject"] = relationship("Subject", back_populates="timetable_slots")

    def __repr__(self) -> str:
        return (
            f"<Timetable subject={self.subject_id} "
            f"day={self.day} time={self.time} room={self.classroom}>"
        )
