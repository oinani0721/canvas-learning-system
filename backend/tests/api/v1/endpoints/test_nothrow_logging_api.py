# CARD-OBS-nothrow-logging (BATCH-2026-09-01-第八批) — 端点层日志不得成为业务失败源
"""注入式回归锁 — 日志后端坏掉时, HTTP 状态码与 detail 必须原样不变。

移交来源 CARD-G4-3 Codex round-4 HIGH-1 的两条实测:
- patch ``rag.py`` `/weak-concepts` 入口的 ``logger.info`` 抛错 → HTTP **500**,
  且 ``rag_service.get_weak_concepts`` 的 ``await_count=0`` (业务根本没跑);
- patch 同端点 ``except`` 分支的 ``logger.error`` 抛错 → 本该结构化 **503** 的
  响应变成裸 **500**。

本文件用**注入**而非"把日志系统真弄坏"来锁这两类回归。三条不变量:

1. **状态码不变** — 日志抛错不改变 HTTP 状态码 (200 仍 200, 503 仍 503);
2. **detail 不变** — 结构化错误文案不被降级成裸 ``Internal Server Error``;
3. **业务照跑** — 入口日志失败不得让 service 一次都没被 await。

⚠️ ``raise_server_exceptions=False`` 是**必须**的, 不是图省事: TestClient 默认
把未处理异常直接抛进测试进程, 那样看到的是 ``RuntimeError`` 而不是真实客户端
看到的 **500 响应**。本卡锁的正是"客户端拿到什么", 所以必须让 TestClient 表现
得像 uvicorn。(``app/main.py`` 无全局 exception handler, 2026-09-01 实查。)

⚠️ 二级降级的注入点**刻意不用**类级 patch: ``_FALLBACK_LOGGER`` 本身就是一个
``logging.Logger`` 实例, ``patch.object(logging.Logger, "warning")`` 会**连它一起
打掉** (2026-09-01 探针实测: 类级双 patch 下 ``Logger.warning`` spy 仍被调用 1 次)。
只用类级 patch 写 ⑥ 等于测了个假东西 —— 分不清"二级真被走到"还是"一级就短路了"。
因此一级用类级 patch (打 inner), 二级 patch ``nothrow_logging._FALLBACK_LOGGER``
模块属性 (打 fallback), 两个 spy 分层断言。

[Source: _bmad-output/审查/codex-review-CARD-G4-3-round4.md:9-21]
[Source: app/core/decision_tracker.py:128-156 — 两级 fail-open 先例]
[Source: tests/api/v1/endpoints/test_memory_four_state_api.py:706-760 — 注入测试范式]
"""

import logging
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import memory as memory_module
from app.api.v1.endpoints import rag as rag_module
from app.api.v1.endpoints.memory import get_memory_service, memory_router
from app.api.v1.endpoints.rag import rag_router
from app.core import nothrow_logging
from app.core.nothrow_logging import NoThrowLogger
from app.models.service_status import StatusedResult
from app.security import require_internal_api_key
from app.services.rag_service import (
    RAGServiceError,
    RAGUnavailableError,
    get_rag_service,
)

SINK_DEAD = "log sink dead"

# CARD-G4-4: vault_id 必填 (缺 → 422), 且请求 vault ≠ 进程 active vault → 409
# fail-closed。本文件的 /rag/query 用例既不是测作用域也不是测 409, 所以把进程
# active vault 钉到固定值、请求体用同一个值 —— 让失败信号只可能来自日志注入
# (fixture 形态照抄 test_rag_four_state_api.py 的 CARD-G4-4 最小适配)。
_QUERY_BODY = {"query": "什么是逆否命题？", "vault_id": "v_active"}


@pytest.fixture(autouse=True)
def _pin_active_vault_for_g44(monkeypatch):
    import app.config as app_config_mod

    monkeypatch.setattr(app_config_mod, "get_current_vault_id", lambda: "v_active", raising=True)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures — 裸 FastAPI, 不起 lifespan (不碰 Neo4j/LanceDB)
# ═══════════════════════════════════════════════════════════════════════════


def _weak_concept() -> Dict[str, Any]:
    return {
        "concept": "逆否命题",
        "stability": 0.3,
        "last_review": "2026-08-31T10:00:00",
        "review_count": 2,
    }


def _rag_state() -> Dict[str, Any]:
    return {
        "reranked_results": [{"doc_id": "node-1", "content": "逆否命题…", "score": 0.9, "metadata": {}}],
        "multimodal_results": [],
        "quality_grade": "high",
        "retrieval_status": "ok",
        "retrieval_status_reason": None,
    }


def _history_payload(items: Optional[List[Dict]] = None) -> Dict[str, Any]:
    items = items or []
    return {
        "items": items,
        "total": len(items),
        "page": 1,
        "page_size": 50,
        "pages": 0,
        "retrieval_status": "ok",
        "retrieval_status_reason": None,
    }


def _concept_payload() -> Dict[str, Any]:
    return {
        "concept_id": "concept-123",
        "timeline": [],
        "score_trend": {
            "first": None,
            "last": None,
            "average": None,
            "improvement": None,
        },
        "total_reviews": 0,
        "retrieval_status": "ok",
        "retrieval_status_reason": None,
    }


@pytest.fixture
def mock_rag_service() -> MagicMock:
    service = MagicMock()
    service.query = AsyncMock(return_value=_rag_state())
    service.get_weak_concepts = AsyncMock(return_value=[_weak_concept()])
    return service


@pytest.fixture
def mock_memory_service() -> MagicMock:
    service = MagicMock()
    service.get_learning_history = AsyncMock(return_value=_history_payload())
    service.get_concept_history = AsyncMock(return_value=_concept_payload())
    service.get_review_suggestions_with_status = AsyncMock(return_value=StatusedResult.from_items([]))
    return service


@pytest.fixture
def client(mock_rag_service: MagicMock, mock_memory_service: MagicMock) -> TestClient:
    """裸挂两个 router 的最小 app。

    ``raise_server_exceptions=False`` — 见模块 docstring: 本卡锁的是"客户端拿到
    什么状态码", 不是"测试进程里抛了什么异常"。
    """
    app = FastAPI()
    app.include_router(rag_router, prefix="/api/v1/rag")
    app.include_router(memory_router, prefix="/api/v1/memory")

    async def _override_rag():
        return mock_rag_service

    async def _override_memory():
        yield mock_memory_service

    app.dependency_overrides[get_rag_service] = _override_rag
    app.dependency_overrides[get_memory_service] = _override_memory
    # 鉴权不是本卡战场: 显式旁路, 让失败信号只可能来自日志注入本身。
    app.dependency_overrides[require_internal_api_key] = lambda: None
    return TestClient(app, raise_server_exceptions=False)


def _kill(level: str):
    """类级 patch (卡文指定的注入形态) + 调用方甄别。

    为什么不是裸 ``side_effect=RuntimeError``: 实测 (2026-09-01) httpx 在每次
    TestClient 请求完成后会调 ``logger.info("HTTP Request: ...")`` —— 纯类级
    info patch 把**请求本身**炸掉, 测到的就成了 httpx 层的错误而不是端点行为。
    所以 side_effect 先甄别调用方: 端点模块的调用抛错, 其余 (httpx/starlette)
    放行返回 None (与 stdlib info 的返回值一致)。

    "包装去掉后同一测试必红"仍然成立: M1/M2 变异把模块 logger 拆回裸 stdlib
    Logger, 它仍在 ``logging.Logger`` 类上 —— 类级 patch 照样命中, 端点调用
    照样抛错。

    帧遍历的两个坑 (都实测踩过):
    - 起点必须是 ``_getframe(1)`` (mock 内部帧) —— 不能经由辅助函数取帧, 辅助
      函数自己的帧会变成"第一个调用方" (它住在测试模块里, 既不在穿越名单、
      也不匹配 app.api 前缀 → killer 恒放行, 全部门假绿);
    - 必须穿透 ``app.core.nothrow_logging``: 被包装链是 端点 → 包装器 →
      inner.info(patched), 不穿透包装器帧的话 killer 永远看不见端点 (二级
      fallback 门抓出: ``fallback.warning.call_count == 0``)。这与
      ``_STACKLEVEL_OFFSET`` 是同一哲学 —— 包装器对调用点透明。
    """

    def _raiser(*args: Any, **kwargs: Any):
        frame = sys._getframe(1)  # mock 内部帧 (跳过 _raiser 自己)
        caller = "<unknown>"
        while frame is not None:
            mod = frame.f_globals.get("__name__", "")
            if mod and not mod.startswith("unittest.mock") and mod != "logging" and mod != "app.core.nothrow_logging":
                caller = mod
                break
            frame = frame.f_back
        if caller.startswith("app.api.v1.endpoints"):
            raise RuntimeError(SINK_DEAD)
        return None

    return patch.object(logging.Logger, level, side_effect=_raiser)


def _ours(spy, needle: str) -> bool:
    """spy 的调用里有没有**我们那一行**。

    ``spy.call_count >= 1`` 单独用是弱门: 类级 patch 会捕获进程内所有 logger
    的调用 (fastapi / httpx / asyncio 都可能在同一次请求里 log)。所以除了计数,
    还要能指认出被测的那条消息。
    """
    for call in spy.call_args_list:
        if call.args and isinstance(call.args[0], str) and needle in call.args[0]:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
# ① /weak-concepts 入口日志 — 200 必须仍是 200, 且业务必须真的跑了
# ═══════════════════════════════════════════════════════════════════════════


class TestWeakConceptsEntryLog:
    def test_entry_log_failure_keeps_200_and_service_still_awaited(
        self, client: TestClient, mock_rag_service: MagicMock
    ):
        """移交来源实测 #1: 入口 logger.info 抛错 → 500 且 await_count=0。"""
        with _kill("info") as spy:
            response = client.get("/api/v1/rag/weak-concepts/数学/离散数学.canvas")

        assert response.status_code == 200, (
            f"入口日志抛错把 200 打成了 {response.status_code} —— 观测面又成了业务失败源"
        )
        assert mock_rag_service.get_weak_concepts.await_count == 1, (
            "await_count != 1 —— 日志抛错让业务代码一次都没跑到 (移交来源实测的正是这个)"
        )
        assert spy.call_count >= 1, "注入根本没生效 —— 这条门在测一个不存在的场景"
        assert _ours(spy, "Getting weak concepts for"), (
            "被注入的调用里没有端点那一行 —— call_count 是别人贡献的, 这是假门"
        )

    def test_error_log_failure_keeps_structured_503(self, client: TestClient, mock_rag_service: MagicMock):
        """移交来源实测 #2: except 分支 logger.error 抛错 → 结构化 503 变裸 500。"""
        mock_rag_service.get_weak_concepts.side_effect = RAGUnavailableError("bolt://localhost:7687 refused")

        with _kill("error") as spy:
            response = client.get("/api/v1/rag/weak-concepts/数学/离散数学.canvas")

        assert response.status_code == 503, f"503 被日志抛错打成了 {response.status_code} —— 客户端拿到的错误类型都变了"
        assert response.json()["detail"] == "bolt://localhost:7687 refused", (
            "detail 文案丢失 —— 结构化错误被降级成裸 Internal Server Error"
        )
        assert spy.call_count >= 1 and _ours(spy, "RAG service unavailable")


# ═══════════════════════════════════════════════════════════════════════════
# ② /rag/query 的 503 与 500 分支
# ═══════════════════════════════════════════════════════════════════════════


class TestRagQueryErrorLogs:
    @pytest.mark.parametrize(
        "exc_type,expected_status,needle",
        [
            (RAGUnavailableError, 503, "RAG service unavailable"),
            (RAGServiceError, 500, "RAG query failed"),
        ],
    )
    def test_error_log_failure_keeps_status_and_detail(
        self,
        client: TestClient,
        mock_rag_service: MagicMock,
        exc_type,
        expected_status: int,
        needle: str,
    ):
        mock_rag_service.query.side_effect = exc_type("upstream is down")

        with _kill("error") as spy:
            response = client.post("/api/v1/rag/query", json=_QUERY_BODY)

        assert response.status_code == expected_status, f"日志抛错把 {expected_status} 打成了 {response.status_code}"
        # 未包装时异常逃出 except → 裸 500 是 text/plain, response.json() 会
        # 炸 JSONDecodeError —— 先断 content-type, 让失败原因停在可读的
        # AssertionError 上 (负控靠失败消息里的关键字核原因)。
        content_type = response.headers.get("content-type", "")
        assert content_type.startswith("application/json"), (
            f"detail 文案丢失 —— {expected_status} 被打成了裸 "
            f"{response.status_code} Internal Server Error (content-type={content_type!r})"
        )
        assert response.json()["detail"] == "upstream is down", "detail 文案丢失"
        assert spy.call_count >= 1 and _ours(spy, needle)


# ═══════════════════════════════════════════════════════════════════════════
# ③ memory 三主端点 — 500 的 detail 必须仍是结构化文案
# ═══════════════════════════════════════════════════════════════════════════

MEMORY_CASES = [
    # (case_id, path, service_attr, 日志文本 needle, detail 前缀)
    # ⚠️ 日志文本与 detail 文案**不同** (memory.py 原文如此): 日志是
    #    "Failed to get learning history: …", detail 是 "Failed to query
    #    learning history: …"。_ours 要认**日志**那一行, 断言要认 **detail**。
    (
        "episodes",
        "/api/v1/memory/episodes?user_id=u",
        "get_learning_history",
        "Failed to get learning history",
        "Failed to query learning history:",
    ),
    (
        "concept-history",
        "/api/v1/memory/concepts/concept-123/history",
        "get_concept_history",
        "Failed to get concept history",
        "Failed to query concept history:",
    ),
    (
        "review-suggestions",
        "/api/v1/memory/review-suggestions?user_id=u",
        "get_review_suggestions_with_status",
        "Failed to get review suggestions",
        "Failed to get review suggestions:",
    ),
]


class TestMemoryMainEndpointErrorLogs:
    @pytest.mark.parametrize(
        "case_id,path,service_attr,log_needle,detail_prefix",
        MEMORY_CASES,
        ids=[c[0] for c in MEMORY_CASES],
    )
    def test_error_log_failure_keeps_structured_detail(
        self,
        client: TestClient,
        mock_memory_service: MagicMock,
        case_id: str,
        path: str,
        service_attr: str,
        log_needle: str,
        detail_prefix: str,
    ):
        """这三条的状态码**两种情况下都是 500** —— 区别全在 body。

        没有包装时: logger.error 抛错逃出 except → Starlette 返回裸
        ``Internal Server Error`` (text/plain), 客户端再也看不到"到底哪一步失败"。
        有包装时: 500 的 detail 仍是端点自己写的结构化文案。
        所以本门断的是 **detail**, 断状态码是不够的。
        """
        getattr(mock_memory_service, service_attr).side_effect = RuntimeError("neo4j exploded")

        with _kill("error") as spy:
            response = client.get(path)

        assert response.status_code == 500
        content_type = response.headers.get("content-type", "")
        assert content_type.startswith("application/json"), (
            f"detail 文案丢失 —— 结构化 500 被打成了裸 Internal Server Error (content-type={content_type!r})"
        )
        assert response.json()["detail"].startswith(detail_prefix), (
            f"detail 文案丢失 —— 期望以 {detail_prefix!r} 开头, 实得 {response.json().get('detail')!r}"
        )
        assert spy.call_count >= 1 and _ours(spy, log_needle), "被注入的调用里没有端点那一行 —— 假门"


# ═══════════════════════════════════════════════════════════════════════════
# ④ 二级降级 — 分层注入, 证明二级路径**真的**被走到
# ═══════════════════════════════════════════════════════════════════════════


class TestSecondLevelFallback:
    def test_fallback_also_failing_still_keeps_200(self, client: TestClient, mock_rag_service: MagicMock):
        """一级 (inner) 与二级 (fallback) 同时坏掉, 响应仍不变。

        ⚠️ 二级用**模块属性 patch** 而非类级 patch: ``_FALLBACK_LOGGER`` 本身是
        ``logging.Logger`` 实例, 类级 patch 会连它一起打掉, 于是分不清"二级被走
        到了"还是"一级就短路了"。分层后 ``fallback.warning.call_count`` 是二级
        路径被走到的**独立证据**。
        """
        fallback = MagicMock()
        fallback.warning.side_effect = RuntimeError("logging backend is also dead")

        with (
            _kill("info") as primary_spy,
            patch.object(nothrow_logging, "_FALLBACK_LOGGER", fallback),
        ):
            response = client.get("/api/v1/rag/weak-concepts/数学/离散数学.canvas")

        assert response.status_code == 200, "二级兜底失效 —— 日志后端全坏时业务被带崩"
        assert mock_rag_service.get_weak_concepts.await_count == 1
        assert primary_spy.call_count >= 1, "一级注入没生效"
        assert fallback.warning.call_count >= 1, (
            "二级降级路径**没被走到** —— 这条门在测一个不存在的场景 (一级若提前短路, 前面的断言照样全过)"
        )

    def test_fallback_line_carries_diagnostic_context(self, client: TestClient, mock_rag_service: MagicMock):
        """降级那条日志必须能定位到"哪个 logger 的哪个方法为什么坏了"。

        否则"吞掉异常"就变成了"把故障藏起来"。
        """
        fallback = MagicMock()

        with _kill("info"), patch.object(nothrow_logging, "_FALLBACK_LOGGER", fallback):
            client.get("/api/v1/rag/weak-concepts/数学/离散数学.canvas")

        assert fallback.warning.call_count >= 1
        rendered = [
            call.args[0] % tuple(call.args[1:]) if len(call.args) > 1 else call.args[0]
            for call in fallback.warning.call_args_list
        ]
        joined = " | ".join(rendered)
        assert "app.api.v1.endpoints.rag" in joined, "降级行没写清是哪个 logger 坏了"
        assert "'info'" in joined, "降级行没写清是哪个方法坏了"
        assert SINK_DEAD in joined, "降级行没带原始异常, 无法定位根因"


# ═══════════════════════════════════════════════════════════════════════════
# ⑤ 反自欺 — 包装器不能是个"什么都不做"的空壳
# ═══════════════════════════════════════════════════════════════════════════


class TestWrapperIsNotANoOp:
    """上面所有门在"NoThrowLogger 实现成 pass"时**全绿**。

    因为它们只断言"业务响应没被日志带崩" —— 一个什么都不记的 logger 当然不会
    带崩任何东西。没有这一节, 本卡就等于用删掉日志功能来换取"日志不出错"。
    """

    def test_normal_path_still_emits_the_log_record(self, client: TestClient, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger="app.api.v1.endpoints.rag"):
            response = client.get("/api/v1/rag/weak-concepts/数学/离散数学.canvas")

        assert response.status_code == 200
        messages = [r.getMessage() for r in caplog.records]
        assert any("Getting weak concepts for" in m for m in messages), (
            f"包装后日志根本没写出来 —— 观测面被『保护』没了。实得: {messages}"
        )
        assert any("数学/离散数学.canvas" in m for m in messages), "惰性参数没被渲染进最终消息 —— %s 占位符和实参对不上"

    def test_wrapper_is_frame_transparent(self, client: TestClient, caplog: pytest.LogCaptureFixture):
        """调用点信息必须仍指向端点, 不是指向包装器自己。

        锁的是 ``nothrow_logging._STACKLEVEL_OFFSET`` —— 它与 ``_guarded`` 的调用
        深度强耦合, 谁改了包装层数不改这个常量, 这条门就红。
        (生产 JSON 日志当前不含 filename/funcName, 见 ``app/core/logging.py``
        无 ``CallsiteParameterAdder``; 但 caplog 与任何将来加上调用点字段的配置
        看得见, 且"包装器对调用点透明"本身就是该有的性质。)
        """
        with caplog.at_level(logging.INFO, logger="app.api.v1.endpoints.rag"):
            client.get("/api/v1/rag/weak-concepts/数学/离散数学.canvas")

        ours = [r for r in caplog.records if "Getting weak concepts for" in r.getMessage()]
        assert ours, "没抓到端点那条日志"
        record = ours[0]
        assert record.funcName == "get_weak_concepts", (
            f"调用点漂移到了 {record.filename}:{record.funcName} —— "
            "包装器把自己写成了日志来源 (_STACKLEVEL_OFFSET 失准)"
        )
        assert record.filename == "rag.py", f"调用点文件漂移: {record.filename}"


# ═══════════════════════════════════════════════════════════════════════════
# ⑥ 包装确实装上了 (M1/M2 变异的直接靶子)
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleLoggersAreWrapped:
    @pytest.mark.parametrize(
        "module,name",
        [(rag_module, "rag"), (memory_module, "memory")],
        ids=["rag", "memory"],
    )
    def test_module_logger_is_nothrow_wrapped(self, module, name: str):
        assert isinstance(module.logger, NoThrowLogger), f"{name}.py 的模块级 logger 不是 NoThrowLogger —— 包装没装上"
        assert isinstance(module.logger.inner, logging.Logger)
        assert module.logger.inner.name == f"app.api.v1.endpoints.{name}"
