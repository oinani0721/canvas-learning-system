# Canvas Learning System - Logging Configuration
# [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#基础设施层]
"""
Logging configuration for the Canvas Learning System backend.

This module provides centralized logging setup with configurable log levels,
formatters, and handlers for consistent logging across the application.

[Source: ADR-010 - Logging聚合策略]
"""

import logging
import sys
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure application-wide logging.

    Sets up the root logger with appropriate handlers and formatters.
    Uses structured logging format for better log aggregation.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Optional custom log format string.

    Returns:
        logging.Logger: Configured root logger.

    Example:
        >>> setup_logging(log_level="DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # Default structured log format
    # [Source: docs/architecture/coding-standards.md#日志规范]
    if log_format is None:
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        )

    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    This is a convenience function to get a logger that follows
    the application's logging configuration.

    Args:
        name: Logger name (typically __name__).

    Returns:
        logging.Logger: Logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request")
    """
    return logging.getLogger(name)
