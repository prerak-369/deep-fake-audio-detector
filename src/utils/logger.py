"""
Centralized logging — graceful fallback when loguru is not installed.
Uses loguru when available (rich colored output), otherwise stdlib logging.
"""

import sys
import logging
from pathlib import Path


def get_logger(name: str = __name__, log_level: str = "INFO"):
    """
    Get configured logger instance.

    Args:
        name:      Logger name (used as log prefix)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger object (loguru or stdlib logging.Logger)
    """
    try:
        from loguru import logger as _loguru_logger

        # Remove default handler to avoid duplicate output
        _loguru_logger.remove()

        # Create logs directory
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)

        # Console handler
        _loguru_logger.add(
            sys.stderr,
            format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
        )

        # File handler
        _loguru_logger.add(
            log_dir / "app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="500 MB",
            retention="10 days",
        )

        return _loguru_logger

    except ImportError:
        # Fallback to stdlib logging
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        if not logger.handlers:
            # Console
            ch = logging.StreamHandler(sys.stderr)
            ch.setFormatter(logging.Formatter("%(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"))
            logger.addHandler(ch)

            # File
            try:
                fh = logging.FileHandler(log_dir / "app.log")
                fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"))
                logger.addHandler(fh)
            except OSError:
                pass

        return logger
