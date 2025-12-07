# Canvas Learning System - Error Tracking Middleware
# ✅ Verified from ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md (ErrorCode体系)
# ✅ Verified from Context7:/prometheus/client_python (topic: Counter labels)
# ✅ Verified from ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md (structlog集成)
"""
Error tracking middleware for Canvas Learning System.

Integrates with ADR-009 ErrorCode system to provide comprehensive
error tracking with Prometheus metrics.

[Source: docs/architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md]
[Source: docs/architecture/performance-monitoring-architecture.md:381-420]
"""

from enum import IntEnum
from typing import Any

# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
import structlog

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter with labels)
from prometheus_client import Counter

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ErrorCode Enum (ADR-009 Specification)
# [Source: ADR-009:59-87 错误码区间体系]
# ═══════════════════════════════════════════════════════════════════════════════

class ErrorCode(IntEnum):
    """
    Error code enumeration following ADR-009 specification.

    Error code ranges:
    - 1xxx: Client errors (validation, not found)
    - 2xxx: Agent execution errors
    - 3xxx: Memory system errors
    - 4xxx: External service errors
    - 5xxx: System errors (resource, configuration)

    [Source: ADR-009:59-87 错误码区间体系]
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # 1xxx: Client Errors
    # ═══════════════════════════════════════════════════════════════════════════
    VALIDATION_ERROR = 1000
    CANVAS_NOT_FOUND = 1001
    NODE_NOT_FOUND = 1002
    INVALID_COLOR = 1003
    INVALID_NODE_TYPE = 1004
    MISSING_REQUIRED_FIELD = 1005
    INVALID_JSON_FORMAT = 1006

    # ═══════════════════════════════════════════════════════════════════════════
    # 2xxx: Agent Execution Errors
    # ═══════════════════════════════════════════════════════════════════════════
    AGENT_TIMEOUT = 2000
    AGENT_EXECUTION_FAILED = 2001
    AGENT_NOT_FOUND = 2002
    AGENT_INVALID_RESPONSE = 2003
    AGENT_RATE_LIMITED = 2004
    AGENT_CONTEXT_TOO_LARGE = 2005
    AGENT_MODEL_ERROR = 2006

    # ═══════════════════════════════════════════════════════════════════════════
    # 3xxx: Memory System Errors
    # ═══════════════════════════════════════════════════════════════════════════
    MEMORY_CONNECTION_ERROR = 3000
    MEMORY_TIMEOUT = 3001
    MEMORY_QUERY_FAILED = 3002
    GRAPHITI_ERROR = 3010
    LANCEDB_ERROR = 3020
    TEMPORAL_ERROR = 3030
    SQLITE_ERROR = 3040

    # ═══════════════════════════════════════════════════════════════════════════
    # 4xxx: External Service Errors
    # ═══════════════════════════════════════════════════════════════════════════
    EXTERNAL_API_ERROR = 4000
    EXTERNAL_TIMEOUT = 4001
    EXTERNAL_RATE_LIMITED = 4002
    OBSIDIAN_FILE_ERROR = 4010
    LLM_API_ERROR = 4020

    # ═══════════════════════════════════════════════════════════════════════════
    # 5xxx: System Errors
    # ═══════════════════════════════════════════════════════════════════════════
    INTERNAL_ERROR = 5000
    RESOURCE_EXHAUSTED = 5001
    CONFIGURATION_ERROR = 5002
    DATABASE_ERROR = 5003
    FILE_SYSTEM_ERROR = 5004


# ═══════════════════════════════════════════════════════════════════════════════
# Error Category Mapping
# [Source: ADR-009:88-120 错误分类]
# ═══════════════════════════════════════════════════════════════════════════════

ERROR_CATEGORIES = {
    "client": range(1000, 2000),
    "agent": range(2000, 3000),
    "memory": range(3000, 4000),
    "external": range(4000, 5000),
    "system": range(5000, 6000),
}


def get_error_category(error_code: int) -> str:
    """
    Get the category for an error code.

    Args:
        error_code: Error code value

    Returns:
        Category name (client, agent, memory, external, system, unknown)
    """
    for category, code_range in ERROR_CATEGORIES.items():
        if error_code in code_range:
            return category
    return "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Metrics Definitions
# [Source: docs/architecture/performance-monitoring-architecture.md:381-420]
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter with labels)
# Counter for tracking errors by code and category
ERROR_COUNTER = Counter(
    "canvas_errors_total",
    "Total errors by error code",
    ["error_code", "category", "component"]
)

# Counter for tracking retryable vs non-retryable errors
ERROR_RETRY_COUNTER = Counter(
    "canvas_error_retries_total",
    "Total error retry attempts",
    ["error_code", "retry_outcome"]
)


# ═══════════════════════════════════════════════════════════════════════════════
# Retryability Configuration
# [Source: ADR-009:121-160 重试策略]
# ═══════════════════════════════════════════════════════════════════════════════

# Errors that are safe to retry
RETRYABLE_ERRORS = frozenset([
    ErrorCode.AGENT_TIMEOUT,
    ErrorCode.AGENT_RATE_LIMITED,
    ErrorCode.MEMORY_TIMEOUT,
    ErrorCode.MEMORY_CONNECTION_ERROR,
    ErrorCode.EXTERNAL_TIMEOUT,
    ErrorCode.EXTERNAL_RATE_LIMITED,
    ErrorCode.RESOURCE_EXHAUSTED,
])

# Maximum retry attempts per error category
MAX_RETRIES = {
    "agent": 3,
    "memory": 2,
    "external": 3,
    "system": 1,
    "client": 0,  # Client errors should not be retried
}


def is_retryable(error_code: ErrorCode) -> bool:
    """
    Check if an error code is retryable.

    [Source: ADR-009:121-160 重试策略]

    Args:
        error_code: Error code to check

    Returns:
        True if the error is retryable, False otherwise
    """
    return error_code in RETRYABLE_ERRORS


def get_max_retries(error_code: ErrorCode) -> int:
    """
    Get the maximum retry attempts for an error code.

    [Source: ADR-009:121-160 重试策略]

    Args:
        error_code: Error code to check

    Returns:
        Maximum retry attempts
    """
    category = get_error_category(error_code)
    return MAX_RETRIES.get(category, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# Error Recording Functions
# [Source: docs/architecture/performance-monitoring-architecture.md:381-420]
# ═══════════════════════════════════════════════════════════════════════════════

def record_error(
    error_code: ErrorCode | int,
    component: str,
    error_message: str | None = None,
    details: dict[str, Any] | None = None
) -> None:
    """
    Record an error occurrence in Prometheus metrics and logs.

    [Source: docs/architecture/performance-monitoring-architecture.md:381-420]

    Args:
        error_code: Error code (ErrorCode enum or int)
        component: Component where error occurred (e.g., "agent", "canvas", "memory")
        error_message: Human-readable error message (optional)
        details: Additional error details for logging (optional)

    Example:
        >>> record_error(ErrorCode.AGENT_TIMEOUT, "scoring-agent", "Agent timed out after 30s")
        >>> record_error(ErrorCode.CANVAS_NOT_FOUND, "canvas", "Canvas not found", {"canvas_name": "test"})
    """
    # Convert to int if ErrorCode enum
    code_value = int(error_code)
    category = get_error_category(code_value)

    # ✅ Verified from Context7:/prometheus/client_python (Counter.labels().inc())
    ERROR_COUNTER.labels(
        error_code=str(code_value),
        category=category,
        component=component
    ).inc()

    # Log the error
    log = logger.bind(
        error_code=code_value,
        category=category,
        component=component
    )

    if details:
        log = log.bind(**details)

    log.error(
        "error_tracking.error_recorded",
        error_message=error_message or f"Error {code_value} in {component}"
    )


def record_retry_attempt(
    error_code: ErrorCode | int,
    attempt: int,
    success: bool
) -> None:
    """
    Record a retry attempt in Prometheus metrics.

    [Source: ADR-009:121-160 重试策略]

    Args:
        error_code: Error code being retried
        attempt: Retry attempt number (1, 2, 3, ...)
        success: Whether the retry was successful

    Example:
        >>> record_retry_attempt(ErrorCode.AGENT_TIMEOUT, 1, False)  # First retry failed
        >>> record_retry_attempt(ErrorCode.AGENT_TIMEOUT, 2, True)   # Second retry succeeded
    """
    code_value = int(error_code)
    outcome = "success" if success else "failed"

    # ✅ Verified from Context7:/prometheus/client_python (Counter.labels().inc())
    ERROR_RETRY_COUNTER.labels(
        error_code=str(code_value),
        retry_outcome=outcome
    ).inc()

    logger.debug(
        "error_tracking.retry_attempt",
        error_code=code_value,
        attempt=attempt,
        outcome=outcome
    )


def get_error_metrics_snapshot() -> dict[str, Any]:
    """
    Get a snapshot of current error metrics for summary endpoint.

    Returns aggregated error metrics suitable for the /metrics/summary endpoint.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]

    Returns:
        Dictionary with error metrics summary

    Example:
        >>> snapshot = get_error_metrics_snapshot()
        >>> print(snapshot["total_errors"])
        42
    """
    from prometheus_client import REGISTRY

    total_errors = 0
    by_category: dict[str, int] = {}
    by_component: dict[str, int] = {}
    retry_success = 0
    retry_failed = 0

    # ✅ Verified from Context7:/prometheus/client_python (REGISTRY.collect())
    for metric in REGISTRY.collect():
        # Process error counter
        if metric.name == "canvas_errors_total":
            for sample in metric.samples:
                if sample.name.endswith("_total"):
                    count = int(sample.value)
                    total_errors += count

                    category = sample.labels.get("category", "unknown")
                    by_category[category] = by_category.get(category, 0) + count

                    component = sample.labels.get("component", "unknown")
                    by_component[component] = by_component.get(component, 0) + count

        # Process retry counter
        elif metric.name == "canvas_error_retries_total":
            for sample in metric.samples:
                if sample.name.endswith("_total"):
                    outcome = sample.labels.get("retry_outcome", "unknown")
                    count = int(sample.value)
                    if outcome == "success":
                        retry_success += count
                    elif outcome == "failed":
                        retry_failed += count

    retry_total = retry_success + retry_failed
    retry_success_rate = retry_success / retry_total if retry_total > 0 else 0.0

    return {
        "total_errors": total_errors,
        "by_category": by_category,
        "by_component": by_component,
        "retries": {
            "total": retry_total,
            "success": retry_success,
            "failed": retry_failed,
            "success_rate": round(retry_success_rate, 4)
        }
    }
