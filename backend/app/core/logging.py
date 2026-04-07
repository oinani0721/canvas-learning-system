# Canvas Learning System - Logging Configuration
# [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#基础设施层]
"""
Logging configuration for the Canvas Learning System backend.

This module provides a unified configuration entry point for both structlog
and stdlib `logging`. The bridge ensures:

1. structlog logs flow through stdlib's logging pipeline so pytest's
   `caplog` fixture can capture them.
2. stdlib `logging.getLogger()` records also get JSON-formatted output
   via `ProcessorFormatter.foreign_pre_chain`.
3. `request_id` from `structlog.contextvars` is available on every record
   (no separate filter needed; `merge_contextvars` is in both chains).

[Source: ADR-010 - Logging聚合策略]
[Source: openspec/changes/fix-structlog-caplog-compat — Task 1]
[Source: Context7 /websites/structlog_en_stable — ProcessorFormatter pattern]
"""

import io
import logging
import sys
from typing import Optional

import structlog


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure unified structlog + stdlib logging with bidirectional bridge.

    This is the canonical logging entry point. It is idempotent — subsequent
    calls return immediately without re-installing handlers.

    The bridge works in two directions:
    - structlog → stdlib: `structlog.stdlib.LoggerFactory()` causes
      `structlog.get_logger()` to return loggers that delegate to stdlib's
      `logging.Logger`. The final structlog processor `wrap_for_formatter`
      packs the event dict so `ProcessorFormatter` can render it later.
    - stdlib → structlog: `foreign_pre_chain` runs structlog processors
      (timestamper, log level, contextvars) on records emitted by direct
      `logging.getLogger()` callers.

    Args:
        level: stdlib logging level (e.g. ``logging.INFO``, ``logging.DEBUG``).

    [Source: Context7 /websites/structlog_en_stable - ProcessorFormatter]
    """
    if getattr(configure_logging, "_configured", False):
        return

    _configure_structlog()
    _configure_stdlib_handler(level)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Reconfigure Uvicorn handlers to use the same UTF-8 stdout we wired up.
    # [Source: Story 12.J.1 - Uvicorn handler reconfiguration]
    root_handlers = logging.getLogger().handlers
    if root_handlers:
        primary_stream = root_handlers[0].stream  # type: ignore[attr-defined]
        for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
            uv_logger = logging.getLogger(logger_name)
            for handler in uv_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler):
                    handler.stream = primary_stream

    configure_logging._configured = True  # type: ignore[attr-defined]


def _shared_processors() -> list:
    """structlog processors run for BOTH structlog-native and foreign records.

    These run before any renderer:
    - merge_contextvars: pulls request_id (and other ContextVars) into the dict
    - add_logger_name: includes the logger name (typically __name__)
    - add_log_level: adds level as a string field
    - TimeStamper: ISO 8601 timestamp
    """
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]


def _configure_structlog() -> None:
    """Configure structlog to bridge through stdlib's logging.

    `wrap_for_formatter` MUST be the final processor — it packs the event
    dict so the downstream `ProcessorFormatter` can render it as JSON.
    """
    structlog.configure(
        processors=[
            *_shared_processors(),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Last processor — packs event_dict for ProcessorFormatter.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _configure_stdlib_handler(level: int) -> None:
    """Install root stdlib handler with `ProcessorFormatter` for JSON output.

    UTF-8 wrapping for stdout/stderr is preserved from Story 12.I.1 / 12.J.1
    so emoji and Unicode characters do not crash on Windows GBK terminals.
    """
    # UTF-8 wrapping for stdout (Story 12.I.1)
    utf8_stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # Run shared processors on records that did NOT originate from structlog.
        foreign_pre_chain=_shared_processors(),
        # Run on ALL records after the pre_chain is done.
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(utf8_stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates on hot reload.
    for existing in root_logger.handlers[:]:
        root_logger.removeHandler(existing)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


# ───────────────────────────────────────────────────────────────────────────
# Backwards compatibility shim
# ───────────────────────────────────────────────────────────────────────────


def setup_logging(
    log_level: str = "INFO", log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure application-wide logging (backwards-compat wrapper).

    .. deprecated::
        Use :func:`configure_logging` instead. This wrapper exists so
        existing call sites in ``main.py`` continue to work. The
        ``log_format`` parameter is **ignored** — output is now always JSON
        via :class:`structlog.stdlib.ProcessorFormatter`.

    Args:
        log_level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Ignored. Retained for API compatibility.

    Returns:
        logging.Logger: The configured root logger.
    """
    del log_format  # ignored — JSON output is now mandatory
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    configure_logging(level=numeric_level)
    return logging.getLogger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a stdlib logger by name (convenience wrapper).

    For new code, prefer ``structlog.get_logger(__name__)`` directly so you
    get the structlog `BoundLogger` interface (kwargs become structured
    fields). This helper exists for legacy stdlib-style call sites.

    Args:
        name: Logger name (typically ``__name__``).

    Returns:
        logging.Logger: Stdlib logger instance.
    """
    return logging.getLogger(name)
