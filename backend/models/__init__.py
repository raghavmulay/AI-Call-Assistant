"""models/__init__.py — Re-export all ORM models for easy import."""

from backend.models.student import Student
from backend.models.faculty import Faculty
from backend.models.subject import Subject
from backend.models.attendance import Attendance
from backend.models.timetable import Timetable
from backend.models.notice import Notice
from backend.models.chat_history import ChatHistory
from backend.models.assignment import Assignment

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
