# Canvas Learning System - Story 12.A.4 Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Story 12.A.4 - Memory System Injection Tests

Tests for _get_learning_memories() method with:
- AC5: 500ms timeout control
- AC6: 30-second cache mechanism

[Source: docs/stories/story-12.A.4-memory-injection.md#Testing]
[Source: docs/architecture/coding-standards.md#测试规范]
"""

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional

import pytest
from app.services.agent_service import AgentService


@dataclass
class MockLearningMemory:
    """Mock LearningMemory for testing."""
    concept: str
    understanding: str
    score: int
    timestamp: str
    canvas_name: Optional[str] = None
    node_id: Optional[str] = None


class MockLearningMemoryClient:
    """Mock LearningMemoryClient for testing."""

    def __init__(self, delay: float = 0.0, should_fail: bool = False):
        """
        Initialize mock client.

        Args:
            delay: Artificial delay in seconds to simulate slow queries
            should_fail: If True, search_memories raises an exception
        """
        self.delay = delay
        self.should_fail = should_fail
        self.call_count = 0

    async def search_memories(
        self,
        query: str,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None,
        limit: int = 5
    ) -> List[MockLearningMemory]:
        """Mock search_memories with configurable delay."""
        self.call_count += 1

        if self.should_fail:
            raise Exception("Mock search failure")

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        return [
            MockLearningMemory(
                concept="逆否命题",
                understanding="用户理解了基本定义",
                score=75,
                timestamp="2025-12-14T10:00:00Z",
                canvas_name=canvas_name,
                node_id=node_id
            )
        ]

    def format_for_context(self, memories: List[MockLearningMemory], max_chars: int = 1000) -> str:
        """Mock format_for_context."""
        if not memories:
            return ""
        return "\n".join([
            f"[{m.timestamp}] {m.concept} (得分: {m.score}/100)\n  理解: {m.understanding}"
            for m in memories
        ])


class TestMemoryInjection:
    """Story 12.A.4 - Memory System Injection Tests."""

    @pytest.fixture
    def agent_service_with_mock_memory(self):
        """Create AgentService with mock memory client."""
        mock_memory = MockLearningMemoryClient(delay=0.0)
        service = AgentService(memory_client=mock_memory)
        return service, mock_memory

    @pytest.fixture
    def agent_service_with_slow_memory(self):
        """Create AgentService with slow mock memory client (>500ms)."""
        mock_memory = MockLearningMemoryClient(delay=0.7)  # 700ms delay
        service = AgentService(memory_client=mock_memory)
        return service, mock_memory

    @pytest.fixture
    def agent_service_with_failing_memory(self):
        """Create AgentService with failing mock memory client."""
        mock_memory = MockLearningMemoryClient(should_fail=True)
        service = AgentService(memory_client=mock_memory)
        return service, mock_memory

    # ==========================================================================
    # AC6: Cache Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_get_learning_memories_with_cache_hit(self, agent_service_with_mock_memory):
        """AC6: Cache hit scenario - 30s内相同查询应使用缓存."""
        service, mock_memory = agent_service_with_mock_memory

        # First call - should query memory client
        result1 = await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53",
            node_id="node1"
        )
        assert result1 != ""
        assert "逆否命题" in result1
        assert mock_memory.call_count == 1

        # Second call with same parameters - should use cache
        result2 = await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53",
            node_id="node1"
        )
        assert result2 == result1
        assert mock_memory.call_count == 1  # No additional query

    @pytest.mark.asyncio
    async def test_get_learning_memories_cache_expired(self, agent_service_with_mock_memory):
        """AC6: Cache expired scenario - 30秒后应重新查询."""
        service, mock_memory = agent_service_with_mock_memory

        # First call
        await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53",
            node_id="node1"
        )
        assert mock_memory.call_count == 1

        # Expire the cache entry (TTLCache handles TTL internally;
        # for testing, we delete the key to simulate expiration)
        cache_key = "Math53:node1:逆否命题的定义"
        if cache_key in service._memory_cache:
            del service._memory_cache[cache_key]

        # Third call after expiration - should query again
        await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53",
            node_id="node1"
        )
        assert mock_memory.call_count == 2  # Fresh query after expiration

    @pytest.mark.asyncio
    async def test_cache_different_parameters(self, agent_service_with_mock_memory):
        """AC6: Different parameters should not hit cache."""
        service, mock_memory = agent_service_with_mock_memory

        # Query with parameter set 1
        await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53",
            node_id="node1"
        )
        assert mock_memory.call_count == 1

        # Query with different canvas_name - should not hit cache
        await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math54",  # Different canvas
            node_id="node1"
        )
        assert mock_memory.call_count == 2

        # Query with different content - should not hit cache
        await service._get_learning_memories(
            content="充分必要条件",  # Different content
            canvas_name="Math53",
            node_id="node1"
        )
        assert mock_memory.call_count == 3

    # ==========================================================================
    # AC5: Timeout Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_get_learning_memories_timeout(self, agent_service_with_slow_memory):
        """AC5: Timeout scenario - 超过500ms应返回空字符串."""
        service, mock_memory = agent_service_with_slow_memory

        start_time = time.time()
        result = await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53",
            node_id="node1"
        )
        elapsed = time.time() - start_time

        # Should return empty string due to timeout
        assert result == ""
        # Should timeout around 500ms, not wait full 700ms
        assert elapsed < 0.65  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_get_learning_memories_timeout_graceful_degradation(self, agent_service_with_slow_memory):
        """AC5: Timeout graceful degradation - 超时不应阻塞Agent响应."""
        service, mock_memory = agent_service_with_slow_memory

        # Even with timeout, should not raise exception
        try:
            result = await service._get_learning_memories(
                content="逆否命题的定义",
                canvas_name="Math53"
            )
            # Should gracefully return empty string
            assert result == ""
        except asyncio.TimeoutError:
            pytest.fail("TimeoutError should be caught internally, not propagated")

    # ==========================================================================
    # AC6: Performance Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_cache_performance(self, agent_service_with_mock_memory):
        """AC6: Performance test - 缓存命中应 < 10ms."""
        service, mock_memory = agent_service_with_mock_memory

        # First call to populate cache
        await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53",
            node_id="node1"
        )

        # Measure cache hit performance
        iterations = 100
        start_time = time.time()
        for _ in range(iterations):
            await service._get_learning_memories(
                content="逆否命题的定义",
                canvas_name="Math53",
                node_id="node1"
            )
        elapsed = time.time() - start_time

        avg_time_ms = (elapsed / iterations) * 1000
        assert avg_time_ms < 10, f"Cache hit took {avg_time_ms:.2f}ms on average, expected < 10ms"
        assert mock_memory.call_count == 1  # Only first call should query

    # ==========================================================================
    # Graceful Degradation Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_exception(self, agent_service_with_failing_memory):
        """AC4: Exception should not propagate, return empty string."""
        service, mock_memory = agent_service_with_failing_memory

        # Should not raise exception
        result = await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53"
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_graceful_degradation_no_memory_client(self):
        """AC4: No memory client should return empty string."""
        service = AgentService(memory_client=None)

        result = await service._get_learning_memories(
            content="逆否命题的定义",
            canvas_name="Math53"
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_graceful_degradation_empty_content(self, agent_service_with_mock_memory):
        """Empty content should return empty string without query."""
        service, mock_memory = agent_service_with_mock_memory

        result = await service._get_learning_memories(
            content="",
            canvas_name="Math53"
        )
        assert result == ""
        assert mock_memory.call_count == 0  # No query should be made


class TestCacheKeyGeneration:
    """Test cache key generation edge cases."""

    @pytest.mark.asyncio
    async def test_cache_key_with_long_content(self):
        """Cache key should truncate content to 50 chars."""
        mock_memory = MockLearningMemoryClient()
        service = AgentService(memory_client=mock_memory)

        long_content = "A" * 100  # 100 character content

        await service._get_learning_memories(
            content=long_content,
            canvas_name="Math53",
            node_id="node1"
        )

        # Cache key should use truncated content
        expected_key = f"Math53:node1:{long_content[:50]}"
        assert expected_key in service._memory_cache

    @pytest.mark.asyncio
    async def test_cache_key_with_none_values(self):
        """Cache key should handle None values."""
        mock_memory = MockLearningMemoryClient()
        service = AgentService(memory_client=mock_memory)

        await service._get_learning_memories(
            content="测试内容",
            canvas_name=None,
            node_id=None
        )

        expected_key = "None:None:测试内容"
        assert expected_key in service._memory_cache
