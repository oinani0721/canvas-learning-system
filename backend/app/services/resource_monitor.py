# Canvas Learning System - Resource Monitor Service
# ✅ Verified from Context7:/giampaolo/psutil (topic: cpu_percent virtual_memory disk_usage)
# ✅ Verified from Context7:/prometheus/client_python (topic: Gauge labels set)
# ✅ Verified from ADR-010-LOGGING-AGGREGATION-STRUCTLOG.md (structlog集成)
"""
System resource monitoring service for Prometheus metrics.

Provides utilities for tracking CPU, memory, and disk usage
with configurable thresholds and alerts.

[Source: docs/architecture/performance-monitoring-architecture.md:281-320]
[Source: specs/api/canvas-api.openapi.yml:661-700]
"""

import asyncio
import shutil
import sys
from typing import Any

# ✅ Verified from Context7:/giampaolo/psutil (topic: cpu_percent virtual_memory disk_usage)
import psutil

# ✅ Verified from ADR-010:77-100 (structlog get_logger and bind)
import structlog

# ✅ Verified from Context7:/prometheus/client_python (topic: Gauge with labels)
from prometheus_client import Gauge

logger = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Prometheus Metrics Definitions
# [Source: docs/architecture/performance-monitoring-architecture.md:281-320]
# ═══════════════════════════════════════════════════════════════════════════════

# ✅ Verified from Context7:/prometheus/client_python (topic: Gauge)
# Gauge for CPU usage percentage
RESOURCE_CPU_USAGE = Gauge(
    "canvas_resource_cpu_percent",
    "CPU usage percentage"
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Gauge with labels)
# Gauge for memory usage
RESOURCE_MEMORY_USAGE = Gauge(
    "canvas_resource_memory_percent",
    "Memory usage percentage"
)

RESOURCE_MEMORY_USED_BYTES = Gauge(
    "canvas_resource_memory_used_bytes",
    "Memory used in bytes"
)

RESOURCE_MEMORY_AVAILABLE_BYTES = Gauge(
    "canvas_resource_memory_available_bytes",
    "Memory available in bytes"
)

# ✅ Verified from Context7:/prometheus/client_python (topic: Gauge with labels)
# Gauge for disk usage
RESOURCE_DISK_USAGE = Gauge(
    "canvas_resource_disk_percent",
    "Disk usage percentage",
    ["mount_point"]
)

RESOURCE_DISK_USED_BYTES = Gauge(
    "canvas_resource_disk_used_bytes",
    "Disk used in bytes",
    ["mount_point"]
)

RESOURCE_DISK_FREE_BYTES = Gauge(
    "canvas_resource_disk_free_bytes",
    "Disk free in bytes",
    ["mount_point"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# Default Thresholds
# [Source: docs/architecture/performance-monitoring-architecture.md:281-320]
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_THRESHOLDS = {
    "cpu_warning": 70.0,
    "cpu_critical": 90.0,
    "memory_warning": 70.0,
    "memory_critical": 90.0,
    "disk_warning": 80.0,
    "disk_critical": 95.0,
}


class ResourceMonitor:
    """
    System resource monitor with Prometheus metrics integration.

    Provides methods for collecting CPU, memory, and disk metrics
    with configurable thresholds and alert levels.

    [Source: docs/architecture/performance-monitoring-architecture.md:281-320]

    Attributes:
        thresholds: Dictionary of warning/critical thresholds
        disk_paths: List of disk mount points to monitor

    Example:
        >>> monitor = ResourceMonitor()
        >>> metrics = monitor.collect_metrics()
        >>> print(metrics["cpu"]["percent"])
        45.2
    """

    def __init__(
        self,
        thresholds: dict[str, float] | None = None,
        disk_paths: list[str] | None = None
    ):
        """
        Initialize the resource monitor.

        Args:
            thresholds: Custom thresholds (optional, uses defaults if not provided)
            disk_paths: Disk mount points to monitor (defaults to ["/"])
        """
        self.thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        # Cross-platform default disk path: "/" on Unix, "C:\\" on Windows
        default_disk = "C:\\" if sys.platform == "win32" else "/"
        self.disk_paths = disk_paths or [default_disk]
        self._running = False
        self._task: asyncio.Task | None = None

        logger.info(
            "resource_monitor.initialized",
            thresholds=self.thresholds,
            disk_paths=self.disk_paths
        )

    def get_cpu_metrics(self) -> dict[str, Any]:
        """
        Get current CPU metrics.

        Returns:
            Dictionary with CPU metrics including percent usage and status

        ✅ Verified from Context7:/giampaolo/psutil (topic: cpu_percent)
        """
        # ✅ Verified from Context7:/giampaolo/psutil
        # cpu_percent(interval=None) returns immediately with last measurement
        percent = psutil.cpu_percent(interval=None)

        # Determine status based on thresholds
        if percent >= self.thresholds["cpu_critical"]:
            status = "critical"
        elif percent >= self.thresholds["cpu_warning"]:
            status = "warning"
        else:
            status = "normal"

        # Update Prometheus gauge
        # ✅ Verified from Context7:/prometheus/client_python (Gauge.set())
        RESOURCE_CPU_USAGE.set(percent)

        return {
            "percent": percent,
            "status": status,
            "threshold_warning": self.thresholds["cpu_warning"],
            "threshold_critical": self.thresholds["cpu_critical"],
        }

    def get_memory_metrics(self) -> dict[str, Any]:
        """
        Get current memory metrics.

        Returns:
            Dictionary with memory metrics including percent, used, available

        ✅ Verified from Context7:/giampaolo/psutil (topic: virtual_memory)
        """
        # ✅ Verified from Context7:/giampaolo/psutil
        # virtual_memory() returns named tuple with total, available, percent, used, free
        mem = psutil.virtual_memory()

        # Determine status based on thresholds
        if mem.percent >= self.thresholds["memory_critical"]:
            status = "critical"
        elif mem.percent >= self.thresholds["memory_warning"]:
            status = "warning"
        else:
            status = "normal"

        # Update Prometheus gauges
        # ✅ Verified from Context7:/prometheus/client_python (Gauge.set())
        RESOURCE_MEMORY_USAGE.set(mem.percent)
        RESOURCE_MEMORY_USED_BYTES.set(mem.used)
        RESOURCE_MEMORY_AVAILABLE_BYTES.set(mem.available)

        return {
            "percent": mem.percent,
            "used_bytes": mem.used,
            "available_bytes": mem.available,
            "total_bytes": mem.total,
            "status": status,
            "threshold_warning": self.thresholds["memory_warning"],
            "threshold_critical": self.thresholds["memory_critical"],
        }

    def get_disk_metrics(self) -> dict[str, dict[str, Any]]:
        """
        Get current disk metrics for configured mount points.

        Returns:
            Dictionary mapping mount points to their metrics

        ✅ Verified from Context7:/giampaolo/psutil (topic: disk_usage)
        """
        results: dict[str, dict[str, Any]] = {}

        for path in self.disk_paths:
            try:
                # Try psutil first, fall back to shutil for Git Bash compatibility
                # ✅ Verified from Context7:/giampaolo/psutil
                # disk_usage(path) returns named tuple with total, used, free, percent
                try:
                    disk = psutil.disk_usage(path)
                    total = disk.total
                    used = disk.used
                    free = disk.free
                    percent = disk.percent
                except SystemError:
                    # psutil.disk_usage has known issues in Git Bash on Windows
                    # Fall back to shutil.disk_usage which works correctly
                    logger.debug(
                        "resource_monitor.psutil_fallback",
                        path=path,
                        reason="SystemError in psutil.disk_usage"
                    )
                    shutil_usage = shutil.disk_usage(path)
                    total = shutil_usage.total
                    used = shutil_usage.used
                    free = shutil_usage.free
                    percent = (used / total) * 100.0 if total > 0 else 0.0

                # Determine status based on thresholds
                if percent >= self.thresholds["disk_critical"]:
                    status = "critical"
                elif percent >= self.thresholds["disk_warning"]:
                    status = "warning"
                else:
                    status = "normal"

                # Update Prometheus gauges
                # ✅ Verified from Context7:/prometheus/client_python (Gauge.labels().set())
                RESOURCE_DISK_USAGE.labels(mount_point=path).set(percent)
                RESOURCE_DISK_USED_BYTES.labels(mount_point=path).set(used)
                RESOURCE_DISK_FREE_BYTES.labels(mount_point=path).set(free)

                results[path] = {
                    "percent": percent,
                    "used_bytes": used,
                    "free_bytes": free,
                    "total_bytes": total,
                    "status": status,
                    "threshold_warning": self.thresholds["disk_warning"],
                    "threshold_critical": self.thresholds["disk_critical"],
                }

            except OSError as e:
                logger.warning(
                    "resource_monitor.disk_error",
                    path=path,
                    error=str(e)
                )
                results[path] = {
                    "error": str(e),
                    "status": "error"
                }

        return results

    def collect_metrics(self) -> dict[str, Any]:
        """
        Collect all resource metrics at once.

        Returns:
            Dictionary with cpu, memory, and disk metrics

        Example:
            >>> monitor = ResourceMonitor()
            >>> metrics = monitor.collect_metrics()
            >>> print(metrics["cpu"]["percent"])
        """
        cpu = self.get_cpu_metrics()
        memory = self.get_memory_metrics()
        disk = self.get_disk_metrics()

        # Calculate overall system status
        statuses = [cpu["status"], memory["status"]]
        for disk_metrics in disk.values():
            if "status" in disk_metrics:
                statuses.append(disk_metrics["status"])

        if "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses:
            overall_status = "warning"
        elif "error" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        logger.debug(
            "resource_monitor.metrics_collected",
            cpu_percent=cpu["percent"],
            memory_percent=memory["percent"],
            overall_status=overall_status
        )

        return {
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "overall_status": overall_status,
        }

    async def start_background_collection(
        self,
        interval_seconds: float = 5.0
    ) -> None:
        """
        Start background metrics collection loop.

        [Source: Story 17.2 AC-4: 采集频率≤5秒]

        Args:
            interval_seconds: Collection interval in seconds (default: 5, AC requirement ≤5s)

        Note:
            Call stop_background_collection() to stop the loop.
        """
        if self._running:
            logger.warning("resource_monitor.already_running")
            return

        self._running = True

        async def collection_loop() -> None:
            logger.info(
                "resource_monitor.background_started",
                interval_seconds=interval_seconds
            )

            while self._running:
                try:
                    self.collect_metrics()
                except Exception as e:
                    logger.error(
                        "resource_monitor.collection_error",
                        error=str(e)
                    )

                await asyncio.sleep(interval_seconds)

            logger.info("resource_monitor.background_stopped")

        self._task = asyncio.create_task(collection_loop())

    async def stop_background_collection(self) -> None:
        """Stop background metrics collection loop."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("resource_monitor.stopped")


def get_resource_metrics_snapshot() -> dict[str, Any]:
    """
    Get a one-time snapshot of resource metrics.

    Convenience function for getting resource metrics without
    instantiating a ResourceMonitor.

    [Source: specs/api/canvas-api.openapi.yml:661-700]

    Returns:
        Dictionary with cpu, memory, and disk metrics

    Example:
        >>> snapshot = get_resource_metrics_snapshot()
        >>> print(snapshot["cpu"]["percent"])
    """
    monitor = ResourceMonitor()
    return monitor.collect_metrics()


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level Monitor Instance
# ═══════════════════════════════════════════════════════════════════════════════

# Singleton instance for application-wide usage
_default_monitor: ResourceMonitor | None = None


def get_default_monitor() -> ResourceMonitor:
    """
    Get or create the default ResourceMonitor instance.

    Returns:
        The default ResourceMonitor singleton instance
    """
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = ResourceMonitor()
    return _default_monitor
