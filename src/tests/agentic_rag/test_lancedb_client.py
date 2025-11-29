"""
LanceDBClient 单元测试

Story 12.2: LanceDB POC验证
- AC 2.1: LanceDB连接测试
- AC 2.2: 向量检索接口
- AC 2.3: 性能基准 (P95 < 400ms)
- AC 2.4: 结果转换为SearchResult

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the client under test
from src.agentic_rag.clients.lancedb_client import LanceDBClient

# ============================================================
# Story 12.2 AC 2.1: LanceDB连接测试
# ============================================================

class TestLanceDBClientInitialization:
    """测试 LanceDBClient 初始化和连接"""

    def test_default_initialization(self):
        """AC 2.1: 默认参数初始化"""
        client = LanceDBClient()

        assert client.db_path == os.path.expanduser("~/.lancedb")
        assert client.embedding_dim == 1536
        assert client.timeout_ms == 400
        assert client.batch_size == 10
        assert client.enable_fallback is True
        assert client._initialized is False
        assert client._db is None

    def test_custom_initialization(self):
        """AC 2.1: 自定义参数初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = LanceDBClient(
                db_path=tmpdir,
                embedding_dim=768,
                timeout_ms=500,
                batch_size=20,
                enable_fallback=False
            )

            assert client.db_path == tmpdir
            assert client.embedding_dim == 768
            assert client.timeout_ms == 500
            assert client.batch_size == 20
            assert client.enable_fallback is False

    @pytest.mark.asyncio
    async def test_initialize_creates_connection(self, mock_lancedb_connection, lancedb_available):
        """AC 2.1: 初始化创建数据库连接"""
        if not lancedb_available:
            pytest.skip("LanceDB not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            client = LanceDBClient(db_path=tmpdir)

            with patch('src.agentic_rag.clients.lancedb_client.lancedb') as mock_lancedb:
                mock_lancedb.connect.return_value = mock_lancedb_connection

                await client.initialize()

                assert client._initialized is True
                mock_lancedb.connect.assert_called_once_with(tmpdir)

    @pytest.mark.asyncio
    async def test_initialize_without_lancedb(self):
        """AC 2.1: 无LanceDB环境初始化"""
        with patch('src.agentic_rag.clients.lancedb_client.LANCEDB_AVAILABLE', False):
            client = LanceDBClient()

            result = await client.initialize()

            assert client._initialized is True
            assert result is False

    def test_default_tables_defined(self):
        """AC 2.1: 默认表名已定义"""
        assert LanceDBClient.DEFAULT_TABLES == ["canvas_explanations", "canvas_concepts"]


# ============================================================
# Story 12.2 AC 2.2: 向量检索接口
# ============================================================

class TestLanceDBClientSearch:
    """测试向量检索接口"""

    @pytest.mark.asyncio
    async def test_search_returns_list(self, mock_lancedb_connection):
        """AC 2.2: search返回列表"""
        client = LanceDBClient()
        client._db = mock_lancedb_connection
        client._initialized = True

        results = await client.search("逆否命题")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_table_name(self, mock_lancedb_connection):
        """AC 2.2: search支持table_name参数"""
        client = LanceDBClient()
        client._db = mock_lancedb_connection
        client._initialized = True

        results = await client.search(
            query="逆否命题",
            table_name="canvas_concepts"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_canvas_file_filter(self, mock_lancedb_connection):
        """AC 2.2: search支持canvas_file过滤"""
        client = LanceDBClient()
        client._db = mock_lancedb_connection
        client._initialized = True

        results = await client.search(
            query="逆否命题",
            canvas_file="离散数学.canvas"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_auto_initializes(self, mock_lancedb_connection):
        """AC 2.2: search自动初始化"""
        with patch('src.agentic_rag.clients.lancedb_client.LANCEDB_AVAILABLE', True):
            with patch('src.agentic_rag.clients.lancedb_client.lancedb') as mock_lancedb:
                mock_lancedb.connect.return_value = mock_lancedb_connection

                client = LanceDBClient()
                # Don't call initialize()

                await client.search("逆否命题")

                assert client._initialized is True

    @pytest.mark.asyncio
    async def test_search_multiple_tables(self, mock_lancedb_connection):
        """AC 2.2: search_multiple_tables搜索多个表"""
        client = LanceDBClient()
        client._db = mock_lancedb_connection
        client._initialized = True

        # Mock table cache
        mock_table = MagicMock()
        mock_table.search.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.to_list.return_value = [
            {"doc_id": "1", "content": "test", "_distance": 0.1}
        ]
        client._tables_cache = {
            "canvas_explanations": mock_table,
            "canvas_concepts": mock_table
        }

        # Mock _get_query_vector
        with patch.object(client, '_get_query_vector', new_callable=AsyncMock) as mock_vector:
            mock_vector.return_value = [0.1] * 1536

            results = await client.search_multiple_tables("逆否命题")

            assert isinstance(results, list)


# ============================================================
# Story 12.2 AC 2.3: 性能基准 (P95 < 400ms)
# ============================================================

class TestLanceDBClientPerformance:
    """测试性能相关功能"""

    @pytest.mark.asyncio
    async def test_timeout_returns_empty_with_fallback(self):
        """AC 2.3: 超时时启用fallback返回空列表"""
        client = LanceDBClient(timeout_ms=1, enable_fallback=True)
        client._initialized = True
        client._db = MagicMock()

        with patch.object(client, '_search_internal', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = asyncio.TimeoutError()

            results = await client.search("测试")

            assert results == []

    @pytest.mark.asyncio
    async def test_timeout_raises_without_fallback(self):
        """AC 2.3: 超时时禁用fallback抛出异常"""
        client = LanceDBClient(timeout_ms=1, enable_fallback=False)
        client._initialized = True
        client._db = MagicMock()

        with patch.object(client, '_search_internal', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await client.search("测试")

    @pytest.mark.asyncio
    async def test_error_returns_empty_with_fallback(self):
        """AC 2.3: 错误时启用fallback返回空列表"""
        client = LanceDBClient(enable_fallback=True)
        client._initialized = True
        client._db = MagicMock()

        with patch.object(client, '_search_internal', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("Test error")

            results = await client.search("测试")

            assert results == []


# ============================================================
# Story 12.2 AC 2.4: 结果转换为SearchResult
# ============================================================

class TestLanceDBClientResultConversion:
    """测试结果转换"""

    def test_convert_to_search_results_basic(self):
        """AC 2.4: 基本结果转换"""
        client = LanceDBClient()

        raw_results = [
            {
                "doc_id": "doc_001",
                "content": "口语化解释-逆否命题",
                "_distance": 0.12,
                "canvas_file": "离散数学.canvas"
            }
        ]

        results = client._convert_to_search_results(raw_results)

        assert len(results) == 1
        assert results[0]["doc_id"].startswith("lancedb_")
        assert results[0]["content"] == "口语化解释-逆否命题"
        assert results[0]["metadata"]["source"] == "lancedb"
        assert results[0]["metadata"]["canvas_file"] == "离散数学.canvas"
        assert results[0]["metadata"]["original_distance"] == 0.12

    def test_convert_to_search_results_distance_to_score(self):
        """AC 2.4: 距离转换为相似度分数"""
        client = LanceDBClient()

        raw_results = [
            {"doc_id": "1", "content": "test", "_distance": 0.0},   # Perfect match
            {"doc_id": "2", "content": "test", "_distance": 0.5},   # Medium
            {"doc_id": "3", "content": "test", "_distance": 1.0},   # Lower
        ]

        results = client._convert_to_search_results(raw_results)

        # score = 1 / (1 + distance)
        assert results[0]["score"] == 1.0        # 1 / (1 + 0) = 1.0
        assert results[1]["score"] == pytest.approx(0.6667, rel=0.01)  # 1 / (1 + 0.5)
        assert results[2]["score"] == 0.5        # 1 / (1 + 1) = 0.5

    def test_convert_to_search_results_with_canvas_file(self):
        """AC 2.4: 转换时包含canvas_file"""
        client = LanceDBClient()

        raw_results = [
            {"doc_id": "1", "content": "test", "_distance": 0.1}
        ]

        results = client._convert_to_search_results(
            raw_results,
            canvas_file="离散数学.canvas"
        )

        assert results[0]["metadata"]["canvas_file"] == "离散数学.canvas"

    def test_convert_to_search_results_preserves_metadata(self):
        """AC 2.4: 保留额外的metadata字段"""
        client = LanceDBClient()

        raw_results = [
            {
                "doc_id": "doc_001",
                "content": "测试",
                "_distance": 0.1,
                "concept": "逆否命题",
                "agent_type": "oral-explanation",
                "node_id": "node_123",
                "metadata_json": "{\"key\": \"value\"}"
            }
        ]

        results = client._convert_to_search_results(raw_results)

        assert results[0]["metadata"]["concept"] == "逆否命题"
        assert results[0]["metadata"]["agent_type"] == "oral-explanation"
        assert results[0]["metadata"]["node_id"] == "node_123"
        assert results[0]["metadata"]["metadata_json"] == "{\"key\": \"value\"}"

    def test_convert_to_search_results_extracts_content(self):
        """AC 2.4: 从多个字段提取content"""
        client = LanceDBClient()

        # Test different content field names
        test_cases = [
            {"doc_id": "1", "content": "from content", "_distance": 0.1},
            {"doc_id": "2", "text": "from text", "_distance": 0.1},
            {"doc_id": "3", "document": "from document", "_distance": 0.1},
        ]

        for tc in test_cases:
            results = client._convert_to_search_results([tc])
            expected = tc.get("content") or tc.get("text") or tc.get("document")
            assert results[0]["content"] == expected


# ============================================================
# Additional Tests: Embedder and Add Documents
# ============================================================

class TestLanceDBClientEmbedder:
    """测试嵌入器相关功能"""

    def test_set_embedder(self):
        """set_embedder设置嵌入器"""
        client = LanceDBClient()

        async def mock_embedder(text: str):
            return [0.1] * 1536

        client.set_embedder(mock_embedder)

        assert client._embedder == mock_embedder

    @pytest.mark.asyncio
    async def test_get_query_vector_with_embedder(self):
        """使用embedder生成查询向量"""
        client = LanceDBClient()

        async def mock_embedder(text: str):
            return [0.1] * 1536

        client.set_embedder(mock_embedder)

        vector = await client._get_query_vector("测试查询")

        assert vector == [0.1] * 1536

    @pytest.mark.asyncio
    async def test_get_query_vector_with_list_input(self):
        """直接传入向量列表"""
        client = LanceDBClient()

        input_vector = [0.5] * 1536
        vector = await client._get_query_vector(input_vector)

        assert vector == input_vector


class TestLanceDBClientAddDocuments:
    """测试添加文档功能"""

    @pytest.mark.asyncio
    async def test_add_documents_returns_count(self, mock_lancedb_connection):
        """add_documents返回添加的文档数量"""
        client = LanceDBClient()
        client._db = mock_lancedb_connection
        client._initialized = True

        mock_table = MagicMock()
        client._tables_cache = {"test_table": mock_table}

        documents = [
            {
                "doc_id": "doc_001",
                "content": "测试内容",
                "vector": [0.1] * 1536,
                "metadata": {"canvas_file": "test.canvas"}
            }
        ]

        count = await client.add_documents("test_table", documents)

        assert count == 1
        mock_table.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_documents_without_db(self):
        """无数据库连接时返回0"""
        client = LanceDBClient()
        client._db = None

        documents = [{"doc_id": "1", "content": "test"}]
        count = await client.add_documents("test_table", documents)

        assert count == 0


class TestLanceDBClientStats:
    """测试统计信息"""

    def test_get_stats(self):
        """get_stats返回客户端统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = LanceDBClient(
                db_path=tmpdir,
                timeout_ms=500,
                batch_size=15
            )

            stats = client.get_stats()

            assert stats["initialized"] is False
            assert stats["db_available"] is False
            assert stats["db_path"] == tmpdir
            assert stats["tables"] == []
            assert stats["timeout_ms"] == 500
            assert stats["batch_size"] == 15
            assert stats["enable_fallback"] is True
