"""
Centralized logging configuration for the Virtual Try-On application.

Provides structured logging with proper levels, formatting, and Railway compatibility.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that provides structured output with consistent formatting.
    Includes timestamp, level, module, and message.
    """

    # ANSI color codes for console output
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structure and optional colors."""
        # Get color for level
        color = self.COLORS.get(record.levelname, '') if self.use_colors else ''
        reset = self.COLORS['RESET'] if self.use_colors else ''

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Build structured message
        parts = [
            f"{color}[{record.levelname}]{reset}",
            f"{timestamp}",
            f"[{record.name}]",
            record.getMessage()
        ]

        # Add exception info if present
        if record.exc_info:
            parts.append(self.formatException(record.exc_info))

        return " ".join(parts)


def setup_logger(
    name: str,
    level: Optional[str] = None,
    use_colors: bool = True
) -> logging.Logger:
    """
    Set up a logger with structured formatting.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, uses environment variable LOG_LEVEL or defaults to INFO
        use_colors: Whether to use colored output (auto-disabled in non-TTY)

    Returns:
        Configured logger instance

    Example:
        logger = setup_logger(__name__)
        logger.info("Application started")
        logger.error("Error occurred", exc_info=True)
    """
    import os

    # Determine log level
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler with structured formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logger.level)
    formatter = StructuredFormatter(use_colors=use_colors)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Don't propagate to root logger (avoid duplicate logs)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        from backend.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Processing request")
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logger(name)

    return logger


# Pre-configured loggers for common modules
app_logger = setup_logger('app')
auth_logger = setup_logger('auth')
db_logger = setup_logger('database')
api_logger = setup_logger('api')


__all__ = [
    'setup_logger',
    'get_logger',
    'app_logger',
    'auth_logger',
    'db_logger',
    'api_logger'
]
