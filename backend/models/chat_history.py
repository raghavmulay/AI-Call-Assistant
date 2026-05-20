"""
models/chat_history.py — Chat History ORM Model
Maps to the `chat_history` table in PostgreSQL.
Stores every student ↔ AI conversation turn for context and analytics.
"""

import uuid
from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # ── Foreign Key ───────────────────────────────────────────────────────────
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Common query: get all chats for a student
    )

    # ── Message Content ───────────────────────────────────────────────────────
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    student: Mapped["Student"] = relationship("Student", back_populates="chat_histories")

    def __repr__(self) -> str:
        return f"<ChatHistory id={self.id} student={self.student_id} at={self.created_at}>"
