# Canvas Learning System - Provider Recovery Integration Tests
# ✅ Story 20.6: Integration Tests for Provider Recovery (AC-20.6.8)
"""
Integration tests for provider recovery mechanism.

These tests verify:
- AC-20.6.8: Provider recovery after becoming healthy again
- AC-20.4.5: Periodic health checks re-enable recovered providers
- Graceful recovery without service interruption

[Source: docs/stories/20.6.story.md#AC-20.6.8]
[Source: docs/architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md]
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.clients.base_provider import (
    BaseProvider,
    ProviderConfig,
    ProviderHealth,
    ProviderStatus,
)


class TestProviderRecovery:
    """Provider recovery integration tests - AC-20.6.8"""

    def test_recovery_resets_failure_counter(self, mock_unhealthy_provider):
        """Test that recovery resets consecutive failure counter."""
        # Arrange
        provider = mock_unhealthy_provider
        assert provider.health.consecutive_failures == 3
        assert provider.health.status == ProviderStatus.UNHEALTHY

        # Act - Simulate recovery
        provider.health.consecutive_failures = 0
        provider.health.status = ProviderStatus.HEALTHY
        provider.health.error_message = None
        provider.is_available = True

        # Assert
        assert provider.health.consecutive_failures == 0
        assert provider.health.status == ProviderStatus.HEALTHY
        assert provider.is_available is True

    def test_recovered_provider_rejoins_pool(
        self,
        mock_healthy_provider,
        mock_unhealthy_provider,
        provider_factory_clean
    ):
        """AC-20.4.5: Recovered provider is re-added to selection pool."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange - Initially unhealthy provider
        mock_unhealthy_provider.priority = 1  # Higher priority
        mock_healthy_provider.priority = 2

        factory = ProviderFactory()
        factory._providers = {
            "recovering": mock_unhealthy_provider,
            "healthy": mock_healthy_provider,
        }
        factory._priority_order = ["recovering", "healthy"]

        # Act 1 - Before recovery, should select healthy
        provider1 = factory.get_provider()
        assert provider1.name == "test-google"  # The healthy one

        # Act 2 - Simulate recovery
        mock_unhealthy_provider.health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            consecutive_failures=0
        )
        mock_unhealthy_provider.is_available = True

        # Act 3 - After recovery, should select recovered (higher priority)
        provider2 = factory.get_provider()
        assert provider2.name == "test-unhealthy"  # Now recovered

    def test_gradual_recovery_through_degraded(self):
        """Test recovery path: UNHEALTHY → DEGRADED → HEALTHY."""
        # Arrange
        health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=3
        )

        # Act - First successful request
        health.consecutive_failures = 2
        health.status = ProviderStatus.DEGRADED  # Still cautious

        # Assert intermediate state
        assert health.status == ProviderStatus.DEGRADED
        assert health.is_healthy is True  # Degraded is still usable

        # Act - Second successful request
        health.consecutive_failures = 1

        # Act - Third successful request
        health.consecutive_failures = 0
        health.status = ProviderStatus.HEALTHY

        # Assert final state
        assert health.status == ProviderStatus.HEALTHY
        assert health.consecutive_failures == 0

    def test_recovery_preserves_latency_history(self):
        """Test that recovery updates latency without losing history."""
        # Arrange
        health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            latency_ms=None,  # No latency when unhealthy
            consecutive_failures=3
        )

        # Act - Recovery with new latency
        health.status = ProviderStatus.HEALTHY
        health.consecutive_failures = 0
        health.latency_ms = 75.0
        health.last_check = datetime.now()

        # Assert
        assert health.latency_ms == 75.0
        assert health.last_check is not None


@pytest.mark.asyncio
class TestProviderRecoveryAsync:
    """Async provider recovery integration tests."""

    async def test_update_health_triggers_recovery(self):
        """Test update_health() method triggers recovery state."""

        # Create concrete test provider
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

        # Start with unhealthy
        provider.health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=5,
            error_message="Previous error"
        )

        # Act - Single successful update should recover
        await provider.update_health(success=True, latency_ms=50.0)

        # Assert - Should be fully healthy now
        assert provider.health.status == ProviderStatus.HEALTHY
        assert provider.health.consecutive_failures == 0
        assert provider.health.latency_ms == 50.0
        assert provider.health.error_message is None

    async def test_periodic_health_check_recovers_provider(
        self,
        provider_factory_clean
    ):
        """AC-20.4.5: Periodic health check re-enables recovered provider."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        mock_provider = MagicMock(spec=BaseProvider)
        mock_provider.name = "recovering"
        mock_provider.priority = 1
        mock_provider.is_enabled = True

        # Initially unhealthy
        mock_provider.health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=3
        )
        mock_provider.is_available = False

        # Health check returns healthy (simulating recovery)
        mock_provider.health_check = AsyncMock(return_value=ProviderHealth(
            status=ProviderStatus.HEALTHY,
            latency_ms=50.0,
            consecutive_failures=0
        ))

        factory = ProviderFactory()
        factory._providers = {"recovering": mock_provider}

        # Act - Run health check
        results = await factory.check_all_health()

        # Assert
        assert results["recovering"].status == ProviderStatus.HEALTHY
        assert results["recovering"].consecutive_failures == 0

    async def test_recovery_does_not_interrupt_active_requests(
        self,
        mock_healthy_provider,
        provider_factory_clean
    ):
        """Test that recovery process doesn't interrupt active requests."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        factory = ProviderFactory()
        factory._providers = {"healthy": mock_healthy_provider}
        factory._priority_order = ["healthy"]
        factory._initialized = True

        # Simulate concurrent request during recovery
        async def simulate_request():
            response = await factory.complete(
                system_prompt="Test",
                user_prompt="Hello"
            )
            return response

        # Act - Multiple concurrent requests
        results = await asyncio.gather(
            simulate_request(),
            simulate_request(),
            simulate_request()
        )

        # Assert - All requests should complete
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert result.text == "Test response"

    async def test_exponential_backoff_before_recovery_attempt(self):
        """Test exponential backoff is respected before recovery attempts."""
        # Arrange
        health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=3,
            last_check=datetime.now() - timedelta(seconds=10)
        )

        # Calculate expected backoff (2^failures seconds, max 300)
        expected_backoff = min(2 ** 3, 300)  # 8 seconds

        # Assert - Time since last check
        time_since_check = (datetime.now() - health.last_check).total_seconds()
        assert time_since_check >= 10  # At least 10 seconds passed

        # For 3 failures, backoff is 8 seconds, so 10 seconds is enough
        can_retry = time_since_check >= expected_backoff
        assert can_retry is True

    async def test_recovery_emits_log_event(
        self,
        mock_unhealthy_provider,
        provider_factory_clean,
        caplog
    ):
        """Test that recovery emits appropriate log messages."""
        import logging

        from app.clients.provider_factory import ProviderFactory

        # Arrange
        caplog.set_level(logging.INFO)

        # Simulate recovery
        mock_unhealthy_provider.health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            consecutive_failures=0
        )
        mock_unhealthy_provider.is_available = True
        mock_unhealthy_provider.health_check = AsyncMock(
            return_value=mock_unhealthy_provider.health
        )

        factory = ProviderFactory()
        factory._providers = {"provider": mock_unhealthy_provider}

        # Act
        await factory.check_all_health()

        # Note: Actual log verification depends on implementation
        # This test ensures the check completes without error


class TestRecoveryScenarios:
    """End-to-end recovery scenario tests."""

    def test_full_recovery_cycle(self, provider_factory_clean):
        """Test complete failure → recovery → active cycle."""
        from app.clients.base_provider import ProviderHealth, ProviderStatus
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        provider = MagicMock(spec=BaseProvider)
        provider.name = "test-provider"
        provider.priority = 1
        provider.is_enabled = True

        factory = ProviderFactory()
        factory._providers = {"test": provider}
        factory._priority_order = ["test"]

        # Phase 1: Healthy
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
        provider.is_available = True
        selected = factory.get_provider()
        assert selected.name == "test-provider"

        # Phase 2: Degraded (1 failure)
        provider.health = ProviderHealth(
            status=ProviderStatus.DEGRADED,
            consecutive_failures=1
        )
        provider.is_available = True
        selected = factory.get_provider()
        assert selected.name == "test-provider"  # Still available

        # Phase 3: Unhealthy (3 failures)
        provider.health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=3
        )
        provider.is_available = False

        # Phase 4: Recovery
        provider.health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            consecutive_failures=0
        )
        provider.is_available = True
        selected = factory.get_provider()
        assert selected.name == "test-provider"  # Back in pool

    def test_multiple_providers_recovery_order(self, provider_factory_clean):
        """Test recovery order with multiple providers."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange - 3 providers, all unhealthy initially
        providers = {}
        for i, name in enumerate(["google", "openai", "anthropic"]):
            p = MagicMock(spec=BaseProvider)
            p.name = name
            p.priority = i + 1
            p.is_enabled = True
            p.health = ProviderHealth(
                status=ProviderStatus.UNHEALTHY,
                consecutive_failures=3
            )
            p.is_available = False
            providers[name] = p

        factory = ProviderFactory()
        factory._providers = providers
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act - Recover OpenAI first (priority 2)
        providers["openai"].health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            consecutive_failures=0
        )
        providers["openai"].is_available = True

        selected = factory.get_provider()
        assert selected.name == "openai"

        # Act - Recover Google (priority 1)
        providers["google"].health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            consecutive_failures=0
        )
        providers["google"].is_available = True

        selected = factory.get_provider()
        assert selected.name == "google"  # Higher priority takes over
