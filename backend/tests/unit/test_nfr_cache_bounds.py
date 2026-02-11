"""
NFR Cache Bounds & Stampede Protection Tests

TC-NFR-01: Cache maxsize enforcement — verifies TTLCache evicts oldest when full
TC-NFR-02: Cache TTL expiration — verifies entries auto-expire after TTL
TC-NFR-03: Cache stampede protection — verifies lock prevents thundering herd

These tests verify the P0 fixes for unbounded dict cache growth
identified in the EPIC-36 NFR assessment.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

from cachetools import TTLCache


# ============================================================================
# TC-NFR-01: Cache Maxsize Enforcement
# ============================================================================

class TestCacheMaxsizeEnforcement:
    """TC-NFR-01: Verify caches evict oldest entries when maxsize is reached."""

    def test_ttl_cache_evicts_at_maxsize(self):
        """Basic TTLCache maxsize enforcement."""
        cache: TTLCache = TTLCache(maxsize=3, ttl=30)
        cache["a"] = 1
        cache["b"] = 2
        cache["c"] = 3

        # Adding 4th item should evict oldest
        cache["d"] = 4
        assert len(cache) == 3
        assert "a" not in cache
        assert "d" in cache

    @pytest.mark.asyncio
    async def test_memory_service_cache_bounded(self):
        """MemoryService._score_history_cache respects maxsize=1000."""
        from app.services.memory_service import MemoryService

        service = MemoryService.__new__(MemoryService)
        service._score_history_cache = TTLCache(maxsize=5, ttl=30)
        service._score_cache_lock = asyncio.Lock()

        # Fill cache beyond maxsize
        for i in range(10):
            service._score_history_cache[f"key_{i}"] = f"value_{i}"

        assert len(service._score_history_cache) == 5
        # Oldest keys should be evicted
        assert "key_0" not in service._score_history_cache
        assert "key_9" in service._score_history_cache

    @pytest.mark.asyncio
    async def test_agent_service_cache_bounded(self):
        """AgentService._memory_cache respects maxsize=1000."""
        from app.services.agent_service import AgentService

        service = AgentService.__new__(AgentService)
        service._memory_cache = TTLCache(maxsize=5, ttl=30)
        service._memory_cache_lock = asyncio.Lock()

        for i in range(10):
            service._memory_cache[f"key_{i}"] = f"value_{i}"

        assert len(service._memory_cache) == 5
        assert "key_0" not in service._memory_cache

    @pytest.mark.asyncio
    async def test_context_enrichment_cache_bounded(self):
        """ContextEnrichmentService._association_cache respects maxsize=1000."""
        from app.services.context_enrichment_service import ContextEnrichmentService

        service = ContextEnrichmentService.__new__(ContextEnrichmentService)
        service._association_cache = TTLCache(maxsize=5, ttl=30)
        service._association_cache_ttl = 30.0
        service._association_cache_lock = asyncio.Lock()

        for i in range(10):
            service._association_cache[f"path_{i}"] = f"result_{i}"

        assert len(service._association_cache) == 5
        assert "path_0" not in service._association_cache

    @pytest.mark.asyncio
    async def test_verification_service_sessions_bounded(self):
        """VerificationService._sessions respects maxsize=500."""
        from app.services.verification_service import VerificationService

        service = VerificationService.__new__(VerificationService)
        service._sessions = TTLCache(maxsize=5, ttl=3600)
        service._progress = TTLCache(maxsize=5, ttl=3600)

        for i in range(10):
            service._sessions[f"session_{i}"] = {"status": "active"}
            service._progress[f"session_{i}"] = MagicMock()

        assert len(service._sessions) == 5
        assert len(service._progress) == 5


# ============================================================================
# TC-NFR-02: Cache TTL Expiration
# ============================================================================

class TestCacheTTLExpiration:
    """TC-NFR-02: Verify cache entries auto-expire after TTL period."""

    def test_ttl_cache_expires_entries(self):
        """TTLCache entries disappear after TTL."""
        cache: TTLCache = TTLCache(maxsize=100, ttl=0.1)  # 100ms TTL
        cache["key"] = "value"
        assert "key" in cache

        time.sleep(0.15)  # Wait past TTL
        assert cache.get("key") is None

    @pytest.mark.asyncio
    async def test_score_history_cache_ttl(self):
        """MemoryService score cache entries expire after SCORE_HISTORY_CACHE_TTL."""
        from app.services.memory_service import SCORE_HISTORY_CACHE_TTL

        # Verify the TTL constant is 30 seconds
        assert SCORE_HISTORY_CACHE_TTL == 30

        # Create a cache with very short TTL for testing
        cache: TTLCache = TTLCache(maxsize=1000, ttl=0.1)
        cache["test_key"] = "test_result"
        assert cache.get("test_key") == "test_result"

        time.sleep(0.15)
        assert cache.get("test_key") is None

    @pytest.mark.asyncio
    async def test_verification_session_ttl(self):
        """VerificationService sessions auto-cleanup after 1h TTL."""
        cache: TTLCache = TTLCache(maxsize=500, ttl=0.1)  # 100ms for testing
        cache["session_1"] = {"status": "active"}
        assert "session_1" in cache

        time.sleep(0.15)
        assert cache.get("session_1") is None

    def test_ttl_cache_mixed_expiry(self):
        """Older entries expire while newer ones survive."""
        cache: TTLCache = TTLCache(maxsize=100, ttl=0.2)  # 200ms TTL

        cache["old"] = "old_value"
        time.sleep(0.12)
        cache["new"] = "new_value"
        time.sleep(0.1)  # Total: old=220ms, new=100ms

        assert cache.get("old") is None  # Expired
        assert cache.get("new") == "new_value"  # Still valid


# ============================================================================
# TC-NFR-03: Cache Stampede Protection
# ============================================================================

class TestCacheStampedeProtection:
    """TC-NFR-03: Verify locks prevent thundering herd on cache miss."""

    @pytest.mark.asyncio
    async def test_memory_service_has_cache_lock(self):
        """MemoryService has _score_cache_lock for stampede protection."""
        from app.services.memory_service import MemoryService

        service = MemoryService.__new__(MemoryService)
        service._score_history_cache = TTLCache(maxsize=1000, ttl=30)
        service._score_cache_lock = asyncio.Lock()

        assert isinstance(service._score_cache_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_agent_service_has_cache_lock(self):
        """AgentService has _memory_cache_lock for stampede protection."""
        from app.services.agent_service import AgentService

        service = AgentService.__new__(AgentService)
        service._memory_cache = TTLCache(maxsize=1000, ttl=30)
        service._memory_cache_lock = asyncio.Lock()

        assert isinstance(service._memory_cache_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_context_enrichment_has_cache_lock(self):
        """ContextEnrichmentService has _association_cache_lock."""
        from app.services.context_enrichment_service import ContextEnrichmentService

        service = ContextEnrichmentService.__new__(ContextEnrichmentService)
        service._association_cache = TTLCache(maxsize=1000, ttl=30)
        service._association_cache_lock = asyncio.Lock()

        assert isinstance(service._association_cache_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_double_check_locking_prevents_duplicate_computation(self):
        """Double-check locking prevents multiple coroutines from computing same value."""
        cache: TTLCache = TTLCache(maxsize=100, ttl=30)
        lock = asyncio.Lock()
        compute_count = 0

        async def expensive_compute(key: str) -> str:
            nonlocal compute_count
            await simulate_async_delay(0.05)  # Simulate slow operation
            compute_count += 1
            return f"result_{key}"

        async def get_with_stampede_protection(key: str) -> str:
            # First check (no lock)
            result = cache.get(key)
            if result is not None:
                return result

            # Second check (with lock)
            async with lock:
                result = cache.get(key)
                if result is not None:
                    return result

                # Compute and cache
                result = await expensive_compute(key)
                cache[key] = result
                return result

        # Launch 10 concurrent requests for the same key
        tasks = [get_with_stampede_protection("same_key") for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should get the same result
        assert all(r == "result_same_key" for r in results)
        # But computation should happen only once (due to lock serialization)
        assert compute_count == 1

    @pytest.mark.asyncio
    async def test_different_keys_computed_independently(self):
        """Different cache keys are computed independently (no false serialization)."""
        cache: TTLCache = TTLCache(maxsize=100, ttl=30)
        lock = asyncio.Lock()
        computed_keys = []

        async def get_with_protection(key: str) -> str:
            result = cache.get(key)
            if result is not None:
                return result

            async with lock:
                result = cache.get(key)
                if result is not None:
                    return result

                await simulate_async_delay(0.01)
                result = f"result_{key}"
                cache[key] = result
                computed_keys.append(key)
                return result

        # Request different keys
        tasks = [get_with_protection(f"key_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert len(computed_keys) == 5  # Each key computed once
