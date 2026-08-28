# CARD-G4-2 (BATCH-2026-08-28-第五批) — 四态贯穿注入测试.
"""故障注入 → 四态各就位 (unavailable/degraded 带 reason, empty 无 reason).

覆盖:
- MemoryService.search_memories_with_status: Tier1+Tier2 全灭→unavailable;
  单 Tier 灭→degraded; 全通空результ→empty; 有结果→ok。
- 旧 search_memories() 委托契约: 仍返回 list (调用方零破坏)。
- get_learning_history: dict 加性键 retrieval_status (Neo4j 失败→degraded)。
- get_concept_score_history: ScoreHistoryResponse 加性字段 status
  (失败→unavailable 带 reason; 空→empty)。
- rag_service.query_with_fallback: fallback dict 带 retrieval_status。
- rag_service.get_weak_concepts_with_status: 失败→unavailable。
- nodes.retrieve_graphiti/retrieve_lancedb: 通道失败→channel_errors 进 state。
- 真实不可达 bolt 地址 (bolt://localhost:1) → unavailable 而非假空。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.service_status import ServiceStatus


def _healthy_neo4j_mock() -> AsyncMock:
    """健康后端的 mock — 必须显式设置 ``is_fallback_mode`` / ``stats``。

    CARD-G4-2 Codex round-1 BLOCKER-1: 生产 Neo4jClient 会在故障后进入
    JSON_FALLBACK 模式 (不抛异常、返回空), 四态检测因此**先探测客户端
    健康**再看异常。裸 ``AsyncMock()`` 的 ``is_fallback_mode`` 是 truthy
    Mock, 会被正确判成故障 —— 所以「健康后端」必须在 fixture 里显式表达。
    """
    client = AsyncMock()
    client.is_fallback_mode = False
    client.stats = {"initialized": True, "health_status": "healthy"}
    return client


@pytest.fixture
async def memory_service():
    """已初始化的 MemoryService, Neo4j/Graphiti 均为 mock (unit 层)。"""
    from app.services.memory_service import MemoryService

    svc = MemoryService()
    svc._initialized = True
    svc._episodes_recovered = True
    svc.neo4j = _healthy_neo4j_mock()
    return svc


class TestSearchMemoriesFourStates:
    @pytest.mark.asyncio
    async def test_all_remote_tiers_dead_and_no_cache_is_unavailable(
        self, memory_service
    ):
        """Tier1 (Graphiti) 与 Tier2 (fulltext) 全灭 + Tier3 内存空
        → unavailable 带 reason (不再假装空结果)."""
        with (
            patch.object(
                memory_service,
                "_search_graphiti",
                new=AsyncMock(
                    side_effect=lambda *a, **kw: _sink_fail(
                        kw.get("fail_sink"), "graphiti: connection refused"
                    )
                ),
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new=AsyncMock(
                    side_effect=lambda *a, **kw: _sink_fail(
                        kw.get("fail_sink"), "neo4j fulltext: connection refused"
                    )
                ),
            ),
        ):
            result = await memory_service.search_memories_with_status("query")

        assert result.status is ServiceStatus.UNAVAILABLE
        assert result.reason and "refused" in result.reason
        assert result.items == []

    @pytest.mark.asyncio
    async def test_single_tier_dead_with_other_tier_alive_is_degraded(
        self, memory_service
    ):
        """Tier1 灭 + Tier2 有结果 → degraded 带 reason, 结果保留."""
        # Tier2 (Neo4j fulltext) 的分数键是 Lucene 原始 `score`
        # (_compute_unified_score tier=2 归一化为 score/10), 必须高于
        # min_relevance 地板 0.05, 否则命中被剔除、四态误判为 unavailable
        hit = {
            "episode_id": "e1",
            "content": "x",
            "episode_type": "t",
            "score": 9.0,
        }
        with (
            patch.object(
                memory_service,
                "_search_graphiti",
                new=AsyncMock(
                    side_effect=lambda *a, **kw: _sink_fail(
                        kw.get("fail_sink"), "graphiti: timeout"
                    )
                ),
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new=AsyncMock(return_value=[hit]),
            ),
        ):
            result = await memory_service.search_memories_with_status("query")

        assert result.status is ServiceStatus.DEGRADED
        assert result.reason and "timeout" in result.reason
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_true_empty_is_empty_without_reason(self, memory_service):
        """全 Tier 正常但真空 → empty, 无 reason (空是数据事实非故障)."""
        with (
            patch.object(
                memory_service, "_search_graphiti", new=AsyncMock(return_value=[])
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new=AsyncMock(return_value=[]),
            ),
        ):
            result = await memory_service.search_memories_with_status("query")

        assert result.status is ServiceStatus.EMPTY
        assert result.reason is None
        assert result.items == []

    @pytest.mark.asyncio
    async def test_results_present_is_ok(self, memory_service):
        # relevance_score 需高于 min_relevance 地板 (0.05), 否则命中被
        # 检索质量过滤器剔除, 四态会误判为 empty
        hit = {
            "episode_id": "e1",
            "content": "x",
            "episode_type": "t",
            "relevance_score": 0.9,
        }
        with (
            patch.object(
                memory_service, "_search_graphiti", new=AsyncMock(return_value=[hit])
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new=AsyncMock(return_value=[]),
            ),
        ):
            result = await memory_service.search_memories_with_status("query")

        assert result.status is ServiceStatus.OK
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_low_score_results_filtered_out_still_degraded_not_unavailable(
        self, memory_service
    ):
        """Codex round-1 HIGH-5: 状态不得被质量过滤污染。

        T1 挂 + T2 命中低分 → 地板 (min_relevance) 把结果滤光。
        源层面这是 degraded (T2 明明活着并检索到了东西), 报 unavailable
        等于说「记忆系统挂了」——不实。原测试用高分绕开了这个场景。
        """
        low_score_hit = {
            "episode_id": "e-low",
            "content": "x",
            "episode_type": "t",
            "score": 0.1,  # 归一化后 0.01 < min_relevance 0.05 → 被滤掉
        }
        with (
            patch.object(
                memory_service,
                "_search_graphiti",
                new=AsyncMock(
                    side_effect=lambda *a, **kw: _sink_fail(
                        kw.get("fail_sink"), "graphiti: timeout"
                    )
                ),
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new=AsyncMock(return_value=[low_score_hit]),
            ),
        ):
            result = await memory_service.search_memories_with_status("query")

        assert result.status is ServiceStatus.DEGRADED, (
            f"质量地板滤光结果不得把 degraded 升级成 unavailable (得到 {result.status})"
        )
        assert result.items == []  # 载荷确实被滤空, 但状态诚实

    @pytest.mark.asyncio
    async def test_coverage_failure_alone_is_degraded_not_unavailable(
        self, memory_service
    ):
        """HIGH-5 另一半: 仅子组枚举失败 (覆盖面收窄) 时, 两个主 Tier
        都成功且真空 → degraded (结果可能不全), 而非 unavailable。"""

        async def _graphiti_with_coverage_gap(*a, **kw):
            sink = kw.get("coverage_sink")
            if sink is not None:
                sink.append("subgroup enumeration: timeout")
            return []

        with (
            patch.object(
                memory_service, "_search_graphiti", new=_graphiti_with_coverage_gap
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new=AsyncMock(return_value=[]),
            ),
        ):
            result = await memory_service.search_memories_with_status("query")

        assert result.status is ServiceStatus.DEGRADED
        assert "subgroup" in result.reason

    def test_delegate_signature_matches_status_method(self):
        """兼容铁律的机械判据: 委托方法与状态方法签名/默认值逐一相同 —
        任一侧新增参数而另一侧漏加, 调用方就会静默丢参数 (如 min_relevance
        不透传 → 检索质量地板失效)."""
        import inspect

        from app.services.memory_service import MemoryService

        new_sig = inspect.signature(MemoryService.search_memories_with_status)
        old_sig = inspect.signature(MemoryService.search_memories)

        assert list(new_sig.parameters) == list(old_sig.parameters)
        for name, new_param in new_sig.parameters.items():
            assert new_param.default == old_sig.parameters[name].default, name

    @pytest.mark.asyncio
    async def test_legacy_delegate_forwards_all_kwargs(self, memory_service):
        """委托不仅签名一致, 值也必须真的传下去."""
        captured = {}

        async def fake_with_status(*args, **kwargs):
            captured.update(kwargs)
            from app.models.service_status import StatusedResult

            return StatusedResult.from_items([])

        memory_service.search_memories_with_status = fake_with_status
        await memory_service.search_memories(
            "q",
            group_id="vault:x",
            max_results=7,
            limit=3,
            search_config="node_rrf",
            search_filter="F",
            min_relevance=0.42,
        )

        assert captured["group_id"] == "vault:x"
        assert captured["max_results"] == 7
        assert captured["limit"] == 3
        assert captured["search_config"] == "node_rrf"
        assert captured["search_filter"] == "F"
        assert captured["min_relevance"] == 0.42

    @pytest.mark.asyncio
    async def test_legacy_search_memories_still_returns_list(self, memory_service):
        """兼容铁律: 旧 search_memories() 保 list 契约 (委托新方法)."""
        with (
            patch.object(
                memory_service, "_search_graphiti", new=AsyncMock(return_value=[])
            ),
            patch.object(
                memory_service,
                "_search_neo4j_fulltext",
                new=AsyncMock(return_value=[]),
            ),
        ):
            result = await memory_service.search_memories("query")

        assert isinstance(result, list)


class TestLearningHistoryStatusKey:
    @pytest.mark.asyncio
    async def test_neo4j_failure_marks_degraded(self, memory_service):
        """Neo4j 读失败 (内存兜底接管) → dict 加性键 retrieval_status=degraded."""
        memory_service.neo4j.get_learning_history = AsyncMock(
            side_effect=ConnectionError("bolt down")
        )
        result = await memory_service.get_learning_history(user_id="u1")

        assert result["retrieval_status"] == "degraded"
        assert "bolt down" in result["retrieval_status_reason"]
        assert isinstance(result["items"], list)  # 原契约键全在位

    @pytest.mark.asyncio
    async def test_healthy_path_status_ok_or_empty(self, memory_service):
        memory_service.neo4j.get_learning_history = AsyncMock(return_value=[])
        result = await memory_service.get_learning_history(user_id="u1")

        assert result["retrieval_status"] in ("ok", "empty")
        assert result.get("retrieval_status_reason") is None


class TestScoreHistoryFourStates:
    @pytest.mark.asyncio
    async def test_neo4j_failure_is_unavailable_with_reason(self, memory_service):
        memory_service.neo4j.get_concept_score_history = AsyncMock(
            side_effect=ConnectionError("bolt down")
        )
        result = await memory_service.get_concept_score_history("c1", "canvas.canvas")

        assert result.status == "unavailable"
        assert result.status_reason and "bolt down" in result.status_reason
        assert result.scores == []

    @pytest.mark.asyncio
    async def test_true_empty_history_is_empty_without_reason(self, memory_service):
        memory_service.neo4j.get_concept_score_history = AsyncMock(return_value=[])
        result = await memory_service.get_concept_score_history("c1", "canvas.canvas")

        assert result.status == "empty"
        assert result.status_reason is None

    @pytest.mark.asyncio
    async def test_scores_present_is_ok(self, memory_service):
        memory_service.neo4j.get_concept_score_history = AsyncMock(
            return_value=[{"score": 80, "timestamp": "2026-08-28T00:00:00"}]
        )
        result = await memory_service.get_concept_score_history("c1", "canvas.canvas")

        assert result.status == "ok"
        assert result.scores == [80]

    @pytest.mark.asyncio
    async def test_failure_result_not_cached(self, memory_service):
        """故障结果不得进 30s 缓存 — 否则恢复后 30s 内仍假 unavailable."""
        memory_service.neo4j.get_concept_score_history = AsyncMock(
            side_effect=ConnectionError("bolt down")
        )
        await memory_service.get_concept_score_history("c1", "canvas.canvas")

        memory_service.neo4j.get_concept_score_history = AsyncMock(
            return_value=[{"score": 90, "timestamp": "t"}]
        )
        result = await memory_service.get_concept_score_history("c1", "canvas.canvas")
        assert result.status == "ok"
        assert result.scores == [90]


class TestSilentBackendFailover:
    """Codex round-1 BLOCKER-1: 生产最常见的故障形态**不抛异常**。

    ``Neo4jClient`` 初始化失败 / 运行中降级后进入 JSON_FALLBACK：
    ``initialized`` 仍为 True、查询正常返回 ``[]``、无任何异常。
    只靠 try/except 的四态会把它误报成 ok/empty —— 这组用例锁死探针。
    """

    @pytest.fixture
    async def fallback_service(self):
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes_recovered = True
        client = AsyncMock()
        client.is_fallback_mode = True  # ← 降级中, 但不抛异常
        client.stats = {"initialized": True, "mode": "JSON_FALLBACK"}
        client.get_learning_history = AsyncMock(return_value=[])
        client.get_concept_score_history = AsyncMock(return_value=[])
        svc.neo4j = client
        return svc

    @pytest.mark.asyncio
    async def test_score_history_fallback_is_unavailable_not_empty(
        self, fallback_service
    ):
        result = await fallback_service.get_concept_score_history("c1", "x.canvas")
        assert result.status == "unavailable", (
            "JSON_FALLBACK 返回的空历史不可信, 不得报 empty"
        )
        assert "JSON_FALLBACK" in result.status_reason

    @pytest.mark.asyncio
    async def test_learning_history_fallback_is_degraded(self, fallback_service):
        result = await fallback_service.get_learning_history(user_id="u1")
        assert result["retrieval_status"] == "degraded"
        assert "JSON_FALLBACK" in result["retrieval_status_reason"]

    @pytest.mark.asyncio
    async def test_search_fulltext_tier_reports_fallback(self, fallback_service):
        """Tier2 在降级后端上恒空 — 必须进 fail_sink 而非静默."""
        sink: list = []
        await fallback_service._search_neo4j_fulltext("q", None, 10, fail_sink=sink)
        assert sink and "JSON_FALLBACK" in sink[0]

    @pytest.mark.asyncio
    async def test_uninitialized_client_also_detected(self):
        """未初始化同样是「查询恒空且不抛异常」的形态."""
        from app.services.memory_service import MemoryService, _neo4j_backend_failure

        svc = MemoryService()
        client = AsyncMock()
        client.is_fallback_mode = False
        client.stats = {"initialized": False}
        svc.neo4j = client

        assert _neo4j_backend_failure(client) is not None

    @pytest.mark.asyncio
    async def test_unhealthy_health_status_detected(self):
        from app.services.memory_service import _neo4j_backend_failure

        client = AsyncMock()
        client.is_fallback_mode = False
        client.stats = {"initialized": True, "health_status": "unhealthy"}

        reason = _neo4j_backend_failure(client)
        assert reason and "unhealthy" in reason

    def test_healthy_client_passes_probe(self):
        from app.services.memory_service import _neo4j_backend_failure

        client = AsyncMock()
        client.is_fallback_mode = False
        client.stats = {"initialized": True, "health_status": "healthy"}

        assert _neo4j_backend_failure(client) is None


class TestMemoryDegradedChain:
    """Codex round-1 BLOCKER-3: MemoryService 四态必须一路活到 state。

    链路: MemoryService → mastery_injection._search_via_memory_service →
    retrieve_learning_memories → compress_context 的 memory_degraded 字段。
    此前中间层调旧 list 方法, 状态被剥成 .items, 故障与「真的没记忆」
    在下游完全无法分辨。
    """

    @pytest.mark.asyncio
    async def test_unavailable_service_does_not_look_like_no_memories(self):
        """service 报 unavailable → helper 返回 None (交降级路径),
        绝不能变成「空结果 + reason=None」。"""
        from agentic_rag.mastery_injection import _search_via_memory_service
        from app.models.service_status import StatusedResult

        svc = AsyncMock()
        svc.search_memories_with_status = AsyncMock(
            return_value=StatusedResult.unavailable("neo4j down")
        )

        with patch(
            "app.services.memory_service.get_memory_service",
            new=AsyncMock(return_value=svc),
        ):
            result = await _search_via_memory_service("n1", "vault:x")

        assert result is None, "unavailable 必须交降级路径, 不得当成空结果"

    @pytest.mark.asyncio
    async def test_degraded_reason_survives_to_caller(self):
        """service 报 degraded → 原因随条目一起返回, 供上层标记。"""
        from agentic_rag.mastery_injection import _search_via_memory_service
        from app.models.service_status import StatusedResult

        svc = AsyncMock()
        svc.search_memories_with_status = AsyncMock(
            return_value=StatusedResult.degraded([{"content": "x"}], "graphiti timeout")
        )

        with patch(
            "app.services.memory_service.get_memory_service",
            new=AsyncMock(return_value=svc),
        ):
            result = await _search_via_memory_service("n1", "vault:x")

        assert result is not None
        items, reason = result
        assert len(items) == 1
        assert reason == "graphiti timeout"

    @pytest.mark.asyncio
    async def test_degraded_and_empty_is_not_reported_as_no_memories(self):
        """最关键的一条: degraded **且**无命中 —— 旧实现返回
        ("", None) = 「真的没有记忆」; 现在必须带降级原因。"""
        from agentic_rag.mastery_injection import (
            MEMORY_DEGRADED_SERVICE,
            retrieve_learning_memories,
        )

        async def _degraded_empty(node_id, group_id, limit=10):
            return [], "graphiti: timeout"

        with patch(
            "agentic_rag.mastery_injection._search_via_memory_service",
            new=_degraded_empty,
        ):
            text, reason = await retrieve_learning_memories("n1", group_id="vault:x")

        assert text == ""
        assert reason is not None, "降级+空 不得伪装成「真的没有记忆」"
        assert reason.startswith(MEMORY_DEGRADED_SERVICE)
        assert "timeout" in reason

    @pytest.mark.asyncio
    async def test_genuine_empty_still_has_no_reason(self):
        """反向锁: 检索成功且真无命中 → reason 仍为 None (空是事实)。"""
        from agentic_rag.mastery_injection import retrieve_learning_memories

        async def _clean_empty(node_id, group_id, limit=10):
            return [], None

        with patch(
            "agentic_rag.mastery_injection._search_via_memory_service",
            new=_clean_empty,
        ):
            text, reason = await retrieve_learning_memories("n1", group_id="vault:x")

        assert text == ""
        assert reason is None


class TestRealUnreachableBolt:
    @pytest.mark.asyncio
    async def test_unreachable_bolt_address_yields_unavailable(self):
        """真实不可达地址 (bolt://localhost:1) — 读路径不得假装空成功.

        走 Neo4jClient 真连接失败路径 (非 mock), 验证 search_memories_with_status
        把连接层失败如实上报为 unavailable/degraded 而非 ok/empty。
        (7692 真库正向路径归 integration 门测试, 本 unit 只锁故障向。)
        """
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes_recovered = True

        from app.clients.neo4j_client import Neo4jClient

        bad_client = Neo4jClient(uri="bolt://localhost:1", user="neo4j", password="x")
        svc.neo4j = bad_client

        # Graphiti worker 不在 → Tier1 fail; Tier2 真连接拒绝 → fail
        result = await svc.search_memories_with_status("any query")
        assert result.status in (ServiceStatus.UNAVAILABLE, ServiceStatus.DEGRADED)
        if result.status is ServiceStatus.UNAVAILABLE:
            assert result.reason


class TestRagServiceFourStates:
    @pytest.mark.asyncio
    async def test_query_with_fallback_unavailable_carries_status(self):
        from app.services.rag_service import RAGService

        svc = RAGService()
        with patch("app.services.rag_service.LANGGRAPH_AVAILABLE", False):
            result = await svc.query_with_fallback("q")

        assert result["retrieval_status"] == "unavailable"
        assert result["retrieval_status_reason"]

    @pytest.mark.asyncio
    async def test_query_with_fallback_error_carries_status(self):
        from app.services.rag_service import RAGService

        svc = RAGService()
        with patch.object(
            svc, "query", new=AsyncMock(side_effect=RuntimeError("boom"))
        ):
            with patch("app.services.rag_service.LANGGRAPH_AVAILABLE", True):
                result = await svc.query_with_fallback("q")

        assert result["retrieval_status"] == "unavailable"
        assert "boom" in result["retrieval_status_reason"]

    @pytest.mark.asyncio
    async def test_internal_fallback_result_carries_unavailable(self):
        """第三个空结果出口 (_get_fallback_result, 如 ainvoke 返回 None):
        空载荷不可信 = unavailable, 不得伪装 empty."""
        from app.services.rag_service import RAGService

        svc = RAGService()
        result = svc._get_fallback_result(fallback_reason="ainvoke_returned_none")

        assert result["retrieval_status"] == "unavailable"
        assert "ainvoke_returned_none" in result["retrieval_status_reason"]
        assert result["fallback_used"] is True  # 原有键不动

    @pytest.mark.asyncio
    async def test_get_weak_concepts_with_status_unavailable_on_failure(self):
        from app.services.rag_service import RAGService

        svc = RAGService()
        with patch("app.services.rag_service.LANGGRAPH_AVAILABLE", True):
            with patch(
                "app.clients.graphiti_client.get_learning_memory_client",
                side_effect=RuntimeError("client init failed"),
            ):
                result = await svc.get_weak_concepts_with_status("c.canvas")

        assert result.status is ServiceStatus.UNAVAILABLE
        assert result.reason

    @pytest.mark.asyncio
    async def test_initialize_returning_false_is_unavailable(self):
        """Codex round-1 HIGH-9: 客户端 initialize() 坏 JSON/权限错误时
        返回 False 而**不抛异常**, 后续默认 _data 产出 [] —— 不检查布尔
        值就会把它报成 empty。"""
        from app.services.rag_service import RAGService

        svc = RAGService()
        client = AsyncMock()
        client.initialize = AsyncMock(return_value=False)
        client.get_learning_history = AsyncMock(return_value=[])

        with patch("app.services.rag_service.LANGGRAPH_AVAILABLE", True):
            with patch(
                "app.clients.graphiti_client.get_learning_memory_client",
                return_value=client,
            ):
                result = await svc.get_weak_concepts_with_status("c.canvas")

        assert result.status is ServiceStatus.UNAVAILABLE
        assert "False" in result.reason or "不可信" in result.reason

    @pytest.mark.asyncio
    async def test_initialize_true_with_empty_history_is_empty(self):
        """反向锁: 初始化成功 + 真无历史 → empty (无 reason)。"""
        from app.services.rag_service import RAGService

        svc = RAGService()
        client = AsyncMock()
        client.initialize = AsyncMock(return_value=True)
        client.get_learning_history = AsyncMock(return_value=[])

        with patch("app.services.rag_service.LANGGRAPH_AVAILABLE", True):
            with patch(
                "app.clients.graphiti_client.get_learning_memory_client",
                return_value=client,
            ):
                result = await svc.get_weak_concepts_with_status("c.canvas")

        assert result.status is ServiceStatus.EMPTY
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_get_weak_concepts_legacy_list_contract(self):
        from app.services.rag_service import RAGService

        svc = RAGService()
        with patch("app.services.rag_service.LANGGRAPH_AVAILABLE", True):
            with patch(
                "app.clients.graphiti_client.get_learning_memory_client",
                side_effect=RuntimeError("client init failed"),
            ):
                result = await svc.get_weak_concepts("c.canvas")

        assert isinstance(result, list)


class TestNodesChannelErrors:
    @pytest.mark.asyncio
    async def test_init_false_does_not_publish_singleton(self):
        """Codex round-1 BLOCKER-2: 客户端 initialize() 返回 False 时,
        失败实例不得被发布为 singleton —— 否则 enable_fallback 让之后每次
        检索都静默返回 [], 节点 except 永不触发, 且恢复后不会重连。"""
        import sys

        import agentic_rag.nodes  # noqa: F401

        nodes_mod = sys.modules["agentic_rag._nodes_impl"]

        failing_client = AsyncMock()
        failing_client.initialize = AsyncMock(return_value=False)

        nodes_mod._graphiti_client = None
        with patch.object(
            nodes_mod, "GraphitiClient", return_value=failing_client
        ):
            with pytest.raises(RuntimeError):
                await nodes_mod._get_graphiti_client()

        assert nodes_mod._graphiti_client is None, (
            "初始化失败的实例不得留在 singleton (会导致永久假空且不重连)"
        )

    @pytest.mark.asyncio
    async def test_init_false_surfaces_as_channel_error(self):
        """初始化失败必须一路走到 channel_errors, 而不是空结果。"""
        import sys

        import agentic_rag.nodes  # noqa: F401

        nodes_mod = sys.modules["agentic_rag._nodes_impl"]

        failing_client = AsyncMock()
        failing_client.initialize = AsyncMock(return_value=False)
        nodes_mod._lancedb_client = None

        state = {"messages": [{"role": "user", "content": "q"}], "canvas_file": None}
        runtime = type("FakeRuntime", (), {"context": {}})()

        with patch.object(nodes_mod, "LanceDBClient", return_value=failing_client):
            update = await nodes_mod.retrieve_lancedb(state, runtime)

        assert "lancedb" in update.get("channel_errors", {})
        nodes_mod._lancedb_client = None  # 复位, 免污染同进程其他用例

    @pytest.mark.asyncio
    async def test_retrieve_graphiti_failure_lands_in_channel_errors(self):
        """LanceDB/Graphiti 通道失败 → channel_errors 进 state (不再只吞成 []).

        坑注记 (reference_agentic_rag_nodes_ghost_package): agentic_rag.nodes
        是 re-export 包, mock 私有 helper 必须打 ``agentic_rag._nodes_impl``。
        """
        import agentic_rag.nodes  # noqa: F401 — 触发 _nodes_impl 装载
        import sys

        nodes_mod = sys.modules["agentic_rag._nodes_impl"]

        state = {"messages": [{"role": "user", "content": "q"}], "canvas_file": None}
        runtime = type("FakeRuntime", (), {"context": {}})()
        with patch.object(
            nodes_mod,
            "_get_graphiti_client",
            new=AsyncMock(side_effect=RuntimeError("graphiti down")),
        ):
            update = await nodes_mod.retrieve_graphiti(state, runtime)

        assert update["graphiti_results"] == []
        assert "graphiti" in update.get("channel_errors", {})
        assert "graphiti down" in update["channel_errors"]["graphiti"]


class TestFusionStatusFolding:
    """Codex round-1 HIGH-8: 融合层四态折算必须看「已尝试通道」。"""

    @staticmethod
    async def _fuse(state):
        import sys

        import agentic_rag.nodes  # noqa: F401

        nodes_mod = sys.modules["agentic_rag._nodes_impl"]
        runtime = type("FakeRuntime", (), {"context": {}})()
        base = {
            "graphiti_results": [],
            "lancedb_results": [],
            "multimodal_results": [],
            "cross_canvas_results": [],
            "vault_notes_results": [],
            "fusion_strategy": "rrf",
        }
        base.update(state)
        return await nodes_mod.fuse_results(base, runtime)

    @pytest.mark.asyncio
    async def test_one_channel_failed_other_healthy_empty_is_degraded(self):
        """一路失败 + 另一路健康地查到 0 条 → degraded, 不是 unavailable。
        (原实现把它误报成「整个检索系统不可用」)"""
        update = await self._fuse({"channel_errors": {"graphiti": "timeout"}})
        assert update["retrieval_status"] == "degraded"
        assert "graphiti" in update["retrieval_status_reason"]

    @pytest.mark.asyncio
    async def test_all_primary_channels_failed_is_unavailable(self):
        update = await self._fuse(
            {"channel_errors": {"graphiti": "timeout", "lancedb": "conn refused"}}
        )
        assert update["retrieval_status"] == "unavailable"

    @pytest.mark.asyncio
    async def test_coverage_only_failure_is_degraded(self):
        """仅跨学科扩展失败 (覆盖面收窄) → degraded。"""
        update = await self._fuse(
            {"channel_errors": {"lancedb_cross_subject": "neo4j unavailable"}}
        )
        assert update["retrieval_status"] == "degraded"

    @pytest.mark.asyncio
    async def test_clean_empty_is_empty(self):
        update = await self._fuse({})
        assert update["retrieval_status"] == "empty"
        assert update["retrieval_status_reason"] is None

    @pytest.mark.asyncio
    async def test_results_present_is_ok(self):
        hit = {"doc_id": "d1", "content": "c", "score": 0.9, "metadata": {}}
        update = await self._fuse({"graphiti_results": [hit]})
        assert update["retrieval_status"] == "ok"
        assert update["retrieval_status_reason"] is None


def _sink_fail(fail_sink, reason):
    """Helper: 模拟带 fail_sink 契约的私有搜索方法失败 — 记录原因并返回空."""
    if fail_sink is not None:
        fail_sink.append(reason)
    return []
