# Canvas Learning System - Story 12.G.3 Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Story 12.G.3 - Agent Health Check Endpoint Tests

Tests for GET /api/v1/agents/health endpoint:
- AC1: Returns health status (healthy/degraded/unhealthy)
- AC2: Checks API key configuration (without exposing key)
- AC3: Checks GeminiClient initialization
- AC4: Checks prompt template availability
- AC5: Optional API call test (include_api_test=true)
- AC6: 60-second TTL cache (ADR-007)
- AC7: Response matches JSON Schema

[Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#Testing]
[Source: specs/data/health-check-response.schema.json]
"""

import time
from datetime import datetime, timezone

import pytest
from app.api.v1.endpoints.agents import (
    HEALTH_CHECK_CACHE_TTL,
    get_agent_health,
)
from app.models import (
    AgentHealthCheckResponse,
    AgentHealthChecks,
    AgentHealthStatus,
    PromptTemplateCheck,
)


class MockAgentService:
    """Mock AgentService for testing Story 12.G.3."""

    def __init__(
        self,
        api_key_configured: bool = True,
        gemini_initialized: bool = True,
        missing_templates: list[str] | None = None,
        api_test_success: bool = True,
    ):
        """
        Initialize mock service.

        Args:
            api_key_configured: Whether API key is configured
            gemini_initialized: Whether GeminiClient is initialized
            missing_templates: List of missing template names
            api_test_success: Whether API test should succeed
        """
        self.api_key_configured = api_key_configured
        self.gemini_initialized = gemini_initialized
        self.missing_templates = missing_templates or []
        self.api_test_success = api_test_success
        self.health_check_call_count = 0

    async def health_check(self, include_api_test: bool = False) -> dict:
        """Mock health_check method."""
        self.health_check_call_count += 1

        expected_templates = [
            "basic-decomposition",
            "deep-decomposition",
            "question-decomposition",
            "oral-explanation",
            "four-level-explanation",
            "clarification-path",
            "comparison-table",
            "example-teaching",
            "memory-anchor",
            "scoring-agent",
            "verification-question-agent",
            "canvas-orchestrator",
        ]

        available_count = len(expected_templates) - len(self.missing_templates)

        # Determine status
        if not self.api_key_configured or not self.gemini_initialized:
            status = "unhealthy"
        elif len(self.missing_templates) > 0:
            status = "degraded"
        else:
            status = "healthy"

        api_test_result = {"enabled": False, "result": None}
        if include_api_test:
            if self.api_test_success:
                api_test_result = {"enabled": True, "result": "success"}
            else:
                api_test_result = {"enabled": True, "result": "API Error"}

        return {
            "status": status,
            "checks": {
                "api_key_configured": self.api_key_configured,
                "gemini_client_initialized": self.gemini_initialized,
                "prompt_templates": {
                    "total": len(expected_templates),
                    "available": available_count,
                    "missing": self.missing_templates,
                },
                "api_test": api_test_result,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AC1: Health Status Tests
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_healthy_status():
    """
    AC1.1: Returns 'healthy' when all checks pass.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.1]
    """
    # Clear cache to ensure fresh check
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        missing_templates=[],
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.healthy
    assert response.checks.api_key_configured is True
    assert response.checks.gemini_client_initialized is True
    assert response.checks.prompt_templates.total == 12
    assert response.checks.prompt_templates.available == 12
    assert response.checks.prompt_templates.missing == []
    assert response.cached is False


@pytest.mark.asyncio
async def test_health_check_degraded_status():
    """
    AC1.2: Returns 'degraded' when some templates are missing.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.2]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        missing_templates=["comparison-table", "review-board"],
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.degraded
    assert response.checks.prompt_templates.missing == ["comparison-table", "review-board"]
    assert response.checks.prompt_templates.available == 10


@pytest.mark.asyncio
async def test_health_check_unhealthy_no_api_key():
    """
    AC1.3: Returns 'unhealthy' when API key is not configured.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.3]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=False,
        gemini_initialized=True,
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.unhealthy
    assert response.checks.api_key_configured is False


@pytest.mark.asyncio
async def test_health_check_unhealthy_no_client():
    """
    AC1.4: Returns 'unhealthy' when GeminiClient is not initialized.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-1.4]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=False,
    )

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.status == AgentHealthStatus.unhealthy
    assert response.checks.gemini_client_initialized is False


# ═══════════════════════════════════════════════════════════════════════════════
# AC5: Optional API Test
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_with_api_test_success():
    """
    AC5.1: Returns successful API test result when include_api_test=true.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-5.1]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        api_test_success=True,
    )

    response = await get_agent_health(mock_service, include_api_test=True)

    assert response.checks.api_test is not None
    assert response.checks.api_test.enabled is True
    assert response.checks.api_test.result == "success"


@pytest.mark.asyncio
async def test_health_check_with_api_test_failure():
    """
    AC5.2: Returns error message when API test fails.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-5.2]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService(
        api_key_configured=True,
        gemini_initialized=True,
        api_test_success=False,
    )

    response = await get_agent_health(mock_service, include_api_test=True)

    assert response.checks.api_test is not None
    assert response.checks.api_test.enabled is True
    assert response.checks.api_test.result == "API Error"


@pytest.mark.asyncio
async def test_health_check_without_api_test():
    """
    AC5.3: API test is disabled by default.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-5.3]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    response = await get_agent_health(mock_service, include_api_test=False)

    assert response.checks.api_test is not None
    assert response.checks.api_test.enabled is False
    assert response.checks.api_test.result is None


# ═══════════════════════════════════════════════════════════════════════════════
# AC6: Cache Tests (60-second TTL per ADR-007)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_cache_ttl():
    """
    AC6.1: Results are cached for 60 seconds (ADR-007).

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-6.1]
    [Source: ADR-007 - Cache TTL]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    # First call - should NOT be cached
    response1 = await get_agent_health(mock_service, include_api_test=False)
    assert response1.cached is False
    assert mock_service.health_check_call_count == 1

    # Second call immediately - should be cached
    response2 = await get_agent_health(mock_service, include_api_test=False)
    assert response2.cached is True
    assert mock_service.health_check_call_count == 1  # No additional call

    # Verify cache TTL constant
    assert HEALTH_CHECK_CACHE_TTL == 60


@pytest.mark.asyncio
async def test_health_check_cache_expired():
    """
    AC6.2: Cache is invalidated after 60 seconds.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-6.2]
    """
    import app.api.v1.endpoints.agents as agents_module

    mock_service = MockAgentService()

    # Set cache to expired state (61 seconds ago)
    agents_module._health_check_cache = {"health_False": {"status": "healthy", "checks": {}, "timestamp": datetime.now(timezone.utc).isoformat()}}
    agents_module._health_check_cache_time = time.time() - 61

    # Call should NOT use cache (expired)
    response = await get_agent_health(mock_service, include_api_test=False)
    assert response.cached is False
    assert mock_service.health_check_call_count == 1


@pytest.mark.asyncio
async def test_health_check_separate_cache_keys():
    """
    AC6.3: Different cache keys for include_api_test=true/false.

    [Source: docs/stories/story-12.G.3-agent-health-check-endpoint.md#AC-6.3]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    # First call without API test
    response1 = await get_agent_health(mock_service, include_api_test=False)
    assert response1.cached is False
    assert mock_service.health_check_call_count == 1

    # Call with API test - should NOT use cache (different key)
    response2 = await get_agent_health(mock_service, include_api_test=True)
    assert response2.cached is False
    assert mock_service.health_check_call_count == 2


# ═══════════════════════════════════════════════════════════════════════════════
# AC7: Response Model Validation
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check_response_model():
    """
    AC7.1: Response matches AgentHealthCheckResponse model.

    [Source: specs/data/health-check-response.schema.json]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    response = await get_agent_health(mock_service, include_api_test=False)

    # Verify response type
    assert isinstance(response, AgentHealthCheckResponse)
    assert isinstance(response.status, AgentHealthStatus)
    assert isinstance(response.checks, AgentHealthChecks)
    assert isinstance(response.checks.prompt_templates, PromptTemplateCheck)
    assert isinstance(response.timestamp, datetime)
    assert isinstance(response.cached, bool)


@pytest.mark.asyncio
async def test_health_check_timestamp_format():
    """
    AC7.2: Timestamp is in ISO 8601 format.

    [Source: specs/data/health-check-response.schema.json#timestamp]
    """
    import app.api.v1.endpoints.agents as agents_module
    agents_module._health_check_cache = {}
    agents_module._health_check_cache_time = 0.0

    mock_service = MockAgentService()

    response = await get_agent_health(mock_service, include_api_test=False)

    # Verify timestamp is valid datetime
    assert response.timestamp is not None
    assert response.timestamp.tzinfo is not None  # Has timezone info
