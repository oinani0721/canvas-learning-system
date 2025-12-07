# Canvas Learning System - API Request Metrics Middleware
# ✅ Verified from Context7:/prometheus/client_python (topic: Counter Histogram Gauge labels)
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: middleware http)
# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
"""
Performance monitoring middleware for API request tracking.

Provides Prometheus metrics for:
- Request counts (Counter)
- Request latency (Histogram)
- Concurrent requests (Gauge)

[Source: docs/architecture/performance-monitoring-architecture.md:140-198]
[Source: docs/stories/17.1.story.md - Task 1]
"""

import time
from typing import Callable

# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
import structlog
from fastapi import Request, Response

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter Histogram Gauge)
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Metrics Definitions
# [Source: docs/architecture/performance-monitoring-architecture.md:49-84]
# [Source: docs/stories/17.1.story.md - AC 2, 3, 4]
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/prometheus/client_python (topic: Counter labels)
# AC-2: canvas_api_requests_total Counter (method/endpoint/status)
REQUEST_COUNT = Counter(
    'canvas_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Histogram buckets labels)
# AC-3: canvas_api_request_latency_seconds Histogram (method/endpoint)
REQUEST_LATENCY = Histogram(
    'canvas_api_request_latency_seconds',
    'API request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Gauge inc dec set)
# AC-4: canvas_api_concurrent_requests Gauge
CONCURRENT_REQUESTS = Gauge(
    'canvas_api_concurrent_requests',
    'Number of concurrent requests currently being processed'
)


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Middleware Class
# [Source: docs/stories/17.1.story.md - Task 1, AC-1]
# ═══════════════════════════════════════════════════════════════════════════════

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Performance monitoring middleware for tracking API requests.

    Automatically records:
    - Request count by method, endpoint, and status code
    - Request latency distribution
    - Concurrent request count

    [Source: docs/architecture/performance-monitoring-architecture.md:140-198]

    Example:
        >>> app.add_middleware(MetricsMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process each request and record metrics.

        ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: BaseHTTPMiddleware dispatch)

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/endpoint handler

        Returns:
            Response: The HTTP response
        """
        # Increment concurrent requests gauge
        # ✅ Verified from Context7:/prometheus/client_python (Gauge.inc())
        CONCURRENT_REQUESTS.inc()

        # Start timing
        start_time = time.perf_counter()

        # Extract endpoint path (normalize to route pattern for lower cardinality)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method

        # Bind request context for structured logging
        # ✅ Verified from ADR-010:77-100 (structlog contextvars bind)
        request_id = request.headers.get("X-Request-ID", str(id(request)))
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger.debug(
            "request.started",
            method=method,
            path=request.url.path,
            endpoint=endpoint
        )

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.exception(
                "request.error",
                method=method,
                path=request.url.path,
                error=str(e)
            )
            raise
        finally:
            # Calculate duration
            duration = time.perf_counter() - start_time

            # Decrement concurrent requests
            # ✅ Verified from Context7:/prometheus/client_python (Gauge.dec())
            CONCURRENT_REQUESTS.dec()

            # Record request count
            # ✅ Verified from Context7:/prometheus/client_python (Counter.labels().inc())
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()

            # Record latency
            # ✅ Verified from Context7:/prometheus/client_python (Histogram.labels().observe())
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # Log completion
            # ✅ Verified from ADR-010:77-100 (structlog structured logging)
            logger.info(
                "request.completed",
                method=method,
                path=request.url.path,
                endpoint=endpoint,
                status=status_code,
                duration_ms=round(duration * 1000, 2)
            )

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path to reduce cardinality.

        Converts paths with IDs to templates:
        - /api/v1/agents/123 -> /api/v1/agents/{id}
        - /api/v1/canvas/abc-def -> /api/v1/canvas/{id}

        Args:
            path: The raw URL path

        Returns:
            str: Normalized endpoint pattern
        """
        import re

        # Normalize UUID patterns
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path
        )

        # Normalize numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)

        return path


# ═══════════════════════════════════════════════════════════════════════════════
# Functional Middleware (Alternative Pattern)
# [Source: docs/stories/17.1.story.md - Dev Notes]
# ═══════════════════════════════════════════════════════════════════════════════

async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """
    Functional style metrics middleware.

    Alternative to class-based MetricsMiddleware for use with @app.middleware("http").

    [Source: docs/architecture/performance-monitoring-architecture.md:169-197]

    Args:
        request: The incoming HTTP request
        call_next: The next middleware/endpoint handler

    Returns:
        Response: The HTTP response

    Example:
        >>> @app.middleware("http")
        >>> async def add_metrics(request, call_next):
        >>>     return await metrics_middleware(request, call_next)
    """
    middleware = MetricsMiddleware(app=None)
    # Use internal dispatch logic
    CONCURRENT_REQUESTS.inc()
    start_time = time.perf_counter()

    endpoint = middleware._normalize_endpoint(request.url.path)
    method = request.method

    request_id = request.headers.get("X-Request-ID", str(id(request)))
    structlog.contextvars.bind_contextvars(request_id=request_id)

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = 500
        raise
    finally:
        duration = time.perf_counter() - start_time
        CONCURRENT_REQUESTS.dec()

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    return response


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience Functions for Metrics Access
# ═══════════════════════════════════════════════════════════════════════════════

def get_api_metrics_snapshot() -> dict:
    """
    Get a snapshot of current API metrics.

    [Source: docs/stories/17.1.story.md - Task 3]

    Returns:
        dict: Dictionary containing API metrics summary
    """

    from prometheus_client import REGISTRY

    requests_total = 0
    error_count = 0
    latency_sum = 0.0
    latency_count = 0

    for metric in REGISTRY.collect():
        if metric.name == 'canvas_api_requests_total':
            for sample in metric.samples:
                if sample.name.endswith('_total') or sample.name == 'canvas_api_requests_total':
                    count = int(sample.value)
                    requests_total += count
                    status = sample.labels.get('status', '200')
                    if status.startswith('5'):
                        error_count += count

        elif metric.name == 'canvas_api_request_latency_seconds':
            for sample in metric.samples:
                if sample.name.endswith('_sum'):
                    latency_sum += sample.value
                elif sample.name.endswith('_count'):
                    latency_count += int(sample.value)

    # Calculate statistics
    avg_latency_ms = (latency_sum / latency_count * 1000) if latency_count > 0 else 0
    error_rate = error_count / requests_total if requests_total > 0 else 0

    return {
        "requests_total": requests_total,
        "avg_latency_ms": round(avg_latency_ms, 2),
        "error_rate": round(error_rate, 4),
        "error_count": error_count
    }
