# Canvas Learning System - Unit Tests for Agent Service Neo4j Memory Integration
# Story 36.7: Agent上下文注入增强（Neo4j数据源）
"""
Unit tests for AgentService Neo4j learning memory integration.

Story 36.7 Test Coverage:
- AC1: Neo4jClient injection
- AC2: Neo4j Cypher query execution
- AC3: Relevance sorting and top 5 limit
- AC4: 30-second cache mechanism
- AC5: 500ms timeout with graceful degradation
- AC6: Fallback to JSON storage when NEO4J_MOCK=true

[Source: docs/stories/36.7.story.md - Task 5]
"""

import asyncio
import pytest
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Import the service to test
from app.services.agent_service import AgentService


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_neo4j_client():
    """
    Create a mock Neo4jClient for testing.

    Story 36.7 AC1: Neo4jClient injection test support.
    """
    client = MagicMock()
    client._use_json_fallback = False  # Simulate real Neo4j mode
    client.run_query = AsyncMock()
    return client


@pytest.fixture
def mock_neo4j_client_json_fallback():
    """
    Create a mock Neo4jClient in JSON fallback mode.

    Story 36.7 AC6: Fallback mode test support.
    """
    client = MagicMock()
    client._use_json_fallback = True  # Simulate JSON fallback mode
    client.run_query = AsyncMock()
    return client


@pytest.fixture
def mock_memory_client():
    """Create a mock LearningMemoryClient for fallback testing."""
    client = MagicMock()
    client.search_memories = AsyncMock(return_value=[
        {"concept": "fallback_concept", "score": 80}
    ])
    client.format_for_context = MagicMock(return_value="## Fallback Memory Context")
    return client


@pytest.fixture
def agent_service_with_neo4j(mock_neo4j_client):
    """
    Create AgentService with Neo4jClient for AC1 testing.

    Story 36.7 AC1: Tests that Neo4jClient is correctly injected.
    """
    return AgentService(
        gemini_client=None,
        memory_client=None,
        canvas_service=None,
        neo4j_client=mock_neo4j_client
    )


@pytest.fixture
def agent_service_with_fallback(mock_neo4j_client_json_fallback, mock_memory_client):
    """
    Create AgentService with Neo4jClient in fallback mode.

    Story 36.7 AC6: Tests fallback to memory_client.
    """
    return AgentService(
        gemini_client=None,
        memory_client=mock_memory_client,
        canvas_service=None,
        neo4j_client=mock_neo4j_client_json_fallback
    )


@pytest.fixture
def sample_neo4j_results():
    """Sample Neo4j query results for testing."""
    return [
        {
            "concept": "微积分基础",
            "timestamp": "2026-01-15T10:30:00Z",
            "relevance": 0.95,
            "score": 85,
            "user_understanding": "理解了导数的基本概念"
        },
        {
            "concept": "极限定义",
            "timestamp": "2026-01-14T14:20:00Z",
            "relevance": 0.88,
            "score": 78,
            "user_understanding": "掌握了极限的ε-δ定义"
        },
        {
            "concept": "连续性",
            "timestamp": "2026-01-13T09:15:00Z",
            "relevance": 0.75,
            "score": 92,
            "user_understanding": None
        }
    ]


# =============================================================================
# AC1: Neo4jClient注入 Tests
# =============================================================================

class TestAC1Neo4jClientInjection:
    """
    Story 36.7 AC1: Neo4jClient注入测试

    Tests that _get_learning_memories() correctly uses the injected Neo4jClient.
    """

    def test_neo4j_client_stored_on_init(self, mock_neo4j_client):
        """Test that Neo4jClient is stored in AgentService._neo4j_client"""
        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_neo4j_client
        )
        assert service._neo4j_client is mock_neo4j_client

    def test_neo4j_client_none_graceful(self):
        """Test that AgentService works without Neo4jClient"""
        service = AgentService(
            gemini_client=None,
            neo4j_client=None
        )
        assert service._neo4j_client is None

    @pytest.mark.asyncio
    async def test_neo4j_client_used_for_query(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client,
        sample_neo4j_results
    ):
        """Test that Neo4jClient.run_query is called when available"""
        mock_neo4j_client.run_query.return_value = sample_neo4j_results

        result = await agent_service_with_neo4j._get_learning_memories(
            content="微积分",
            canvas_name="数学笔记"
        )

        # Verify run_query was called
        mock_neo4j_client.run_query.assert_called_once()

        # Verify result contains expected content
        assert "历史学习记忆" in result
        assert "微积分基础" in result


# =============================================================================
# AC2: 真实Neo4j查询 Tests
# =============================================================================

class TestAC2Neo4jQuery:
    """
    Story 36.7 AC2: 真实Neo4j查询测试

    Tests that Cypher queries are correctly constructed and executed.
    """

    @pytest.mark.asyncio
    async def test_cypher_query_structure(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client
    ):
        """Test that Cypher query contains correct clauses"""
        mock_neo4j_client.run_query.return_value = []

        await agent_service_with_neo4j._query_neo4j_memories(
            content="导数计算",
            canvas_name="高等数学"
        )

        # Get the query that was passed
        call_args = mock_neo4j_client.run_query.call_args
        query = call_args[0][0]  # First positional argument is the query

        # Verify query structure
        assert "MATCH (m:LearningMemory)" in query
        assert "WHERE m.content CONTAINS $query_text" in query
        assert "ORDER BY m.relevance DESC" in query
        assert "LIMIT 5" in query

    @pytest.mark.asyncio
    async def test_query_params_passed_correctly(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client
    ):
        """Test that query parameters are correctly passed"""
        mock_neo4j_client.run_query.return_value = []

        await agent_service_with_neo4j._query_neo4j_memories(
            content="微积分基础概念",
            canvas_name="数学Canvas"
        )

        call_args = mock_neo4j_client.run_query.call_args
        kwargs = call_args[1]  # Keyword arguments

        assert kwargs["query_text"] == "微积分基础概念"
        assert kwargs["canvas_name"] == "数学Canvas"


# =============================================================================
# AC3: Relevance排序 Tests
# =============================================================================

class TestAC3RelevanceSorting:
    """
    Story 36.7 AC3: Relevance排序测试

    Tests that results are sorted by relevance and limited to top 5.
    """

    @pytest.mark.asyncio
    async def test_cypher_query_has_order_by_relevance(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client
    ):
        """Test that query contains ORDER BY relevance DESC"""
        mock_neo4j_client.run_query.return_value = []

        await agent_service_with_neo4j._query_neo4j_memories("test", None)

        query = mock_neo4j_client.run_query.call_args[0][0]
        assert "ORDER BY m.relevance DESC" in query

    @pytest.mark.asyncio
    async def test_cypher_query_has_limit_5(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client
    ):
        """Test that query contains LIMIT 5"""
        mock_neo4j_client.run_query.return_value = []

        await agent_service_with_neo4j._query_neo4j_memories("test", None)

        query = mock_neo4j_client.run_query.call_args[0][0]
        assert "LIMIT 5" in query


# =============================================================================
# AC4: 30秒缓存 Tests
# =============================================================================

class TestAC4CacheMechanism:
    """
    Story 36.7 AC4: 30秒缓存机制测试

    Tests that memory results are cached for 30 seconds.
    """

    @pytest.mark.asyncio
    async def test_cache_hit_on_second_query(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client,
        sample_neo4j_results
    ):
        """Test that second identical query hits cache"""
        mock_neo4j_client.run_query.return_value = sample_neo4j_results

        # First query - should call Neo4j
        result1 = await agent_service_with_neo4j._get_learning_memories(
            content="微积分",
            canvas_name="数学",
            node_id="node123"
        )

        # Second query - should hit cache
        result2 = await agent_service_with_neo4j._get_learning_memories(
            content="微积分",
            canvas_name="数学",
            node_id="node123"
        )

        # Neo4j should only be called once
        assert mock_neo4j_client.run_query.call_count == 1

        # Both results should be the same
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_cache_expires_after_30_seconds(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client,
        sample_neo4j_results
    ):
        """Test that cache expires after 30 seconds"""
        mock_neo4j_client.run_query.return_value = sample_neo4j_results

        # First query
        await agent_service_with_neo4j._get_learning_memories(
            content="微积分",
            canvas_name="数学"
        )

        # Simulate cache expiration (TTLCache handles TTL internally;
        # for testing, delete the key to simulate expiration)
        cache_key = "数学:None:微积分"
        if cache_key in agent_service_with_neo4j._memory_cache:
            del agent_service_with_neo4j._memory_cache[cache_key]

        # Second query - should call Neo4j again due to expired cache
        await agent_service_with_neo4j._get_learning_memories(
            content="微积分",
            canvas_name="数学"
        )

        # Neo4j should be called twice (cache expired)
        assert mock_neo4j_client.run_query.call_count == 2


# =============================================================================
# AC5: 500ms超时 Tests
# =============================================================================

class TestAC5TimeoutMechanism:
    """
    Story 36.7 AC5: 500ms超时机制测试

    Tests that queries timeout after 500ms with graceful degradation.
    """

    @pytest.mark.asyncio
    async def test_timeout_returns_empty_string(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client
    ):
        """Test that timeout returns empty string (graceful degradation)"""
        # Make run_query take longer than 500ms
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(1.0)  # 1 second delay
            return []

        mock_neo4j_client.run_query = slow_query

        result = await agent_service_with_neo4j._get_learning_memories(
            content="slow query test"
        )

        # Should return empty string on timeout
        assert result == ""

    @pytest.mark.asyncio
    async def test_fast_query_returns_results(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client,
        sample_neo4j_results
    ):
        """Test that fast query returns results normally"""
        mock_neo4j_client.run_query.return_value = sample_neo4j_results

        result = await agent_service_with_neo4j._get_learning_memories(
            content="fast query test"
        )

        # Should return formatted results
        assert "历史学习记忆" in result


# =============================================================================
# AC6: Fallback机制 Tests
# =============================================================================

class TestAC6FallbackMechanism:
    """
    Story 36.7 AC6: Fallback机制测试

    Tests that system falls back to memory_client when Neo4j is unavailable.
    """

    @pytest.mark.asyncio
    async def test_fallback_when_json_fallback_mode(
        self,
        agent_service_with_fallback,
        mock_memory_client
    ):
        """Test fallback to memory_client when NEO4J_MOCK=true"""
        result = await agent_service_with_fallback._get_learning_memories(
            content="fallback test"
        )

        # Verify memory_client was used
        mock_memory_client.search_memories.assert_called_once()

        # Verify result contains fallback content
        assert "Fallback Memory Context" in result

    @pytest.mark.asyncio
    async def test_no_fallback_when_neo4j_available(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client,
        sample_neo4j_results
    ):
        """Test that Neo4j is used when available (no fallback)"""
        mock_neo4j_client.run_query.return_value = sample_neo4j_results

        result = await agent_service_with_neo4j._get_learning_memories(
            content="neo4j test"
        )

        # Verify Neo4j was used
        mock_neo4j_client.run_query.assert_called_once()

        # Verify result contains Neo4j content
        assert "微积分基础" in result


# =============================================================================
# Memory Formatting Tests
# =============================================================================

class TestMemoryFormatting:
    """
    Tests for _format_learning_memories() method.

    Story 36.7: LearningMemory数据结构格式化测试
    """

    def test_format_empty_memories(self, agent_service_with_neo4j):
        """Test formatting empty memory list"""
        result = agent_service_with_neo4j._format_learning_memories([])
        assert result == ""

    def test_format_single_memory(self, agent_service_with_neo4j):
        """Test formatting single memory item"""
        memories = [{
            "concept": "测试概念",
            "timestamp": "2026-01-15T10:30:00Z",
            "relevance": 0.85,
            "score": 90
        }]

        result = agent_service_with_neo4j._format_learning_memories(memories)

        assert "## 历史学习记忆" in result
        assert "测试概念" in result
        assert "85%" in result  # relevance formatted as percentage
        assert "90" in result  # score

    def test_format_memory_with_none_score(self, agent_service_with_neo4j):
        """Test formatting memory with None score"""
        memories = [{
            "concept": "未评分概念",
            "timestamp": "2026-01-15T10:30:00Z",
            "relevance": 0.75,
            "score": None
        }]

        result = agent_service_with_neo4j._format_learning_memories(memories)

        assert "N/A" in result  # None score shows as N/A

    def test_format_multiple_memories(self, agent_service_with_neo4j, sample_neo4j_results):
        """Test formatting multiple memory items"""
        result = agent_service_with_neo4j._format_learning_memories(sample_neo4j_results)

        # Should contain all concepts
        assert "微积分基础" in result
        assert "极限定义" in result
        assert "连续性" in result

        # Should be formatted as bullet list
        assert result.count("- [") == 3


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """
    Edge case and error handling tests.

    Story 36.7: 边界情况和错误处理测试
    """

    @pytest.mark.asyncio
    async def test_empty_content_returns_empty(self, agent_service_with_neo4j):
        """Test that empty content returns empty string"""
        result = await agent_service_with_neo4j._get_learning_memories(
            content=""
        )
        assert result == ""

    @pytest.mark.asyncio
    async def test_neo4j_query_error_returns_empty(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client
    ):
        """Test that Neo4j query error returns empty string"""
        mock_neo4j_client.run_query.side_effect = Exception("Neo4j connection failed")

        result = await agent_service_with_neo4j._get_learning_memories(
            content="error test"
        )

        assert result == ""

    @pytest.mark.asyncio
    async def test_no_neo4j_no_memory_client_returns_empty(self):
        """Test that service with no clients returns empty"""
        service = AgentService(
            gemini_client=None,
            memory_client=None,
            neo4j_client=None
        )

        result = await service._get_learning_memories(content="test")
        assert result == ""

    @pytest.mark.asyncio
    async def test_long_content_truncated(
        self,
        agent_service_with_neo4j,
        mock_neo4j_client
    ):
        """Test that long content is truncated to 100 chars for query"""
        mock_neo4j_client.run_query.return_value = []

        long_content = "x" * 200  # 200 character content

        await agent_service_with_neo4j._query_neo4j_memories(
            content=long_content
        )

        # Check that query_text param is truncated
        kwargs = mock_neo4j_client.run_query.call_args[1]
        assert len(kwargs["query_text"]) == 100


# =============================================================================
# Integration with Dependencies Tests
# =============================================================================

class TestDependencyIntegration:
    """
    Tests for dependency injection integration.

    Story 36.7 AC1: 验证依赖注入正确配置
    """

    def test_agent_service_accepts_neo4j_client_param(self):
        """Test that AgentService constructor accepts neo4j_client parameter"""
        mock_client = MagicMock()

        # This should not raise an error
        service = AgentService(
            gemini_client=None,
            neo4j_client=mock_client
        )

        assert service._neo4j_client is mock_client

    def test_agent_service_logs_neo4j_client_status(self, caplog):
        """Test that AgentService logs Neo4jClient injection status"""
        import logging

        with caplog.at_level(logging.DEBUG):
            mock_client = MagicMock()
            AgentService(
                gemini_client=None,
                neo4j_client=mock_client
            )

        # Check that logging occurred (actual log message may vary)
        assert len(caplog.records) > 0
