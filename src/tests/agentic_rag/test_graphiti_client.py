"""
GraphitiClient 单元测试

Story 12.1: Graphiti时序知识图谱集成
- AC 1.1: Graphiti MCP client初始化
- AC 1.2: search_nodes接口封装
- AC 1.3: 错误处理和超时
- AC 1.4: 结果转换为SearchResult

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

# Import the client under test
from src.agentic_rag.clients.graphiti_client import GraphitiClient

# ============================================================
# Story 12.1 AC 1.1: Graphiti MCP client初始化
# ============================================================

class TestGraphitiClientInitialization:
    """测试 GraphitiClient 初始化"""

    def test_default_initialization(self):
        """AC 1.1: 默认参数初始化"""
        client = GraphitiClient()

        assert client.timeout_ms == 200
        assert client.batch_size == 10
        assert client.enable_fallback is True
        assert client._initialized is False
        assert client._mcp_available is False

    def test_custom_initialization(self):
        """AC 1.1: 自定义参数初始化"""
        client = GraphitiClient(
            timeout_ms=500,
            batch_size=20,
            enable_fallback=False
        )

        assert client.timeout_ms == 500
        assert client.batch_size == 20
        assert client.enable_fallback is False

    @pytest.mark.asyncio
    async def test_initialize_without_mcp(self):
        """AC 1.1: 无MCP环境初始化（fallback模式）"""
        client = GraphitiClient()

        # MCP tools not available in test environment
        result = await client.initialize()

        assert client._initialized is True
        assert client._mcp_available is False
        assert result is False  # MCP not available

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized_flag(self):
        """AC 1.1: 初始化后设置initialized标志"""
        client = GraphitiClient()

        await client.initialize()

        assert client._initialized is True


# ============================================================
# Story 12.1 AC 1.2: search_nodes接口封装
# ============================================================

class TestGraphitiClientSearchNodes:
    """测试 search_nodes 接口"""

    @pytest.mark.asyncio
    async def test_search_nodes_returns_list(self):
        """AC 1.2: search_nodes返回列表"""
        client = GraphitiClient()
        await client.initialize()

        results = await client.search_nodes("逆否命题")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_nodes_with_canvas_file(self):
        """AC 1.2: search_nodes支持canvas_file过滤"""
        client = GraphitiClient()
        await client.initialize()

        results = await client.search_nodes(
            query="逆否命题",
            canvas_file="离散数学.canvas"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_nodes_with_entity_types(self):
        """AC 1.2: search_nodes支持entity_types过滤"""
        client = GraphitiClient()
        await client.initialize()

        results = await client.search_nodes(
            query="逆否命题",
            entity_types=["concept", "topic"]
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_nodes_respects_num_results(self):
        """AC 1.2: search_nodes尊重num_results参数"""
        client = GraphitiClient()
        await client.initialize()

        results = await client.search_nodes(
            query="逆否命题",
            num_results=5
        )

        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_search_nodes_auto_initializes(self):
        """AC 1.2: search_nodes自动初始化"""
        client = GraphitiClient()
        # Don't call initialize()

        results = await client.search_nodes("逆否命题")

        assert client._initialized is True
        assert isinstance(results, list)


# ============================================================
# Story 12.1 AC 1.3: 错误处理和超时
# ============================================================

class TestGraphitiClientErrorHandling:
    """测试错误处理和超时"""

    @pytest.mark.asyncio
    async def test_timeout_returns_empty_with_fallback(self):
        """AC 1.3: 超时时启用fallback返回空列表"""
        client = GraphitiClient(timeout_ms=1, enable_fallback=True)
        await client.initialize()

        # Force MCP available to trigger timeout path
        client._mcp_available = True

        with patch.object(client, '_search_via_mcp', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = asyncio.TimeoutError()

            results = await client.search_nodes("测试")

            assert results == []

    @pytest.mark.asyncio
    async def test_timeout_raises_without_fallback(self):
        """AC 1.3: 超时时禁用fallback抛出异常"""
        client = GraphitiClient(timeout_ms=1, enable_fallback=False)
        await client.initialize()

        client._mcp_available = True

        with patch.object(client, '_search_via_mcp', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await client.search_nodes("测试")

    @pytest.mark.asyncio
    async def test_error_returns_empty_with_fallback(self):
        """AC 1.3: 错误时启用fallback返回空列表"""
        client = GraphitiClient(enable_fallback=True)
        await client.initialize()

        client._mcp_available = True

        with patch.object(client, '_search_via_mcp', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("Test error")

            results = await client.search_nodes("测试")

            assert results == []

    @pytest.mark.asyncio
    async def test_error_raises_without_fallback(self):
        """AC 1.3: 错误时禁用fallback抛出异常"""
        client = GraphitiClient(enable_fallback=False)
        await client.initialize()

        client._mcp_available = True

        with patch.object(client, '_search_via_mcp', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("Test error")

            with pytest.raises(Exception) as excinfo:
                await client.search_nodes("测试")

            assert "Test error" in str(excinfo.value)


# ============================================================
# Story 12.1 AC 1.4: 结果转换为SearchResult
# ============================================================

class TestGraphitiClientResultConversion:
    """测试结果转换"""

    def test_convert_to_search_results_basic(self):
        """AC 1.4: 基本结果转换"""
        client = GraphitiClient()

        raw_results = [
            {
                "id": "node_001",
                "content": "逆否命题的定义",
                "score": 0.89,
                "_graphiti_type": "node"
            }
        ]

        results = client._convert_to_search_results(raw_results)

        assert len(results) == 1
        assert results[0]["doc_id"].startswith("graphiti_")
        assert results[0]["content"] == "逆否命题的定义"
        assert results[0]["score"] == 0.89
        assert results[0]["metadata"]["source"] == "graphiti"
        assert results[0]["metadata"]["graphiti_type"] == "node"

    def test_convert_to_search_results_with_canvas_file(self):
        """AC 1.4: 转换时包含canvas_file"""
        client = GraphitiClient()

        raw_results = [
            {"id": "node_001", "content": "测试内容", "score": 0.9}
        ]

        results = client._convert_to_search_results(
            raw_results,
            canvas_file="离散数学.canvas"
        )

        assert results[0]["metadata"]["canvas_file"] == "离散数学.canvas"

    def test_convert_to_search_results_respects_num_results(self):
        """AC 1.4: 转换时尊重num_results限制"""
        client = GraphitiClient()

        raw_results = [
            {"id": f"node_{i}", "content": f"内容{i}"} for i in range(10)
        ]

        results = client._convert_to_search_results(raw_results, num_results=5)

        assert len(results) == 5

    def test_convert_to_search_results_score_normalization(self):
        """AC 1.4: 分数归一化到[0,1]"""
        client = GraphitiClient()

        raw_results = [
            {"id": "1", "content": "test", "score": 1.5},  # Above 1
            {"id": "2", "content": "test", "score": -0.5},  # Below 0
            {"id": "3", "content": "test", "score": 0.5},   # Normal
        ]

        results = client._convert_to_search_results(raw_results)

        assert results[0]["score"] == 1.0  # Capped at 1
        assert results[1]["score"] == 0.0  # Capped at 0
        assert results[2]["score"] == 0.5  # Unchanged

    def test_convert_to_search_results_fallback_score(self):
        """AC 1.4: 无分数时使用排名倒推"""
        client = GraphitiClient()

        raw_results = [
            {"id": "1", "content": "test"},  # No score
            {"id": "2", "content": "test"},
            {"id": "3", "content": "test"},
        ]

        results = client._convert_to_search_results(raw_results)

        # Scores should decrease by 0.05 per rank
        assert results[0]["score"] == 1.0
        assert results[1]["score"] == 0.95
        assert results[2]["score"] == 0.90

    def test_convert_to_search_results_extracts_content(self):
        """AC 1.4: 从多个字段提取content"""
        client = GraphitiClient()

        # Test different content field names
        test_cases = [
            {"id": "1", "content": "from content"},
            {"id": "2", "text": "from text"},
            {"id": "3", "name": "from name"},
            {"id": "4", "fact": "from fact"},
        ]

        for tc in test_cases:
            results = client._convert_to_search_results([tc])
            expected = tc.get("content") or tc.get("text") or tc.get("name") or tc.get("fact")
            assert results[0]["content"] == expected

    def test_convert_to_search_results_preserves_metadata(self):
        """AC 1.4: 保留额外的metadata字段"""
        client = GraphitiClient()

        raw_results = [
            {
                "id": "node_001",
                "content": "测试",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-02T00:00:00",
                "entity_type": "concept",
                "importance": 0.8,
                "_graphiti_type": "node"
            }
        ]

        results = client._convert_to_search_results(raw_results)

        assert results[0]["metadata"]["created_at"] == "2025-01-01T00:00:00"
        assert results[0]["metadata"]["updated_at"] == "2025-01-02T00:00:00"
        assert results[0]["metadata"]["entity_type"] == "concept"
        assert results[0]["metadata"]["importance"] == 0.8


# ============================================================
# Additional Tests: Convenience Methods
# ============================================================

class TestGraphitiClientConvenienceMethods:
    """测试便捷方法"""

    @pytest.mark.asyncio
    async def test_search_memories(self):
        """search_memories是search_nodes的便捷包装"""
        client = GraphitiClient()
        await client.initialize()

        results = await client.search_memories("测试查询", num_results=5)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_weak_concepts(self):
        """get_weak_concepts获取薄弱概念"""
        client = GraphitiClient()
        await client.initialize()

        results = await client.get_weak_concepts(
            canvas_file="离散数学.canvas",
            threshold=0.5
        )

        assert isinstance(results, list)

    def test_get_stats(self):
        """get_stats返回客户端统计信息"""
        client = GraphitiClient(timeout_ms=300, batch_size=15)

        stats = client.get_stats()

        assert stats["initialized"] is False
        assert stats["mcp_available"] is False
        assert stats["timeout_ms"] == 300
        assert stats["batch_size"] == 15
        assert stats["enable_fallback"] is True


# ============================================================
# Integration Tests with Mock MCP
# ============================================================

class TestGraphitiClientWithMockMCP:
    """使用Mock MCP的集成测试"""

    @pytest.mark.asyncio
    async def test_search_with_mock_mcp_results(self, sample_graphiti_results):
        """使用Mock MCP结果测试完整流程"""
        client = GraphitiClient()
        await client.initialize()

        # Simulate MCP available
        client._mcp_available = True

        with patch.object(client, '_search_via_mcp', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = sample_graphiti_results

            results = await client.search_nodes("逆否命题")

            mock_search.assert_called_once()
            assert len(results) == len(sample_graphiti_results)

    def test_tag_results(self):
        """_tag_results为结果添加类型标签"""
        client = GraphitiClient()

        results = [{"id": "1", "content": "test"}]
        tagged = client._tag_results(results, "node")

        assert tagged[0]["_graphiti_type"] == "node"
