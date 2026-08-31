# CARD-G4-3 (BATCH-2026-08-31-第七批) — 四态贯穿 API 面 · rag router
"""API 层四态透传测试 — POST /api/v1/rag/query.

G4-2 已经让 ``CanvasRAGState.retrieval_status`` 在 fuse_results 汇聚层被折算
出来 (lib/agentic_rag/nodes.py:589), 并让 rag_service 的三个 fallback 出口
也带上状态 (rag_service.py:226/487/506)。但 ``rag_query`` 端点在把 state
映射成 ``RAGQueryResponse`` 时逐字段挑拣, 状态字段不在挑拣清单里 → 丢弃。

本文件锁**纯透传**语义: 端点是管道, 不是判官。

特别注意 ``None`` 用例 —— state 的初始值就是 None (state.py:274-275), 图若
未走到 fuse_results 就早退, 状态确实是"本次没算出来"。端点此时必须原样透出
null, **不得**归一成 "ok" 或 "empty": 那正是本卡要消灭的"故障伪装成空结果"
的同一种病, 只是换了个发生地点。

[Source: 2026-08-31-第七批开跑手册 §二 G4-3 要点]
"""

from typing import Any, Dict, List, Literal, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.api.v1.endpoints.rag import rag_router
from app.models.service_status import SERVICE_STATUS_VALUES
from app.services.rag_service import get_rag_service

# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


def _state(*, status: Optional[str], reason: Optional[str], results: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """构造 rag_service.query() 返回的 LangGraph state 形态。"""
    return {
        "reranked_results": results
        if results is not None
        else [{"doc_id": "node-1", "content": "逆否命题…", "score": 0.9, "metadata": {}}],
        "multimodal_results": [],
        "quality_grade": "high",
        "graphiti_latency_ms": 12.0,
        "lancedb_latency_ms": 8.0,
        "fusion_latency_ms": 1.0,
        "query_rewritten": False,
        "rewrite_count": 0,
        "fusion_strategy": "rrf",
        "reranking_strategy": "hybrid_auto",
        "retrieval_status": status,
        "retrieval_status_reason": reason,
    }


@pytest.fixture
def mock_rag_service() -> MagicMock:
    service = MagicMock()
    service.query = AsyncMock(return_value=_state(status="ok", reason=None))
    return service


@pytest.fixture
def client(mock_rag_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(rag_router, prefix="/api/v1/rag")

    async def _override_service():
        return mock_rag_service

    app.dependency_overrides[get_rag_service] = _override_service
    return TestClient(app)


def _post(client: TestClient):
    return client.post("/api/v1/rag/query", json={"query": "什么是逆否命题？"})


def _traced_output(spy) -> str:
    """取出 trace 实际写下的 output **字符串**。

    ⚠️ 这个 ``str()`` 不是装饰: ``log_decision`` 内部正是 ``str(output)``。
    而 ``ServiceStatus`` 是 ``class X(str, Enum)``, 它同时满足
    ``ServiceStatus.DEGRADED == "degraded"`` (True) 与
    ``str(ServiceStatus.DEGRADED) == "ServiceStatus.DEGRADED"`` ——
    直接对枚举成员做 ``== "degraded"`` 的断言**恒真**, 看不见归一有没有做。
    (2026-08-31 变异实测: 去掉归一后原断言 61 passed 全绿, 是一道死门。)
    """
    return str(spy.call_args.kwargs["output"])


# ═══════════════════════════════════════════════════════════════════════════
# 纯透传
# ═══════════════════════════════════════════════════════════════════════════


class TestRagQueryFourStatePassthrough:
    @pytest.mark.parametrize(
        "injected_status,injected_reason",
        [
            ("ok", None),
            ("empty", None),
            ("degraded", "graphiti timeout — lancedb 独扛"),
            ("unavailable", "rag fallback: ainvoke returned None"),
        ],
    )
    def test_state_status_reaches_http_surface(self, client, mock_rag_service, injected_status, injected_reason):
        results = [] if injected_status in ("empty", "unavailable") else None
        mock_rag_service.query.return_value = _state(status=injected_status, reason=injected_reason, results=results)

        response = _post(client)

        assert response.status_code == 200
        body = response.json()
        assert body["retrieval_status"] == injected_status
        assert body["retrieval_status_reason"] == injected_reason

    def test_missing_status_stays_null_not_invented(self, client, mock_rag_service):
        """state 未产出状态 → null 原样透出, 端点不许补一个 'ok'。"""
        mock_rag_service.query.return_value = _state(status=None, reason=None)

        body = _post(client).json()

        assert body["retrieval_status"] is None
        assert body["retrieval_status_reason"] is None

    def test_state_key_entirely_absent_is_tolerated(self, client, mock_rag_service):
        """老 state (键根本不存在) 不得让端点 500 — 透传要能吃下缺键。"""
        state = _state(status="ok", reason=None)
        state.pop("retrieval_status")
        state.pop("retrieval_status_reason")
        mock_rag_service.query.return_value = state

        response = _post(client)

        assert response.status_code == 200
        assert response.json()["retrieval_status"] is None

    def test_unavailable_still_returns_200(self, client, mock_rag_service):
        """unavailable 是**载荷不可信**, 不是 HTTP 故障 — 状态码语义不变。

        真正的 503 由 RAGUnavailableError 触发 (服务整体不可达), 与本字段
        表达的"这一次检索的结果不可信"是两件事, 本卡不合并二者。
        """
        mock_rag_service.query.return_value = _state(status="unavailable", reason="all sources down", results=[])

        response = _post(client)

        assert response.status_code == 200
        assert response.json()["result_count"] == 0

    def test_status_value_domain_matches_unified_enum(self, client, mock_rag_service):
        """透出的值必须落在 G4-2 统一枚举值域内 (不得出现第五种词汇)。"""
        for status in SERVICE_STATUS_VALUES:
            mock_rag_service.query.return_value = _state(
                status=status,
                reason="r" if status in ("degraded", "unavailable") else None,
            )
            body = _post(client).json()
            assert body["retrieval_status"] in SERVICE_STATUS_VALUES


# ═══════════════════════════════════════════════════════════════════════════
# trace 对齐
# ═══════════════════════════════════════════════════════════════════════════


class TestRagTraceAlignment:
    def test_degraded_logs_decision_with_enum_value(self, client, mock_rag_service):
        mock_rag_service.query.return_value = _state(status="degraded", reason="graphiti timeout")

        with patch("app.core.decision_tracker.log_decision") as spy:
            _post(client)

        assert spy.call_count == 1
        assert _traced_output(spy) == "degraded"
        assert _traced_output(spy) in SERVICE_STATUS_VALUES

    def test_entry_logger_failure_does_not_break_response(self, client, mock_rag_service):
        """入口 `logger.info` 在主 try **之外** —— 它抛错会让服务一次都没被调用。

        (Codex round-3 HIGH-1: 这是本卡**已修改文件内**的第六个绕过点,
        不能推给"服务层硬边界外"。整改前实测 500 且 `query.await_count == 0`。)
        """
        mock_rag_service.query.return_value = _state(status="ok", reason=None)

        with patch(
            "app.api.v1.endpoints.rag.logger.info",
            side_effect=RuntimeError("entry log sink failed"),
        ):
            response = _post(client)

        assert response.status_code == 200
        assert mock_rag_service.query.await_count == 1, "入口日志抛错把请求打断在服务调用之前"

    @pytest.mark.parametrize("healthy_status", ["ok", "empty"])
    def test_healthy_states_do_not_log_decision(self, client, mock_rag_service, healthy_status):
        """ok **与 empty** 都不落 trace。

        (Codex round-3 MEDIUM-2: 前版只注入 ok, 于是"把 EMPTY 加进
        _TRACEABLE_FAULT_STATES"这个变异**真存活** —— 一个核心语义没有门。)
        """
        mock_rag_service.query.return_value = _state(
            status=healthy_status, reason=None, results=[] if healthy_status == "empty" else None
        )

        with patch("app.core.decision_tracker.log_decision") as spy:
            _post(client)

        assert spy.call_count == 0

    def test_ok_does_not_log_decision(self, client, mock_rag_service):
        mock_rag_service.query.return_value = _state(status="ok", reason=None)

        with patch("app.core.decision_tracker.log_decision") as spy:
            _post(client)

        assert spy.call_count == 0

    def test_null_status_does_not_log_decision(self, client, mock_rag_service):
        """ "没算出状态"不是故障, 不该占用决策日志。"""
        mock_rag_service.query.return_value = _state(status=None, reason=None)

        with patch("app.core.decision_tracker.log_decision") as spy:
            _post(client)

        assert spy.call_count == 0


# ═══════════════════════════════════════════════════════════════════════════
# 契约门: 旧 schema 解析新响应
# ═══════════════════════════════════════════════════════════════════════════


class LegacySearchResultItem(BaseModel):
    doc_id: str
    content: str
    score: float
    metadata: dict = Field(default_factory=dict)


class LegacyMultimodalResultItem(BaseModel):
    id: str
    media_type: Literal["image", "pdf", "audio", "video"]
    path: str
    thumbnail: Optional[str] = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)


class LegacyLatencyInfo(BaseModel):
    graphiti: Optional[float] = None
    lancedb: Optional[float] = None
    multimodal: Optional[float] = None
    fusion: Optional[float] = None
    reranking: Optional[float] = None


class LegacyRAGQueryMetadata(BaseModel):
    query_rewritten: bool = False
    rewrite_count: int = 0
    fusion_strategy: Optional[str] = None
    reranking_strategy: Optional[str] = None


class LegacyRAGQueryResponse(BaseModel):
    """本卡改动**前** RAGQueryResponse 的**字段契约语义等价副本** (无四态字段)。

    ⚠️ 副本不能图省事写松 (例如把 multimodal_results 写成
    List[dict])。副本一旦比原模型宽松, 这个"加性证明"就成了自证的伪品 ——
    它会放过正是它应当抓住的类型收窄。
    """

    results: List[LegacySearchResultItem] = Field(default_factory=list)
    multimodal_results: List[LegacyMultimodalResultItem] = Field(default_factory=list)
    quality_grade: str = "low"
    result_count: int = 0
    latency_ms: LegacyLatencyInfo = Field(default_factory=LegacyLatencyInfo)
    total_latency_ms: float = 0.0
    metadata: LegacyRAGQueryMetadata = Field(default_factory=LegacyRAGQueryMetadata)


class TestRagAdditiveContract:
    @pytest.mark.parametrize("status", list(SERVICE_STATUS_VALUES) + [None])
    def test_legacy_schema_parses_new_response(self, client, mock_rag_service, status):
        reason = "injected" if status in ("degraded", "unavailable") else None
        mock_rag_service.query.return_value = _state(status=status, reason=reason)

        body = _post(client).json()

        parsed = LegacyRAGQueryResponse.model_validate(body)
        assert parsed.quality_grade == "high"
        assert parsed.result_count == 1

    def test_legacy_nested_multimodal_model_actually_participates(self, client, mock_rag_service):
        """非空 multimodal_results —— 否则嵌套的 Legacy 条目模型是摆设。

        (Codex round-1 LOW-1)
        """
        state = _state(status="ok", reason=None)
        state["multimodal_results"] = [
            {
                "id": "mm-001",
                "media_type": "image",
                "path": "images/逆否命题图解.png",
                "thumbnail": None,
                "relevance_score": 0.87,
                "metadata": {"width": 800},
            }
        ]
        mock_rag_service.query.return_value = state

        body = _post(client).json()
        parsed = LegacyRAGQueryResponse.model_validate(body)

        assert parsed.multimodal_results[0].media_type == "image"
        assert parsed.multimodal_results[0].relevance_score == 0.87
        assert parsed.results[0].doc_id == "node-1"

    def test_legacy_required_keys_all_preserved(self, client):
        body = _post(client).json()

        for key in (
            "results",
            "multimodal_results",
            "quality_grade",
            "result_count",
            "latency_ms",
            "total_latency_ms",
            "metadata",
        ):
            assert key in body, f"旧键 {key} 丢失 — 违反加性"


class TestRagSchemaRequiredSetFrozen:
    """``RAGQueryResponse`` 改动前**没有任何必填字段**, 改动后也必须一个都没有。"""

    def test_required_set_stays_empty(self):
        from app.api.v1.endpoints.rag import RAGQueryResponse

        required = set(RAGQueryResponse.model_json_schema().get("required", []))

        assert required == set(), f"RAGQueryResponse 冒出了必填字段 {required} — 旧构造点会炸, 不是加性"

    def test_status_field_value_domain_is_the_unified_enum(self):
        from app.api.v1.endpoints.rag import RAGQueryResponse

        schema = RAGQueryResponse.model_json_schema()

        assert list(schema["$defs"]["ServiceStatus"]["enum"]) == list(SERVICE_STATUS_VALUES)


# ═══════════════════════════════════════════════════════════════════════════
# 真实入口回归 — Codex round-1 BLOCKER-1
# ═══════════════════════════════════════════════════════════════════════════


class TestRagRealFallbackEntrypoint:
    """走**真实** ``RAGService.query`` 的 unavailable 出口, 不用合成 state。

    为什么必须有这个类: 上面所有用例的 ``_state()`` 都固定给
    ``quality_grade="high"``, 而 rag_service 的三个 fallback 出口
    (:216 / :481 / :500) 实际写的是 ``"quality_grade": None``。端点原先用
    ``result.get("quality_grade", "low")`` —— 默认值只在**键缺失**时生效,
    键存在且为 None 时原样返回 None → 撞 ``quality_grade: str`` 响应模型 → 500。

    也就是说: 「unavailable 仍 200」在合成 state 上成立, 在**真实生产形状**上
    是 500。合成 fixture 与生产形状的这条缝, 正是假绿的藏身处。
    """

    def _real_service_client(self) -> tuple:
        from app.services.rag_service import RAGService, get_rag_service

        svc = RAGService()
        svc._initialized = True  # 跳过初始化, 直接测 query 的 fallback 分支

        app = FastAPI()
        app.include_router(rag_router, prefix="/api/v1/rag")

        async def _override():
            return svc

        app.dependency_overrides[get_rag_service] = _override
        return app, svc

    def test_real_ainvoke_none_fallback_returns_200_unavailable(self):
        app, _ = self._real_service_client()

        with patch("app.services.rag_service.canvas_agentic_rag") as graph:
            graph.ainvoke = AsyncMock(return_value=None)
            with TestClient(app, raise_server_exceptions=False) as c:
                response = c.post("/api/v1/rag/query", json={"query": "什么是逆否命题？"})
            assert graph.ainvoke.await_count == 1, "没走到真实图执行, 这个门就没测到东西"

        assert response.status_code == 200, "真实 fallback 出口返回了非 200 —— 「unavailable 仍 200」在生产形状上不成立"
        body = response.json()
        assert body["retrieval_status"] == "unavailable"
        assert "ainvoke_returned_none" in body["retrieval_status_reason"]
        # quality_grade 是 None 被端点兜成 "low", 不是被丢弃
        assert body["quality_grade"] == "low"
        assert body["results"] == []

    def test_query_with_fallback_exception_exit_reports_unavailable(self):
        """锁住服务层另外两个 fallback 出口的**形状**, 而不是端点行为。

        端点的 ``or "low"`` 兜底是否还有必要, 取决于服务层是否仍会发出
        ``quality_grade=None``。这条门就是那个前提的哨兵: 若服务层哪天改成
        发 ``"low"``, 本门变红, 提醒重新评估端点兜底 (而不是让它悄悄变成
        一段没人知道还需不需要的死代码)。
        """
        import asyncio

        from app.services.rag_service import RAGService

        svc = RAGService()
        svc._initialized = True

        async def _boom(*a, **k):
            raise RuntimeError("graphiti exploded")

        with patch.object(RAGService, "query", new=_boom):
            state = asyncio.run(svc.query_with_fallback("q"))

        assert state["retrieval_status"] == "unavailable"
        assert state["retrieval_status_reason"] == "graphiti exploded"
        # ⚠️ 刻意**不**断言 quality_grade is None (Codex round-2 LOW-1):
        # 那会把上游的合法改进 (哪天服务层改成发 "low") 判成回归 —— 一条在
        # 别人变好时变红的门是噪音。端点的 `or "low"` 防御不需要靠冻结上游
        # 缺陷来证明自己有价值; 它的价值由 TestRagProductionStateShapesAllReturn200
        # 直接证明 (拿生产 state 形态过端点, 恒 200)。这里只锁本出口的四态语义。
        assert state["quality_grade"] in (None, "low", "medium", "high")


# ═══════════════════════════════════════════════════════════════════════════
# trace fail-open — Codex round-1 HIGH-1
# ═══════════════════════════════════════════════════════════════════════════


class TestRagTraceFailOpen:
    def test_trace_sink_failure_does_not_break_the_response(self, client, mock_rag_service):
        """落账炸了只损失可观测性, 不得把本该 200 的降级响应变成 500。

        整改前实测: patch 真实落账函数抛错 → /rag/query 返回 500。
        """
        mock_rag_service.query.return_value = _state(status="degraded", reason="graphiti timeout")

        with patch(
            "app.core.decision_tracker.log_decision",
            side_effect=RuntimeError("trace sink failed"),
        ) as spy:
            response = _post(client)

        assert response.status_code == 200
        body = response.json()
        assert body["retrieval_status"] == "degraded"
        assert body["retrieval_status_reason"] == "graphiti timeout"
        assert spy.call_count == 1, "落账根本没被调用 —— 这条门在测一个不存在的场景"

    def test_both_sink_and_fallback_logger_failing_still_returns_200(self, client, mock_rag_service):
        """落账**和**降级 logger 同时坏掉 (Codex round-2 MEDIUM-1 的缺口)。"""
        mock_rag_service.query.return_value = _state(status="unavailable", reason="all sources down", results=[])

        with (
            patch(
                "app.core.decision_tracker.log_decision",
                side_effect=RuntimeError("trace sink failed"),
            ) as spy,
            patch(
                "app.core.decision_tracker.logger.exception",
                side_effect=RuntimeError("logging backend is also dead"),
            ) as log_spy,
        ):
            response = _post(client)

        assert response.status_code == 200
        assert response.json()["retrieval_status"] == "unavailable"
        assert response.json()["retrieval_status_reason"] == "all sources down"
        assert spy.call_count == 1
        assert log_spy.call_count == 1, "二级兜底路径没走到"


class TestRagProductionStateShapesAllReturn200:
    """机械门: 把**生产真实产出的 state 形态**逐个喂给端点, 断言恒 200。

    为什么需要这道门 (Codex round-1 BLOCKER-1 的教训):
    BLOCKER 的本体不是"某个字段写错了", 而是**合成 fixture 与生产形状之间有缝**。
    逐字段人眼比对能查出已知的那一颗地雷, 查不出第二颗。这道门换个思路 ——
    不比对字段, 直接拿生产形态过一遍端点, 让 pydantic 自己去炸。

    覆盖的形态:
    - `create_initial_state()` —— 图未执行/早退时的 state (含 quality_grade=None,
      所有 latency 为 None, retrieval_status=None);
    - `_get_fallback_result()` —— rag_service 的 fallback 出口 (retrieval_status=unavailable)。

    若将来有人往 state 里加一个 `None` 值而端点用 `.get(k, 默认)` 取它, 这道门
    会在那一刻变红, 不用等到线上 500。
    """

    def _post_with_state(self, mock_rag_service, client, state):
        mock_rag_service.query.return_value = state
        return _post(client)

    def test_create_initial_state_shape_returns_200(self, client, mock_rag_service):
        from lib.agentic_rag.state import create_initial_state

        state = create_initial_state()
        response = self._post_with_state(mock_rag_service, client, state)

        assert response.status_code == 200, (
            f"图初始 state 形态把端点打崩了 —— 早退路径会 500。state 键: {sorted(state)[:12]}…"
        )
        body = response.json()
        assert body["quality_grade"] == "low", "初始 state 的 quality_grade=None 必须被兜成 low"
        assert body["retrieval_status"] is None

    @pytest.mark.parametrize("reason", ["ainvoke_returned_none", "some_other_reason"])
    def test_fallback_result_shape_returns_200(self, client, mock_rag_service, reason):
        from app.services.rag_service import RAGService

        state = RAGService()._get_fallback_result(reason)
        response = self._post_with_state(mock_rag_service, client, state)

        assert response.status_code == 200
        body = response.json()
        assert body["retrieval_status"] == "unavailable"
        assert body["quality_grade"] == "low"
        assert body["result_count"] == 0
