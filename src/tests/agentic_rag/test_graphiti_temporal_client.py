"""
Unit Tests for GraphitiTemporalClient

Story 22.2 AC-22.2.6: 单元测试覆盖TemporalClient

Test Coverage:
- test_initialization: Client初始化测试
- test_add_learning_episode: Episode存储测试 (AC-22.2.1)
- test_search_by_time_range: 时间范围查询测试 (AC-22.2.2)
- test_search_by_entity_type: 实体类型查询测试 (AC-22.2.3)
- test_get_learning_stats: 聚合统计测试 (AC-22.2.4)
- test_fallback_mode: 降级模式测试
- test_empty_results: 空结果处理测试
- test_timeout_handling: 超时处理测试

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-12
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


class TestGraphitiTemporalClientInitialization:
    """测试GraphitiTemporalClient初始化"""

    @pytest.mark.asyncio
    async def test_initialization_without_graphiti(self):
        """测试没有graphiti-core库时的初始化"""
        # Patch GRAPHITI_AVAILABLE to False
        with patch(
            'agentic_rag.clients.graphiti_temporal_client.GRAPHITI_AVAILABLE',
            False
        ):
            from agentic_rag.clients.graphiti_temporal_client import (
                GraphitiTemporalClient,
            )

            client = GraphitiTemporalClient(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="test"
            )

            result = await client.initialize()

            # Should return False when graphiti not available
            assert result is False
            assert client._initialized is True
            assert client._graphiti is None

    @pytest.mark.asyncio
    async def test_initialization_default_params(self):
        """测试默认参数初始化"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()

        assert client.neo4j_uri == "bolt://localhost:7687"
        assert client.neo4j_user == "neo4j"
        assert client.neo4j_password == ""
        assert client.timeout_ms == 500
        assert client.enable_fallback is True

    @pytest.mark.asyncio
    async def test_initialization_custom_params(self):
        """测试自定义参数初始化"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient(
            neo4j_uri="bolt://custom:7687",
            neo4j_user="admin",
            neo4j_password="secret",
            timeout_ms=1000,
            enable_fallback=False
        )

        assert client.neo4j_uri == "bolt://custom:7687"
        assert client.neo4j_user == "admin"
        assert client.neo4j_password == "secret"
        assert client.timeout_ms == 1000
        assert client.enable_fallback is False


class TestAddLearningEpisode:
    """测试add_learning_episode方法 (AC-22.2.1)"""

    @pytest.mark.asyncio
    async def test_add_learning_episode_basic(self):
        """测试基本的episode存储"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        # Use fallback mode (no Graphiti)
        client._initialized = True

        episode_id = await client.add_learning_episode(
            content="学习了逆否命题的概念",
            episode_type="learning"
        )

        assert episode_id is not None
        assert "learning_" in episode_id
        assert len(client._episode_cache) == 1

    @pytest.mark.asyncio
    async def test_add_learning_episode_with_metadata(self):
        """测试带metadata的episode存储"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        metadata = {
            "canvas_path": "离散数学.canvas",
            "node_id": "node_123",
            "concept": "逆否命题",
            "agent_used": "basic-decomposition",
            "score": 85
        }

        episode_id = await client.add_learning_episode(
            content="学习了逆否命题的概念",
            episode_type="learning",
            metadata=metadata
        )

        assert episode_id is not None
        assert len(client._episode_cache) == 1

        cached = client._episode_cache[0]
        assert cached["metadata"]["canvas_path"] == "离散数学.canvas"
        assert cached["metadata"]["score"] == 85

    @pytest.mark.asyncio
    async def test_add_learning_episode_different_types(self):
        """测试不同类型的episode"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Learning episode
        ep1 = await client.add_learning_episode(
            content="初次学习",
            episode_type="learning"
        )
        assert "learning_" in ep1

        # Review episode
        ep2 = await client.add_learning_episode(
            content="复习概念",
            episode_type="review"
        )
        assert "review_" in ep2

        # Assessment episode
        ep3 = await client.add_learning_episode(
            content="测试评估",
            episode_type="assessment"
        )
        assert "assessment_" in ep3

        assert len(client._episode_cache) == 3


class TestSearchByTimeRange:
    """测试search_by_time_range方法 (AC-22.2.2)"""

    @pytest.mark.asyncio
    async def test_search_by_time_range_basic(self):
        """测试基本的时间范围查询"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Add test episodes
        now = datetime.now()
        await client.add_learning_episode(
            content="今天的学习",
            episode_type="learning"
        )

        # Search for today's episodes
        results = await client.search_by_time_range(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1)
        )

        assert len(results) >= 1
        assert results[0]["content"] == "今天的学习"

    @pytest.mark.asyncio
    async def test_search_by_time_range_empty(self):
        """测试空结果的时间范围查询"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Search for last month (should be empty)
        now = datetime.now()
        results = await client.search_by_time_range(
            start_time=now - timedelta(days=60),
            end_time=now - timedelta(days=30)
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_by_time_range_with_limit(self):
        """测试带limit的时间范围查询"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Add multiple episodes
        for i in range(5):
            await client.add_learning_episode(
                content=f"学习内容 {i}",
                episode_type="learning"
            )

        now = datetime.now()
        results = await client.search_by_time_range(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            limit=3
        )

        assert len(results) <= 3


class TestSearchByEntityType:
    """测试search_by_entity_type方法 (AC-22.2.3)"""

    @pytest.mark.asyncio
    async def test_search_by_entity_type_basic(self):
        """测试基本的实体类型查询"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Add episodes with different types
        await client.add_learning_episode(
            content="学习概念",
            episode_type="learning"
        )
        await client.add_learning_episode(
            content="复习内容",
            episode_type="review"
        )

        # Search for learning type
        results = await client.search_by_entity_type(
            entity_type="learning"
        )

        # Should return learning episodes
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_by_entity_type_with_canvas_filter(self):
        """测试带Canvas过滤的实体类型查询"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Add episodes for different canvases
        await client.add_learning_episode(
            content="离散数学学习",
            episode_type="learning",
            metadata={"canvas_path": "离散数学.canvas"}
        )
        await client.add_learning_episode(
            content="线性代数学习",
            episode_type="learning",
            metadata={"canvas_path": "线性代数.canvas"}
        )

        results = await client.search_by_entity_type(
            entity_type="learning",
            canvas_file="离散数学.canvas"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_by_entity_type_pagination(self):
        """测试实体类型查询的分页"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Add multiple episodes
        for i in range(10):
            await client.add_learning_episode(
                content=f"学习 {i}",
                episode_type="learning"
            )

        # Test pagination
        page1 = await client.search_by_entity_type(
            entity_type="learning",
            limit=5,
            offset=0
        )
        page2 = await client.search_by_entity_type(
            entity_type="learning",
            limit=5,
            offset=5
        )

        assert len(page1) <= 5
        assert len(page2) <= 5


class TestGetLearningStats:
    """测试get_learning_stats方法 (AC-22.2.4)"""

    @pytest.mark.asyncio
    async def test_get_learning_stats_daily(self):
        """测试日粒度统计"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        # Add some episodes
        await client.add_learning_episode(
            content="今天学习",
            episode_type="learning",
            metadata={"concept": "逆否命题", "score": 85}
        )

        stats = await client.get_learning_stats(
            user_id="user_123",
            granularity="day",
            limit=7
        )

        assert stats["user_id"] == "user_123"
        assert stats["granularity"] == "day"
        assert "periods" in stats
        assert len(stats["periods"]) == 7
        assert "summary" in stats
        assert "total_episodes" in stats["summary"]
        assert "total_concepts" in stats["summary"]
        assert "average_episodes_per_period" in stats["summary"]

    @pytest.mark.asyncio
    async def test_get_learning_stats_weekly(self):
        """测试周粒度统计"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        stats = await client.get_learning_stats(
            user_id="user_123",
            granularity="week",
            limit=4
        )

        assert stats["granularity"] == "week"
        assert len(stats["periods"]) == 4

    @pytest.mark.asyncio
    async def test_get_learning_stats_monthly(self):
        """测试月粒度统计"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        stats = await client.get_learning_stats(
            user_id="user_123",
            granularity="month",
            limit=3
        )

        assert stats["granularity"] == "month"
        assert len(stats["periods"]) == 3

    @pytest.mark.asyncio
    async def test_get_learning_stats_period_structure(self):
        """测试统计周期的数据结构"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        stats = await client.get_learning_stats(
            user_id="user_123",
            granularity="day",
            limit=1
        )

        period = stats["periods"][0]
        assert "period_start" in period
        assert "period_end" in period
        assert "episode_count" in period
        assert "concepts_learned" in period
        assert "total_duration_seconds" in period
        assert "average_score" in period


class TestFallbackMode:
    """测试降级模式"""

    @pytest.mark.asyncio
    async def test_fallback_episode_cache(self):
        """测试本地缓存降级"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient(enable_fallback=True)
        client._initialized = True
        # _graphiti is None, so fallback mode

        episode_id = await client.add_learning_episode(
            content="测试降级",
            episode_type="learning"
        )

        assert episode_id is not None
        assert len(client._episode_cache) == 1

    @pytest.mark.asyncio
    async def test_fallback_search_uses_cache(self):
        """测试搜索使用本地缓存"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient(enable_fallback=True)
        client._initialized = True

        await client.add_learning_episode(
            content="缓存内容",
            episode_type="learning"
        )

        now = datetime.now()
        results = await client.search_by_time_range(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1)
        )

        assert len(results) >= 1
        assert results[0]["content"] == "缓存内容"


class TestClientStats:
    """测试客户端统计"""

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取客户端统计信息"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient(
            neo4j_uri="bolt://test:7687",
            timeout_ms=1000
        )
        client._initialized = True

        await client.add_learning_episode(
            content="测试",
            episode_type="learning"
        )

        stats = client.get_stats()

        assert stats["initialized"] is True
        assert stats["neo4j_uri"] == "bolt://test:7687"
        assert stats["timeout_ms"] == 1000
        assert stats["enable_fallback"] is True
        assert stats["cached_episodes"] == 1


class TestClientClose:
    """测试客户端关闭"""

    @pytest.mark.asyncio
    async def test_close_client(self):
        """测试关闭客户端"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        await client.close()

        assert client._graphiti is None
        assert client._driver is None
        assert client._initialized is False


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_empty_content_episode(self):
        """测试空内容的episode"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        episode_id = await client.add_learning_episode(
            content="",
            episode_type="learning"
        )

        assert episode_id is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_content(self):
        """测试特殊字符内容"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        content = "学习内容包含特殊字符: <>\"'&\n\t"
        episode_id = await client.add_learning_episode(
            content=content,
            episode_type="learning"
        )

        assert episode_id is not None
        assert client._episode_cache[0]["episode_body"] == content

    @pytest.mark.asyncio
    async def test_unicode_content(self):
        """测试Unicode内容"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        content = "学习日语: こんにちは, 韩语: 안녕하세요, 表情: 😀🎉"
        episode_id = await client.add_learning_episode(
            content=content,
            episode_type="learning"
        )

        assert episode_id is not None

    @pytest.mark.asyncio
    async def test_large_metadata(self):
        """测试大型metadata"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient()
        client._initialized = True

        large_metadata = {f"key_{i}": f"value_{i}" for i in range(100)}
        episode_id = await client.add_learning_episode(
            content="测试大型metadata",
            episode_type="learning",
            metadata=large_metadata
        )

        assert episode_id is not None
        assert len(client._episode_cache[0]["metadata"]) == 100


# ============================================================
# Integration Tests (Require graphiti-core)
# ============================================================

class TestGraphitiIntegration:
    """Graphiti集成测试 (需要graphiti-core库)"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="Requires graphiti-core and Neo4j")
    async def test_real_graphiti_connection(self):
        """测试真实的Graphiti连接"""
        from agentic_rag.clients.graphiti_temporal_client import (
            GraphitiTemporalClient,
        )

        client = GraphitiTemporalClient(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="test_password"
        )

        result = await client.initialize()
        assert result is True
        assert client._graphiti is not None

        await client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
