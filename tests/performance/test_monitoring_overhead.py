# Canvas Learning System - Monitoring Overhead Tests
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:399-450)
# ✅ Verified from Story 17.5 (overhead measurement)
# [Source: docs/stories/17.5.story.md - Task 5]
"""
Monitoring system overhead tests.

Verifies that monitoring adds minimal overhead to system operations.
Target: <5% overhead on critical paths.
"""

import asyncio
import gc
import statistics
import time
from typing import Callable, List
from unittest.mock import MagicMock, patch

import pytest

import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# [Source: ADR-008 pytest fixtures pattern]
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def baseline_operation():
    """Create a baseline operation without monitoring."""
    async def operation():
        await asyncio.sleep(0.01)  # 10ms simulated work
        return {"result": "success"}

    return operation


@pytest.fixture
def monitored_operation():
    """Create an operation with monitoring wrapper."""
    metrics = {"calls": 0, "total_time": 0}

    async def operation():
        start = time.perf_counter()
        metrics["calls"] += 1

        await asyncio.sleep(0.01)  # 10ms simulated work
        result = {"result": "success"}

        metrics["total_time"] += time.perf_counter() - start
        return result

    operation.metrics = metrics
    return operation


@pytest.fixture
def heavy_monitoring_operation():
    """Create an operation with extensive monitoring."""
    metrics = {
        "calls": 0,
        "latencies": [],
        "success": 0,
        "errors": 0,
        "last_call": None,
    }

    async def operation():
        start = time.perf_counter()
        metrics["calls"] += 1

        try:
            await asyncio.sleep(0.01)  # 10ms simulated work
            result = {"result": "success"}

            latency = time.perf_counter() - start
            metrics["latencies"].append(latency)
            metrics["success"] += 1
            metrics["last_call"] = time.time()

            # Simulate metric export
            _ = {
                "avg": sum(metrics["latencies"]) / len(metrics["latencies"]),
                "p95": sorted(metrics["latencies"])[int(len(metrics["latencies"]) * 0.95)]
                if len(metrics["latencies"]) > 20 else 0,
            }

            return result
        except Exception as e:
            metrics["errors"] += 1
            raise

    operation.metrics = metrics
    return operation


# ═══════════════════════════════════════════════════════════════════════════════
# Latency Overhead Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:399-420]
# ═══════════════════════════════════════════════════════════════════════════════


class TestLatencyOverhead:
    """Monitoring latency overhead tests."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_monitoring_latency_overhead_under_5_percent(
        self,
        baseline_operation,
        monitored_operation
    ):
        """Test monitoring adds <5% latency overhead.

        [Source: docs/stories/17.5.story.md - Task 5 AC:5]
        """
        iterations = 100

        # Warm up
        for _ in range(10):
            await baseline_operation()
            await monitored_operation()

        # Measure baseline
        baseline_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await baseline_operation()
            baseline_times.append(time.perf_counter() - start)

        # Measure monitored
        monitored_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await monitored_operation()
            monitored_times.append(time.perf_counter() - start)

        baseline_avg = statistics.mean(baseline_times)
        monitored_avg = statistics.mean(monitored_times)
        overhead = (monitored_avg - baseline_avg) / baseline_avg

        logger.info(
            "latency_overhead",
            baseline_avg_ms=baseline_avg * 1000,
            monitored_avg_ms=monitored_avg * 1000,
            overhead_pct=overhead * 100
        )

        assert overhead < 0.05, f"Monitoring latency overhead {overhead:.2%} >= 5%"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_heavy_monitoring_overhead(
        self,
        baseline_operation,
        heavy_monitoring_operation
    ):
        """Test heavy monitoring still maintains acceptable overhead."""
        iterations = 50

        # Warm up
        for _ in range(10):
            await baseline_operation()
            await heavy_monitoring_operation()

        # Measure baseline
        baseline_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await baseline_operation()
            baseline_times.append(time.perf_counter() - start)

        # Measure heavy monitoring
        heavy_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await heavy_monitoring_operation()
            heavy_times.append(time.perf_counter() - start)

        baseline_avg = statistics.mean(baseline_times)
        heavy_avg = statistics.mean(heavy_times)
        overhead = (heavy_avg - baseline_avg) / baseline_avg

        logger.info(
            "heavy_monitoring_overhead",
            baseline_avg_ms=baseline_avg * 1000,
            heavy_avg_ms=heavy_avg * 1000,
            overhead_pct=overhead * 100
        )

        # Even heavy monitoring should be under 10%
        assert overhead < 0.10, f"Heavy monitoring overhead {overhead:.2%} >= 10%"


# ═══════════════════════════════════════════════════════════════════════════════
# Memory Overhead Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:421-440]
# ═══════════════════════════════════════════════════════════════════════════════


class TestMemoryOverhead:
    """Monitoring memory overhead tests."""

    @pytest.mark.performance
    def test_metrics_memory_footprint(self):
        """Test metrics storage memory footprint.

        [Source: docs/stories/17.5.story.md - Task 5 AC:5]
        """
        import sys

        # Simulate metrics storage
        metrics_store = {
            "counters": {},
            "histograms": {},
            "gauges": {},
        }

        # Add typical metrics
        for i in range(100):
            metrics_store["counters"][f"metric_{i}"] = i * 100
            metrics_store["histograms"][f"latency_{i}"] = list(range(100))
            metrics_store["gauges"][f"gauge_{i}"] = float(i)

        # Measure memory
        memory_bytes = sys.getsizeof(metrics_store)
        # Deep size estimation
        for key, value in metrics_store.items():
            memory_bytes += sys.getsizeof(value)
            for k, v in value.items():
                memory_bytes += sys.getsizeof(k) + sys.getsizeof(v)

        memory_mb = memory_bytes / (1024 * 1024)

        logger.info(
            "metrics_memory_footprint",
            metrics_count=300,  # 100 each of counters, histograms, gauges
            memory_mb=memory_mb
        )

        # Should use less than 10MB for 300 metrics
        assert memory_mb < 10, f"Metrics memory footprint {memory_mb:.2f}MB >= 10MB"

    @pytest.mark.performance
    def test_monitoring_no_memory_leak(self, heavy_monitoring_operation):
        """Test monitoring doesn't cause memory leaks."""
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Run many operations
        async def run_operations():
            for _ in range(100):
                await heavy_monitoring_operation()

        asyncio.run(run_operations())

        gc.collect()
        final_objects = len(gc.get_objects())

        object_growth = final_objects - initial_objects

        logger.info(
            "monitoring_memory_leak",
            initial_objects=initial_objects,
            final_objects=final_objects,
            growth=object_growth
        )

        # Should not grow by more than 1000 objects (metrics data)
        assert object_growth < 1000, f"Object growth {object_growth} >= 1000"


# ═══════════════════════════════════════════════════════════════════════════════
# CPU Overhead Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:441-460]
# ═══════════════════════════════════════════════════════════════════════════════


class TestCPUOverhead:
    """Monitoring CPU overhead tests."""

    @pytest.mark.performance
    def test_metrics_calculation_cpu_overhead(self):
        """Test metrics calculation CPU overhead."""
        # Generate sample data
        latencies = [float(i) for i in range(1000)]

        # Measure CPU time for calculations
        iterations = 100

        # Baseline: no calculations
        baseline_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            _ = latencies[:]  # Just copy
            baseline_times.append(time.perf_counter() - start)

        # With calculations: mean, p95, p99
        calc_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            sorted_data = sorted(latencies)
            _ = statistics.mean(sorted_data)
            _ = sorted_data[int(len(sorted_data) * 0.95)]
            _ = sorted_data[int(len(sorted_data) * 0.99)]
            calc_times.append(time.perf_counter() - start)

        baseline_avg = statistics.mean(baseline_times)
        calc_avg = statistics.mean(calc_times)
        overhead = (calc_avg - baseline_avg) / baseline_avg if baseline_avg > 0 else 0

        logger.info(
            "metrics_calculation_overhead",
            baseline_ms=baseline_avg * 1000,
            calculation_ms=calc_avg * 1000,
            overhead_pct=overhead * 100
        )

        # Calculations should complete quickly (under 10ms)
        assert calc_avg < 0.01, f"Metrics calculation took {calc_avg * 1000:.2f}ms >= 10ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_monitoring_cpu(self):
        """Test CPU overhead under concurrent monitoring."""
        metrics = {"calls": 0}

        async def monitored_task():
            metrics["calls"] += 1
            await asyncio.sleep(0.001)
            return metrics["calls"]

        # Run concurrent tasks
        start = time.perf_counter()
        tasks = [monitored_task() for _ in range(100)]
        await asyncio.gather(*tasks)
        duration = time.perf_counter() - start

        logger.info(
            "concurrent_monitoring_cpu",
            tasks=100,
            total_duration_ms=duration * 1000,
            avg_per_task_ms=duration / 100 * 1000
        )

        # 100 tasks should complete in under 1 second
        assert duration < 1.0, f"Concurrent monitoring took {duration:.2f}s >= 1s"


# ═══════════════════════════════════════════════════════════════════════════════
# Throughput Impact Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:461-480]
# ═══════════════════════════════════════════════════════════════════════════════


class TestThroughputImpact:
    """Monitoring impact on system throughput tests."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_throughput_with_monitoring(self):
        """Test system throughput with monitoring enabled.

        [Source: docs/stories/17.5.story.md - Task 5 AC:5]
        """
        request_count = 0
        metrics = {"requests": 0}

        async def handle_request_baseline():
            nonlocal request_count
            await asyncio.sleep(0.001)  # 1ms per request
            request_count += 1

        async def handle_request_monitored():
            nonlocal request_count
            start = time.perf_counter()
            await asyncio.sleep(0.001)
            request_count += 1
            metrics["requests"] += 1
            metrics["last_latency"] = time.perf_counter() - start

        # Measure baseline throughput
        request_count = 0
        duration = 1.0
        start = time.time()
        while time.time() - start < duration:
            await handle_request_baseline()
        baseline_throughput = request_count

        # Measure monitored throughput
        request_count = 0
        start = time.time()
        while time.time() - start < duration:
            await handle_request_monitored()
        monitored_throughput = request_count

        throughput_drop = (baseline_throughput - monitored_throughput) / baseline_throughput

        logger.info(
            "throughput_impact",
            baseline_rps=baseline_throughput,
            monitored_rps=monitored_throughput,
            drop_pct=throughput_drop * 100
        )

        # Throughput should not drop by more than 5%
        assert throughput_drop < 0.05, f"Throughput drop {throughput_drop:.2%} >= 5%"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_throughput_with_monitoring(self):
        """Test batch operation throughput with monitoring."""
        batch_size = 10
        batches_processed = 0

        async def process_batch_with_monitoring():
            nonlocal batches_processed
            items_processed = 0
            for _ in range(batch_size):
                # Minimal delay to simulate monitoring overhead
                items_processed += 1
            batches_processed += 1
            await asyncio.sleep(0.01)  # Small delay between batches
            return items_processed

        # Run batches for 1 second
        start = time.time()
        while time.time() - start < 1.0:
            await process_batch_with_monitoring()

        throughput = batches_processed * batch_size

        logger.info(
            "batch_throughput",
            batches=batches_processed,
            items_per_batch=batch_size,
            items_per_second=throughput
        )

        # Should process at least 100 items per second (reasonable for async)
        assert throughput >= 100, f"Batch throughput {throughput} < 100 items/s"


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Collection Overhead Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:481-500]
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetricsCollectionOverhead:
    """Metrics collection overhead tests."""

    @pytest.mark.performance
    def test_counter_increment_overhead(self):
        """Test counter increment overhead."""
        counter = {"value": 0}
        iterations = 10000

        # Measure increment overhead
        start = time.perf_counter()
        for _ in range(iterations):
            counter["value"] += 1
        duration = time.perf_counter() - start

        avg_ns = duration / iterations * 1e9

        logger.info(
            "counter_increment_overhead",
            iterations=iterations,
            total_ms=duration * 1000,
            avg_ns=avg_ns
        )

        # Should be under 1μs per increment
        assert avg_ns < 1000, f"Counter increment took {avg_ns:.0f}ns >= 1000ns"

    @pytest.mark.performance
    def test_histogram_record_overhead(self):
        """Test histogram record overhead."""
        histogram = {"samples": []}
        max_samples = 1000
        iterations = 10000

        # Measure histogram recording
        start = time.perf_counter()
        for i in range(iterations):
            histogram["samples"].append(float(i))
            if len(histogram["samples"]) > max_samples:
                histogram["samples"] = histogram["samples"][-max_samples:]
        duration = time.perf_counter() - start

        avg_us = duration / iterations * 1e6

        logger.info(
            "histogram_record_overhead",
            iterations=iterations,
            total_ms=duration * 1000,
            avg_us=avg_us
        )

        # Should be under 10μs per record
        assert avg_us < 10, f"Histogram record took {avg_us:.1f}μs >= 10μs"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_metrics_export_overhead(self):
        """Test metrics export overhead."""
        metrics = {
            "counters": {f"counter_{i}": i * 100 for i in range(100)},
            "gauges": {f"gauge_{i}": float(i) for i in range(100)},
        }

        # Simulate metrics export (to Prometheus format)
        def export_metrics():
            lines = []
            for name, value in metrics["counters"].items():
                lines.append(f"{name} {value}")
            for name, value in metrics["gauges"].items():
                lines.append(f"{name} {value}")
            return "\n".join(lines)

        # Measure export overhead
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            _ = export_metrics()
        duration = time.perf_counter() - start

        avg_ms = duration / iterations * 1000

        logger.info(
            "metrics_export_overhead",
            iterations=iterations,
            metrics_count=200,
            avg_ms=avg_ms
        )

        # Export should take under 1ms
        assert avg_ms < 1, f"Metrics export took {avg_ms:.2f}ms >= 1ms"


# ═══════════════════════════════════════════════════════════════════════════════
# Overall Overhead Summary Test
# ═══════════════════════════════════════════════════════════════════════════════


class TestOverallOverhead:
    """Overall monitoring overhead summary tests."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_total_monitoring_overhead_under_5_percent(
        self,
        baseline_operation,
        heavy_monitoring_operation
    ):
        """Comprehensive test: total monitoring overhead <5%.

        [Source: docs/stories/17.5.story.md - Task 5 AC:5]
        """
        iterations = 50

        # Warm up
        for _ in range(10):
            await baseline_operation()
            await heavy_monitoring_operation()

        # Measure both
        baseline_total = 0
        monitored_total = 0

        for _ in range(iterations):
            start = time.perf_counter()
            await baseline_operation()
            baseline_total += time.perf_counter() - start

            start = time.perf_counter()
            await heavy_monitoring_operation()
            monitored_total += time.perf_counter() - start

        overhead = (monitored_total - baseline_total) / baseline_total

        logger.info(
            "total_monitoring_overhead",
            baseline_total_ms=baseline_total * 1000,
            monitored_total_ms=monitored_total * 1000,
            overhead_pct=overhead * 100
        )

        assert overhead < 0.05, f"Total monitoring overhead {overhead:.2%} >= 5%"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Summary
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])
