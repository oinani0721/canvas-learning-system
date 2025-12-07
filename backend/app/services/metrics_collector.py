# Canvas Learning System - Metrics Collector Service
# ✅ Verified from Context7:/prometheus/client_python (topic: REGISTRY collect generate_latest)
# ✅ Verified from ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md (structlog集成)
"""
Unified metrics collector service for Canvas Learning System.

Aggregates all Prometheus metrics (Agent, Memory, Resource) into a single
summary endpoint for dashboard consumption.

[Source: docs/architecture/performance-monitoring-architecture.md:321-380]
[Source: specs/api/canvas-api.openapi.yml:987-1060]
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
import structlog

# ✅ Verified from Context7:/prometheus/client_python (topic: REGISTRY generate_latest)
from prometheus_client import REGISTRY, generate_latest

from app.middleware.agent_metrics import get_agent_metrics_snapshot
from app.middleware.memory_metrics import get_memory_metrics_snapshot
from app.services.resource_monitor import get_resource_metrics_snapshot

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MetricsSummary Data Class
# [Source: docs/architecture/performance-monitoring-architecture.md:321-380]
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetricsSummary:
    """
    Unified metrics summary for all Canvas Learning System components.

    Aggregates Agent execution metrics, Memory system metrics, and
    Resource usage metrics into a single summary structure.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]

    Attributes:
        timestamp: ISO timestamp when metrics were collected
        agent_metrics: Agent execution metrics summary
        memory_metrics: Memory system metrics summary
        resource_metrics: System resource metrics summary
        overall_health: Overall system health status
        alerts: List of active alerts based on thresholds

    Example:
        >>> summary = MetricsSummary.collect()
        >>> print(summary.overall_health)
        "healthy"
    """

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_metrics: dict[str, Any] = field(default_factory=dict)
    memory_metrics: dict[str, Any] = field(default_factory=dict)
    resource_metrics: dict[str, Any] = field(default_factory=dict)
    overall_health: str = "unknown"
    alerts: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def collect(cls) -> "MetricsSummary":
        """
        Collect all metrics and create a summary instance.

        Returns:
            MetricsSummary: Populated metrics summary

        Example:
            >>> summary = MetricsSummary.collect()
            >>> print(summary.agent_metrics["invocations_total"])
        """
        # Collect metrics from all sources
        agent_metrics = get_agent_metrics_snapshot()
        memory_metrics = get_memory_metrics_snapshot()
        resource_metrics = get_resource_metrics_snapshot()

        # Determine overall health and generate alerts
        alerts = []
        health_indicators = []

        # Check resource health
        resource_status = resource_metrics.get("overall_status", "unknown")
        health_indicators.append(resource_status)

        if resource_status == "critical":
            alerts.append({
                "level": "critical",
                "source": "resource",
                "message": "System resources at critical level",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif resource_status == "warning":
            alerts.append({
                "level": "warning",
                "source": "resource",
                "message": "System resources approaching limits",
                "timestamp": datetime.utcnow().isoformat()
            })

        # Check for high agent error rates
        if agent_metrics.get("invocations_total", 0) > 0:
            by_type = agent_metrics.get("by_type", {})
            for agent_type, type_data in by_type.items():
                error_count = type_data.get("error_count", 0)
                total_count = type_data.get("count", 0)
                if total_count > 0:
                    error_rate = error_count / total_count
                    if error_rate > 0.1:  # >10% error rate
                        alerts.append({
                            "level": "warning",
                            "source": "agent",
                            "message": f"High error rate for {agent_type}: {error_rate:.1%}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        health_indicators.append("warning")

        # Check for high memory latency
        if memory_metrics.get("avg_latency_s", 0) > 2.0:  # >2s average
            alerts.append({
                "level": "warning",
                "source": "memory",
                "message": f"High memory query latency: {memory_metrics['avg_latency_s']:.2f}s",
                "timestamp": datetime.utcnow().isoformat()
            })
            health_indicators.append("warning")

        # Determine overall health
        if "critical" in health_indicators:
            overall_health = "critical"
        elif "warning" in health_indicators:
            overall_health = "degraded"
        elif "error" in health_indicators:
            overall_health = "degraded"
        else:
            overall_health = "healthy"

        logger.debug(
            "metrics_collector.summary_collected",
            overall_health=overall_health,
            alert_count=len(alerts)
        )

        return cls(
            timestamp=datetime.utcnow().isoformat(),
            agent_metrics=agent_metrics,
            memory_metrics=memory_metrics,
            resource_metrics=resource_metrics,
            overall_health=overall_health,
            alerts=alerts
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert MetricsSummary to dictionary for API response.

        Returns:
            Dictionary representation of the metrics summary
        """
        return {
            "timestamp": self.timestamp,
            "overall_health": self.overall_health,
            "agent": self.agent_metrics,
            "memory": self.memory_metrics,
            "resource": self.resource_metrics,
            "alerts": self.alerts,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Endpoint Utilities
# [Source: specs/api/canvas-api.openapi.yml:987-1060]
# ═══════════════════════════════════════════════════════════════════════════════

def get_prometheus_metrics() -> bytes:
    """
    Get raw Prometheus metrics in exposition format.

    Returns metrics in the standard Prometheus text format for
    scraping by Prometheus server.

    ✅ Verified from Context7:/prometheus/client_python (topic: generate_latest REGISTRY)

    Returns:
        bytes: Prometheus metrics in text exposition format

    Example:
        >>> metrics = get_prometheus_metrics()
        >>> print(metrics.decode())
        # HELP canvas_agent_execution_seconds ...
    """
    # ✅ Verified from Context7:/prometheus/client_python
    # generate_latest(registry) returns bytes in Prometheus exposition format
    return generate_latest(REGISTRY)


def get_metrics_summary() -> dict[str, Any]:
    """
    Get aggregated metrics summary for dashboard.

    Convenience function for getting all metrics at once.

    [Source: specs/api/canvas-api.openapi.yml:987-1060]

    Returns:
        Dictionary with all metrics summary

    Example:
        >>> summary = get_metrics_summary()
        >>> print(summary["overall_health"])
    """
    return MetricsSummary.collect().to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# Health Check Utilities
# [Source: specs/api/canvas-api.openapi.yml:701-750]
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HealthStatus:
    """
    System health status for health check endpoint.

    [Source: specs/api/canvas-api.openapi.yml:701-750]

    Attributes:
        status: Overall status (healthy, degraded, unhealthy)
        components: Individual component statuses
        timestamp: ISO timestamp
    """

    status: str
    components: dict[str, dict[str, Any]]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @classmethod
    def check(cls) -> "HealthStatus":
        """
        Perform health check on all system components.

        Returns:
            HealthStatus: Current system health status
        """
        components: dict[str, dict[str, Any]] = {}

        # Check resource health
        try:
            resource_metrics = get_resource_metrics_snapshot()
            resource_status = resource_metrics.get("overall_status", "unknown")
            components["resources"] = {
                "status": resource_status,
                "cpu_percent": resource_metrics.get("cpu", {}).get("percent"),
                "memory_percent": resource_metrics.get("memory", {}).get("percent"),
            }
        except Exception as e:
            logger.error("health_check.resource_error", error=str(e))
            components["resources"] = {"status": "error", "error": str(e)}

        # Check metrics collection
        try:
            agent_metrics = get_agent_metrics_snapshot()
            components["agent_metrics"] = {
                "status": "healthy",
                "invocations_total": agent_metrics.get("invocations_total", 0)
            }
        except Exception as e:
            logger.error("health_check.agent_metrics_error", error=str(e))
            components["agent_metrics"] = {"status": "error", "error": str(e)}

        # Check memory metrics
        try:
            memory_metrics = get_memory_metrics_snapshot()
            components["memory_metrics"] = {
                "status": "healthy",
                "queries_total": memory_metrics.get("queries_total", 0)
            }
        except Exception as e:
            logger.error("health_check.memory_metrics_error", error=str(e))
            components["memory_metrics"] = {"status": "error", "error": str(e)}

        # Determine overall status
        statuses = [c.get("status", "unknown") for c in components.values()]
        if "error" in statuses or "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "critical" in statuses:
            overall_status = "unhealthy"
        elif "warning" in statuses or "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return cls(
            status=overall_status,
            components=components,
            timestamp=datetime.utcnow().isoformat()
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "status": self.status,
            "components": self.components,
            "timestamp": self.timestamp,
        }
