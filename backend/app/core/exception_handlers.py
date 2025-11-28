# Canvas Learning System - Global Exception Handlers
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
"""
Global exception handlers for Canvas Learning System FastAPI application.

This module provides centralized exception handling for all API endpoints,
ensuring consistent error response formatting across the application.

Exception Handler Registry:
- CanvasException: Custom Canvas exceptions (400, 404, 500)
- HTTPException: Standard FastAPI HTTP exceptions
- RequestValidationError: Pydantic validation errors
- Exception: Generic fallback handler

[Source: specs/data/error-response.schema.json - Error response format]
[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md - Error handling design]
"""

from typing import Any, Dict

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import CanvasException

# Get logger instance
logger = structlog.get_logger(__name__)


async def canvas_exception_handler(
    request: Request,
    exc: CanvasException,
) -> JSONResponse:
    """
    Handle CanvasException and its subclasses.

    Converts Canvas-specific exceptions to standardized JSON responses
    following the error-response.schema.json format.

    Args:
        request: The incoming HTTP request
        exc: The CanvasException instance

    Returns:
        JSONResponse with error payload

    Example:
        ```python
        raise CanvasNotFoundError("my_canvas")
        # Returns: {"code": 404, "message": "Canvas 'my_canvas' not found", "details": {...}}
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: @app.exception_handler(CustomException)

    [Source: specs/data/error-response.schema.json]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "canvas_exception",
        request_id=request_id,
        error_type=type(exc).__name__,
        error_code=exc.code,
        error_message=exc.message,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.code,
        content=exc.to_dict(),
        headers={"X-Request-ID": request_id},
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Handle FastAPI HTTPException.

    Converts standard HTTPException to the standardized error response format.

    Args:
        request: The incoming HTTP request
        exc: The HTTPException instance

    Returns:
        JSONResponse with error payload

    Example:
        ```python
        raise HTTPException(status_code=404, detail="Item not found")
        # Returns: {"code": 404, "message": "Item not found"}
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: Reusing default handlers with custom preprocessing

    [Source: specs/data/error-response.schema.json]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "http_exception",
        request_id=request_id,
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url.path),
    )

    # Build response body matching error-response.schema.json
    body: Dict[str, Any] = {
        "code": exc.status_code,
        "message": str(exc.detail) if exc.detail else "HTTP Error",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers={"X-Request-ID": request_id},
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic RequestValidationError.

    Converts validation errors to a user-friendly error response format
    with detailed field-level error information.

    Args:
        request: The incoming HTTP request
        exc: The RequestValidationError instance

    Returns:
        JSONResponse with error payload including validation details

    Example:
        Request body missing required field 'name':
        # Returns: {"code": 400, "message": "Validation error", "details": {...}}

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: Custom validation error handling

    [Source: specs/data/error-response.schema.json]
    [Source: specs/data/error-detail.schema.json]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Extract validation error details
    errors = exc.errors()
    error_details = []

    for error in errors:
        # Format location as dot-separated path
        loc = error.get("loc", [])
        field = ".".join(str(x) for x in loc if x != "body")

        error_details.append({
            "field": field,
            "message": error.get("msg", "Invalid value"),
            "code": error.get("type", "validation_error"),
        })

    logger.warning(
        "validation_exception",
        request_id=request_id,
        error_count=len(errors),
        errors=error_details,
        path=str(request.url.path),
    )

    # Build response body matching error-response.schema.json
    body: Dict[str, Any] = {
        "code": 400,
        "message": "Validation error",
        "details": {
            "errors": error_details,
        },
    }

    return JSONResponse(
        status_code=400,
        content=body,
        headers={"X-Request-ID": request_id},
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle all unhandled exceptions as a fallback.

    This handler catches any exception that wasn't caught by more
    specific handlers, ensuring a consistent error response.

    IMPORTANT: In production, this should NOT expose internal error details.

    Args:
        request: The incoming HTTP request
        exc: The unhandled exception

    Returns:
        JSONResponse with generic error payload

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)

    [Source: specs/data/error-response.schema.json]
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "unhandled_exception",
        request_id=request_id,
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=str(request.url.path),
        exc_info=True,  # Include stack trace in logs
    )

    # Generic error response - don't expose internal details
    body: Dict[str, Any] = {
        "code": 500,
        "message": "Internal server error",
    }

    return JSONResponse(
        status_code=500,
        content=body,
        headers={"X-Request-ID": request_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    This function should be called during application startup to
    set up the global exception handling.

    Handler Registration Order (from specific to generic):
    1. CanvasException - Custom Canvas exceptions
    2. HTTPException - Standard HTTP exceptions
    3. RequestValidationError - Pydantic validation errors
    4. Exception - Generic fallback

    Args:
        app: The FastAPI application instance

    Example:
        ```python
        from fastapi import FastAPI
        from app.core.exception_handlers import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
        ```

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
    # Pattern: @app.exception_handler(ExceptionClass)

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md]
    """
    # Register handlers from most specific to least specific
    app.add_exception_handler(CanvasException, canvas_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("exception_handlers_registered")
