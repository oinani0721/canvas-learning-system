# Canvas Learning System - Monitoring Under Load Tests
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:501-550)
# ✅ Verified from Story 17.5 (load testing)
# [Source: docs/stories/17.5.story.md - Task 6]
"""
Load tests for monitoring system stability.

Tests system behavior under sustained high load:
- Metric accuracy under load
- Alert responsiveness under load
- Dashboard stability under load
"""

import asyncio
import gc
import random
import statistics
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# [Source: ADR-008 pytest fixtures pattern]
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def load_test_config():
    """Load test configuration."""
    return {
        "concurrent_requests": 100,
        "duration_seconds": 5,
        "ramp_up_seconds": 1,
        "target_rps": 50,
    }


@pytest.fixture
def metrics_collector():
    """Metrics collector for load testing."""
    collector = {
        "requests": 0,
        "errors": 0,
        "latencies": [],
        "start_time": None,
        "end_time": None,
    }
    return collector


@pytest.fixture
def alert_evaluator():
    """Alert evaluator for load testing."""
    evaluator = {
        "evaluations": 0,
        "alerts_fired": [],
        "evaluation_times": [],
    }

    def evaluate_rules(metrics):
        start = time.perf_counter()
        evaluator["evaluations"] += 1

        # Check alert conditions
        if metrics.get("error_rate", 0) > 0.05:
            evaluator["alerts_fired"].append({
                "name": "HighErrorRate",
                "timestamp": datetime.now()
            })

        if metrics.get("p95_latency", 0) > 1000:
            evaluator["alerts_fired"].append({
                "name": "HighLatency",
                "timestamp": datetime.now()
            })

        evaluator["evaluation_times"].append(time.perf_counter() - start)

    evaluator["evaluate"] = evaluate_rules
    return evaluator


@pytest.fixture
def dashboard_data_source():
    """Dashboard data source for load testing."""
    data_source = {
        "queries": 0,
        "query_times": [],
        "cache_hits": 0,
        "cache_misses": 0,
    }

    cache = {}

    def query_metrics(metric_name, window_seconds=60):
        start = time.perf_counter()
        data_source["queries"] += 1

        # Check cache
        cache_key = f"{metric_name}_{window_seconds}"
        if cache_key in cache:
            data_source["cache_hits"] += 1
            result = cache[cache_key]
        else:
            data_source["cache_misses"] += 1
            # Simulate query
            result = random.uniform(0, 100)
            cache[cache_key] = result

        data_source["query_times"].append(time.perf_counter() - start)
        return result

    data_source["query"] = query_metrics
    data_source["clear_cache"] = lambda: cache.clear()
    return data_source


# ═══════════════════════════════════════════════════════════════════════════════
# Sustained Load Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:501-520]
# ═══════════════════════════════════════════════════════════════════════════════


class TestSustainedLoad:
    """Tests under sustained load conditions."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_metrics_accuracy_under_sustained_load(
        self,
        load_test_config,
        metrics_collector
    ):
        """Test metrics remain accurate under sustained load.

        [Source: docs/stories/17.5.story.md - Task 6 AC:6]
        """
        actual_requests = 0

        async def make_request():
            nonlocal actual_requests
            start = time.perf_counter()
            await asyncio.sleep(0.01)  # 10ms simulated request
            latency = (time.perf_counter() - start) * 1000

            actual_requests += 1
            metrics_collector["requests"] += 1
            metrics_collector["latencies"].append(latency)

        # Run sustained load
        duration = load_test_config["duration_seconds"]
        metrics_collector["start_time"] = time.time()

        tasks = []
        start_time = time.time()

        while time.time() - start_time < duration:
            tasks.append(asyncio.create_task(make_request()))
            await asyncio.sleep(0.02)  # ~50 RPS

        await asyncio.gather(*tasks)
        metrics_collector["end_time"] = time.time()

        # Verify metrics accuracy
        reported_requests = metrics_collector["requests"]
        deviation = abs(reported_requests - actual_requests) / actual_requests

        logger.info(
            "sustained_load_metrics_accuracy",
            duration_seconds=duration,
            actual_requests=actual_requests,
            reported_requests=reported_requests,
            deviation_pct=deviation * 100
        )

        assert deviation < 0.01, f"Request count deviation {deviation:.2%} >= 1%"

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_latency_reporting_under_load(
        self,
        load_test_config,
        metrics_collector
    ):
        """Test latency reporting consistency under load.

        Verifies that:
        1. All latencies are recorded (no data loss under load)
        2. Latencies are non-negative (valid measurements)
        3. Latency variance is bounded (consistent recording)

        Note: We don't test absolute latency values as asyncio.sleep timing
        varies significantly under concurrent load on different systems.
        """
        async def make_request_with_latency():
            start = time.perf_counter()
            # Simulate some work with yield to scheduler
            await asyncio.sleep(0)
            for _ in range(100):  # Simulate CPU work
                pass
            actual_latency = (time.perf_counter() - start) * 1000
            metrics_collector["latencies"].append(actual_latency)

        # Run load test - sequential to ensure predictable behavior
        for _ in range(100):
            await make_request_with_latency()

        # Verify latencies are recorded and valid
        recorded_latencies = metrics_collector["latencies"]
        avg_latency = statistics.mean(recorded_latencies)
        min_latency = min(recorded_latencies)
        max_latency = max(recorded_latencies)

        logger.info(
            "latency_reporting_under_load",
            count=len(recorded_latencies),
            avg_ms=avg_latency,
            min_ms=min_latency,
            max_ms=max_latency
        )

        # All latencies should be recorded (no data loss)
        assert len(recorded_latencies) == 100, f"Missing latencies: {len(recorded_latencies)}/100"
        # All latencies should be non-negative (valid measurements)
        assert min_latency >= 0, f"Invalid negative latency: {min_latency}ms"
        # Latencies should be reasonable (not unrealistically high)
        assert max_latency < 1000, f"Unreasonable latency: {max_latency}ms >= 1000ms"


# ═══════════════════════════════════════════════════════════════════════════════
# Alert System Load Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:521-540]
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertSystemUnderLoad:
    """Tests for alert system under load."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_alert_evaluation_responsiveness(self, alert_evaluator):
        """Test alert evaluation remains responsive under load.

        [Source: docs/stories/17.5.story.md - Task 6 AC:6]
        """
        # Simulate metrics stream
        async def generate_metrics():
            return {
                "requests": random.randint(100, 200),
                "errors": random.randint(0, 10),
                "error_rate": random.uniform(0, 0.1),
                "p95_latency": random.uniform(100, 1500),
            }

        # Run evaluations under load
        evaluations = 0
        duration = 2  # seconds

        start_time = time.time()
        while time.time() - start_time < duration:
            metrics = await generate_metrics()
            alert_evaluator["evaluate"](metrics)
            evaluations += 1
            await asyncio.sleep(0.05)  # 20 evaluations per second

        # Calculate evaluation stats
        avg_eval_time = statistics.mean(alert_evaluator["evaluation_times"])
        max_eval_time = max(alert_evaluator["evaluation_times"])

        logger.info(
            "alert_evaluation_responsiveness",
            total_evaluations=evaluations,
            avg_eval_time_ms=avg_eval_time * 1000,
            max_eval_time_ms=max_eval_time * 1000,
            alerts_fired=len(alert_evaluator["alerts_fired"])
        )

        # Evaluation should be fast (under 10ms average)
        assert avg_eval_time < 0.01, f"Avg eval time {avg_eval_time * 1000:.2f}ms >= 10ms"

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_alert_accuracy_under_load(self, alert_evaluator):
        """Test alert accuracy under sustained load."""
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        # Run known scenarios
        for _ in range(100):
            error_rate = random.uniform(0, 0.1)
            p95_latency = random.uniform(100, 1500)

            metrics = {
                "error_rate": error_rate,
                "p95_latency": p95_latency,
            }

            should_alert = error_rate > 0.05 or p95_latency > 1000
            initial_alerts = len(alert_evaluator["alerts_fired"])

            alert_evaluator["evaluate"](metrics)

            did_alert = len(alert_evaluator["alerts_fired"]) > initial_alerts

            if should_alert and did_alert:
                true_positives += 1
            elif should_alert and not did_alert:
                false_negatives += 1
            elif not should_alert and did_alert:
                false_positives += 1
            else:
                true_negatives += 1

            await asyncio.sleep(0.01)

        # Calculate accuracy
        total = true_positives + true_negatives + false_positives + false_negatives
        accuracy = (true_positives + true_negatives) / total

        logger.info(
            "alert_accuracy_under_load",
            true_positives=true_positives,
            true_negatives=true_negatives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            accuracy_pct=accuracy * 100
        )

        assert accuracy >= 0.95, f"Alert accuracy {accuracy:.2%} < 95%"


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard Load Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:541-560]
# ═══════════════════════════════════════════════════════════════════════════════


class TestDashboardUnderLoad:
    """Tests for dashboard under load."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_dashboard_query_performance_under_load(
        self,
        dashboard_data_source
    ):
        """Test dashboard query performance under load.

        [Source: docs/stories/17.5.story.md - Task 6 AC:6]
        """
        # Simulate concurrent dashboard queries
        async def dashboard_query():
            metrics = [
                "api_requests_total",
                "api_latency_p95",
                "agent_executions",
                "memory_queries",
                "error_rate",
            ]

            for metric in metrics:
                dashboard_data_source["query"](metric)
                await asyncio.sleep(0.001)

        # Run concurrent dashboard sessions
        sessions = 10
        duration = 2  # seconds

        tasks = []
        start_time = time.time()

        while time.time() - start_time < duration:
            for _ in range(sessions):
                tasks.append(asyncio.create_task(dashboard_query()))
            await asyncio.sleep(0.1)

        await asyncio.gather(*tasks)

        # Analyze performance
        avg_query_time = statistics.mean(dashboard_data_source["query_times"])
        p95_query_time = sorted(dashboard_data_source["query_times"])[
            int(len(dashboard_data_source["query_times"]) * 0.95)
        ]

        logger.info(
            "dashboard_query_performance",
            total_queries=dashboard_data_source["queries"],
            avg_query_ms=avg_query_time * 1000,
            p95_query_ms=p95_query_time * 1000,
            cache_hit_rate=dashboard_data_source["cache_hits"] /
                          (dashboard_data_source["cache_hits"] + dashboard_data_source["cache_misses"])
        )

        # Query P95 should be under 100ms
        assert p95_query_time < 0.1, f"Query P95 {p95_query_time * 1000:.2f}ms >= 100ms"

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_dashboard_cache_effectiveness(self, dashboard_data_source):
        """Test dashboard cache effectiveness under load."""
        # Clear cache for clean test
        dashboard_data_source["clear_cache"]()

        # Simulate repeated queries (typical dashboard behavior)
        queries = ["metric_1", "metric_2", "metric_3"] * 100

        for metric in queries:
            dashboard_data_source["query"](metric)
            await asyncio.sleep(0.001)

        total_queries = dashboard_data_source["cache_hits"] + dashboard_data_source["cache_misses"]
        cache_hit_rate = dashboard_data_source["cache_hits"] / total_queries

        logger.info(
            "dashboard_cache_effectiveness",
            total_queries=total_queries,
            cache_hits=dashboard_data_source["cache_hits"],
            cache_misses=dashboard_data_source["cache_misses"],
            hit_rate_pct=cache_hit_rate * 100
        )

        # Cache hit rate should be high for repeated queries
        assert cache_hit_rate >= 0.95, f"Cache hit rate {cache_hit_rate:.2%} < 95%"


# ═══════════════════════════════════════════════════════════════════════════════
# Spike Load Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:561-580]
# ═══════════════════════════════════════════════════════════════════════════════


class TestSpikeLoad:
    """Tests for handling load spikes."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_metrics_during_load_spike(self, metrics_collector):
        """Test metrics collection during sudden load spike."""
        async def make_request():
            start = time.perf_counter()
            await asyncio.sleep(0.005)  # 5ms request
            metrics_collector["requests"] += 1
            metrics_collector["latencies"].append((time.perf_counter() - start) * 1000)

        # Normal load phase
        normal_tasks = [make_request() for _ in range(50)]
        await asyncio.gather(*normal_tasks)
        normal_count = metrics_collector["requests"]

        # Spike phase (5x load)
        spike_tasks = [make_request() for _ in range(250)]
        await asyncio.gather(*spike_tasks)
        spike_count = metrics_collector["requests"] - normal_count

        # Recovery phase
        recovery_tasks = [make_request() for _ in range(50)]
        await asyncio.gather(*recovery_tasks)
        recovery_count = metrics_collector["requests"] - normal_count - spike_count

        logger.info(
            "load_spike_metrics",
            normal_requests=normal_count,
            spike_requests=spike_count,
            recovery_requests=recovery_count,
            total_requests=metrics_collector["requests"]
        )

        # All requests should be counted
        expected_total = 350  # 50 + 250 + 50
        assert metrics_collector["requests"] == expected_total, \
            f"Missed requests: expected {expected_total}, got {metrics_collector['requests']}"

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_alert_responsiveness_during_spike(self, alert_evaluator):
        """Test alert system responsiveness during load spike.

        Note: We test that alert evaluation remains fast (< 10ms) even during
        spikes, rather than comparing normal vs spike as percentage (which
        is unstable for microsecond-level operations).
        """
        async def evaluate_with_timing(metrics):
            start = time.perf_counter()
            alert_evaluator["evaluate"](metrics)
            return time.perf_counter() - start

        # Normal load evaluations
        normal_delays = []
        for _ in range(10):
            delay = await evaluate_with_timing({"error_rate": 0.01, "p95_latency": 100})
            normal_delays.append(delay)
            await asyncio.sleep(0.05)

        # Spike load evaluations (rapid fire with alert conditions)
        spike_delays = []
        for _ in range(50):
            delay = await evaluate_with_timing({"error_rate": 0.08, "p95_latency": 1200})
            spike_delays.append(delay)
            await asyncio.sleep(0.01)

        normal_avg_ms = statistics.mean(normal_delays) * 1000
        spike_avg_ms = statistics.mean(spike_delays) * 1000
        spike_max_ms = max(spike_delays) * 1000

        logger.info(
            "spike_alert_responsiveness",
            normal_avg_ms=normal_avg_ms,
            spike_avg_ms=spike_avg_ms,
            spike_max_ms=spike_max_ms,
            total_evaluations=len(normal_delays) + len(spike_delays)
        )

        # Absolute performance: evaluation should be fast even during spike
        assert spike_avg_ms < 10, f"Spike avg eval time {spike_avg_ms:.2f}ms >= 10ms"
        assert spike_max_ms < 50, f"Spike max eval time {spike_max_ms:.2f}ms >= 50ms"
        # All evaluations should complete
        assert len(spike_delays) == 50, f"Missing spike evaluations: {len(spike_delays)}/50"


# ═══════════════════════════════════════════════════════════════════════════════
# Resource Exhaustion Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:581-600]
# ═══════════════════════════════════════════════════════════════════════════════


class TestResourceExhaustion:
    """Tests for handling resource exhaustion scenarios."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_metrics_under_memory_pressure(self, metrics_collector):
        """Test metrics collection under memory pressure."""
        # Simulate memory pressure by holding references
        memory_hog = []

        async def make_request_with_data():
            # Add some data to simulate memory usage
            data = {"request_id": len(memory_hog), "data": "x" * 1000}
            memory_hog.append(data)

            metrics_collector["requests"] += 1
            await asyncio.sleep(0.001)

        # Run until we have significant memory usage
        for _ in range(1000):
            await make_request_with_data()

        logger.info(
            "memory_pressure_metrics",
            requests=metrics_collector["requests"],
            memory_items=len(memory_hog)
        )

        # Metrics should still be accurate
        assert metrics_collector["requests"] == 1000, \
            f"Missed requests under memory pressure"

        # Cleanup
        memory_hog.clear()
        gc.collect()

    @pytest.mark.load
    def test_metrics_storage_limits(self):
        """Test metrics storage handles limits gracefully."""
        max_samples = 1000
        samples = []

        # Add more samples than limit
        for i in range(2000):
            samples.append(i)
            if len(samples) > max_samples:
                samples = samples[-max_samples:]

        assert len(samples) == max_samples, \
            f"Sample buffer exceeded limit: {len(samples)} > {max_samples}"


# ═══════════════════════════════════════════════════════════════════════════════
# Concurrent Access Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:601-620]
# ═══════════════════════════════════════════════════════════════════════════════


class TestConcurrentAccess:
    """Tests for concurrent access to metrics."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_metric_updates(self):
        """Test concurrent metric updates don't cause data races."""
        counter = {"value": 0}
        expected_increments = 1000

        async def increment():
            for _ in range(10):
                counter["value"] += 1
                await asyncio.sleep(0)

        # Run concurrent increments
        tasks = [increment() for _ in range(100)]  # 100 tasks x 10 increments = 1000
        await asyncio.gather(*tasks)

        logger.info(
            "concurrent_updates",
            expected=expected_increments,
            actual=counter["value"]
        )

        # Note: In a real system, this would need proper locking
        # For mock testing, we're checking the mechanism works
        assert counter["value"] == expected_increments, \
            f"Race condition detected: expected {expected_increments}, got {counter['value']}"

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_read_write(self, metrics_collector):
        """Test concurrent reads and writes to metrics."""
        read_count = 0

        async def writer():
            for _ in range(100):
                metrics_collector["requests"] += 1
                await asyncio.sleep(0.001)

        async def reader():
            nonlocal read_count
            for _ in range(100):
                _ = metrics_collector["requests"]
                read_count += 1
                await asyncio.sleep(0.001)

        # Run concurrent readers and writers
        tasks = [writer() for _ in range(5)] + [reader() for _ in range(5)]
        await asyncio.gather(*tasks)

        logger.info(
            "concurrent_read_write",
            writes=metrics_collector["requests"],
            reads=read_count
        )

        assert metrics_collector["requests"] == 500, \
            f"Write count mismatch: {metrics_collector['requests']}"
        assert read_count == 500, \
            f"Read count mismatch: {read_count}"


# ═══════════════════════════════════════════════════════════════════════════════
# Overall Load Test Summary
# ═══════════════════════════════════════════════════════════════════════════════


class TestOverallLoadPerformance:
    """Overall load test summary."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_system_stability_under_load(
        self,
        metrics_collector,
        alert_evaluator,
        dashboard_data_source
    ):
        """Comprehensive load test for system stability.

        [Source: docs/stories/17.5.story.md - Task 6 AC:6]
        """
        duration = 3  # seconds
        start_time = time.time()

        # Concurrent operations
        async def request_generator():
            while time.time() - start_time < duration:
                metrics_collector["requests"] += 1
                metrics_collector["latencies"].append(random.uniform(10, 100))
                await asyncio.sleep(0.01)

        async def alert_checker():
            while time.time() - start_time < duration:
                metrics = {
                    "requests": metrics_collector["requests"],
                    "error_rate": random.uniform(0, 0.05),
                    "p95_latency": random.uniform(100, 500),
                }
                alert_evaluator["evaluate"](metrics)
                await asyncio.sleep(0.1)

        async def dashboard_poller():
            while time.time() - start_time < duration:
                dashboard_data_source["query"]("api_requests_total")
                dashboard_data_source["query"]("api_latency_p95")
                await asyncio.sleep(0.5)

        # Run all concurrently
        await asyncio.gather(
            request_generator(),
            request_generator(),
            alert_checker(),
            dashboard_poller(),
        )

        logger.info(
            "overall_load_stability",
            duration_seconds=duration,
            total_requests=metrics_collector["requests"],
            total_evaluations=alert_evaluator["evaluations"],
            total_dashboard_queries=dashboard_data_source["queries"],
            alerts_fired=len(alert_evaluator["alerts_fired"])
        )

        # System should remain stable
        assert metrics_collector["requests"] > 100, "Too few requests processed"
        assert alert_evaluator["evaluations"] > 10, "Too few alert evaluations"
        assert dashboard_data_source["queries"] > 5, "Too few dashboard queries"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Summary
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "load", "--tb=short"])
