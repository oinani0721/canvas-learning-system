# Canvas Learning System - Error Handler Middleware
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware exception handler)
"""
Error handling middleware for Canvas Learning System.

This middleware catches all unhandled exceptions and converts them
to standardized error responses following the error-response.schema.json format.

Features:
- Catches all unhandled exceptions
- Converts to JSON error response format
- Logs errors with full stack trace
- Preserves error context for debugging

[Source: specs/data/error-response.schema.json - Error response format]
[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md - Error handling requirements]
"""

import traceback
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.exceptions import CanvasException

# Get logger instance
logger = structlog.get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware that catches and handles all unhandled exceptions.

    This middleware acts as a safety net, catching any exceptions that
    escape the normal exception handlers. It ensures that all errors
    return a standardized JSON response format.

    Error Response Format (from error-response.schema.json):
    {
        "code": <int>,      # HTTP status code
        "message": <str>,   # Human-readable error message
        "details": <obj>    # Optional additional details
    }

    Example:
        ```python
        from fastapi import FastAPI
        from app.middleware.error_handler import ErrorHandlerMiddleware

        app = FastAPI()
        app.add_middleware(ErrorHandlerMiddleware)
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware)
    # Pattern: Using BaseHTTPMiddleware with dispatch method

    [Source: specs/data/error-response.schema.json]
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """
        Process the request and catch any unhandled exceptions.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            The HTTP response, or an error response if an exception occurred

        # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware)
        """
        try:
            # Call the next middleware/handler
            response = await call_next(request)
            return response

        except CanvasException as exc:
            # Handle our custom Canvas exceptions
            # These should normally be caught by exception handlers,
            # but this acts as a safety net
            request_id = getattr(request.state, "request_id", "unknown")

            logger.warning(
                "canvas_exception_in_middleware",
                request_id=request_id,
                error_type=type(exc).__name__,
                error_code=exc.code,
                error_message=exc.message,
                path=str(request.url.path),
            )

            return self._create_error_response(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=request_id,
            )

        except Exception as exc:
            # Handle all other unhandled exceptions
            request_id = getattr(request.state, "request_id", "unknown")

            # Log the full exception with stack trace
            logger.error(
                "unhandled_exception",
                request_id=request_id,
                error_type=type(exc).__name__,
                error_message=str(exc),
                path=str(request.url.path),
                method=request.method,
                traceback=traceback.format_exc(),
            )

            return self._create_error_response(
                code=500,
                message="Internal server error",
                details=None,
                request_id=request_id,
            )

    def _create_error_response(
        self,
        code: int,
        message: str,
        details: dict | None,
        request_id: str,
    ) -> JSONResponse:
        """
        Create a standardized error response.

        Args:
            code: HTTP status code
            message: Human-readable error message
            details: Optional additional error details
            request_id: Request ID for correlation

        Returns:
            JSONResponse with error payload

        [Source: specs/data/error-response.schema.json]
        """
        # Build response body matching error-response.schema.json
        body: dict = {
            "code": code,
            "message": message,
        }

        if details:
            body["details"] = details

        return JSONResponse(
            status_code=code,
            content=body,
            headers={"X-Request-ID": request_id},
        )
