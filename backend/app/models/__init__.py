"""models/__init__.py — Re-export all ORM models for easy import."""

from backend.app.models.student import Student
from backend.app.models.faculty import Faculty
from backend.app.models.subject import Subject
from backend.app.models.attendance import Attendance
from backend.app.models.timetable import Timetable
from backend.app.models.notice import Notice
from backend.app.models.chat_history import ChatHistory
from backend.app.models.assignment import Assignment

__all__ = [
    "Student",
    "Faculty",
    "Subject",
    "Attendance",
    "Timetable",
    "Notice",
    "ChatHistory",
    "Assignment",
]
