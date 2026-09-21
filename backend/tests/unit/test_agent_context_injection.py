# Story 36.7: Agent Context Injection - AC Coverage Tests
"""
Tests for AC-36.7.2 (Neo4j query delegation) and AC-36.7.3 (relevance sorting).

Verifies:
- _search_learning_relations() delegates to graphiti_service.search_memories()
- Results are limited to top 5 and sorted by relevance

[Source: docs/stories/36.7.story.md]
"""

from unittest.mock import AsyncMock, MagicMock

import asyncio

import pytest
from app.services.context_enrichment_service import ContextEnrichmentService


@pytest.fixture
def mock_canvas_service():
    """Create mock canvas service."""
    service = MagicMock()
    service.canvas_base_path = "/test/vault"
    return service


@pytest.fixture
def mock_learning_memory_service():
    """Create mock LearningMemoryClient（历史名 graphiti_service，5d2b95ba 改名）."""
    service = AsyncMock()
    service.initialize = AsyncMock(return_value=True)
    service.search_memories = AsyncMock(return_value=[])
    return service


@pytest.fixture
def enrichment_service(mock_canvas_service, mock_learning_memory_service):
    """Create ContextEnrichmentService with graphiti_service."""
    return ContextEnrichmentService(
        canvas_service=mock_canvas_service,
        learning_memory_service=mock_learning_memory_service,
    )


class TestGraphitiSearchDelegation:
    """AC-36.7.2: Verify _search_learning_relations delegates to learning_memory_service.

    契约演进（5d2b95ba, 2026-03-29 G-FAKE-001）：假 "graphiti" 标识符批量改名为真实
    Neo4j 名称（能力仍在，纯改名）。本类测试原先调旧方法名 ⇒ AttributeError。
    处置 = 改指新名，断言语义不变。[CARD-RED-C2]"""

    @pytest.mark.asyncio
    async def test_search_calls_learning_memory_service(self, enrichment_service, mock_learning_memory_service):
        """AC-36.7.2: _search_learning_relations calls graphiti_service.search_memories()."""
        mock_learning_memory_service.search_memories = AsyncMock(
            return_value=[
                {"concept": "矩阵乘法", "relevance": 0.9, "timestamp": "2026-02-10"},
            ]
        )

        results = await enrichment_service._search_learning_relations(
            query="矩阵乘法定义",
            canvas_name="test.canvas",
            node_id="node-1",
        )

        mock_learning_memory_service.search_memories.assert_called_once_with(
            query="矩阵乘法定义",
            canvas_name="test.canvas",
            node_id="node-1",
            limit=5,
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_returns_empty_without_learning_memory_service(self, mock_canvas_service):
        """AC-36.7.2: Returns empty list when graphiti_service is None."""
        service = ContextEnrichmentService(
            canvas_service=mock_canvas_service,
            learning_memory_service=None,
        )

        results = await service._search_learning_relations(query="test")

        assert results == []


class TestRelevanceSorting:
    """AC-36.7.3: Verify results sorted by relevance, top 5."""

    @pytest.mark.asyncio
    async def test_search_limits_to_top_5(self, enrichment_service, mock_learning_memory_service):
        """AC-36.7.3: Search passes limit=5 to graphiti_service."""
        mock_learning_memory_service.search_memories = AsyncMock(return_value=[])

        await enrichment_service._search_learning_relations(query="test query")

        # Verify limit=5 was passed
        call_kwargs = mock_learning_memory_service.search_memories.call_args.kwargs
        assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_graceful_on_exception(self, enrichment_service, mock_learning_memory_service):
        """AC-36.7.3: Returns empty list on dependency failure (graceful degradation).

        契约演进（a9304c69, 2026-03-29 S35 except 精确化）：本方法的重试/降级分支由
        宽 ``except Exception`` 收窄为 ``(RuntimeError, asyncio.TimeoutError,
        AttributeError)``——依赖故障降级、编程错误传播。原测试 mock 裸 ``Exception``
        不在元组内 ⇒ 按现行契约**应当传播**，旧断言必红。对齐 = mock 改成元组内
        现实形态（连接超时），降级语义照旧验证。[CARD-RED-C2]
        """
        mock_learning_memory_service.search_memories = AsyncMock(side_effect=asyncio.TimeoutError("Connection failed"))

        results = await enrichment_service._search_learning_relations(query="test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_propagates_unexpected_exception(self, enrichment_service, mock_learning_memory_service):
        """S35 契约的反向锚：元组外的异常必须传播，不得静默吞成空列表。

        a9304c69 把降级分支收窄为 (RuntimeError, asyncio.TimeoutError,
        AttributeError) 是有意裁定——宽 except 会把编程错误（如 TypeError）吞成
        「无相关记忆」，静默掩盖缺陷。若有人改回 ``except Exception``，本条翻红。
        [CARD-RED-C2]
        """
        mock_learning_memory_service.search_memories = AsyncMock(side_effect=TypeError("bug: None is not iterable"))

        with pytest.raises(TypeError):
            await enrichment_service._search_learning_relations(query="q")
