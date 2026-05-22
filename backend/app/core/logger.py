"""
core/logger.py — Centralized Structured Logging System
Uses Loguru for high-performance, structured logging.
"""

import sys
from loguru import logger

# ── Logging Configuration ───────────────────────────────────────────────────

def setup_logging():
    # Remove default handler
    logger.remove()

    # Add stdout handler with color support
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # Add file handler for production logs
    logger.add(
        "logs/campus_assistant.log",
        rotation="10 MB",
        retention="10 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip",
    )

setup_logging()

# Global logger instance
logger = logger
