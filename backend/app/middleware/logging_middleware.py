# Canvas Learning System - Logging Middleware
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware)
# ✅ Verified from Context7:/hynek/structlog (topic: configure processors)
"""
Logging middleware for Canvas Learning System.

This middleware logs all HTTP requests and responses using structlog
for structured logging output.

Features:
- Request logging (method, path, client IP, request_id)
- Response logging (status_code, process_time)
- Structured JSON output format
- Request ID tracking for correlation

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md - Logging requirements]
"""

import time
import uuid
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ✅ Verified from Context7:/hynek/structlog (topic: configure processors)
# Configure structlog with processors compatible with PrintLoggerFactory
# Note: Using simpler processor chain that doesn't require stdlib logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Get logger instance
logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware that logs all requests and responses.

    This middleware implements structured logging using structlog,
    capturing request details on entry and response details on exit.

    Request logging includes:
    - HTTP method
    - Request path
    - Client IP address
    - Request ID (UUID for correlation)

    Response logging includes:
    - HTTP status code
    - Processing time in milliseconds

    Example:
        ```python
        from fastapi import FastAPI
        from app.middleware.logging_middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware)
    # Pattern: Using BaseHTTPMiddleware with dispatch method

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md]
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """
        Process the request and log entry/exit details.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            The HTTP response from the downstream handler

        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware)
        # Pattern: async def dispatch(self, request, call_next)
        """
        # Generate unique request ID for correlation
        request_id = str(uuid.uuid4())

        # Store request_id in request state for access in handlers
        request.state.request_id = request_id

        # Get client IP (handle proxy headers)
        client_ip = self._get_client_ip(request)

        # Record start time
        start_time = time.perf_counter()

        # Log request entry
        # ✅ Verified from Context7:/hynek/structlog (topic: configure processors)
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            query_string=str(request.url.query) if request.url.query else None,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
        )

        # Call the next middleware/handler
        response: Response = await call_next(request)

        # Calculate processing time
        process_time_ms = (time.perf_counter() - start_time) * 1000

        # Log response exit
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            process_time_ms=round(process_time_ms, 2),
        )

        # Add request ID to response headers for client correlation
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Handles proxy headers (X-Forwarded-For, X-Real-IP) for
        applications behind reverse proxies.

        Args:
            request: The incoming HTTP request

        Returns:
            Client IP address as string
        """
        # Check for proxy headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For may contain multiple IPs; take the first one
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"


def get_request_logger(request: Request):
    """
    Get a logger instance bound with the current request context.

    This utility function creates a logger with the request_id
    pre-bound, making it easy to correlate logs within a single request.

    Args:
        request: The current HTTP request

    Returns:
        A structlog BoundLogger with request context

    Example:
        ```python
        @router.get("/items")
        async def get_items(request: Request):
            log = get_request_logger(request)
            log.info("fetching_items", count=10)
        ```

    # ✅ Verified from Context7:/hynek/structlog (topic: configure processors)
    """
    request_id = getattr(request.state, "request_id", "unknown")
    return logger.bind(request_id=request_id)
