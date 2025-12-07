# Canvas Learning System - Memory Metrics Middleware
# ✅ Verified from Context7:/prometheus/client_python (topic: Counter Histogram Gauge labels observe)
# ✅ Verified from ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md (ErrorCode体系)
# ✅ Verified from ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md (structlog集成)
"""
Memory system monitoring middleware for Prometheus metrics.

Provides context managers and utilities for tracking memory system
(Graphiti, LanceDB, Temporal) query latency and error rates.

[Source: docs/architecture/performance-monitoring-architecture.md:239-280]
[Source: specs/api/canvas-api.openapi.yml:629-660]
"""

import time
from contextlib import contextmanager
from typing import Any, Generator

# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
import structlog

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter Histogram labels)
from prometheus_client import Counter, Histogram

logger = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Memory Types
# [Source: docs/prd/sections/v117-3层记忆技术栈勘误修正-2025-11-12-必读.md]
# ═══════════════════════════════════════════════════════════════════════════════

VALID_MEMORY_TYPES = frozenset([
    "graphiti",      # Knowledge graph layer (Neo4j-based)
    "lancedb",       # Semantic memory layer (vector embeddings)
    "temporal",      # Temporal memory layer (learning history)
    "sqlite",        # Local cache/fallback
])

VALID_OPERATIONS = frozenset([
    "read",
    "write",
    "search",
    "delete",
    "sync",
    "batch_read",
    "batch_write",
])

# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Metrics Definitions
# [Source: docs/architecture/performance-monitoring-architecture.md:239-280]
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/prometheus/client_python (topic: Histogram with labels and buckets)
# Histogram for tracking memory query latency
MEMORY_QUERY_LATENCY = Histogram(
    "canvas_memory_query_seconds",
    "Memory system query latency in seconds",
    ["memory_type", "operation"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter with labels)
# Counter for tracking memory query errors
MEMORY_ERRORS = Counter(
    "canvas_memory_errors_total",
    "Total memory system errors",
    ["memory_type", "operation", "error_type"]
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter with labels)
# Counter for tracking memory query counts
MEMORY_QUERIES = Counter(
    "canvas_memory_queries_total",
    "Total memory system queries",
    ["memory_type", "operation", "status"]
)


# ═══════════════════════════════════════════════════════════════════════════════
# Context Manager for Memory Query Tracking
# [Source: docs/architecture/performance-monitoring-architecture.md:239-280]
# ═══════════════════════════════════════════════════════════════════════════════

@contextmanager
def track_memory_query(
    memory_type: str,
    operation: str
) -> Generator[None, None, None]:
    """
    Context manager for tracking memory system query metrics.

    Automatically tracks query latency, count, and errors for the wrapped
    memory operation.

    [Source: docs/architecture/performance-monitoring-architecture.md:239-280]

    Args:
        memory_type: Memory system type (graphiti, lancedb, temporal, sqlite)
        operation: Operation type (read, write, search, delete, sync, batch_*)

    Yields:
        None: Context manager yields control to the wrapped operation

    Usage:
        with track_memory_query("graphiti", "search"):
            results = graphiti_client.search(query)

    Example:
        >>> with track_memory_query("lancedb", "read"):
        ...     data = lancedb_client.get("entity_123")
    """
    # Validate inputs
    if memory_type not in VALID_MEMORY_TYPES:
        logger.warning(
            "memory_metrics.unknown_memory_type",
            memory_type=memory_type,
            valid_types=list(VALID_MEMORY_TYPES)
        )

    if operation not in VALID_OPERATIONS:
        logger.warning(
            "memory_metrics.unknown_operation",
            operation=operation,
            valid_operations=list(VALID_OPERATIONS)
        )

    # ✅ Verified from Context7:/prometheus/client_python (time.perf_counter for high precision)
    start = time.perf_counter()
    log = logger.bind(memory_type=memory_type, operation=operation)

    try:
        yield

        # ✅ Verified from Context7:/prometheus/client_python (Counter.labels().inc())
        MEMORY_QUERIES.labels(
            memory_type=memory_type,
            operation=operation,
            status="success"
        ).inc()

        log.debug(
            "memory_metrics.query_success",
            duration_s=time.perf_counter() - start
        )

    except Exception as e:
        # ✅ Verified from ADR-009:59-87 (ErrorCode体系)
        error_type = type(e).__name__

        # ✅ Verified from Context7:/prometheus/client_python (Counter.labels().inc())
        MEMORY_ERRORS.labels(
            memory_type=memory_type,
            operation=operation,
            error_type=error_type
        ).inc()

        MEMORY_QUERIES.labels(
            memory_type=memory_type,
            operation=operation,
            status="error"
        ).inc()

        log.error(
            "memory_metrics.query_error",
            error_type=error_type,
            error_message=str(e),
            duration_s=time.perf_counter() - start
        )

        raise

    finally:
        # Always record query latency
        duration = time.perf_counter() - start

        # ✅ Verified from Context7:/prometheus/client_python (Histogram.labels().observe())
        MEMORY_QUERY_LATENCY.labels(
            memory_type=memory_type,
            operation=operation
        ).observe(duration)


def record_memory_query(
    memory_type: str,
    operation: str,
    status: str = "success",
    duration_s: float = 0.0,
    error_type: str | None = None
) -> None:
    """
    Manually record a memory query metric.

    Use this function when the context manager approach is not suitable,
    for example when tracking async operations or external memory calls.

    [Source: docs/architecture/performance-monitoring-architecture.md:239-280]

    Args:
        memory_type: Memory system type
        operation: Operation type
        status: Query status ("success" or "error")
        duration_s: Query duration in seconds
        error_type: Error type name (required if status is "error")

    Example:
        >>> record_memory_query("graphiti", "search", "success", 0.5)
        >>> record_memory_query("lancedb", "write", "error", 0.1, "ConnectionError")
    """
    # Record query count
    MEMORY_QUERIES.labels(
        memory_type=memory_type,
        operation=operation,
        status=status
    ).inc()

    # Record query latency
    if duration_s > 0:
        MEMORY_QUERY_LATENCY.labels(
            memory_type=memory_type,
            operation=operation
        ).observe(duration_s)

    # Record error if applicable
    if status == "error" and error_type:
        MEMORY_ERRORS.labels(
            memory_type=memory_type,
            operation=operation,
            error_type=error_type
        ).inc()

    logger.debug(
        "memory_metrics.manual_record",
        memory_type=memory_type,
        operation=operation,
        status=status,
        duration_s=duration_s,
        error_type=error_type
    )


def get_memory_metrics_snapshot() -> dict[str, Any]:
    """
    Get a snapshot of current memory metrics for summary endpoint.

    Returns aggregated metrics suitable for the /metrics/summary endpoint.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]

    Returns:
        Dictionary with memory metrics summary

    Example:
        >>> snapshot = get_memory_metrics_snapshot()
        >>> print(snapshot["queries_total"])
        150
    """
    from prometheus_client import REGISTRY

    queries_total = 0
    total_time = 0.0
    total_count = 0
    by_type: dict[str, dict[str, Any]] = {}

    # ✅ Verified from Context7:/prometheus/client_python (REGISTRY.collect())
    for metric in REGISTRY.collect():
        # Process query counter
        if metric.name == "canvas_memory_queries_total":
            for sample in metric.samples:
                if sample.name.endswith("_total"):
                    memory_type = sample.labels.get("memory_type", "unknown")
                    operation = sample.labels.get("operation", "unknown")
                    status = sample.labels.get("status", "unknown")
                    count = int(sample.value)

                    if memory_type not in by_type:
                        by_type[memory_type] = {
                            "query_count": 0,
                            "success_count": 0,
                            "error_count": 0,
                            "avg_latency_s": 0.0,
                            "by_operation": {}
                        }

                    by_type[memory_type]["query_count"] += count
                    queries_total += count

                    if status == "success":
                        by_type[memory_type]["success_count"] += count
                    elif status == "error":
                        by_type[memory_type]["error_count"] += count

                    # Track by operation
                    if operation not in by_type[memory_type]["by_operation"]:
                        by_type[memory_type]["by_operation"][operation] = 0
                    by_type[memory_type]["by_operation"][operation] += count

        # Process query latency histogram
        elif metric.name == "canvas_memory_query_seconds":
            for sample in metric.samples:
                if sample.name.endswith("_sum"):
                    memory_type = sample.labels.get("memory_type", "unknown")
                    total_time += sample.value
                    if memory_type in by_type:
                        if "_sum" not in by_type[memory_type]:
                            by_type[memory_type]["_sum"] = 0.0
                        by_type[memory_type]["_sum"] += sample.value

                elif sample.name.endswith("_count"):
                    memory_type = sample.labels.get("memory_type", "unknown")
                    total_count += int(sample.value)
                    if memory_type in by_type:
                        if "_count" not in by_type[memory_type]:
                            by_type[memory_type]["_count"] = 0
                        by_type[memory_type]["_count"] += int(sample.value)

    # Calculate averages
    avg_latency_s = total_time / total_count if total_count > 0 else 0.0

    for memory_type_data in by_type.values():
        count = memory_type_data.pop("_count", 0)
        sum_time = memory_type_data.pop("_sum", 0.0)
        memory_type_data["avg_latency_s"] = sum_time / count if count > 0 else 0.0

    return {
        "queries_total": queries_total,
        "avg_latency_s": round(avg_latency_s, 4),
        "by_type": by_type
    }
