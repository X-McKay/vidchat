"""
Logging utilities for VidChat.
"""
import logging
import sys
from typing import Optional


def setup_logger(name: str = "vidchat", level: str = "INFO") -> logging.Logger:
    """
    Setup logger with consistent formatting.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only add handler if logger doesn't have one already
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper()))
    return logger


def get_logger(name: str = "vidchat") -> logging.Logger:
    """
    Get existing logger or create new one.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
