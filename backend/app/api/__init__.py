"""
backend/app/api/__init__.py — API Routers Export
"""

from .auth import router as auth
from .student import router as student
from .faculty import router as faculty
from .notices import router as notices
from .ai import router as ai
from .chat_history import router as chat_history
