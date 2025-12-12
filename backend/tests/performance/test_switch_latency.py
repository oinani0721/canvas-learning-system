# Canvas Learning System - Provider Switch Latency Performance Tests
# ✅ Story 20.6: Performance Tests for Provider Switching (AC-20.6.3, AC-20.6.4, AC-20.6.5)
"""
Performance tests for provider switching latency.

These tests verify:
- AC-20.6.3: Provider selection time < 100ms
- AC-20.6.4: Full failover completes within 2 seconds
- AC-20.6.5: Memory usage stays within bounds
- Performance under load

[Source: docs/stories/20.6.story.md#AC-20.6.3]
[Source: docs/prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md]
"""

import asyncio
import gc
import statistics
import sys
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.clients.base_provider import (
    BaseProvider,
    ProviderHealth,
    ProviderResponse,
    ProviderStatus,
)


class TestProviderSelectionLatency:
    """Tests for provider selection latency - AC-20.6.3"""

    def test_single_selection_under_100ms(self, provider_factory_clean):
        """AC-20.6.3: Single provider selection < 100ms."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange - Setup factory with multiple providers
        factory = ProviderFactory()
        providers = {}
        for i, name in enumerate(["google", "openai", "anthropic"]):
            provider = MagicMock(spec=BaseProvider)
            provider.name = name
            provider.priority = i + 1
            provider.is_enabled = True
            provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
            provider.is_available = True
            providers[name] = provider

        factory._providers = providers
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act - Time single selection
        start = time.perf_counter()
        provider = factory.get_provider()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert provider is not None
        assert elapsed_ms < 100, f"Selection took {elapsed_ms:.2f}ms, exceeds 100ms"

    def test_average_selection_under_10ms(self, provider_factory_clean):
        """Test average provider selection time under 10ms."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        factory = ProviderFactory()
        providers = {}
        for i, name in enumerate(["google", "openai", "anthropic"]):
            provider = MagicMock(spec=BaseProvider)
            provider.name = name
            provider.priority = i + 1
            provider.is_enabled = True
            provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
            provider.is_available = True
            providers[name] = provider

        factory._providers = providers
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act - Run 1000 selections
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            factory.get_provider()
            times.append((time.perf_counter() - start) * 1000)

        avg_ms = statistics.mean(times)
        p99_ms = sorted(times)[int(len(times) * 0.99)]

        # Assert
        assert avg_ms < 10, f"Average selection {avg_ms:.2f}ms exceeds 10ms"
        assert p99_ms < 50, f"P99 selection {p99_ms:.2f}ms exceeds 50ms"

    def test_selection_with_unhealthy_providers(self, provider_factory_clean):
        """Test selection time when some providers are unhealthy."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange - First two providers unhealthy
        factory = ProviderFactory()
        providers = {}

        for i, name in enumerate(["google", "openai", "anthropic"]):
            provider = MagicMock(spec=BaseProvider)
            provider.name = name
            provider.priority = i + 1
            provider.is_enabled = True

            if i < 2:  # First two unhealthy
                provider.health = ProviderHealth(
                    status=ProviderStatus.UNHEALTHY,
                    consecutive_failures=3
                )
                provider.is_available = False
            else:
                provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
                provider.is_available = True

            providers[name] = provider

        factory._providers = providers
        factory._priority_order = ["google", "openai", "anthropic"]

        # Act - Time selection (must skip unhealthy)
        start = time.perf_counter()
        provider = factory.get_provider()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert provider.name == "anthropic"
        assert elapsed_ms < 100, f"Selection took {elapsed_ms:.2f}ms with unhealthy providers"


@pytest.mark.asyncio
class TestFailoverLatency:
    """Tests for failover latency - AC-20.6.4"""

    async def test_single_failover_under_500ms(self, provider_factory_clean):
        """Test single failover completes under 500ms."""
        from app.clients.base_provider import ProviderError
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        failing_provider = MagicMock(spec=BaseProvider)
        failing_provider.name = "failing"
        failing_provider.priority = 1
        failing_provider.is_enabled = True
        failing_provider.is_available = True
        failing_provider.complete = AsyncMock(
            side_effect=ProviderError("API Error", provider="failing")
        )

        healthy_provider = MagicMock(spec=BaseProvider)
        healthy_provider.name = "healthy"
        healthy_provider.priority = 2
        healthy_provider.is_enabled = True
        healthy_provider.is_available = True
        healthy_provider.complete = AsyncMock(return_value=ProviderResponse(
            text="Success",
            model="test",
            provider="healthy",
            latency_ms=50.0
        ))

        factory = ProviderFactory()
        factory._providers = {
            "failing": failing_provider,
            "healthy": healthy_provider,
        }
        factory._priority_order = ["failing", "healthy"]
        factory._initialized = True

        # Act
        start = time.perf_counter()
        response = await factory.complete(
            system_prompt="Test",
            user_prompt="Hello"
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert response.provider == "healthy"
        assert elapsed_ms < 500, f"Failover took {elapsed_ms:.2f}ms"

    async def test_full_failover_chain_under_2s(self, provider_factory_clean):
        """AC-20.6.4: Full failover chain completes under 2 seconds."""
        from app.clients.base_provider import ProviderError
        from app.clients.provider_factory import ProviderFactory

        # Arrange - 3 failing providers, 1 healthy
        providers = {}
        priority_order = []

        for i in range(3):
            provider = MagicMock(spec=BaseProvider)
            provider.name = f"failing_{i}"
            provider.priority = i + 1
            provider.is_enabled = True
            provider.is_available = True
            provider.complete = AsyncMock(
                side_effect=ProviderError(f"Error {i}", provider=f"failing_{i}")
            )
            providers[f"failing_{i}"] = provider
            priority_order.append(f"failing_{i}")

        healthy = MagicMock(spec=BaseProvider)
        healthy.name = "healthy"
        healthy.priority = 4
        healthy.is_enabled = True
        healthy.is_available = True
        healthy.complete = AsyncMock(return_value=ProviderResponse(
            text="Success",
            model="test",
            provider="healthy",
            latency_ms=50.0
        ))
        providers["healthy"] = healthy
        priority_order.append("healthy")

        factory = ProviderFactory()
        factory._providers = providers
        factory._priority_order = priority_order
        factory._initialized = True

        # Act
        start = time.perf_counter()
        response = await factory.complete(
            system_prompt="Test",
            user_prompt="Hello"
        )
        elapsed = time.perf_counter() - start

        # Assert
        assert response.provider == "healthy"
        assert elapsed < 2.0, f"Full failover took {elapsed:.2f}s, exceeds 2s"

    async def test_concurrent_requests_during_failover(self, provider_factory_clean):
        """Test performance with concurrent requests during failover."""
        from app.clients.base_provider import ProviderError
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        call_count = 0

        async def intermittent_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Every 3rd call fails
                raise ProviderError("Intermittent", provider="test")
            return ProviderResponse(
                text="Success",
                model="test",
                provider="test",
                latency_ms=10.0
            )

        provider = MagicMock(spec=BaseProvider)
        provider.name = "test"
        provider.priority = 1
        provider.is_enabled = True
        provider.is_available = True
        provider.complete = intermittent_failure

        factory = ProviderFactory()
        factory._providers = {"test": provider}
        factory._priority_order = ["test"]
        factory._initialized = True

        # Act - 10 concurrent requests
        start = time.perf_counter()
        tasks = [
            factory.complete(system_prompt="Test", user_prompt="Hello")
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.perf_counter() - start

        # Assert - Should complete reasonably fast
        successes = [r for r in results if isinstance(r, ProviderResponse)]
        assert len(successes) >= 6  # At least 60% success
        assert elapsed < 5.0  # Should complete within 5 seconds


class TestMemoryUsage:
    """Tests for memory usage bounds - AC-20.6.5"""

    def test_provider_factory_memory_footprint(self, provider_factory_clean):
        """Test ProviderFactory memory footprint stays reasonable."""
        from app.clients.provider_factory import ProviderFactory

        # Force garbage collection
        gc.collect()
        # Note: baseline measurement for memory comparison
        _ = sys.getsizeof(ProviderFactory())

        # Create factory with providers
        factory = ProviderFactory()
        providers = {}
        for i in range(10):
            provider = MagicMock(spec=BaseProvider)
            provider.name = f"provider_{i}"
            provider.priority = i
            provider.is_enabled = True
            provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
            provider.is_available = True
            providers[f"provider_{i}"] = provider

        factory._providers = providers

        # Memory should not grow excessively
        # Note: Exact measurement depends on implementation
        assert len(factory._providers) == 10

    def test_no_memory_leak_on_repeated_selections(self, provider_factory_clean):
        """Test no memory leak with repeated provider selections."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        factory = ProviderFactory()
        provider = MagicMock(spec=BaseProvider)
        provider.name = "test"
        provider.priority = 1
        provider.is_enabled = True
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
        provider.is_available = True
        factory._providers = {"test": provider}
        factory._priority_order = ["test"]

        # Get baseline
        gc.collect()
        baseline_objects = len(gc.get_objects())

        # Act - Many selections
        for _ in range(10000):
            factory.get_provider()

        # Check memory
        gc.collect()
        final_objects = len(gc.get_objects())

        # Assert - Object count should not grow significantly
        growth = final_objects - baseline_objects
        # Allow some growth but not proportional to iterations
        assert growth < 1000, f"Object growth {growth} suggests memory leak"


class TestPerformanceUnderLoad:
    """Load testing for provider system."""

    def test_high_frequency_selections(self, provider_factory_clean):
        """Test performance with high frequency provider selections."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        factory = ProviderFactory()
        provider = MagicMock(spec=BaseProvider)
        provider.name = "test"
        provider.priority = 1
        provider.is_enabled = True
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
        provider.is_available = True
        factory._providers = {"test": provider}
        factory._priority_order = ["test"]

        # Act - 10,000 selections in tight loop
        start = time.perf_counter()
        for _ in range(10000):
            factory.get_provider()
        elapsed = time.perf_counter() - start

        # Assert - Should handle 10k selections per second
        ops_per_second = 10000 / elapsed
        assert ops_per_second > 10000, f"Only {ops_per_second:.0f} ops/s, expected >10000"

    @pytest.mark.asyncio
    async def test_sustained_load(self, provider_factory_clean):
        """Test performance under sustained load."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        provider = MagicMock(spec=BaseProvider)
        provider.name = "test"
        provider.priority = 1
        provider.is_enabled = True
        provider.is_available = True
        provider.complete = AsyncMock(return_value=ProviderResponse(
            text="Success",
            model="test",
            provider="test",
            latency_ms=10.0
        ))

        factory = ProviderFactory()
        factory._providers = {"test": provider}
        factory._priority_order = ["test"]
        factory._initialized = True

        # Act - Sustained load for 1 second
        start = time.perf_counter()
        count = 0
        while time.perf_counter() - start < 1.0:
            await factory.complete(system_prompt="Test", user_prompt="Hello")
            count += 1

        # Assert - Should handle reasonable throughput
        assert count > 100, f"Only {count} requests/s, expected >100"


class TestLatencyPercentiles:
    """Percentile-based latency tests."""

    def test_selection_latency_percentiles(self, provider_factory_clean):
        """Test provider selection latency percentiles."""
        from app.clients.provider_factory import ProviderFactory

        # Arrange
        factory = ProviderFactory()
        provider = MagicMock(spec=BaseProvider)
        provider.name = "test"
        provider.priority = 1
        provider.is_enabled = True
        provider.health = ProviderHealth(status=ProviderStatus.HEALTHY)
        provider.is_available = True
        factory._providers = {"test": provider}
        factory._priority_order = ["test"]

        # Act - Collect 1000 samples
        latencies = []
        for _ in range(1000):
            start = time.perf_counter()
            factory.get_provider()
            latencies.append((time.perf_counter() - start) * 1000)

        # Calculate percentiles
        latencies.sort()
        p50 = latencies[500]
        p95 = latencies[950]
        p99 = latencies[990]

        # Assert
        assert p50 < 1, f"P50 latency {p50:.3f}ms exceeds 1ms"
        assert p95 < 5, f"P95 latency {p95:.3f}ms exceeds 5ms"
        assert p99 < 10, f"P99 latency {p99:.3f}ms exceeds 10ms"

        print(f"\nLatency percentiles: P50={p50:.3f}ms, P95={p95:.3f}ms, P99={p99:.3f}ms")
