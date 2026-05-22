"""
config.py — Application Configuration
Reads all environment variables from the .env file using Pydantic BaseSettings.
All sensitive values (DB URL, secret keys) live here — never hardcoded.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os

# Absolute path to the project root directory
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CORE_DIR, "..", "..", ".."))
_ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI Campus Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str

    # ── Redis (New in 2.5) ───────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    MEMORY_TTL: int = 3600  # 1 hour
    MAX_CONVERSATION_WINDOW: int = 15

    # ── JWT Authentication ────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── AI Services ─────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    OLLAMA_TIMEOUT: int = 30
    GROQ_API_KEY: str = ""

    # ── Rate Limiting (New in 2.5) ──────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 20
    RATE_LIMIT_WINDOW: int = 60  # seconds

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra env vars without error

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return ALLOWED_ORIGINS as a Python list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Use this as a FastAPI dependency: settings = Depends(get_settings)
    """
    return Settings()


# Module-level singleton for imports outside FastAPI DI
settings = get_settings()
