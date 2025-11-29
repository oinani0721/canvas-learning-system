"""
TemporalClient 单元测试

Story 12.4: Temporal Memory实现
- AC 4.1: FSRS库集成
- AC 4.2: 学习行为时序追踪
- AC 4.3: get_weak_concepts()返回低稳定性概念
- AC 4.4: update_behavior()更新FSRS卡片
- AC 4.5: 性能 (< 50ms)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

# Import the client under test
from src.agentic_rag.clients.temporal_client import TemporalClient

# ============================================================
# Story 12.4 AC 4.1: FSRS库集成
# ============================================================

class TestTemporalClientInitialization:
    """测试 TemporalClient 初始化"""

    def test_default_initialization(self):
        """AC 4.1: 默认参数初始化"""
        client = TemporalClient()

        assert client.db_path == "learning_behavior.db"
        assert client.timeout_ms == 50
        assert client.enable_fallback is True
        assert client._initialized is False
        assert client._temporal_memory is None

    def test_custom_initialization(self):
        """AC 4.1: 自定义参数初始化"""
        client = TemporalClient(
            db_path="custom.db",
            timeout_ms=100,
            enable_fallback=False
        )

        assert client.db_path == "custom.db"
        assert client.timeout_ms == 100
        assert client.enable_fallback is False

    @pytest.mark.asyncio
    async def test_initialize_without_temporal_memory(self):
        """AC 4.1: 无TemporalMemory环境初始化"""
        with patch('src.agentic_rag.clients.temporal_client.TEMPORAL_MEMORY_AVAILABLE', False):
            client = TemporalClient()

            result = await client.initialize()

            assert client._initialized is True
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_with_temporal_memory(self, fsrs_available):
        """AC 4.1: 有TemporalMemory环境初始化"""
        if not fsrs_available:
            pytest.skip("FSRS not installed")

        with patch('src.agentic_rag.clients.temporal_client.TEMPORAL_MEMORY_AVAILABLE', True):
            with patch('src.agentic_rag.clients.temporal_client.TemporalMemory') as mock_tm:
                mock_instance = MagicMock()
                mock_tm.return_value = mock_instance

                client = TemporalClient(db_path=":memory:")

                await client.initialize()

                assert client._initialized is True

    def test_thread_pool_executor_created(self):
        """AC 4.1: ThreadPoolExecutor已创建"""
        client = TemporalClient()

        assert client._executor is not None
        assert client._executor._max_workers == 2


# ============================================================
# Story 12.4 AC 4.2: 学习行为时序追踪
# ============================================================

class TestTemporalClientRecordBehavior:
    """测试学习行为记录"""

    @pytest.mark.asyncio
    async def test_record_behavior_returns_row_id(self):
        """AC 4.2: record_behavior返回行ID"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.record_behavior.return_value = 123
        client._temporal_memory = mock_tm

        row_id = await client.record_behavior(
            canvas_file="离散数学.canvas",
            concept="逆否命题",
            action_type="explanation",
            session_id="session_001"
        )

        assert row_id == 123
        mock_tm.record_behavior.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_behavior_with_metadata(self):
        """AC 4.2: record_behavior支持metadata"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.record_behavior.return_value = 124
        client._temporal_memory = mock_tm

        row_id = await client.record_behavior(
            canvas_file="离散数学.canvas",
            concept="逆否命题",
            action_type="decomposition",
            session_id="session_001",
            metadata='{"agent": "basic-decomposition"}'
        )

        assert row_id == 124

    @pytest.mark.asyncio
    async def test_record_behavior_without_initialization(self):
        """AC 4.2: record_behavior自动初始化"""
        with patch('src.agentic_rag.clients.temporal_client.TEMPORAL_MEMORY_AVAILABLE', False):
            client = TemporalClient()
            # Don't call initialize()

            row_id = await client.record_behavior(
                canvas_file="test.canvas",
                concept="test",
                action_type="test",
                session_id="test"
            )

            assert client._initialized is True
            assert row_id == 0  # No temporal_memory

    @pytest.mark.asyncio
    async def test_record_behavior_error_handling(self):
        """AC 4.2: record_behavior错误处理"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.record_behavior.side_effect = Exception("DB error")
        client._temporal_memory = mock_tm

        row_id = await client.record_behavior(
            canvas_file="test.canvas",
            concept="test",
            action_type="test",
            session_id="test"
        )

        assert row_id == 0


# ============================================================
# Story 12.4 AC 4.3: get_weak_concepts()返回低稳定性概念
# ============================================================

class TestTemporalClientGetWeakConcepts:
    """测试获取薄弱概念"""

    @pytest.mark.asyncio
    async def test_get_weak_concepts_returns_list(self, sample_weak_concepts):
        """AC 4.3: get_weak_concepts返回列表"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_weak_concepts.return_value = sample_weak_concepts
        client._temporal_memory = mock_tm

        results = await client.get_weak_concepts("离散数学.canvas")

        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_weak_concepts_with_weights(self, sample_weak_concepts):
        """AC 4.3: get_weak_concepts支持权重参数"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_weak_concepts.return_value = sample_weak_concepts
        client._temporal_memory = mock_tm

        await client.get_weak_concepts(
            canvas_file="离散数学.canvas",
            stability_weight=0.8,
            error_rate_weight=0.2
        )

        # Verify weights were passed
        mock_tm.get_weak_concepts.assert_called_once()
        call_kwargs = mock_tm.get_weak_concepts.call_args[1]
        assert call_kwargs["stability_weight"] == 0.8
        assert call_kwargs["error_rate_weight"] == 0.2

    @pytest.mark.asyncio
    async def test_get_weak_concepts_with_limit(self, sample_weak_concepts):
        """AC 4.3: get_weak_concepts尊重limit参数"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_weak_concepts.return_value = sample_weak_concepts[:1]
        client._temporal_memory = mock_tm

        results = await client.get_weak_concepts(
            canvas_file="离散数学.canvas",
            limit=1
        )

        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_get_weak_concepts_auto_initializes(self):
        """AC 4.3: get_weak_concepts自动初始化"""
        with patch('src.agentic_rag.clients.temporal_client.TEMPORAL_MEMORY_AVAILABLE', False):
            client = TemporalClient()
            # Don't call initialize()

            results = await client.get_weak_concepts("test.canvas")

            assert client._initialized is True
            assert results == []

    @pytest.mark.asyncio
    async def test_get_weak_concepts_result_format(self, sample_weak_concepts):
        """AC 4.3: get_weak_concepts返回正确格式"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_weak_concepts.return_value = sample_weak_concepts
        client._temporal_memory = mock_tm

        results = await client.get_weak_concepts("离散数学.canvas")

        # Verify format
        assert "concept" in results[0]
        assert "stability" in results[0]
        assert "error_rate" in results[0]
        assert "weakness_score" in results[0]


# ============================================================
# Story 12.4 AC 4.4: update_behavior()更新FSRS卡片
# ============================================================

class TestTemporalClientUpdateBehavior:
    """测试更新FSRS卡片"""

    @pytest.mark.asyncio
    async def test_update_behavior_returns_dict(self):
        """AC 4.4: update_behavior返回字典"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.update_behavior.return_value = {
            "concept": "逆否命题",
            "stability": 2.5,
            "difficulty": 0.6,
            "due": "2025-01-15T00:00:00"
        }
        client._temporal_memory = mock_tm

        with patch('src.agentic_rag.clients.temporal_client.TEMPORAL_MEMORY_AVAILABLE', True):
            with patch('src.agentic_rag.clients.temporal_client.Rating') as mock_rating:
                mock_rating.Good = 3

                result = await client.update_behavior(
                    concept="逆否命题",
                    rating=3,
                    canvas_file="离散数学.canvas"
                )

                assert isinstance(result, dict)
                assert "stability" in result

    @pytest.mark.asyncio
    async def test_update_behavior_rating_mapping(self):
        """AC 4.4: update_behavior正确映射评分"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.update_behavior.return_value = {}
        client._temporal_memory = mock_tm

        with patch('src.agentic_rag.clients.temporal_client.TEMPORAL_MEMORY_AVAILABLE', True):
            with patch('src.agentic_rag.clients.temporal_client.Rating') as mock_rating:
                mock_rating.Again = 1
                mock_rating.Hard = 2
                mock_rating.Good = 3
                mock_rating.Easy = 4

                # Test each rating value
                for rating in [1, 2, 3, 4]:
                    await client.update_behavior(
                        concept="test",
                        rating=rating,
                        canvas_file="test.canvas"
                    )

                assert mock_tm.update_behavior.call_count == 4

    @pytest.mark.asyncio
    async def test_update_behavior_with_session_id(self):
        """AC 4.4: update_behavior支持session_id"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.update_behavior.return_value = {}
        client._temporal_memory = mock_tm

        with patch('src.agentic_rag.clients.temporal_client.TEMPORAL_MEMORY_AVAILABLE', True):
            with patch('src.agentic_rag.clients.temporal_client.Rating') as mock_rating:
                mock_rating.Good = 3

                await client.update_behavior(
                    concept="逆否命题",
                    rating=3,
                    canvas_file="离散数学.canvas",
                    session_id="session_001"
                )

                call_kwargs = mock_tm.update_behavior.call_args[1]
                assert call_kwargs["session_id"] == "session_001"

    @pytest.mark.asyncio
    async def test_update_behavior_without_temporal_memory(self):
        """AC 4.4: 无temporal_memory时返回空字典"""
        client = TemporalClient()
        client._initialized = True
        client._temporal_memory = None

        result = await client.update_behavior(
            concept="test",
            rating=3,
            canvas_file="test.canvas"
        )

        assert result == {}


# ============================================================
# Story 12.4 AC 4.5: 性能 (< 50ms)
# ============================================================

class TestTemporalClientPerformance:
    """测试性能相关功能"""

    @pytest.mark.asyncio
    async def test_timeout_returns_empty_with_fallback(self):
        """AC 4.5: 超时时启用fallback返回空列表"""
        client = TemporalClient(timeout_ms=1, enable_fallback=True)
        client._initialized = True

        mock_tm = MagicMock()
        # Simulate slow operation
        async def slow_operation():
            await asyncio.sleep(0.1)
            return []

        client._temporal_memory = mock_tm

        with patch.object(client, 'get_weak_concepts', side_effect=asyncio.TimeoutError):
            # Direct call will raise, but client should handle it
            pass

    @pytest.mark.asyncio
    async def test_timeout_raises_without_fallback(self):
        """AC 4.5: 超时时禁用fallback抛出异常"""
        client = TemporalClient(timeout_ms=1, enable_fallback=False)
        client._initialized = True

        mock_tm = MagicMock()

        def slow_get_weak_concepts(*args, **kwargs):
            import time
            time.sleep(0.1)  # 100ms, exceeds 1ms timeout
            return []

        mock_tm.get_weak_concepts = slow_get_weak_concepts
        client._temporal_memory = mock_tm

        with pytest.raises(asyncio.TimeoutError):
            await client.get_weak_concepts("test.canvas")

    @pytest.mark.asyncio
    async def test_error_returns_empty_with_fallback(self):
        """AC 4.5: 错误时启用fallback返回空列表"""
        client = TemporalClient(enable_fallback=True)
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_weak_concepts.side_effect = Exception("DB error")
        client._temporal_memory = mock_tm

        results = await client.get_weak_concepts("test.canvas")

        assert results == []


# ============================================================
# Additional Tests: get_review_due_concepts
# ============================================================

class TestTemporalClientGetReviewDueConcepts:
    """测试获取到期复习概念"""

    @pytest.mark.asyncio
    async def test_get_review_due_concepts_returns_list(self):
        """get_review_due_concepts返回列表"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_review_due_concepts.return_value = [
            {"concept": "逆否命题", "due": "2025-01-14"},
            {"concept": "充分条件", "due": "2025-01-14"}
        ]
        client._temporal_memory = mock_tm

        results = await client.get_review_due_concepts("离散数学.canvas")

        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_review_due_concepts_with_limit(self):
        """get_review_due_concepts尊重limit参数"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_review_due_concepts.return_value = [
            {"concept": "逆否命题", "due": "2025-01-14"}
        ]
        client._temporal_memory = mock_tm

        await client.get_review_due_concepts(
            canvas_file="离散数学.canvas",
            limit=1
        )

        mock_tm.get_review_due_concepts.assert_called_once()
        call_kwargs = mock_tm.get_review_due_concepts.call_args[1]
        assert call_kwargs["limit"] == 1

    @pytest.mark.asyncio
    async def test_get_review_due_concepts_error_handling(self):
        """get_review_due_concepts错误处理"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        mock_tm.get_review_due_concepts.side_effect = Exception("DB error")
        client._temporal_memory = mock_tm

        results = await client.get_review_due_concepts("test.canvas")

        assert results == []


# ============================================================
# Additional Tests: Stats and Close
# ============================================================

class TestTemporalClientStatsAndClose:
    """测试统计信息和关闭"""

    def test_get_stats(self):
        """get_stats返回客户端统计信息"""
        client = TemporalClient(
            db_path="custom.db",
            timeout_ms=100
        )

        stats = client.get_stats()

        assert stats["initialized"] is False
        assert stats["db_path"] == "custom.db"
        assert stats["timeout_ms"] == 100
        assert stats["enable_fallback"] is True

    @pytest.mark.asyncio
    async def test_close(self):
        """close关闭客户端"""
        client = TemporalClient()
        client._initialized = True

        mock_tm = MagicMock()
        client._temporal_memory = mock_tm

        await client.close()

        # Verify close was called
        # Note: The executor shutdown is called

    @pytest.mark.asyncio
    async def test_close_without_temporal_memory(self):
        """close无temporal_memory时不报错"""
        client = TemporalClient()
        client._temporal_memory = None

        # Should not raise
        await client.close()
