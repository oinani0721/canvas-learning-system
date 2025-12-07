# Middleware Package
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware)
"""Custom middleware for Canvas Learning System."""

from app.middleware.agent_metrics import (
    AGENT_ERRORS,
    AGENT_EXECUTION_TIME,
    AGENT_INVOCATIONS,
    get_agent_metrics_snapshot,
    record_agent_invocation,
    track_agent_execution,
)
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.error_tracking import (
    ERROR_COUNTER,
    ERROR_RETRY_COUNTER,
    ErrorCode,
    get_error_category,
    get_error_metrics_snapshot,
    get_max_retries,
    is_retryable,
    record_error,
    record_retry_attempt,
)
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.memory_metrics import (
    MEMORY_ERRORS,
    MEMORY_QUERIES,
    MEMORY_QUERY_LATENCY,
    get_memory_metrics_snapshot,
    record_memory_query,
    track_memory_query,
)
from app.middleware.metrics import (
    CONCURRENT_REQUESTS,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    MetricsMiddleware,
    get_api_metrics_snapshot,
    metrics_middleware,
)

__all__ = [
    # Core middleware
    "ErrorHandlerMiddleware",
    "LoggingMiddleware",
    # Agent metrics
    "track_agent_execution",
    "record_agent_invocation",
    "get_agent_metrics_snapshot",
    "AGENT_EXECUTION_TIME",
    "AGENT_ERRORS",
    "AGENT_INVOCATIONS",
    # Memory metrics
    "track_memory_query",
    "record_memory_query",
    "get_memory_metrics_snapshot",
    "MEMORY_QUERY_LATENCY",
    "MEMORY_ERRORS",
    "MEMORY_QUERIES",
    # Error tracking (ADR-009)
    "ErrorCode",
    "record_error",
    "record_retry_attempt",
    "get_error_metrics_snapshot",
    "is_retryable",
    "get_max_retries",
    "get_error_category",
    "ERROR_COUNTER",
    "ERROR_RETRY_COUNTER",
    # API Metrics (Story 17.1)
    "MetricsMiddleware",
    "metrics_middleware",
    "get_api_metrics_snapshot",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "CONCURRENT_REQUESTS",
]
