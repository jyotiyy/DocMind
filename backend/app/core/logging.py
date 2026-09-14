"""
Structured logging configuration for DocMind, powered by Loguru.

Provides a single `configure_logging()` entry point called at application
startup, and a `get_logger()` helper for module-level loggers with bound
context (e.g. request IDs).
"""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from app.core.config import get_settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure Loguru sinks (console + rotating file). Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        ),
        backtrace=False,
        diagnose=settings.DEBUG,
    )

    logger.add(
        settings.LOG_DIR / "docmind.log",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=False,
    )

    _CONFIGURED = True
    logger.info("Logging configured (level={})", settings.LOG_LEVEL)


def get_logger(**context: Any):
    """Return a Loguru logger optionally bound with extra context fields."""
    configure_logging()
    return logger.bind(**context) if context else logger
