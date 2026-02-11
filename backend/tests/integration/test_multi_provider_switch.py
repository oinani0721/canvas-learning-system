# Canvas Learning System - Multi-Provider Switch Integration Tests
# ✅ Story 20.6: Integration Tests for Multi-Provider Switching (AC-20.6.6)
"""
Integration tests for multi-provider switching mechanism.

These tests verify:
- AC-20.6.2: Primary failure triggers automatic switch within 2 seconds
- AC-20.6.6: Multi-provider switch integration (Google → OpenAI → Anthropic)
- Provider selection strategies (priority, round-robin, latency)

[Source: docs/stories/20.6.story.md#AC-20.6.6]
[Source: docs/prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md]
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import simulate_async_delay

from app.clients.base_provider import (
    BaseProvider,
    NoHealthyProviderError,
    ProviderConfig,
    ProviderHealth,
    ProviderResponse,
    ProviderStatus,
)
from app.clients.provider_factory import ProviderFactory, SelectionStrategy


class TestMultiProviderSwitch:
    """Multi-Provider switching integration tests - AC-20.6.6"""

    @pytest.fixture
    def mock_google_provider(self):
        """Create mock Google provider (priority 1)."""
        provider = MagicMock(spec=BaseProvider)
        provider.name = "google"
        provider.priority = 1
        provider.is_enabled = True
        provider.health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            latency_ms=50.0,
            consecutive_failures=0
        )
        provider.is_available = True
        provider.config = ProviderConfig(
            name="google",
            api_key="test-key",
            model="gemini-2.0-flash-exp",
            priority=1
        )
        provider.initialize = AsyncMock(return_value=True)
        provider.health_check = AsyncMock(return_value=provider.health)
        provider.complete = AsyncMock(return_value=ProviderResponse(
            text="Google response",
            model="gemini-2.0-flash-exp",
            provider="google",
            latency_ms=50.0
        ))
        return provider

    @pytest.fixture
    def mock_openai_provider(self):
        """Create mock OpenAI provider (priority 2)."""
        provider = MagicMock(spec=BaseProvider)
        provider.name = "openai"
        provider.priority = 2
        provider.is_enabled = True
        provider.health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            latency_ms=80.0,
            consecutive_failures=0
        )
        provider.is_available = True
        provider.config = ProviderConfig(
            name="openai",
            api_key="test-key",
            model="gpt-4o",
            priority=2
        )
        provider.initialize = AsyncMock(return_value=True)
        provider.health_check = AsyncMock(return_value=provider.health)
        provider.complete = AsyncMock(return_value=ProviderResponse(
            text="OpenAI response",
            model="gpt-4o",
            provider="openai",
            latency_ms=80.0
        ))
        return provider

    @pytest.fixture
    def mock_anthropic_provider(self):
        """Create mock Anthropic provider (priority 3)."""
        provider = MagicMock(spec=BaseProvider)
        provider.name = "anthropic"
        provider.priority = 3
        provider.is_enabled = True
        provider.health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            latency_ms=100.0,
            consecutive_failures=0
        )
        provider.is_available = True
        provider.config = ProviderConfig(
            name="anthropic",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
            priority=3
        )
        provider.initialize = AsyncMock(return_value=True)
        provider.health_check = AsyncMock(return_value=provider.health)
        provider.complete = AsyncMock(return_value=ProviderResponse(
            text="Anthropic response",
            model="claude-3-5-sonnet-20241022",
            provider="anthropic",
            latency_ms=100.0
        ))
        return provider

    def test_select_highest_priority_healthy_provider(
        self,
        mock_google_provider,
        mock_openai_provider,
        mock_anthropic_provider,
        provider_factory_clean
    ):
        """Test that highest priority healthy provider is selected."""
        # Arrange - Create factory with all healthy providers
        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider,
        }
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act
        provider = factory.get_provider()

        # Assert - Google (priority 1) should be selected
        assert provider.name == "google"
        assert provider.priority == 1

    def test_switch_to_backup_on_primary_failure(
        self,
        mock_google_provider,
        mock_openai_provider,
        mock_anthropic_provider,
        provider_factory_clean
    ):
        """AC-20.6.2: Primary fails, should switch to backup."""
        # Arrange - Make Google unhealthy
        mock_google_provider.health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=3
        )
        mock_google_provider.is_available = False

        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider,
        }
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act
        provider = factory.get_provider()

        # Assert - OpenAI (priority 2) should be selected
        assert provider.name == "openai"
        assert provider.priority == 2

    def test_fallback_chain_google_openai_anthropic(
        self,
        mock_google_provider,
        mock_openai_provider,
        mock_anthropic_provider,
        provider_factory_clean
    ):
        """AC-20.6.6: Test complete failover chain Google → OpenAI → Anthropic."""
        # Arrange - Make Google and OpenAI unhealthy
        mock_google_provider.health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=3
        )
        mock_google_provider.is_available = False

        mock_openai_provider.health = ProviderHealth(
            status=ProviderStatus.UNHEALTHY,
            consecutive_failures=3
        )
        mock_openai_provider.is_available = False

        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider,
        }
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act
        provider = factory.get_provider()

        # Assert - Anthropic (priority 3) should be selected
        assert provider.name == "anthropic"
        assert provider.priority == 3

    def test_no_healthy_provider_raises_error(
        self,
        mock_google_provider,
        mock_openai_provider,
        mock_anthropic_provider,
        provider_factory_clean
    ):
        """Test NoHealthyProviderError when all providers fail."""
        # Arrange - Make all providers unhealthy
        for provider in [mock_google_provider, mock_openai_provider, mock_anthropic_provider]:
            provider.health = ProviderHealth(
                status=ProviderStatus.UNHEALTHY,
                consecutive_failures=3
            )
            provider.is_available = False

        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider,
        }
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act & Assert
        with pytest.raises(NoHealthyProviderError):
            factory.get_provider()

    def test_switch_latency_under_100ms(
        self,
        mock_google_provider,
        mock_openai_provider,
        mock_anthropic_provider,
        provider_factory_clean
    ):
        """AC-20.2.3: Provider switch time < 100ms."""
        # Arrange
        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider,
        }
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act - Time the selection
        start = time.perf_counter()
        for _ in range(100):  # Run 100 times to get meaningful measurement
            factory.get_provider()
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100  # Average per call

        # Assert
        assert elapsed_ms < 100, f"Switch latency {elapsed_ms:.2f}ms exceeds 100ms"

    def test_round_robin_selection(
        self,
        mock_google_provider,
        mock_openai_provider,
        mock_anthropic_provider,
        provider_factory_clean
    ):
        """Test round-robin provider selection strategy."""
        # Arrange
        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider,
        }
        factory._priority_order = ["google", "openai", "anthropic"]
        factory.set_selection_strategy(SelectionStrategy.ROUND_ROBIN)

        # Act - Get providers multiple times
        providers = [factory.get_provider().name for _ in range(6)]

        # Assert - Should cycle through providers
        # Due to priority sorting first, the order follows priority
        assert len(set(providers)) >= 2, "Round-robin should use multiple providers"

    def test_latency_optimal_selection(
        self,
        mock_google_provider,
        mock_openai_provider,
        mock_anthropic_provider,
        provider_factory_clean
    ):
        """Test latency-optimal provider selection strategy."""
        # Arrange - Set different latencies
        mock_google_provider.health.latency_ms = 150.0
        mock_openai_provider.health.latency_ms = 50.0  # Lowest
        mock_anthropic_provider.health.latency_ms = 100.0

        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider,
        }
        factory._priority_order = ["google", "openai", "anthropic"]
        factory.set_selection_strategy(SelectionStrategy.LATENCY_OPTIMAL)

        # Act
        provider = factory.get_provider()

        # Assert - OpenAI has lowest latency
        assert provider.name == "openai"

    def test_degraded_provider_still_available(
        self,
        mock_google_provider,
        mock_openai_provider,
        provider_factory_clean
    ):
        """Test that DEGRADED status providers are still selectable."""
        # Arrange - Make Google degraded (1 failure)
        mock_google_provider.health = ProviderHealth(
            status=ProviderStatus.DEGRADED,
            consecutive_failures=1
        )
        mock_google_provider.is_available = True  # Still available when degraded

        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
        }
        factory._priority_order = ["google", "openai"]

        # Act
        provider = factory.get_provider()

        # Assert - Degraded but highest priority is still selected
        assert provider.name == "google"

    def test_get_specific_provider_by_name(
        self,
        mock_google_provider,
        mock_openai_provider,
        provider_factory_clean
    ):
        """Test getting specific provider by name."""
        # Arrange
        factory = ProviderFactory()
        factory._providers = {
            "google": mock_google_provider,
            "openai": mock_openai_provider,
        }
        factory._priority_order = ["google", "openai"]

        # Act
        provider = factory.get_provider(name="openai")

        # Assert - Should return specific provider regardless of priority
        assert provider.name == "openai"


@pytest.mark.asyncio
class TestMultiProviderSwitchAsync:
    """Async integration tests for provider switching."""

    @pytest.fixture
    def mock_provider_with_delay(self):
        """Create mock provider that simulates network delay."""
        provider = MagicMock(spec=BaseProvider)
        provider.name = "delayed"
        provider.priority = 1
        provider.is_enabled = True
        provider.is_available = True
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)

        async def delayed_complete(*args, **kwargs):
            await simulate_async_delay(0.1)  # 100ms delay
            return ProviderResponse(
                text="Delayed response",
                model="test",
                provider="delayed",
                latency_ms=100.0
            )

        provider.complete = delayed_complete
        return provider

    async def test_complete_with_automatic_failover(
        self,
        mock_healthy_provider,
        mock_unhealthy_provider,
        provider_factory_clean
    ):
        """Test complete() method with automatic failover."""
        from app.clients.base_provider import ProviderError

        # Arrange - First provider fails
        mock_unhealthy_provider.priority = 1
        mock_unhealthy_provider.is_available = True  # Appears available but will fail
        mock_unhealthy_provider.complete = AsyncMock(
            side_effect=ProviderError("API Error", provider="test-unhealthy")
        )

        mock_healthy_provider.priority = 2

        factory = ProviderFactory()
        factory._providers = {
            "unhealthy": mock_unhealthy_provider,
            "healthy": mock_healthy_provider,
        }
        factory._priority_order = ["unhealthy", "healthy"]
        factory._initialized = True

        # Act
        response = await factory.complete(
            system_prompt="You are helpful",
            user_prompt="Hello"
        )

        # Assert - Should have failed over to healthy provider
        assert response.provider == "test-google"
        assert factory._switch_count == 1

    async def test_failover_time_under_2_seconds(
        self,
        mock_healthy_provider,
        provider_factory_clean
    ):
        """AC-20.E2: Provider failover completes within 2 seconds."""
        from app.clients.base_provider import ProviderError

        # Arrange - Create 3 failing providers and 1 healthy
        failing_providers = []
        for i in range(3):
            provider = MagicMock(spec=BaseProvider)
            provider.name = f"failing_{i}"
            provider.priority = i + 1
            provider.is_enabled = True
            provider.is_available = True
            provider.complete = AsyncMock(
                side_effect=ProviderError(f"API Error {i}", provider=f"failing_{i}")
            )
            failing_providers.append(provider)

        mock_healthy_provider.priority = 4

        factory = ProviderFactory()
        factory._providers = {
            **{p.name: p for p in failing_providers},
            "healthy": mock_healthy_provider,
        }
        factory._priority_order = [p.name for p in failing_providers] + ["healthy"]
        factory._initialized = True

        # Act - Time the failover
        start = time.perf_counter()
        response = await factory.complete(
            system_prompt="You are helpful",
            user_prompt="Hello"
        )
        elapsed = time.perf_counter() - start

        # Assert - Should complete within 2 seconds
        assert elapsed < 2.0, f"Failover time {elapsed:.2f}s exceeds 2s"
        assert response is not None
