"""
config.py — Application Configuration
Reads all environment variables from the .env file using Pydantic BaseSettings.
All sensitive values (DB URL, secret keys) live here — never hardcoded.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Absolute path to the backend/ directory — ensures .env is always found
# regardless of which directory uvicorn is launched from.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_FILE = os.path.join(_BACKEND_DIR, ".env")


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI Campus Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str

    # ── JWT Authentication ────────────────────────────────────────────────────
    SECRET_KEY: str                      # Long random string (openssl rand -hex 32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins, e.g. "http://localhost:3000"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── AI Services (optional — used by ai_service.py) ───────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"

    class Config:
        env_file = _ENV_FILE          # FIX: absolute path — always found
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def allowed_origins_list(self) -> list[str]:
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
