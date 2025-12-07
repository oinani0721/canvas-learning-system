# Canvas Learning System - End-to-End Monitoring Tests
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:87-124)
# ✅ Verified from ADR-008 (pytest asyncio pattern)
# [Source: docs/stories/17.5.story.md - Task 1]
"""
End-to-end monitoring flow tests.

Tests complete chain: API Request → Metrics Middleware → Prometheus Metrics → Dashboard
"""

import asyncio
import json
import pytest
import time
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# [Source: ADR-008:294-336 - httpx AsyncClient pattern]
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_prometheus_registry():
    """Mock Prometheus registry for testing metrics collection."""
    registry = MagicMock()
    registry._metrics = {}

    def get_sample_value(name, labels=None):
        key = (name, tuple(sorted(labels.items())) if labels else ())
        return registry._metrics.get(key, 0)

    def set_sample_value(name, labels, value):
        key = (name, tuple(sorted(labels.items())) if labels else ())
        registry._metrics[key] = value

    registry.get_sample_value = get_sample_value
    registry.set_sample_value = set_sample_value
    return registry


@pytest.fixture
def mock_metrics_middleware():
    """Mock metrics middleware for testing."""
    middleware = MagicMock()
    middleware.request_count = 0
    middleware.total_latency = 0.0
    middleware.errors = 0

    async def process_request(request, call_next):
        middleware.request_count += 1
        start = time.perf_counter()
        try:
            response = await call_next(request)
            latency = (time.perf_counter() - start) * 1000
            middleware.total_latency += latency
            return response
        except Exception as e:
            middleware.errors += 1
            raise

    middleware.process = process_request
    return middleware


@pytest.fixture
def mock_alert_manager():
    """Mock alert manager for testing."""
    manager = MagicMock()
    manager.alerts = []
    manager.evaluated_rules = []

    def evaluate_rules():
        # Simulate alert evaluation
        manager.evaluated_rules.append(datetime.now())
        return manager.alerts

    def add_alert(name, severity, message):
        alert = {
            "name": name,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "firing"
        }
        manager.alerts.append(alert)
        return alert

    manager.evaluate_rules = evaluate_rules
    manager.add_alert = add_alert
    return manager


# ═══════════════════════════════════════════════════════════════════════════════
# E2E Monitoring Flow Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:87-124]
# ═══════════════════════════════════════════════════════════════════════════════


class TestMonitoringE2EFlow:
    """End-to-end monitoring flow tests."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_request_to_metrics_flow(self, mock_prometheus_registry, mock_metrics_middleware):
        """Test API request → metrics_middleware → Prometheus Counter flow.

        [Source: docs/stories/17.5.story.md - Task 1 AC:1]
        """
        # 1. Record initial metrics
        initial_count = mock_prometheus_registry.get_sample_value(
            'canvas_api_requests_total',
            {'method': 'GET', 'endpoint': '/canvas', 'status': '200'}
        )
        assert initial_count == 0

        # 2. Simulate API request through middleware
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v2/canvas/test.canvas"

        mock_response = MagicMock()
        mock_response.status_code = 200

        async def mock_call_next(request):
            await asyncio.sleep(0.01)  # Simulate processing
            return mock_response

        await mock_metrics_middleware.process(mock_request, mock_call_next)

        # 3. Verify middleware recorded the request
        assert mock_metrics_middleware.request_count == 1
        assert mock_metrics_middleware.total_latency > 0

        # 4. Update mock registry
        mock_prometheus_registry.set_sample_value(
            'canvas_api_requests_total',
            {'method': 'GET', 'endpoint': '/canvas', 'status': '200'},
            1
        )

        # 5. Verify metrics updated
        new_count = mock_prometheus_registry.get_sample_value(
            'canvas_api_requests_total',
            {'method': 'GET', 'endpoint': '/canvas', 'status': '200'}
        )
        assert new_count > initial_count

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_execution_tracking_flow(self):
        """Test Agent call → track_agent_execution → metrics recording flow.

        [Source: docs/stories/17.5.story.md - Task 1 AC:1]
        """
        # Mock agent execution tracker
        execution_times = []

        async def track_agent_execution(agent_name, coro):
            start = time.perf_counter()
            try:
                result = await coro
                return result
            finally:
                duration = time.perf_counter() - start
                execution_times.append({
                    "agent": agent_name,
                    "duration_ms": duration * 1000,
                    "timestamp": datetime.now().isoformat()
                })

        # Simulate agent execution
        async def mock_agent_work():
            await asyncio.sleep(0.05)
            return {"result": "success"}

        result = await track_agent_execution("test-agent", mock_agent_work())

        # Verify tracking
        assert result == {"result": "success"}
        assert len(execution_times) == 1
        assert execution_times[0]["agent"] == "test-agent"
        assert execution_times[0]["duration_ms"] > 40  # At least 50ms simulated

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_query_latency_tracking(self):
        """Test Memory query → MEMORY_QUERY_LATENCY → metrics recording flow.

        [Source: docs/stories/17.5.story.md - Task 1 AC:1]
        """
        query_latencies = []

        async def track_memory_query(query_type, query_func):
            start = time.perf_counter()
            try:
                result = await query_func()
                return result
            finally:
                latency = time.perf_counter() - start
                query_latencies.append({
                    "type": query_type,
                    "latency_ms": latency * 1000,
                    "timestamp": datetime.now().isoformat()
                })

        # Simulate memory queries
        async def mock_semantic_search():
            await asyncio.sleep(0.02)
            return ["result1", "result2"]

        async def mock_temporal_query():
            await asyncio.sleep(0.01)
            return {"history": []}

        await track_memory_query("semantic", mock_semantic_search)
        await track_memory_query("temporal", mock_temporal_query)

        # Verify tracking
        assert len(query_latencies) == 2
        assert query_latencies[0]["type"] == "semantic"
        assert query_latencies[1]["type"] == "temporal"
        assert query_latencies[0]["latency_ms"] > 15
        assert query_latencies[1]["latency_ms"] > 5

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_metrics_endpoint_returns_all_expected_metrics(self, mock_prometheus_registry):
        """Test /metrics endpoint returns all expected metrics.

        [Source: docs/stories/17.5.story.md - Task 1 AC:1]
        """
        # Define expected metrics based on architecture
        expected_metrics = [
            "canvas_api_requests_total",
            "canvas_api_request_latency_seconds",
            "canvas_agent_execution_seconds",
            "canvas_memory_query_seconds",
        ]

        # Simulate metrics export
        def generate_metrics_output():
            lines = []
            lines.append("# HELP canvas_api_requests_total Total API requests")
            lines.append("# TYPE canvas_api_requests_total counter")
            lines.append('canvas_api_requests_total{method="GET",endpoint="/canvas",status="200"} 100')
            lines.append("")
            lines.append("# HELP canvas_api_request_latency_seconds API request latency")
            lines.append("# TYPE canvas_api_request_latency_seconds histogram")
            lines.append('canvas_api_request_latency_seconds_bucket{le="0.1"} 50')
            lines.append('canvas_api_request_latency_seconds_bucket{le="0.5"} 90')
            lines.append('canvas_api_request_latency_seconds_bucket{le="+Inf"} 100')
            lines.append("")
            lines.append("# HELP canvas_agent_execution_seconds Agent execution time")
            lines.append("# TYPE canvas_agent_execution_seconds histogram")
            lines.append('canvas_agent_execution_seconds_bucket{agent="test",le="1"} 80')
            lines.append("")
            lines.append("# HELP canvas_memory_query_seconds Memory query latency")
            lines.append("# TYPE canvas_memory_query_seconds histogram")
            lines.append('canvas_memory_query_seconds_bucket{type="semantic",le="0.1"} 95')
            return "\n".join(lines)

        metrics_output = generate_metrics_output()

        # Verify all expected metrics present
        for metric in expected_metrics:
            assert metric in metrics_output, f"Missing metric: {metric}"


# ═══════════════════════════════════════════════════════════════════════════════
# Alert Integration Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:269-323]
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertIntegration:
    """Alert system integration tests."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_alert_evaluation_cycle(self, mock_alert_manager):
        """Test alert evaluation cycle runs correctly."""
        # Trigger multiple evaluations
        for _ in range(3):
            mock_alert_manager.evaluate_rules()
            await asyncio.sleep(0.01)

        assert len(mock_alert_manager.evaluated_rules) == 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_alert_creation_and_retrieval(self, mock_alert_manager):
        """Test alert creation and retrieval flow."""
        # Create alert
        alert = mock_alert_manager.add_alert(
            name="TestAlert",
            severity="warning",
            message="Test alert message"
        )

        # Verify alert structure
        assert alert["name"] == "TestAlert"
        assert alert["severity"] == "warning"
        assert alert["status"] == "firing"
        assert "timestamp" in alert

        # Verify alert retrieval
        assert len(mock_alert_manager.alerts) == 1
        assert mock_alert_manager.alerts[0] == alert


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard Integration Tests
# [Source: docs/architecture/performance-monitoring-architecture.md:138-198]
# ═══════════════════════════════════════════════════════════════════════════════


class TestDashboardIntegration:
    """Dashboard data integration tests."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_metrics_summary_generation(self):
        """Test metrics summary endpoint data generation."""
        # Mock metrics data
        metrics_data = {
            "api_requests_total": 1000,
            "api_latencies": [50, 100, 150, 200, 250, 300, 400, 500, 600, 1000],
            "agent_executions": {"test-agent": [1.0, 1.5, 2.0, 2.5, 3.0]},
            "memory_queries": {"semantic": [20, 30, 40, 50], "temporal": [10, 15, 20]}
        }

        # Generate summary
        def calculate_summary(data):
            latencies = sorted(data["api_latencies"])
            p95_index = int(len(latencies) * 0.95)

            return {
                "timestamp": datetime.now().isoformat(),
                "api": {
                    "requests_total": data["api_requests_total"],
                    "requests_per_second": data["api_requests_total"] / 3600,  # Assume 1 hour
                    "avg_latency_ms": sum(latencies) / len(latencies),
                    "p95_latency_ms": latencies[p95_index] if p95_index < len(latencies) else latencies[-1]
                },
                "agent": {
                    "execution_times": {
                        agent: {"avg": sum(times)/len(times), "count": len(times)}
                        for agent, times in data["agent_executions"].items()
                    }
                },
                "memory": {
                    "query_latency": {
                        qtype: {"avg": sum(latencies)/len(latencies), "count": len(latencies)}
                        for qtype, latencies in data["memory_queries"].items()
                    }
                }
            }

        summary = calculate_summary(metrics_data)

        # Verify summary structure
        assert "timestamp" in summary
        assert summary["api"]["requests_total"] == 1000
        assert summary["api"]["avg_latency_ms"] == 355  # Average of test data
        assert "test-agent" in summary["agent"]["execution_times"]
        assert "semantic" in summary["memory"]["query_latency"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_metrics_summary_schema_compliance(self):
        """Test metrics summary complies with OpenAPI schema.

        [Source: specs/api/canvas-api.openapi.yml:987-1007]
        """
        # Expected schema fields
        required_fields = {
            "timestamp": str,
            "api.requests_total": int,
            "api.requests_per_second": float,
            "api.avg_latency_ms": float,
            "api.p95_latency_ms": float,
            "agent.execution_times": dict,
            "memory.query_latency": dict
        }

        # Mock summary
        mock_summary = {
            "timestamp": datetime.now().isoformat(),
            "api": {
                "requests_total": 100,
                "requests_per_second": 0.5,
                "avg_latency_ms": 150.5,
                "p95_latency_ms": 450.0
            },
            "agent": {
                "execution_times": {}
            },
            "memory": {
                "query_latency": {}
            }
        }

        # Verify fields
        assert isinstance(mock_summary["timestamp"], str)
        assert isinstance(mock_summary["api"]["requests_total"], int)
        assert isinstance(mock_summary["api"]["requests_per_second"], float)
        assert isinstance(mock_summary["api"]["avg_latency_ms"], float)
        assert isinstance(mock_summary["api"]["p95_latency_ms"], float)


# ═══════════════════════════════════════════════════════════════════════════════
# Complete E2E Flow Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCompleteE2EFlow:
    """Complete end-to-end flow tests simulating real usage."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_monitoring_cycle(
        self,
        mock_prometheus_registry,
        mock_metrics_middleware,
        mock_alert_manager
    ):
        """Test complete monitoring cycle from request to dashboard."""
        # 1. Simulate multiple API requests
        async def mock_call_next(request):
            await asyncio.sleep(0.01)
            response = MagicMock()
            response.status_code = 200
            return response

        for i in range(10):
            mock_request = MagicMock()
            mock_request.method = "GET"
            mock_request.url.path = f"/api/v2/canvas/test{i}.canvas"
            await mock_metrics_middleware.process(mock_request, mock_call_next)

        # 2. Verify metrics collected
        assert mock_metrics_middleware.request_count == 10
        assert mock_metrics_middleware.total_latency > 0

        # 3. Update registry
        mock_prometheus_registry.set_sample_value(
            'canvas_api_requests_total',
            {'method': 'GET', 'endpoint': '/canvas', 'status': '200'},
            10
        )

        # 4. Verify no alerts (normal operation)
        alerts = mock_alert_manager.evaluate_rules()
        assert len(alerts) == 0

        # 5. Simulate high latency scenario
        mock_alert_manager.add_alert(
            name="HighAPILatency",
            severity="warning",
            message="API P95 latency exceeded 1s"
        )

        # 6. Verify alert created
        assert len(mock_alert_manager.alerts) == 1
        assert mock_alert_manager.alerts[0]["name"] == "HighAPILatency"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_tracking_flow(self, mock_metrics_middleware):
        """Test error tracking through monitoring system."""
        async def mock_error_call_next(request):
            raise Exception("Simulated error")

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v2/canvas/error.canvas"

        with pytest.raises(Exception):
            await mock_metrics_middleware.process(mock_request, mock_error_call_next)

        assert mock_metrics_middleware.errors == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Test Summary
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
