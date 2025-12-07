# Canvas Learning System - Agent Metrics Middleware
# ✅ Verified from Context7:/prometheus/client_python (topic: Counter Histogram Gauge labels observe)
# ✅ Verified from ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md (ErrorCode体系)
# ✅ Verified from ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md (structlog集成)
"""
Agent execution tracking middleware for Prometheus metrics.

Provides decorators and utilities for tracking Agent execution time,
invocation counts, and error rates.

[Source: docs/architecture/performance-monitoring-architecture.md:200-238]
[Source: specs/api/canvas-api.openapi.yml:605-628]
"""

import functools
import time
from typing import Any, Callable, ParamSpec, TypeVar

# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
import structlog

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter Histogram labels)
from prometheus_client import Counter, Histogram

logger = structlog.get_logger(__name__)

# Type variables for decorator typing
P = ParamSpec("P")
R = TypeVar("R")

# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Metrics Definitions
# [Source: docs/architecture/performance-monitoring-architecture.md:200-238]
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/prometheus/client_python (topic: Histogram with labels and buckets)
# Histogram for tracking Agent execution time
AGENT_EXECUTION_TIME = Histogram(
    "canvas_agent_execution_seconds",
    "Agent execution time in seconds",
    ["agent_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter with labels)
# Counter for tracking Agent errors by type
AGENT_ERRORS = Counter(
    "canvas_agent_errors_total",
    "Total Agent execution errors",
    ["agent_type", "error_type"]
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter with labels)
# Counter for tracking Agent invocations by status
AGENT_INVOCATIONS = Counter(
    "canvas_agent_invocations_total",
    "Total Agent invocations",
    ["agent_type", "status"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# Agent Types
# [Source: helpers.md#Section-1-14-agents详细说明]
# ═══════════════════════════════════════════════════════════════════════════════

# 14 Agent types as defined in the system
VALID_AGENT_TYPES = frozenset([
    "basic-decomposition",
    "clarification-path",
    "comparison-table",
    "deep-decomposition",
    "example-teaching",
    "four-level-explanation",
    "graphiti-memory-agent",
    "memory-anchor",
    "oral-explanation",
    "question-decomposition",
    "scoring-agent",
    "verification-question-agent",
    "canvas-orchestrator",
    "general-purpose",
])


def track_agent_execution(agent_type: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for tracking Agent execution metrics.

    Tracks execution time, invocation count, and error rate for the decorated
    async function. Supports both sync and async functions.

    [Source: docs/architecture/performance-monitoring-architecture.md:200-238]

    Args:
        agent_type: Agent type name (e.g., "scoring-agent", "basic-decomposition")

    Returns:
        Decorated function with metric tracking

    Usage:
        @track_agent_execution("scoring-agent")
        async def score_nodes(nodes: List[Node]):
            ...

    Example:
        >>> @track_agent_execution("basic-decomposition")
        ... async def decompose(content: str) -> dict:
        ...     return {"questions": ["What is X?"]}
    """
    # Validate agent_type
    if agent_type not in VALID_AGENT_TYPES:
        logger.warning(
            "agent_metrics.unknown_agent_type",
            agent_type=agent_type,
            valid_types=list(VALID_AGENT_TYPES)
        )

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # ✅ Verified from Context7:/python/cpython (functools.wraps)
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Async wrapper for tracking metrics."""
            # ✅ Verified from Context7:/prometheus/client_python (time.perf_counter for high precision)
            start = time.perf_counter()
            log = logger.bind(agent_type=agent_type, func=func.__name__)

            try:
                result = await func(*args, **kwargs)

                # ✅ Verified from Context7:/prometheus/client_python (Counter.labels().inc())
                AGENT_INVOCATIONS.labels(
                    agent_type=agent_type,
                    status="success"
                ).inc()

                log.debug(
                    "agent_metrics.execution_success",
                    duration_s=time.perf_counter() - start
                )

                return result

            except Exception as e:
                # ✅ Verified from ADR-009:59-87 (ErrorCode体系)
                error_type = type(e).__name__

                # ✅ Verified from Context7:/prometheus/client_python (Counter.labels().inc())
                AGENT_ERRORS.labels(
                    agent_type=agent_type,
                    error_type=error_type
                ).inc()

                AGENT_INVOCATIONS.labels(
                    agent_type=agent_type,
                    status="error"
                ).inc()

                log.error(
                    "agent_metrics.execution_error",
                    error_type=error_type,
                    error_message=str(e),
                    duration_s=time.perf_counter() - start
                )

                raise

            finally:
                # Always record execution time
                duration = time.perf_counter() - start

                # ✅ Verified from Context7:/prometheus/client_python (Histogram.labels().observe())
                AGENT_EXECUTION_TIME.labels(
                    agent_type=agent_type
                ).observe(duration)

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Sync wrapper for tracking metrics."""
            start = time.perf_counter()
            log = logger.bind(agent_type=agent_type, func=func.__name__)

            try:
                result = func(*args, **kwargs)

                AGENT_INVOCATIONS.labels(
                    agent_type=agent_type,
                    status="success"
                ).inc()

                log.debug(
                    "agent_metrics.execution_success",
                    duration_s=time.perf_counter() - start
                )

                return result

            except Exception as e:
                error_type = type(e).__name__

                AGENT_ERRORS.labels(
                    agent_type=agent_type,
                    error_type=error_type
                ).inc()

                AGENT_INVOCATIONS.labels(
                    agent_type=agent_type,
                    status="error"
                ).inc()

                log.error(
                    "agent_metrics.execution_error",
                    error_type=error_type,
                    error_message=str(e),
                    duration_s=time.perf_counter() - start
                )

                raise

            finally:
                duration = time.perf_counter() - start
                AGENT_EXECUTION_TIME.labels(
                    agent_type=agent_type
                ).observe(duration)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def record_agent_invocation(
    agent_type: str,
    status: str = "success",
    duration_s: float = 0.0,
    error_type: str | None = None
) -> None:
    """
    Manually record an Agent invocation metric.

    Use this function when the decorator approach is not suitable,
    for example when tracking external agent calls.

    [Source: docs/architecture/performance-monitoring-architecture.md:200-238]

    Args:
        agent_type: Agent type name
        status: Invocation status ("success" or "error")
        duration_s: Execution duration in seconds
        error_type: Error type name (required if status is "error")

    Example:
        >>> record_agent_invocation("scoring-agent", "success", 1.5)
        >>> record_agent_invocation("scoring-agent", "error", 0.5, "TimeoutError")
    """
    # Record invocation count
    AGENT_INVOCATIONS.labels(
        agent_type=agent_type,
        status=status
    ).inc()

    # Record execution time
    if duration_s > 0:
        AGENT_EXECUTION_TIME.labels(
            agent_type=agent_type
        ).observe(duration_s)

    # Record error if applicable
    if status == "error" and error_type:
        AGENT_ERRORS.labels(
            agent_type=agent_type,
            error_type=error_type
        ).inc()

    logger.debug(
        "agent_metrics.manual_record",
        agent_type=agent_type,
        status=status,
        duration_s=duration_s,
        error_type=error_type
    )


def get_agent_metrics_snapshot() -> dict[str, Any]:
    """
    Get a snapshot of current Agent metrics for summary endpoint.

    Returns aggregated metrics suitable for the /metrics/summary endpoint.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]

    Returns:
        Dictionary with agent metrics summary

    Example:
        >>> snapshot = get_agent_metrics_snapshot()
        >>> print(snapshot["invocations_total"])
        42
    """
    from prometheus_client import REGISTRY

    invocations_total = 0
    total_time = 0.0
    total_count = 0
    by_type: dict[str, dict[str, Any]] = {}

    # ✅ Verified from Context7:/prometheus/client_python (REGISTRY.collect())
    for metric in REGISTRY.collect():
        # Process invocation counter
        if metric.name == "canvas_agent_invocations_total":
            for sample in metric.samples:
                if sample.name.endswith("_total"):
                    agent_type = sample.labels.get("agent_type", "unknown")
                    status = sample.labels.get("status", "unknown")
                    count = int(sample.value)

                    if agent_type not in by_type:
                        by_type[agent_type] = {
                            "count": 0,
                            "success_count": 0,
                            "error_count": 0,
                            "avg_time_s": 0.0
                        }

                    by_type[agent_type]["count"] += count
                    invocations_total += count

                    if status == "success":
                        by_type[agent_type]["success_count"] += count
                    elif status == "error":
                        by_type[agent_type]["error_count"] += count

        # Process execution time histogram
        elif metric.name == "canvas_agent_execution_seconds":
            for sample in metric.samples:
                if sample.name.endswith("_sum"):
                    agent_type = sample.labels.get("agent_type", "unknown")
                    total_time += sample.value
                    if agent_type in by_type:
                        by_type[agent_type]["_sum"] = sample.value

                elif sample.name.endswith("_count"):
                    agent_type = sample.labels.get("agent_type", "unknown")
                    total_count += int(sample.value)
                    if agent_type in by_type:
                        by_type[agent_type]["_count"] = int(sample.value)

    # Calculate averages
    avg_execution_time_s = total_time / total_count if total_count > 0 else 0.0

    for agent_type_data in by_type.values():
        count = agent_type_data.pop("_count", 0)
        sum_time = agent_type_data.pop("_sum", 0.0)
        agent_type_data["avg_time_s"] = sum_time / count if count > 0 else 0.0

    return {
        "invocations_total": invocations_total,
        "avg_execution_time_s": round(avg_execution_time_s, 4),
        "by_type": by_type
    }
