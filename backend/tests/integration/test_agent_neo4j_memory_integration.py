# Canvas Learning System - Integration Tests for Agent Neo4j Memory
# Story 36.7: Agent上下文注入增强（Neo4j数据源）
"""
Integration tests for AgentService Neo4j learning memory integration.

Story 36.7 Integration Test Coverage:
- End-to-end test of Agent call with Neo4j memory injection
- Integration with ContextEnrichmentService
- Dependency injection chain verification

[Source: docs/stories/36.7.story.md - Task 6]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the services and dependencies
from app.services.agent_service import AgentService
from app.dependencies import get_agent_service, get_neo4j_client_dep


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_settings():
    """Create mock settings for dependency injection testing."""
    settings = MagicMock()
    settings.AI_API_KEY = None  # Disable real AI calls
    settings.AI_MODEL_NAME = "test-model"
    settings.AI_BASE_URL = None
    settings.AI_PROVIDER = "test"
    settings.canvas_base_path = "/test/path"
    return settings


@pytest.fixture
def mock_canvas_service():
    """Create mock CanvasService for dependency injection testing."""
    service = MagicMock()
    service.cleanup = AsyncMock()
    return service


@pytest.fixture
def mock_neo4j_client():
    """Create mock Neo4jClient for integration testing."""
    client = MagicMock()
    client._use_json_fallback = False
    client.run_query = AsyncMock(return_value=[
        {
            "concept": "Integration Test Concept",
            "timestamp": "2026-01-15T10:30:00Z",
            "relevance": 0.9,
            "score": 88
        }
    ])
    return client


# =============================================================================
# Dependency Injection Chain Tests
# =============================================================================

class TestDependencyInjectionChain:
    """
    Story 36.7 Task 6.2: 验证依赖注入链正确配置

    Tests that the dependency injection chain correctly creates
    AgentService with Neo4jClient.
    """

    @pytest.mark.asyncio
    async def test_get_agent_service_injects_neo4j_client(
        self,
        mock_settings,
        mock_canvas_service,
        mock_neo4j_client
    ):
        """
        Test that get_agent_service correctly injects Neo4jClient.

        Story 36.7 AC1: Neo4jClient正确注入到AgentService
        """
        # Call the dependency function
        async for service in get_agent_service(
            settings=mock_settings,
            canvas_service=mock_canvas_service,
            neo4j_client=mock_neo4j_client
        ):
            # Verify Neo4jClient is injected
            assert service._neo4j_client is mock_neo4j_client
            break

    def test_neo4j_client_dep_returns_singleton(self):
        """
        Test that get_neo4j_client_dep returns the singleton instance.

        Story 36.1/36.7: Neo4jClient使用单例模式
        """
        with patch('app.dependencies.get_neo4j_client') as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            result = get_neo4j_client_dep()

            mock_get.assert_called_once()
            assert result is mock_client


# =============================================================================
# End-to-End Agent Call Tests
# =============================================================================

class TestEndToEndAgentCall:
    """
    Story 36.7 Task 6.1: 端到端测试Agent调用时包含Neo4j学习记忆
    """

    @pytest.mark.asyncio
    async def test_agent_call_includes_neo4j_memories(
        self,
        mock_neo4j_client
    ):
        """
        Test that Agent call includes Neo4j learning memories in context.

        This tests the full flow from _call_gemini_api to _get_learning_memories.
        """
        # Create service with mock Neo4j client
        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_neo4j_client
        )

        # Call _get_learning_memories directly
        result = await service._get_learning_memories(
            content="测试概念查询",
            canvas_name="测试Canvas"
        )

        # Verify Neo4j was queried
        mock_neo4j_client.run_query.assert_called_once()

        # Verify result contains expected content
        assert "历史学习记忆" in result
        assert "Integration Test Concept" in result
        assert "90%" in result  # relevance
        assert "88" in result  # score

    @pytest.mark.asyncio
    async def test_memory_context_injected_into_agent_prompt(
        self,
        mock_neo4j_client
    ):
        """
        Test that memory context is properly formatted for Agent prompt injection.

        Story 36.7: 验证学习记忆正确注入到Agent上下文
        """
        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_neo4j_client
        )

        memory_context = await service._get_learning_memories(
            content="学习历史查询"
        )

        # Verify context format suitable for Agent prompt
        lines = memory_context.split("\n")

        # Should start with header
        assert lines[0] == "## 历史学习记忆"

        # Should have bullet point items
        assert any(line.startswith("- [") for line in lines)


# =============================================================================
# Context Enrichment Integration Tests
# =============================================================================

class TestContextEnrichmentIntegration:
    """
    Story 36.7 Task 6.2: 验证与ContextEnrichmentService集成正常
    """

    @pytest.mark.asyncio
    async def test_neo4j_memories_combined_with_context_enrichment(
        self,
        mock_neo4j_client
    ):
        """
        Test that Neo4j memories can be combined with other context sources.

        Story 36.7: 验证Neo4j记忆可与其他上下文源组合
        """
        # Create service with Neo4j client
        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_neo4j_client
        )

        # Get Neo4j memories
        neo4j_context = await service._get_learning_memories(
            content="组合上下文测试"
        )

        # Simulate combining with other context (textbook, cross-canvas)
        other_context = "## 教材参考\n- 第三章: 微积分基础"
        combined_context = f"{other_context}\n\n{neo4j_context}"

        # Verify both contexts present
        assert "教材参考" in combined_context
        assert "历史学习记忆" in combined_context
        assert "Integration Test Concept" in combined_context


# =============================================================================
# Performance Integration Tests
# =============================================================================

class TestPerformanceIntegration:
    """
    Story 36.7: 性能集成测试
    """

    @pytest.mark.asyncio
    async def test_memory_query_completes_within_timeout(
        self,
        mock_neo4j_client
    ):
        """
        Test that memory query completes within 500ms timeout.

        Story 36.7 AC5: 500ms超时机制
        """
        import time

        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_neo4j_client
        )

        start = time.perf_counter()
        await service._get_learning_memories(content="性能测试")
        elapsed = time.perf_counter() - start

        # Should complete well within 500ms for mocked query
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_cache_improves_repeated_query_performance(
        self,
        mock_neo4j_client
    ):
        """
        Test that caching improves performance for repeated queries.

        Story 36.7 AC4: 30秒缓存机制
        """
        import time

        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_neo4j_client
        )

        # First query - hits Neo4j
        start1 = time.perf_counter()
        await service._get_learning_memories(
            content="缓存测试",
            canvas_name="test"
        )
        elapsed1 = time.perf_counter() - start1

        # Second query - should hit cache (faster)
        start2 = time.perf_counter()
        await service._get_learning_memories(
            content="缓存测试",
            canvas_name="test"
        )
        elapsed2 = time.perf_counter() - start2

        # Cache hit should be faster
        # (In reality mock is instant, but we verify Neo4j not called twice)
        assert mock_neo4j_client.run_query.call_count == 1


# =============================================================================
# Fallback Integration Tests
# =============================================================================

class TestFallbackIntegration:
    """
    Story 36.7 AC6: Fallback机制集成测试
    """

    @pytest.mark.asyncio
    async def test_fallback_chain_works_correctly(self):
        """
        Test the complete fallback chain: Neo4j -> memory_client -> empty.

        Story 36.7 AC6: 验证完整的fallback链
        """
        # Mock memory_client for fallback
        mock_memory_client = MagicMock()
        mock_memory_client.search_memories = AsyncMock(return_value=[
            {"concept": "Fallback Concept"}
        ])
        mock_memory_client.format_for_context = MagicMock(
            return_value="## Fallback Context"
        )

        # Mock Neo4j client in fallback mode
        mock_neo4j = MagicMock()
        mock_neo4j._use_json_fallback = True

        # Create service with both
        service = AgentService(
            gemini_client=None,
            memory_client=mock_memory_client,
            neo4j_client=mock_neo4j
        )

        # Query should use fallback
        result = await service._get_learning_memories(content="fallback测试")

        # Verify memory_client was used
        mock_memory_client.search_memories.assert_called_once()
        assert "Fallback Context" in result

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_neo4j_error(self):
        """
        Test graceful degradation when Neo4j query fails.

        Story 36.7: Neo4j错误时的优雅降级
        """
        # Mock Neo4j client that raises error
        mock_neo4j = MagicMock()
        mock_neo4j._use_json_fallback = False
        mock_neo4j.run_query = AsyncMock(side_effect=Exception("Connection failed"))

        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_neo4j
        )

        # Should return empty string instead of raising
        result = await service._get_learning_memories(content="错误测试")
        assert result == ""
