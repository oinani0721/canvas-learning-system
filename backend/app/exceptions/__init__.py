# Canvas Learning System - Exceptions Package
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: handling-errors)
"""
Custom exception classes for Canvas Learning System.

Exception Hierarchy:
    CanvasException (base)
    ├── CanvasNotFoundError (404)
    ├── NodeNotFoundError (404)
    ├── ValidationError (400)
    └── AgentExecutionError (500)
"""

from .canvas_exceptions import (
    CanvasException,
    CanvasNotFoundError,
    NodeNotFoundError,
    ValidationError,
    AgentExecutionError,
)

__all__ = [
    "CanvasException",
    "CanvasNotFoundError",
    "NodeNotFoundError",
    "ValidationError",
    "AgentExecutionError",
]
