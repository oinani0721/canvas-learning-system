# Canvas Learning System - Health Check Endpoint Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Tests for the health check endpoint.

These tests verify that the health check endpoint returns correct data
and adheres to the API specification.

[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]
[Source: specs/data/health-check-response.schema.json]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

from datetime import datetime

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for GET /api/v1/health endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """
        Test that health check returns HTTP 200 OK.

        [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1health]
        """
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client: TestClient):
        """
        Test that health check response has correct structure.

        [Source: specs/data/health-check-response.schema.json]
        Schema requires: status, app_name, version, timestamp
        """
        response = client.get("/api/v1/health")
        data = response.json()

        # Verify all required fields are present
        assert "status" in data
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data

    def test_health_check_status_is_healthy(self, client: TestClient):
        """
        Test that health check returns "healthy" status.

        [Source: specs/data/health-check-response.schema.json]
        status enum: ["healthy", "unhealthy"]
        """
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_app_name(self, client: TestClient):
        """
        Test that health check returns correct app name.
        """
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["app_name"] == "Canvas Learning System API (Test)"

    def test_health_check_version(self, client: TestClient):
        """
        Test that health check returns valid version string.
        """
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["version"] == "1.0.0-test"

    def test_health_check_timestamp_format(self, client: TestClient):
        """
        Test that health check returns valid ISO 8601 timestamp.

        [Source: specs/data/health-check-response.schema.json]
        timestamp format: date-time (ISO 8601)
        """
        response = client.get("/api/v1/health")
        data = response.json()

        # Verify timestamp can be parsed as ISO 8601
        timestamp_str = data["timestamp"]
        # FastAPI serializes datetime as ISO format
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert parsed is not None

    def test_health_check_content_type(self, client: TestClient):
        """
        Test that health check returns JSON content type.
        """
        response = client.get("/api/v1/health")
        assert response.headers["content-type"] == "application/json"


class TestRootEndpoint:
    """Test suite for GET / root endpoint."""

    def test_root_returns_200(self, client: TestClient):
        """Test that root endpoint returns HTTP 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_structure(self, client: TestClient):
        """Test that root response has correct structure."""
        response = client.get("/")
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_root_message(self, client: TestClient):
        """Test that root returns correct message."""
        response = client.get("/")
        data = response.json()

        assert data["message"] == "Canvas Learning System API"

    def test_root_docs_status(self, client: TestClient):
        """
        Test that docs status is correctly reported.

        Note: The root endpoint uses the global settings object directly,
        which is loaded at module import time. Default DEBUG=False.
        """
        response = client.get("/")
        data = response.json()

        # Global settings has DEBUG=False by default
        # docs is either "/docs" or "disabled" depending on DEBUG setting
        assert data["docs"] in ["/docs", "disabled"]

    def test_root_health_path(self, client: TestClient):
        """Test that root returns correct health endpoint path."""
        response = client.get("/")
        data = response.json()

        assert data["health"] == "/api/v1/health"


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Endpoint Tests (Story 17.2)
# [Source: specs/api/canvas-api.openapi.yml:605-642]
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetricsEndpoint:
    """Test suite for GET /api/v1/health/metrics endpoint (Prometheus format)."""

    def test_metrics_returns_200(self, client: TestClient):
        """
        Test that metrics endpoint returns HTTP 200 OK.

        [Source: Story 17.2 AC-5]
        """
        response = client.get("/api/v1/health/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client: TestClient):
        """
        Test that metrics endpoint returns Prometheus text format.

        ✅ Verified from Context7:/prometheus/client_python (topic: CONTENT_TYPE_LATEST)
        """
        response = client.get("/api/v1/health/metrics")
        content_type = response.headers["content-type"]
        # Prometheus text format starts with "text/plain" or "text/plain; version=..."
        assert content_type.startswith("text/plain")

    def test_metrics_contains_agent_metrics(self, client: TestClient):
        """
        Test that metrics output contains agent metrics.

        [Source: Story 17.2 AC-1, AC-2]
        """
        response = client.get("/api/v1/health/metrics")
        content = response.text

        # Should contain agent-related metrics
        assert "canvas_agent" in content or "agent" in content.lower()

    def test_metrics_contains_memory_metrics(self, client: TestClient):
        """
        Test that metrics output contains memory system metrics.

        [Source: Story 17.2 AC-3]
        """
        response = client.get("/api/v1/health/metrics")
        content = response.text

        # Should contain memory-related metrics
        assert "canvas_memory" in content or "memory" in content.lower()

    def test_metrics_contains_resource_metrics(self, client: TestClient):
        """
        Test that metrics output contains resource metrics.

        [Source: Story 17.2 AC-4]
        """
        response = client.get("/api/v1/health/metrics")
        content = response.text

        # Should contain resource-related metrics (cpu, memory usage, disk)
        assert "canvas_resource" in content or "resource" in content.lower()


class TestMetricsSummaryEndpoint:
    """Test suite for GET /api/v1/health/metrics/summary endpoint (JSON format)."""

    def test_metrics_summary_returns_200(self, client: TestClient):
        """
        Test that metrics summary endpoint returns HTTP 200 OK.

        [Source: Story 17.2 AC-6]
        """
        response = client.get("/api/v1/health/metrics/summary")
        assert response.status_code == 200

    def test_metrics_summary_content_type(self, client: TestClient):
        """Test that metrics summary returns JSON content type."""
        response = client.get("/api/v1/health/metrics/summary")
        assert response.headers["content-type"] == "application/json"

    def test_metrics_summary_structure(self, client: TestClient):
        """
        Test that metrics summary has correct top-level structure.

        [Source: specs/api/canvas-api.openapi.yml:987-1060]
        """
        response = client.get("/api/v1/health/metrics/summary")
        data = response.json()

        assert "agents" in data
        assert "memory_system" in data
        assert "resources" in data
        assert "timestamp" in data

    def test_metrics_summary_agents_structure(self, client: TestClient):
        """
        Test that agents section has correct structure.

        [Source: Story 17.2 AC-1, AC-2]
        """
        response = client.get("/api/v1/health/metrics/summary")
        data = response.json()

        agents = data["agents"]
        assert "invocations_total" in agents
        assert "avg_execution_time_s" in agents
        assert "by_type" in agents
        assert isinstance(agents["invocations_total"], int)
        assert isinstance(agents["avg_execution_time_s"], (int, float))
        assert isinstance(agents["by_type"], dict)

    def test_metrics_summary_memory_system_structure(self, client: TestClient):
        """
        Test that memory_system section has correct structure.

        [Source: Story 17.2 AC-3]
        """
        response = client.get("/api/v1/health/metrics/summary")
        data = response.json()

        memory = data["memory_system"]
        assert "queries_total" in memory
        assert "avg_latency_s" in memory
        assert "by_type" in memory
        assert isinstance(memory["queries_total"], int)
        assert isinstance(memory["avg_latency_s"], (int, float))
        assert isinstance(memory["by_type"], dict)

    def test_metrics_summary_resources_structure(self, client: TestClient):
        """
        Test that resources section has correct structure.

        [Source: Story 17.2 AC-4]
        """
        response = client.get("/api/v1/health/metrics/summary")
        data = response.json()

        resources = data["resources"]
        assert "cpu_usage_percent" in resources
        assert "memory_usage_percent" in resources
        assert "memory_available_bytes" in resources
        assert "memory_total_bytes" in resources
        assert "disk_usage_percent" in resources
        assert "disk_free_bytes" in resources

    def test_metrics_summary_resources_values_valid(self, client: TestClient):
        """Test that resource values are within valid ranges."""
        response = client.get("/api/v1/health/metrics/summary")
        data = response.json()

        resources = data["resources"]
        # CPU and memory percentages should be 0-100
        assert 0 <= resources["cpu_usage_percent"] <= 100
        assert 0 <= resources["memory_usage_percent"] <= 100
        assert 0 <= resources["disk_usage_percent"] <= 100
        # Bytes should be non-negative
        assert resources["memory_available_bytes"] >= 0
        assert resources["memory_total_bytes"] >= 0
        assert resources["disk_free_bytes"] >= 0

    def test_metrics_summary_timestamp_format(self, client: TestClient):
        """Test that timestamp is valid ISO 8601 format."""
        response = client.get("/api/v1/health/metrics/summary")
        data = response.json()

        timestamp_str = data["timestamp"]
        # Should be parseable as ISO 8601
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert parsed is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Story 21.5.4: Agent Health Check Endpoints Tests
# [Source: docs/stories/21.5.4.story.md]
# [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-4]
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentsHealthEndpoint:
    """Test suite for GET /api/v1/health/agents endpoint.

    [Source: docs/stories/21.5.4.story.md#AC-21.5.4.1]
    """

    def test_health_agents_returns_200(self, client: TestClient):
        """
        Test that /health/agents endpoint returns HTTP 200 OK.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.1]
        """
        response = client.get("/api/v1/health/agents")
        assert response.status_code == 200

    def test_health_agents_response_structure(self, client: TestClient):
        """
        Test that /health/agents response has correct structure.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.1]
        """
        response = client.get("/api/v1/health/agents")
        data = response.json()

        # Verify all required fields are present
        assert "status" in data
        assert "agents" in data
        assert "total_agents" in data
        assert "available_count" in data

    def test_health_agents_status_is_ok(self, client: TestClient):
        """
        Test that /health/agents returns "ok" status.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.1]
        """
        response = client.get("/api/v1/health/agents")
        data = response.json()

        assert data["status"] == "ok"

    def test_health_agents_returns_all_endpoints(self, client: TestClient):
        """
        Test that /health/agents returns all Agent endpoint statuses.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.1]
        """
        response = client.get("/api/v1/health/agents")
        data = response.json()

        # Should have at least 10 agents (per Story requirement)
        assert data["total_agents"] >= 10
        assert len(data["agents"]) >= 10

        # Check that expected agents are present
        expected_agents = [
            "decompose_basic",
            "decompose_deep",
            "explain_oral",
            "scoring",
            "verification",
        ]
        for agent in expected_agents:
            assert agent in data["agents"], f"Agent {agent} not found"

    def test_health_agents_all_available(self, client: TestClient):
        """
        Test that all agents are marked as available.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.1]
        """
        response = client.get("/api/v1/health/agents")
        data = response.json()

        # All agents should be "available"
        for agent_name, status in data["agents"].items():
            assert status == "available", f"Agent {agent_name} is not available"

        # available_count should match total_agents
        assert data["available_count"] == data["total_agents"]

    def test_health_agents_content_type(self, client: TestClient):
        """Test that /health/agents returns JSON content type."""
        response = client.get("/api/v1/health/agents")
        assert response.headers["content-type"] == "application/json"


class TestAIHealthEndpoint:
    """Test suite for GET /api/v1/health/ai endpoint.

    [Source: docs/stories/21.5.4.story.md#AC-21.5.4.2]
    """

    def test_health_ai_returns_valid_status(self, client: TestClient):
        """
        Test that /health/ai endpoint returns valid HTTP status.

        Returns 200 if AI configured, 503 if not configured.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.2]
        """
        response = client.get("/api/v1/health/ai")
        # 200 = AI working, 503 = AI not configured (valid in test environment)
        assert response.status_code in [200, 503]

    def test_health_ai_response_structure(self, client: TestClient):
        """
        Test that /health/ai response has required fields.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.2]
        """
        response = client.get("/api/v1/health/ai")
        data = response.json()

        # Must have status field
        assert "status" in data
        assert data["status"] in ["ok", "error"]

        # Must have model and provider info
        assert "model" in data
        assert "provider" in data

    def test_health_ai_error_has_error_field(self, client: TestClient):
        """
        Test that /health/ai error response includes error details.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.2]
        Note: In test environment without API key, status will be "error"
        """
        response = client.get("/api/v1/health/ai")
        data = response.json()

        # In test environment, API is not configured
        if data["status"] == "error":
            assert "error" in data
            # Error code should be present for categorization
            assert "error_code" in data

    def test_health_ai_content_type(self, client: TestClient):
        """Test that /health/ai returns JSON content type."""
        response = client.get("/api/v1/health/ai")
        assert response.headers["content-type"] == "application/json"


class TestFullHealthEndpoint:
    """Test suite for GET /api/v1/health/full endpoint.

    [Source: docs/stories/21.5.4.story.md#AC-21.5.4.3]
    """

    def test_health_full_returns_200(self, client: TestClient):
        """
        Test that /health/full endpoint returns HTTP 200 OK.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.3]
        """
        response = client.get("/api/v1/health/full")
        assert response.status_code == 200

    def test_health_full_response_structure(self, client: TestClient):
        """
        Test that /health/full response has correct structure.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.3, AC-21.5.4.4]
        """
        response = client.get("/api/v1/health/full")
        data = response.json()

        # Verify all required top-level fields
        assert "status" in data
        assert "components" in data
        assert "config" in data
        assert "timestamp" in data

    def test_health_full_status_value(self, client: TestClient):
        """
        Test that /health/full returns valid status.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.3]
        """
        response = client.get("/api/v1/health/full")
        data = response.json()

        # Status should be "ok" or "degraded"
        assert data["status"] in ["ok", "degraded"]

    def test_health_full_components_structure(self, client: TestClient):
        """
        Test that /health/full components section has correct structure.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.3, AC-21.5.4.4]
        """
        response = client.get("/api/v1/health/full")
        data = response.json()

        components = data["components"]
        # Should have all service components
        assert "api" in components
        assert "ai_provider" in components
        assert "canvas_service" in components

        # api and canvas_service should be "ok"
        assert components["api"] == "ok"
        assert components["canvas_service"] == "ok"

        # ai_provider should be a dict with status
        assert isinstance(components["ai_provider"], dict)
        assert "status" in components["ai_provider"]

    def test_health_full_config_structure(self, client: TestClient):
        """
        Test that /health/full config section has correct structure.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.3]
        """
        response = client.get("/api/v1/health/full")
        data = response.json()

        config = data["config"]
        # Should have AI configuration info
        assert "ai_model" in config
        assert "ai_provider" in config
        assert "cors_origins" in config

        # cors_origins should be a list
        assert isinstance(config["cors_origins"], list)

    def test_health_full_timestamp_format(self, client: TestClient):
        """
        Test that /health/full returns valid ISO 8601 timestamp.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.3]
        """
        response = client.get("/api/v1/health/full")
        data = response.json()

        timestamp_str = data["timestamp"]
        # Should be parseable as ISO 8601
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert parsed is not None

    def test_health_full_content_type(self, client: TestClient):
        """Test that /health/full returns JSON content type."""
        response = client.get("/api/v1/health/full")
        assert response.headers["content-type"] == "application/json"


class TestHealthEndpointsPerformance:
    """Test suite for health endpoints performance requirements.

    [Source: docs/stories/21.5.4.story.md#AC-21.5.4.5 (NFR-3)]
    """

    def test_health_agents_response_time(self, client: TestClient):
        """
        Test that /health/agents responds within 500ms.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.5 (NFR-3)]
        """
        import time

        start = time.time()
        response = client.get("/api/v1/health/agents")
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 500, f"Response time {elapsed_ms:.2f}ms exceeds 500ms limit"

    def test_health_ai_response_time(self, client: TestClient):
        """
        Test that /health/ai responds within 500ms (without network call).

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.5 (NFR-3)]
        Note: In test env without API key, returns 503 fast path
        """
        import time

        start = time.time()
        response = client.get("/api/v1/health/ai")
        elapsed_ms = (time.time() - start) * 1000

        # 200 = AI working, 503 = AI not configured (both valid)
        assert response.status_code in [200, 503]
        # In test environment (no API call), should be very fast
        assert elapsed_ms < 500, f"Response time {elapsed_ms:.2f}ms exceeds 500ms limit"

    def test_health_full_response_time(self, client: TestClient):
        """
        Test that /health/full responds within 500ms.

        [Source: docs/stories/21.5.4.story.md#AC-21.5.4.5 (NFR-3)]
        """
        import time

        start = time.time()
        response = client.get("/api/v1/health/full")
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 500, f"Response time {elapsed_ms:.2f}ms exceeds 500ms limit"
