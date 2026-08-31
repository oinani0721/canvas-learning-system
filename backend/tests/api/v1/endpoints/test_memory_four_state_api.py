# CARD-G4-3 (BATCH-2026-08-31-第七批) — 四态贯穿 API 面 · memory router
"""API 层四态注入测试 — GET /episodes / /concepts/{id}/history / /review-suggestions.

本卡的命题只有一句: **API 边界不许把服务层已经算出来的状态丢掉, 也不许自己
发明状态**。G4-2 已经让 MemoryService 三条读路径返回 ok/empty/degraded/
unavailable, 但端点在构造响应模型时把这两个键静默丢弃 (pydantic 默认
extra=ignore), 于是「Neo4j 挂了」在 HTTP 面上和「这个概念没学过」长得一模一样。

测试策略 = **注入而非真实故障**: mock 服务层分别返回 ok / degraded /
unavailable, 断言 HTTP 响应里的字段值逐字等于注入值。这样测的是「透传管道
是否漏水」, 而不是「Neo4j 能不能被弄挂」——后者是 G4-2 服务层卡的战场。

三条不变量 (每条都有对应用例):
1. **透传纯度** — 端点不改写服务层给的状态 (含 unavailable 这种服务层当前
   走不到、但未来可能走到的值; 端点若"聪明"地把它归一成 empty 就是重犯本卡
   要修的病)。
2. **200 语义不变** — 三态下状态码恒 200。特别是 unavailable **不得**被
   顺手改成 503: 那会让所有旧客户端从"拿到空列表"变成"拿到 5xx", 比换信封
   更狠的破坏。
3. **trace 对齐** — 故障态 (degraded/unavailable) 落 log_decision, 且
   output 是统一枚举的 **.value**。这条有真坑: ``class ServiceStatus(str, Enum)``
   的 ``str()`` 返回 ``'ServiceStatus.OK'`` 而非 ``'ok'`` (只有 StrEnum 才
   返回 value), 而 log_decision 内部正是 ``str(output)`` —— 传枚举本身会
   静默写出错值。

[Source: 2026-08-31-第七批开跑手册 §二 G4-3 要点]
[Source: app/models/service_status.py — G4-2 统一四态定义]
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.v1.endpoints.memory import get_memory_service, memory_router
from app.models.service_status import SERVICE_STATUS_VALUES, StatusedResult
from app.security import require_internal_api_key

# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


def _history_payload(*, status: str, reason: Optional[str], items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构造 MemoryService.get_learning_history 的返回形态 (含 G4-2 加性键)。"""
    return {
        "items": items,
        "total": len(items),
        "page": 1,
        "page_size": 50,
        "pages": 1 if items else 0,
        "retrieval_status": status,
        "retrieval_status_reason": reason,
    }


def _episode_item() -> Dict[str, Any]:
    return {
        "episode_id": "episode-001",
        "user_id": "user-001",
        "canvas_path": "数学/离散数学.canvas",
        "node_id": "node-001",
        "concept": "逆否命题",
        "agent_type": "scoring-agent",
        "score": 85,
        "duration_seconds": 300,
        "timestamp": "2026-08-31T10:30:00",
    }


def _concept_payload(*, status: str, reason: Optional[str], timeline: List[Dict]) -> Dict:
    """构造 MemoryService.get_concept_history 的返回形态。"""
    return {
        "concept_id": "concept-123",
        "timeline": timeline,
        "score_trend": {"first": None, "last": None, "average": None, "improvement": None},
        "total_reviews": len(timeline),
        "retrieval_status": status,
        "retrieval_status_reason": reason,
    }


def _suggestion_item() -> Dict[str, Any]:
    return {
        "concept": "逆否命题",
        "concept_id": "concept-123",
        "last_score": 60,
        "review_count": 2,
        "due_date": "2026-08-31T00:00:00",
        "priority": "high",
    }


@pytest.fixture
def mock_memory_service() -> MagicMock:
    service = MagicMock()
    service.get_learning_history = AsyncMock(
        return_value=_history_payload(status="ok", reason=None, items=[_episode_item()])
    )
    service.get_concept_history = AsyncMock(return_value=_concept_payload(status="ok", reason=None, timeline=[]))
    service.get_review_suggestions_with_status = AsyncMock(return_value=StatusedResult.from_items([_suggestion_item()]))
    return service


@pytest.fixture
def client(mock_memory_service: MagicMock) -> TestClient:
    """裸挂 memory_router 的最小 app — 不拖 app.main 的全量启动副作用。"""
    app = FastAPI()
    app.include_router(memory_router, prefix="/api/v1/memory")

    async def _override_service():
        yield mock_memory_service

    app.dependency_overrides[get_memory_service] = _override_service
    # 鉴权不是本卡战场: 显式旁路, 让失败信号只可能来自四态字段本身。
    app.dependency_overrides[require_internal_api_key] = lambda: None
    return TestClient(app)


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
# 不变量 1+2: 透传纯度 × 200 语义不变 — GET /episodes
# ═══════════════════════════════════════════════════════════════════════════


class TestEpisodesFourState:
    @pytest.mark.parametrize(
        "injected_status,injected_reason",
        [
            ("ok", None),
            ("empty", None),
            ("degraded", "Neo4j unreachable — 内存兜底接管"),
            ("unavailable", "ConnectionRefusedError: bolt://localhost:7687"),
        ],
    )
    def test_status_is_passed_through_verbatim(self, client, mock_memory_service, injected_status, injected_reason):
        """服务层给什么状态, HTTP 面就透出什么状态 — 端点零改写。"""
        items = [_episode_item()] if injected_status == "ok" else []
        mock_memory_service.get_learning_history.return_value = _history_payload(
            status=injected_status, reason=injected_reason, items=items
        )

        response = client.get("/api/v1/memory/episodes?user_id=user-001")

        assert response.status_code == 200, "四态注入下状态码恒 200 (unavailable 不得升 5xx)"
        body = response.json()
        assert body["retrieval_status"] == injected_status
        assert body["retrieval_status_reason"] == injected_reason

    def test_absent_service_keys_yield_null_not_invented_status(self, client, mock_memory_service):
        """服务层没给状态时端点返回 null — 不许自己编一个 ok 出来。

        「没有状态」和「状态是 ok」是两件事; 后者是本卡要消灭的伪装。
        """
        mock_memory_service.get_learning_history.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
            "pages": 0,
        }

        body = client.get("/api/v1/memory/episodes?user_id=user-001").json()

        assert body["retrieval_status"] is None
        assert body["retrieval_status_reason"] is None

    def test_legacy_required_keys_all_preserved(self, client, mock_memory_service):
        """加性铁律: 旧必填键一个不少, 类型不漂移。"""
        body = client.get("/api/v1/memory/episodes?user_id=user-001").json()

        for key in ("items", "total", "page", "page_size", "pages"):
            assert key in body, f"旧必填键 {key} 丢失 — 违反加性"
        assert isinstance(body["items"], list)
        assert isinstance(body["total"], int)
        assert body["items"][0]["episode_id"] == "episode-001"


# ═══════════════════════════════════════════════════════════════════════════
# GET /concepts/{id}/history
# ═══════════════════════════════════════════════════════════════════════════


class TestConceptHistoryFourState:
    @pytest.mark.parametrize(
        "injected_status,injected_reason",
        [
            ("ok", None),
            ("empty", None),
            ("degraded", "partial timeline — graphiti down"),
            ("unavailable", "RuntimeError: driver closed"),
        ],
    )
    def test_status_is_passed_through_verbatim(self, client, mock_memory_service, injected_status, injected_reason):
        timeline = (
            [{"timestamp": "2026-08-31T10:00:00", "score": 80, "review_count": 1}] if injected_status == "ok" else []
        )
        mock_memory_service.get_concept_history.return_value = _concept_payload(
            status=injected_status, reason=injected_reason, timeline=timeline
        )

        response = client.get("/api/v1/memory/concepts/concept-123/history")

        assert response.status_code == 200
        body = response.json()
        assert body["retrieval_status"] == injected_status
        assert body["retrieval_status_reason"] == injected_reason

    def test_unavailable_empty_timeline_is_distinguishable_from_empty(self, client, mock_memory_service):
        """本卡的产品命题: 两个空 timeline 必须能被区分。"""
        mock_memory_service.get_concept_history.return_value = _concept_payload(
            status="empty", reason=None, timeline=[]
        )
        truly_empty = client.get("/api/v1/memory/concepts/c/history").json()

        mock_memory_service.get_concept_history.return_value = _concept_payload(
            status="unavailable", reason="neo4j down", timeline=[]
        )
        broken = client.get("/api/v1/memory/concepts/c/history").json()

        assert truly_empty["timeline"] == broken["timeline"] == []
        assert truly_empty["retrieval_status"] != broken["retrieval_status"], (
            "两个空 timeline 在 HTTP 面上不可区分 — 本卡的全部意义就在这一行"
        )

    def test_legacy_required_keys_all_preserved(self, client):
        body = client.get("/api/v1/memory/concepts/concept-123/history").json()

        for key in ("concept_id", "timeline", "score_trend", "total_reviews"):
            assert key in body, f"旧必填键 {key} 丢失 — 违反加性"


# ═══════════════════════════════════════════════════════════════════════════
# GET /review-suggestions — 拍板项 1: 裸列表 → 信封 (破坏性, 非加性)
# ═══════════════════════════════════════════════════════════════════════════


class TestReviewSuggestionsEnvelope:
    @pytest.mark.parametrize(
        "factory,expected_status,expected_reason",
        [
            (lambda: StatusedResult.from_items([_suggestion_item()]), "ok", None),
            (lambda: StatusedResult.from_items([]), "empty", None),
            (
                lambda: StatusedResult.degraded([_suggestion_item()], "graphiti down"),
                "degraded",
                "graphiti down",
            ),
            (
                lambda: StatusedResult.unavailable("ConnectionRefusedError: bolt"),
                "unavailable",
                "ConnectionRefusedError: bolt",
            ),
        ],
    )
    def test_envelope_carries_status(self, client, mock_memory_service, factory, expected_status, expected_reason):
        mock_memory_service.get_review_suggestions_with_status.return_value = factory()

        response = client.get("/api/v1/memory/review-suggestions?user_id=user-001")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, dict), "拍板项 1: 顶层已换信封 (裸 list 无处可加性)"
        assert body["retrieval_status"] == expected_status
        assert body["retrieval_status_reason"] == expected_reason
        assert isinstance(body["items"], list)

    def test_items_payload_shape_unchanged(self, client):
        """信封换了, **条目自身**的字段契约一个字不动。"""
        body = client.get("/api/v1/memory/review-suggestions?user_id=user-001").json()

        item = body["items"][0]
        for key in ("concept", "concept_id", "last_score", "review_count", "due_date", "priority"):
            assert key in item, f"条目字段 {key} 丢失 — 信封化不得殃及条目契约"
        assert item["priority"] in ("high", "medium", "low")

    def test_endpoint_consumes_status_aware_service_method(self, client, mock_memory_service):
        """端点必须调 _with_status 版 — 调委托版就等于在源头把状态丢了。"""
        client.get("/api/v1/memory/review-suggestions?user_id=user-001")

        mock_memory_service.get_review_suggestions_with_status.assert_awaited()

    def test_unavailable_returns_200_with_empty_items(self, client, mock_memory_service):
        """unavailable 不是 5xx: 载荷空但可信度由字段承载, 状态码语义不变。"""
        mock_memory_service.get_review_suggestions_with_status.return_value = StatusedResult.unavailable("neo4j down")

        response = client.get("/api/v1/memory/review-suggestions?user_id=user-001")

        assert response.status_code == 200
        assert response.json()["items"] == []


# ═══════════════════════════════════════════════════════════════════════════
# 不变量 3: trace 面与统一枚举对齐
# ═══════════════════════════════════════════════════════════════════════════


class TestMemoryTraceAlignment:
    def test_degraded_logs_decision_with_enum_value(self, client, mock_memory_service):
        """故障态落 trace, 且 output 是枚举 .value ('degraded') 而非 'ServiceStatus.DEGRADED'。"""
        mock_memory_service.get_learning_history.return_value = _history_payload(
            status="degraded", reason="neo4j flaky", items=[]
        )

        with patch("app.core.decision_tracker.log_decision") as spy:
            client.get("/api/v1/memory/episodes?user_id=user-001")

        assert spy.call_count == 1
        output = _traced_output(spy)
        assert output in SERVICE_STATUS_VALUES, (
            f"trace output {output!r} 不在统一枚举值域内 — "
            "传枚举本身会被 log_decision 的 str() 写成 'ServiceStatus.DEGRADED'"
        )
        assert output == "degraded"
        assert "neo4j flaky" in spy.call_args.kwargs["reason"]

    @pytest.mark.parametrize("healthy_status", ["ok", "empty"])
    def test_healthy_states_do_not_spam_trace(self, client, mock_memory_service, healthy_status):
        """ok **与 empty** 都不落 trace — 正常流量不该淹没决策日志。

        (Codex round-3 MEDIUM-2: 前版 docstring 写着"ok/empty"却**只注入了 ok**,
        于是"把 EMPTY 加进 _TRACEABLE_FAULT_STATES"这个变异真存活 ——
        文档说覆盖了、代码没覆盖, 是最难发现的那类空洞。)
        """
        mock_memory_service.get_learning_history.return_value = _history_payload(
            status=healthy_status,
            reason=None,
            items=[_episode_item()] if healthy_status == "ok" else [],
        )

        with patch("app.core.decision_tracker.log_decision") as spy:
            client.get("/api/v1/memory/episodes?user_id=user-001")

        assert spy.call_count == 0

    def test_review_suggestions_unavailable_logs_decision(self, client, mock_memory_service):
        mock_memory_service.get_review_suggestions_with_status.return_value = StatusedResult.unavailable("bolt refused")

        with patch("app.core.decision_tracker.log_decision") as spy:
            client.get("/api/v1/memory/review-suggestions?user_id=user-001")

        assert spy.call_count == 1
        assert _traced_output(spy) == "unavailable"

    def test_concept_history_degraded_logs_decision(self, client, mock_memory_service):
        mock_memory_service.get_concept_history.return_value = _concept_payload(
            status="degraded", reason="partial", timeline=[]
        )

        with patch("app.core.decision_tracker.log_decision") as spy:
            client.get("/api/v1/memory/concepts/c/history")

        assert spy.call_count == 1
        assert _traced_output(spy) == "degraded"


# ═══════════════════════════════════════════════════════════════════════════
# 契约门: 旧 schema 解析新响应零失败
# ═══════════════════════════════════════════════════════════════════════════


class LegacyLearningHistoryItem(BaseModel):
    """本卡改动**前** LearningHistoryItem 的字段契约语义等价副本。"""

    episode_id: str
    user_id: str
    canvas_path: str
    node_id: str
    concept: str
    agent_type: str
    score: Optional[int] = None
    duration_seconds: Optional[int] = None
    timestamp: str


class LegacyLearningHistoryResponse(BaseModel):
    """本卡改动**前** LearningHistoryResponse 的字段契约语义等价副本 (无四态字段)。"""

    items: List[LegacyLearningHistoryItem]
    total: int
    page: int
    page_size: int
    pages: int


class LegacyScoreTrend(BaseModel):
    first: Optional[int] = None
    last: Optional[int] = None
    average: Optional[float] = None
    improvement: Optional[int] = None


class LegacyConceptHistoryTimeline(BaseModel):
    timestamp: Optional[str] = None
    score: Optional[int] = None
    user_id: Optional[str] = None
    concept: Optional[str] = None
    review_count: int = 0


class LegacyConceptHistoryResponse(BaseModel):
    """本卡改动**前** ConceptHistoryResponse 的字段契约语义等价副本。"""

    concept_id: str
    timeline: List[LegacyConceptHistoryTimeline]
    score_trend: LegacyScoreTrend
    total_reviews: int


class TestMemoryAdditiveContract:
    """加性证明: 用旧模型解析新响应, 通过即证明「旧必填键全保留 + 类型未漂移」。

    这比肉眼看 diff 强 —— diff 只能看出"加了字段", 看不出"某个旧字段的类型
    被顺手改窄了"。

    副本的性质: **语义等价副本**, 不是源码字节级复制 —— 字段名/必填性/类型/
    默认值/约束逐项对照 ``git show HEAD:...`` 抄写, 但省略 description 与
    example (它们不参与校验)。措辞上不宣称"逐字"。
    """

    @pytest.mark.parametrize("status", list(SERVICE_STATUS_VALUES))
    def test_legacy_schema_parses_episodes_under_all_states(self, client, mock_memory_service, status):
        items = [_episode_item()] if status in ("ok", "degraded") else []
        reason = "injected" if status in ("degraded", "unavailable") else None
        mock_memory_service.get_learning_history.return_value = _history_payload(
            status=status, reason=reason, items=items
        )

        body = client.get("/api/v1/memory/episodes?user_id=user-001").json()

        parsed = LegacyLearningHistoryResponse.model_validate(body)
        assert parsed.total == len(items)

    def test_legacy_nested_timeline_model_actually_participates(self, client, mock_memory_service):
        """非空 timeline —— 否则嵌套的 Legacy 条目模型根本没被解析到。

        (Codex round-1 LOW-1: 全用 timeline=[] 时 LegacyConceptHistoryTimeline
        与 LegacyScoreTrend 是摆设, 它们的字段契约实际从未被验证过。)
        """
        mock_memory_service.get_concept_history.return_value = {
            "concept_id": "concept-123",
            "timeline": [
                {
                    "timestamp": "2026-08-31T10:00:00",
                    "score": 80,
                    "user_id": "user-001",
                    "concept": "逆否命题",
                    "review_count": 3,
                }
            ],
            "score_trend": {"first": 60, "last": 80, "average": 70.0, "improvement": 20},
            "total_reviews": 1,
            "retrieval_status": "ok",
            "retrieval_status_reason": None,
        }

        body = client.get("/api/v1/memory/concepts/concept-123/history").json()
        parsed = LegacyConceptHistoryResponse.model_validate(body)

        assert parsed.timeline[0].score == 80
        assert parsed.timeline[0].review_count == 3
        assert parsed.score_trend.improvement == 20

    @pytest.mark.parametrize("status", list(SERVICE_STATUS_VALUES))
    def test_legacy_schema_parses_concept_history_under_all_states(self, client, mock_memory_service, status):
        reason = "injected" if status in ("degraded", "unavailable") else None
        mock_memory_service.get_concept_history.return_value = _concept_payload(
            status=status, reason=reason, timeline=[]
        )

        body = client.get("/api/v1/memory/concepts/concept-123/history").json()

        parsed = LegacyConceptHistoryResponse.model_validate(body)
        assert parsed.concept_id == "concept-123"

    def test_review_suggestions_envelope_is_declared_breaking_not_additive(self, client):
        """拍板项 1 的**如实登记**: 这一处不是加性, 旧裸 list 消费方会炸。

        实测零生产消费方 (grep 证据见验收单), 故按手册推荐换信封; 但本测试
        存在的意义是让「破坏性」在测试里有名有姓, 而不是被"加性"的措辞掩盖。
        """
        body = client.get("/api/v1/memory/review-suggestions?user_id=user-001").json()

        assert not isinstance(body, list), "若这里又变回 list, 说明信封被回退 — 请同步撤回验收单的豁免记录"
        assert set(body.keys()) == {"items", "retrieval_status", "retrieval_status_reason"}


# ═══════════════════════════════════════════════════════════════════════════
# trace 归一的真坑: 枚举 vs value
# ═══════════════════════════════════════════════════════════════════════════


class TestMemoryTraceEnumNormalization:
    """服务层给枚举**本身**时, trace 里也必须是 'degraded' 而非 'ServiceStatus.DEGRADED'。

    这不是假想: ``StatusedResult.status`` 就是枚举 (review-suggestions 路径
    走的正是这一支), 而 dict 路径给的是 value 字符串 —— 同一个 trace 入口
    要同时吃下两种形态。
    """

    def test_enum_valued_status_normalizes_in_trace_and_body(self, client, mock_memory_service):
        from app.models.service_status import ServiceStatus

        payload = _history_payload(status="degraded", reason="neo4j flaky", items=[])
        payload["retrieval_status"] = ServiceStatus.DEGRADED  # 枚举本身, 非 .value
        mock_memory_service.get_learning_history.return_value = payload

        with patch("app.core.decision_tracker.log_decision") as spy:
            body = client.get("/api/v1/memory/episodes?user_id=user-001").json()

        assert _traced_output(spy) == "degraded"
        assert "ServiceStatus" not in _traced_output(spy), (
            "log_decision 内部 str(output) 会把 str+Enum 写成 'ServiceStatus.DEGRADED'"
        )
        assert body["retrieval_status"] == "degraded"

    def test_out_of_domain_status_fails_loud_not_silently_passed_through(self, mock_memory_service):
        """越界脏值不被静默透出 —— 值域由 schema 强制, 代价是响应校验失败。

        **如实登记的行为变更**: 服务层若给出四态以外的值, 响应校验失败 (5xx),
        而不是把第五种状态原样送给客户端。这正是"用枚举而非裸 str"的意义:
        词汇分裂当场暴露。生产路径不受影响 —— 服务层三处出口实测只发
        ServiceStatus 的四个 value (见验收单 §三)。
        """
        payload = _history_payload(status="ok", reason=None, items=[])
        payload["retrieval_status"] = "sort-of-ok"  # 第五种词汇
        mock_memory_service.get_learning_history.return_value = payload

        app = FastAPI()
        app.include_router(memory_router, prefix="/api/v1/memory")

        async def _override_service():
            yield mock_memory_service

        app.dependency_overrides[get_memory_service] = _override_service
        app.dependency_overrides[require_internal_api_key] = lambda: None
        # raise_server_exceptions=False → 让服务端异常表现为 HTTP 5xx 而非
        # 直接把异常抛进测试, 这样断言的是**客户端实际看到什么**。
        with TestClient(app, raise_server_exceptions=False) as c:
            response = c.get("/api/v1/memory/episodes?user_id=user-001")

        assert response.status_code >= 500


# ═══════════════════════════════════════════════════════════════════════════
# 机械加性门: required 集合逐字锁死
# ═══════════════════════════════════════════════════════════════════════════


class TestMemorySchemaRequiredSetsFrozen:
    """比对 JSON Schema 的 ``required`` 集合与改动前逐字相等。

    与上面的 Legacy 副本解析互补, 且不依赖我手抄副本的忠实度 —— 副本可能抄松,
    这里的期望值直接来自 ``git show HEAD:backend/app/models/memory_schemas.py``
    的字面枚举, 一个字都不能多不能少:

    - 少一个 → 旧必填键被降级成可选 (旧客户端可能拿到缺键的响应)
    - 多一个 → 新字段被写成必填 (旧构造点全炸, 且不再是"加性")
    """

    # 改动前 (HEAD 9cf0fb85) 的 required 集合, 逐字抄录
    LEGACY_REQUIRED = {
        "LearningHistoryResponse": {"items", "total", "page", "page_size", "pages"},
        "ConceptHistoryResponse": {
            "concept_id",
            "timeline",
            "score_trend",
            "total_reviews",
        },
        "LearningHistoryItem": {
            "episode_id",
            "user_id",
            "canvas_path",
            "node_id",
            "concept",
            "agent_type",
            "timestamp",
        },
        "ReviewSuggestionResponse": {
            "concept",
            "concept_id",
            "review_count",
            "due_date",
            "priority",
        },
    }

    @pytest.mark.parametrize("model_name", sorted(LEGACY_REQUIRED))
    def test_required_set_unchanged(self, model_name):
        from app.models import memory_schemas

        model = getattr(memory_schemas, model_name)
        actual = set(model.model_json_schema().get("required", []))

        assert actual == self.LEGACY_REQUIRED[model_name], (
            f"{model_name} 的 required 集合变了 — 这不是加性。"
            f"多出: {actual - self.LEGACY_REQUIRED[model_name]}；"
            f"丢失: {self.LEGACY_REQUIRED[model_name] - actual}"
        )

    def test_new_status_fields_are_optional_everywhere(self):
        """四态字段在所有承载它的模型上都必须是可选的。"""
        from app.models.memory_schemas import (
            ConceptHistoryResponse,
            LearningHistoryResponse,
            ReviewSuggestionsResponse,
        )

        for model in (
            LearningHistoryResponse,
            ConceptHistoryResponse,
            ReviewSuggestionsResponse,
        ):
            required = set(model.model_json_schema().get("required", []))
            assert "retrieval_status" not in required
            assert "retrieval_status_reason" not in required
            # 无参构造得能成立 (信封) / 或至少字段有默认值
            assert model.model_fields["retrieval_status"].default is None
            assert model.model_fields["retrieval_status_reason"].default is None

    @pytest.mark.parametrize(
        "model_name",
        ["LearningHistoryResponse", "ConceptHistoryResponse", "ReviewSuggestionsResponse"],
    )
    def test_status_field_value_domain_is_the_unified_enum(self, model_name):
        """**每个**承载四态的模型, 其值域都必须正好是四态, 不多不少。

        ⚠️ 必须逐模型参数化 (Codex round-4 MEDIUM-2): 前版只检查
        ``LearningHistoryResponse`` 一个, 于是把 ``ConceptHistoryResponse`` 或
        ``ReviewSuggestionsResponse`` 的字段类型从枚举改回 ``Optional[str]``
        这两个变异**真存活** (79 passed 全绿)。
        "检查了一个模型"不等于"检查了这个不变量" —— 同型点必须逐个上门。
        """
        from app.models import memory_schemas

        model = getattr(memory_schemas, model_name)
        schema = model.model_json_schema()

        assert "ServiceStatus" in schema.get("$defs", {}), (
            f"{model_name}.retrieval_status 不再引用 ServiceStatus 枚举 —— "
            "OpenAPI 的值域约束会消失, 第五种词汇可以混进来"
        )
        assert list(schema["$defs"]["ServiceStatus"]["enum"]) == list(SERVICE_STATUS_VALUES)


# ═══════════════════════════════════════════════════════════════════════════
# trace fail-open — Codex round-1 HIGH-1
# ═══════════════════════════════════════════════════════════════════════════


class TestMemoryTraceFailOpen:
    """落账异常必须被隔离在观测面内。

    整改前实测: patch 真实 ``log_decision`` 抛错 → ``/memory/episodes`` 返回
    500, **且** 外层 except 把它误报成 ``"Failed to query learning history:
    trace sink failed"`` —— 查询其实成功了, 错误信息在说谎。

    ⚠️ **射程声明**: 本组门只覆盖**本卡引入的那一处**观测调用
    (``log_retrieval_status_decision``)。服务层与 resolver 内部的日志调用
    (``rag_service`` 的 fallback warning、``vault_scope`` 的 warning、
    ``memory_service`` 的 debug/warning/error) 同样能把观测故障升成 5xx,
    但它们在**本卡硬边界之外**, 已登记移交 (见验收单 §十)。
    本组门**不**宣称"端到端 fail-open 已闭合"。

    三条断言缺一不可 (Codex round-2 LOW-3 指出前两版只断言了第一条):
    1. 状态码仍 200 —— 观测面没有污染业务面;
    2. status **与 reason 都逐字不变** —— 落账失败不得顺手改写载荷;
    3. ``log_decision`` 确实被调用过 —— 否则"helper 提前 return 什么都不做"
       这种退化同样能让前两条通过 (那是把门测成摆设)。
    """

    CASES = [
        (
            "/api/v1/memory/episodes?user_id=u",
            "get_learning_history",
            lambda: _history_payload(status="unavailable", reason="neo4j down", items=[]),
            "unavailable",
            "neo4j down",
        ),
        (
            "/api/v1/memory/concepts/c/history",
            "get_concept_history",
            lambda: _concept_payload(status="degraded", reason="partial timeline", timeline=[]),
            "degraded",
            "partial timeline",
        ),
    ]

    @pytest.mark.parametrize("path,setup_key,factory,expect_status,expect_reason", CASES)
    def test_trace_sink_failure_does_not_break_response(
        self, client, mock_memory_service, path, setup_key, factory, expect_status, expect_reason
    ):
        getattr(mock_memory_service, setup_key).return_value = factory()

        with patch(
            "app.core.decision_tracker.log_decision",
            side_effect=RuntimeError("trace sink failed"),
        ) as spy:
            response = client.get(path)

        assert response.status_code == 200, "落账失败把业务响应带崩了 —— 观测面成了失败源"
        body = response.json()
        assert body["retrieval_status"] == expect_status
        assert body["retrieval_status_reason"] == expect_reason
        assert spy.call_count == 1, (
            "落账根本没被调用 —— 这条门在测一个不存在的场景 (helper 若提前 return, 前面的断言照样全过)"
        )

    @pytest.mark.parametrize("path,setup_key,factory,expect_status,expect_reason", CASES)
    def test_both_sink_and_fallback_logger_failing_still_returns_200(
        self, client, mock_memory_service, path, setup_key, factory, expect_status, expect_reason
    ):
        """落账**和**降级 logger 同时坏掉 —— 二级兜底必须在。

        (Codex round-2 MEDIUM-1 指出: 只 patch log_decision 时, 把
        ``logger.exception`` 的二级 try 删掉测试照样绿 —— 那道保护没有门。)
        """
        getattr(mock_memory_service, setup_key).return_value = factory()

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
            response = client.get(path)

        assert response.status_code == 200, "日志后端也坏时 fail-open 的二级兜底失效了"
        assert response.json()["retrieval_status"] == expect_status
        assert response.json()["retrieval_status_reason"] == expect_reason
        assert spy.call_count == 1
        assert log_spy.call_count == 1, "降级 logger 没被调用 —— 二级兜底路径没走到"

    def test_review_suggestions_trace_failure_does_not_break_response(self, client, mock_memory_service):
        mock_memory_service.get_review_suggestions_with_status.return_value = StatusedResult.unavailable("bolt refused")

        with patch(
            "app.core.decision_tracker.log_decision",
            side_effect=RuntimeError("trace sink failed"),
        ) as spy:
            response = client.get("/api/v1/memory/review-suggestions?user_id=u")

        assert response.status_code == 200
        assert response.json()["retrieval_status"] == "unavailable"
        assert response.json()["retrieval_status_reason"] == "bolt refused"
        assert spy.call_count == 1
