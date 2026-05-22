"""core/logger.py — App-wide logger factory."""

import logging
from backend.core.config import settings


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)
