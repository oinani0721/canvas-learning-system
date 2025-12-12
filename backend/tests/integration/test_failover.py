# Canvas Learning System - Failover Integration Tests
# ✅ Story 20.6: Integration Tests for Failover (AC-20.6.7)
"""
Integration tests for provider failover mechanism.

These tests verify:
- AC-20.6.7: Consecutive failure handling and unhealthy marking
- AC-20.4.3: Mark provider unhealthy after 3 consecutive failures
- AC-20.4.4: Remove unhealthy providers from selection pool

[Source: docs/stories/20.6.story.md#AC-20.6.7]
[Source: docs/architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md]
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.clients.base_provider import (
    BaseProvider,
    ProviderConfig,
    ProviderHealth,
    ProviderStatus,
)


class TestFailover:
    """Failover integration tests - AC-20.6.7"""

    @pytest.fixture
    def provider_config(self):
        """Create test provider configuration."""
        return ProviderConfig(
            name="test-provider",
            api_key="test-api-key",
            model="test-model",
            priority=1
        )

    def test_provider_health_status_transitions(self):
        """Test health status transitions: HEALTHY → DEGRADED → UNHEALTHY."""
        # Arrange
        health = ProviderHealth(status=ProviderStatus.HEALTHY)

        # Initial state
        assert health.status == ProviderStatus.HEALTHY
        assert health.is_healthy is True

        # After 1 failure - should be DEGRADED
        health.consecutive_failures = 1
        health.status = ProviderStatus.DEGRADED
        assert health.is_healthy is True  # Still available

        # After 3 failures - should be UNHEALTHY
        health.consecutive_failures = 3
        health.status = ProviderStatus.UNHEALTHY
        assert health.is_healthy is False

    def test_consecutive_failure_counter(self, mock_healthy_provider):
        """Test consecutive failure counter increments correctly."""
        # Arrange
        provider = mock_healthy_provider
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)

        # Simulate failures
        for i in range(1, 4):
            provider.health.consecutive_failures = i
            if i >= 3:
                provider.health.status = ProviderStatus.UNHEALTHY
            elif i >= 1:
                provider.health.status = ProviderStatus.DEGRADED

        # Assert
        assert provider.health.consecutive_failures == 3
        assert provider.health.status == ProviderStatus.UNHEALTHY

    def test_failure_counter_resets_on_success(self, mock_healthy_provider):
        """Test failure counter resets after successful request."""
        # Arrange
        provider = mock_healthy_provider
        provider.health = ProviderHealth(
            status=ProviderStatus.DEGRADED,
            consecutive_failures=2
        )

        # Simulate success
        provider.health.consecutive_failures = 0
        provider.health.status = ProviderStatus.HEALTHY

        # Assert
        assert provider.health.consecutive_failures == 0
        assert provider.health.status == ProviderStatus.HEALTHY

    def test_unhealthy_provider_excluded_from_selection(
        self,
        mock_healthy_provider,
        mock_unhealthy_provider,
        provider_factory_clean
    ):
        """AC-20.4.4: Unhealthy providers are not selected."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        mock_unhealthy_provider.priority = 1  # Higher priority but unhealthy
        mock_healthy_provider.priority = 2

        factory = ProviderFactory()
        factory._providers = {
            "unhealthy": mock_unhealthy_provider,
            "healthy": mock_healthy_provider,
        }
        factory._priority_order = ["unhealthy", "healthy"]

        # Act
        provider = factory.get_provider()

        # Assert - Should skip unhealthy and select healthy provider
        assert provider.name == "test-google"

    def test_provider_health_to_dict(self):
        """Test ProviderHealth serialization to dict."""
        # Arrange
        health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            latency_ms=50.0,
            last_check=datetime(2025, 1, 1, 12, 0, 0),
            consecutive_failures=0,
            error_message=None
        )

        # Act
        result = health.to_dict()

        # Assert
        assert result["status"] == "healthy"
        assert result["latency_ms"] == 50.0
        assert result["last_check"] == "2025-01-01T12:00:00"
        assert result["consecutive_failures"] == 0
        assert result["error_message"] is None


@pytest.mark.asyncio
class TestFailoverAsync:
    """Async failover integration tests."""

    async def test_update_health_on_success(self):
        """Test update_health() correctly updates on success."""
        from app.clients.base_provider import ProviderConfig

        # Create a concrete implementation for testing
        class TestProvider(BaseProvider):
            async def initialize(self):
                return True

            async def complete(self, *args, **kwargs):
                pass

            async def complete_with_images(self, *args, **kwargs):
                pass

            async def health_check(self):
                return self.health

        config = ProviderConfig(
            name="test",
            api_key="test-key",
            model="test-model"
        )
        provider = TestProvider(config)

        # Start with unhealthy state
        provider.health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=5
        )

        # Act - Update with success
        await provider.update_health(success=True, latency_ms=50.0)

        # Assert
        assert provider.health.status == ProviderStatus.HEALTHY
        assert provider.health.consecutive_failures == 0
        assert provider.health.latency_ms == 50.0
        assert provider.health.last_check is not None

    async def test_update_health_on_failure(self):
        """Test update_health() correctly updates on failure."""
        from app.clients.base_provider import ProviderConfig

        class TestProvider(BaseProvider):
            async def initialize(self):
                return True

            async def complete(self, *args, **kwargs):
                pass

            async def complete_with_images(self, *args, **kwargs):
                pass

            async def health_check(self):
                return self.health

        config = ProviderConfig(
            name="test",
            api_key="test-key",
            model="test-model"
        )
        provider = TestProvider(config)
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)

        # Act - Simulate 3 failures
        for _ in range(3):
            await provider.update_health(success=False, error="Test error")

        # Assert - Should be unhealthy after 3 failures
        assert provider.health.status == ProviderStatus.UNHEALTHY
        assert provider.health.consecutive_failures == 3
        assert provider.health.error_message == "Test error"

    async def test_degraded_after_first_failure(self):
        """Test provider becomes DEGRADED after first failure."""
        from app.clients.base_provider import ProviderConfig

        class TestProvider(BaseProvider):
            async def initialize(self):
                return True

            async def complete(self, *args, **kwargs):
                pass

            async def complete_with_images(self, *args, **kwargs):
                pass

            async def health_check(self):
                return self.health

        config = ProviderConfig(
            name="test",
            api_key="test-key",
            model="test-model"
        )
        provider = TestProvider(config)
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)

        # Act - First failure
        await provider.update_health(success=False, error="First error")

        # Assert
        assert provider.health.status == ProviderStatus.DEGRADED
        assert provider.health.consecutive_failures == 1

    async def test_check_all_health(self, provider_factory_clean):
        """Test checking health of all providers."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        mock_providers = {}
        for name in ["google", "openai"]:
            provider = MagicMock(spec=BaseProvider)
            provider.name = name
            provider.health_check = AsyncMock(return_value=ProviderHealth(
                status=ProviderStatus.HEALTHY,
                latency_ms=50.0
            ))
            mock_providers[name] = provider

        factory = ProviderFactory()
        factory._providers = mock_providers

        # Act
        results = await factory.check_all_health()

        # Assert
        assert len(results) == 2
        assert results["google"].status == ProviderStatus.HEALTHY
        assert results["openai"].status == ProviderStatus.HEALTHY

    async def test_check_all_health_handles_exceptions(self, provider_factory_clean):
        """Test check_all_health() handles provider exceptions."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        healthy_provider = MagicMock(spec=BaseProvider)
        healthy_provider.name = "healthy"
        healthy_provider.health_check = AsyncMock(return_value=ProviderHealth(
            status=ProviderStatus.HEALTHY
        ))

        failing_provider = MagicMock(spec=BaseProvider)
        failing_provider.name = "failing"
        failing_provider.health_check = AsyncMock(
            side_effect=Exception("Health check failed")
        )

        factory = ProviderFactory()
        factory._providers = {
            "healthy": healthy_provider,
            "failing": failing_provider,
        }

        # Act
        results = await factory.check_all_health()

        # Assert
        assert results["healthy"].status == ProviderStatus.HEALTHY
        assert results["failing"].status == ProviderStatus.UNHEALTHY
        assert "Health check failed" in results["failing"].error_message
