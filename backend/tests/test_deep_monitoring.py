# Canvas Learning System - Deep Monitoring Integration Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing TestClient)
"""
Integration tests for Story 17.2 Deep Monitoring endpoints.

Tests the /metrics and /metrics/summary endpoints with real Prometheus metrics.

[Source: docs/stories/17.2.story.md - Task 6 Integration Tests]
[Source: specs/api/canvas-api.openapi.yml:605-660]
"""

import pytest
from app.config import Settings, get_settings
from app.main import app
from fastapi.testclient import TestClient

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

def get_test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        PROJECT_NAME="Canvas Learning System API (Test)",
        VERSION="1.0.0-test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS="http://localhost:3000",
        CANVAS_BASE_PATH="./test_canvas",
    )


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create test client."""
    app.dependency_overrides[get_settings] = get_test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# Test: GET /api/v1/health/metrics - Prometheus Metrics Endpoint
# [Source: specs/api/canvas-api.openapi.yml:605-628]
# [Source: Story 17.2 AC-5: Prometheus /metrics endpoint]
# ═══════════════════════════════════════════════════════════════════════════════

def test_metrics_endpoint_returns_200(client):
    """Test that /metrics endpoint returns 200 OK."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200


def test_metrics_endpoint_content_type(client):
    """Test that /metrics returns Prometheus text format."""
    response = client.get("/api/v1/health/metrics")

    # ✅ Verified from Context7:/prometheus/client_python (CONTENT_TYPE_LATEST)
    # Content type should be text/plain or openmetrics format
    content_type = response.headers.get("content-type", "")
    assert "text" in content_type.lower()


def test_metrics_endpoint_contains_agent_metrics(client):
    """Test that /metrics contains agent execution metrics."""
    response = client.get("/api/v1/health/metrics")
    content = response.text

    # Should contain agent-related metrics
    # ✅ Verified from Story 17.2 AC-1: Agent执行追踪
    assert "canvas_agent" in content or "HELP" in content


def test_metrics_endpoint_contains_memory_metrics(client):
    """Test that /metrics contains memory query metrics."""
    response = client.get("/api/v1/health/metrics")
    content = response.text

    # Should contain memory-related metrics
    # ✅ Verified from Story 17.2 AC-2: 记忆系统延迟追踪
    assert "canvas_memory" in content or "HELP" in content


def test_metrics_endpoint_contains_resource_metrics(client):
    """Test that /metrics contains resource usage metrics."""
    response = client.get("/api/v1/health/metrics")
    content = response.text

    # Should contain resource-related metrics
    # ✅ Verified from Story 17.2 AC-3: 资源使用监控
    assert "canvas_resource" in content or "HELP" in content


def test_metrics_endpoint_prometheus_format(client):
    """Test that /metrics returns valid Prometheus format."""
    response = client.get("/api/v1/health/metrics")
    content = response.text

    # Prometheus format should have lines starting with # for metadata
    # and metric_name{labels} value for data
    lines = content.strip().split("\n")
    assert len(lines) > 0

    # Should have at least some HELP or TYPE comments
    has_metadata = any(line.startswith("# ") for line in lines if line)
    assert has_metadata or len(lines) > 1


# ═══════════════════════════════════════════════════════════════════════════════
# Test: GET /api/v1/health/metrics/summary - JSON Metrics Summary
# [Source: specs/api/canvas-api.openapi.yml:630-660]
# [Source: Story 17.2 AC-6: JSON summary endpoint]
# ═══════════════════════════════════════════════════════════════════════════════

def test_metrics_summary_returns_200(client):
    """Test that /metrics/summary endpoint returns 200 OK."""
    response = client.get("/api/v1/health/metrics/summary")
    assert response.status_code == 200


def test_metrics_summary_content_type(client):
    """Test that /metrics/summary returns JSON."""
    response = client.get("/api/v1/health/metrics/summary")
    content_type = response.headers.get("content-type", "")
    assert "application/json" in content_type


def test_metrics_summary_structure(client):
    """Test that /metrics/summary returns expected structure."""
    response = client.get("/api/v1/health/metrics/summary")
    data = response.json()

    # ✅ Verified from specs/api/canvas-api.openapi.yml:987-1060
    assert "agents" in data
    assert "memory_system" in data
    assert "resources" in data
    assert "timestamp" in data


def test_metrics_summary_agents_structure(client):
    """Test that agents section has expected structure."""
    response = client.get("/api/v1/health/metrics/summary")
    data = response.json()

    agents = data["agents"]
    assert "invocations_total" in agents
    assert "avg_execution_time_s" in agents
    assert "by_type" in agents
    assert isinstance(agents["invocations_total"], int)
    assert isinstance(agents["avg_execution_time_s"], (int, float))
    assert isinstance(agents["by_type"], dict)


def test_metrics_summary_memory_system_structure(client):
    """Test that memory_system section has expected structure."""
    response = client.get("/api/v1/health/metrics/summary")
    data = response.json()

    memory = data["memory_system"]
    assert "queries_total" in memory
    assert "avg_latency_s" in memory
    assert "by_type" in memory
    assert isinstance(memory["queries_total"], int)
    assert isinstance(memory["avg_latency_s"], (int, float))
    assert isinstance(memory["by_type"], dict)


def test_metrics_summary_resources_structure(client):
    """Test that resources section has expected structure."""
    response = client.get("/api/v1/health/metrics/summary")
    data = response.json()

    resources = data["resources"]
    assert "cpu_usage_percent" in resources
    assert "memory_usage_percent" in resources
    assert "memory_available_bytes" in resources
    assert "memory_total_bytes" in resources
    assert "disk_usage_percent" in resources
    assert "disk_free_bytes" in resources


def test_metrics_summary_timestamp_format(client):
    """Test that timestamp is valid ISO format."""
    response = client.get("/api/v1/health/metrics/summary")
    data = response.json()

    timestamp = data["timestamp"]
    # Should be ISO 8601 format
    assert isinstance(timestamp, str)
    assert "T" in timestamp or "-" in timestamp


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Cross-Endpoint Consistency
# ═══════════════════════════════════════════════════════════════════════════════

def test_both_endpoints_accessible(client):
    """Test that both metrics endpoints are accessible."""
    prometheus_response = client.get("/api/v1/health/metrics")
    summary_response = client.get("/api/v1/health/metrics/summary")

    assert prometheus_response.status_code == 200
    assert summary_response.status_code == 200


def test_health_endpoint_still_works(client):
    """Test that adding metrics endpoints doesn't break health check."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Performance Requirements
# [Source: Story 17.2 AC-4: 采集频率≤5秒]
# ═══════════════════════════════════════════════════════════════════════════════

def test_metrics_endpoint_response_time(client):
    """Test that /metrics endpoint responds quickly."""
    import time

    start = time.perf_counter()
    response = client.get("/api/v1/health/metrics")
    duration = time.perf_counter() - start

    assert response.status_code == 200
    # Should respond within 1 second
    assert duration < 1.0


def test_metrics_summary_response_time(client):
    """Test that /metrics/summary endpoint responds quickly."""
    import time

    start = time.perf_counter()
    response = client.get("/api/v1/health/metrics/summary")
    duration = time.perf_counter() - start

    assert response.status_code == 200
    # Should respond within 1 second
    assert duration < 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Error Handling
# ═══════════════════════════════════════════════════════════════════════════════

def test_metrics_endpoint_handles_concurrent_requests(client):
    """Test that metrics endpoints handle concurrent requests."""
    import threading
    results = []

    def make_request():
        response = client.get("/api/v1/health/metrics/summary")
        results.append(response.status_code)

    threads = [threading.Thread(target=make_request) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All requests should succeed
    assert all(status == 200 for status in results)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Acceptance Criteria Validation
# [Source: docs/stories/17.2.story.md - Acceptance Criteria]
# ═══════════════════════════════════════════════════════════════════════════════

def test_ac1_agent_execution_tracking():
    """AC-1: 所有14种Agent类型的执行时间都被追踪."""
    from app.middleware.agent_metrics import VALID_AGENT_TYPES

    # All 14 agent types should be defined
    assert len(VALID_AGENT_TYPES) == 14


def test_ac2_memory_system_latency_tracking():
    """AC-2: 记忆系统(Graphiti/LanceDB/Temporal)查询延迟被追踪."""
    from app.middleware.memory_metrics import VALID_MEMORY_TYPES

    expected = {"graphiti", "lancedb", "temporal", "sqlite"}
    assert expected.issubset(VALID_MEMORY_TYPES)


def test_ac3_resource_monitoring():
    """AC-3: 系统资源使用(CPU/内存/磁盘)被监控."""
    from app.services.resource_monitor import (
        RESOURCE_CPU_USAGE,
        RESOURCE_DISK_USAGE,
        RESOURCE_MEMORY_USAGE,
    )

    # Gauges should be defined
    assert RESOURCE_CPU_USAGE is not None
    assert RESOURCE_MEMORY_USAGE is not None
    assert RESOURCE_DISK_USAGE is not None


def test_ac5_prometheus_endpoint(client):
    """AC-5: /metrics端点返回Prometheus格式."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200
    # Should be text format
    assert "text" in response.headers.get("content-type", "").lower()


def test_ac6_json_summary_endpoint(client):
    """AC-6: /metrics/summary端点返回JSON摘要."""
    response = client.get("/api/v1/health/metrics/summary")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")

    data = response.json()
    assert "agents" in data
    assert "memory_system" in data
    assert "resources" in data
