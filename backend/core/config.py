"""
core/config.py — Centralised application settings.
All env vars live here. Import `settings` everywhere else.
"""

import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_FILE = os.path.join(_BACKEND_DIR, "..", ".env")


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Voice Call Assistant"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    class Config:
        env_file = _ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
