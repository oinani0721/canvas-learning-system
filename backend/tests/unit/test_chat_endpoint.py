"""Story 2.1 Task 5.3 — POST /api/v1/chat/enrich-context endpoint 测试。

覆盖：
- happy path (graph 已 built, 返回 enriched context)
- 降级路径 (graph not built, degraded=True + fallback context)
- 输入验证 (空 node_path → 400)
- max_hops 边界 (1/2/3 接受 / 0/4 拒绝)
"""

from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.wikilink_context_service import (
    EnrichmentResult,
    WikilinkNeighborContext,
)


from tests.support.authed_client import authed_client  # noqa: F401

#: 本文件所有请求携带的 vault_id。桩与 payload 共用这一个定义, 否则改了 payload
#: 默认值却忘了改桩, 全文件会静默退回 409 (CARD-RED-A1-auth)。
TEST_VAULT_ID = "test_vault"


@pytest.fixture
def client(authed_client: TestClient) -> Generator[TestClient, None, None]:
    """带 ``X-CLS-Internal-Key`` 的 TestClient + active vault 桩。

    CARD-RED-A1-auth: 原本是裸 ``TestClient(app)``, 按 pytest 就近覆盖规则遮蔽了
    ``tests/conftest.py:494-517`` 那个配了 key 的共享 client。``security.py``
    自 ``c9bb6c9a`` fail-closed 后 (:110-142), 裸 client 的请求恒 503 —— 本文件
    每条断言都停在 router 级依赖 (``chat.py:48``), 一次都没走到业务层。

    解开鉴权后请求会再撞 ``chat.py:287-293`` 的 ``resolve_vault_scope``:
    「显式 vault_id ≠ 进程 active vault」→ 409 fail-closed
    (``vault_scope.py:166-176``)。本文件测的是 **enrich-context 的组装与降级行为**,
    不是 vault 隔离; 不把 ``TEST_VAULT_ID`` 声明成 active vault, 每条 200 断言都会
    变成 409, 淹没真正要测的信号。桩的形态与理由同 ``test_sync_batch_auth.py:81-84,98``
    的先例。

    ⚠️ 本桩**不证明**「请求 vault 与 active vault 不一致时会被拒」——它恰恰把这个前提
    设成一致。全仓当前也没有任何测试对 enrich-context 断言 409：
    ``test_enrich_context_vault_isolation.py`` 的五条正向用例被 409 阻断（红，已登记移交），
    另两条验 422、一条验 ContextVar 并发，都不是 409 的回归覆盖。这道覆盖缺口本卡不补
    （Codex round-1 MEDIUM-2 实证，如实记录）。

    再往后 ``chat.py:313`` ``await get_memory_service()`` 会**真的**建 MemoryService
    单例 → Neo4jClient 连 ``bolt://localhost:7691``（现网），被 W4 哨兵拦下并把用例判红。
    它是**进程级单例**：只有第一个跑到这里的用例会触发，于是「谁被判红」取决于测试
    执行顺序 —— 单跑本文件红在这里，全量跑可能转嫁给别的文件。桩掉 accessor 让这条
    连接根本不发生（不放宽哨兵、不关 W4）。返回空 list 与生产在 Neo4j 不可用时的降级
    结果逐字一致（``chat.py:341`` 超时分支与 ``:354`` 服务不可用分支同样置
    ``historical_errors=[]``），而空 list 会让 assembler **跳过**整个
    ``<historical_errors>`` 段（``chat_context_assembler.py:473`` AC #5），
    所以 enriched_context / sections_included 这些被断言的字段一字不变。
    """
    mem_svc = MagicMock()
    mem_svc.search_error_memories = AsyncMock(return_value=[])
    with (
        patch("app.config.get_current_vault_id", return_value=TEST_VAULT_ID),
        patch(
            "app.api.v1.endpoints.chat.get_memory_service",
            new=AsyncMock(return_value=mem_svc),
        ),
    ):
        yield authed_client


def _enrich_payload(
    node_path: str = "节点/Eigenvalues.md",
    content: str = "特征值是核心概念。",
    fm: dict[str, Any] | None = None,
    max_hops: int = 2,
    vault_id: str = TEST_VAULT_ID,
) -> dict[str, Any]:
    # Multi-vault P0-1: vault_id 必填（参考 PostTurnExtractRequest 契约）。
    # 测试默认 'test_vault' 让现有测试无需逐一改；测必填行为请显式 omit。
    return {
        "node_path": node_path,
        "current_note_content": content,
        "current_note_frontmatter": fm or {"type": "concept", "mastery_score": 0.5},
        "max_hops": max_hops,
        "vault_id": vault_id,
    }


def test_enrich_context_happy_path(client):
    """graph 已 built，返回组装后的 context"""
    fake_result = EnrichmentResult(
        neighbors=[
            WikilinkNeighborContext(
                slug="Linear-Independence",
                path="节点/Linear-Independence.md",
                hop_distance=1,
                relationship_type="prerequisite",
                frontmatter={"type": "concept", "mastery_score": 0.3},
            )
        ],
        degraded=False,
        elapsed_ms=15.5,
    )
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json=_enrich_payload(),
        )

    assert response.status_code == 200
    body = response.json()
    assert "enriched_context" in body
    assert "节点/Eigenvalues.md" in body["enriched_context"]
    assert "Linear-Independence" in body["enriched_context"]
    assert body["neighbors_count"] == 1
    assert body["degraded"] is False
    assert body["degraded_reason"] is None
    assert body["used_tokens"] > 0
    assert "current_note" in body["sections_included"]
    assert "1hop_fm_tips_errors" in body["sections_included"]


def test_enrich_context_degraded_appends_notice(client):
    """图服务降级时，enriched_context 末尾追加通知"""
    fake_result = EnrichmentResult(
        neighbors=[],
        degraded=True,
        degraded_reason="wikilink_graph_not_built",
        elapsed_ms=2.0,
    )
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json=_enrich_payload(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["degraded"] is True
    assert body["degraded_reason"] == "wikilink_graph_not_built"
    assert body["neighbors_count"] == 0
    assert "邻居上下文暂时不可用" in body["enriched_context"]
    assert "仅基于当前笔记回答" in body["enriched_context"]


def test_enrich_context_empty_node_path_rejected(client):
    response = client.post(
        "/api/v1/chat/enrich-context",
        json=_enrich_payload(node_path="   "),
    )
    assert response.status_code == 400
    assert "node_path" in response.json()["detail"]


def test_enrich_context_max_hops_validation(client):
    # max_hops=0 拒绝
    response = client.post(
        "/api/v1/chat/enrich-context",
        json=_enrich_payload(max_hops=0),
    )
    assert response.status_code == 422

    # max_hops=4 拒绝
    response = client.post(
        "/api/v1/chat/enrich-context",
        json=_enrich_payload(max_hops=4),
    )
    assert response.status_code == 422


def test_enrich_context_default_frontmatter(client):
    """frontmatter 缺失时默认空 dict"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=1.0)
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json={
                "node_path": "节点/X.md",
                "current_note_content": "test",
                "vault_id": TEST_VAULT_ID,  # Multi-vault P0-1: 必填
            },
        )
    assert response.status_code == 200


def test_enrich_context_response_includes_elapsed_ms(client):
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=12.3456)
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json=_enrich_payload(),
        )
    assert response.status_code == 200
    assert response.json()["enrichment_elapsed_ms"] == 12.35


# ════════════════════════════════════════════════════════════════════
# Story 2.1 P1 — retrieval_trace + user_question + mode + assembler_budget
# ════════════════════════════════════════════════════════════════════


def test_enrich_context_returns_retrieval_trace(client):
    """P1.1 — response 含 retrieval_trace（included + graph_version + degradations）"""
    from app.services.wikilink_context_service import RetrievalTrace, TraceItem

    trace = RetrievalTrace(
        seed="节点/Eigenvalues.md",
        max_hops=2,
        graph_version="2026-05-03T10:00:00+00:00",
        elapsed_ms=15.5,
        included=[
            TraceItem(
                path="节点/Linear-Independence.md",
                hop=1,
                relationship_type="prerequisite",
                reason="frontmatter_link",
                tokens=0,
            )
        ],
        omitted=[],
        degradations=[],
    )
    fake_result = EnrichmentResult(
        neighbors=[
            WikilinkNeighborContext(
                slug="Linear-Independence",
                path="节点/Linear-Independence.md",
                hop_distance=1,
                relationship_type="prerequisite",
                frontmatter={"type": "concept"},
            )
        ],
        degraded=False,
        elapsed_ms=15.5,
        trace=trace,
    )
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json=_enrich_payload(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_trace"] is not None
    rt = body["retrieval_trace"]
    assert rt["seed"] == "节点/Eigenvalues.md"
    assert rt["max_hops"] == 2
    assert rt["graph_version"] == "2026-05-03T10:00:00+00:00"
    assert len(rt["included"]) == 1
    assert rt["included"][0]["reason"] == "frontmatter_link"
    assert rt["included"][0]["relationship_type"] == "prerequisite"
    assert rt["omitted"] == []
    assert rt["degradations"] == []


def test_enrich_context_trace_includes_degradation_when_graph_unbuilt(client):
    """P1.1 — graph 未构建时 trace.degradations 含 'wikilink_graph_not_built'"""
    from app.services.wikilink_context_service import RetrievalTrace

    fake_result = EnrichmentResult(
        neighbors=[],
        degraded=True,
        degraded_reason="wikilink_graph_not_built",
        elapsed_ms=2.0,
        trace=RetrievalTrace(
            seed="节点/X.md",
            max_hops=2,
            graph_version="unbuilt",
            elapsed_ms=2.0,
            degradations=["wikilink_graph_not_built"],
        ),
    )
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json=_enrich_payload(),
        )

    body = response.json()
    assert body["degraded"] is True
    assert "wikilink_graph_not_built" in body["retrieval_trace"]["degradations"]


def test_enrich_context_assembler_budget_field(client):
    """P1.3 — response 含 assembler_budget（默认 8192 - 1400 = 6792）"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=1.0)
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json=_enrich_payload(),
        )

    body = response.json()
    assert body["budget"] == 8192
    assert body["assembler_budget"] == 8192 - 1400


def test_enrich_context_accepts_user_question_and_mode_answer(client):
    """P1.4 — request 接受 user_question + mode='answer'（rerank Phase 2 实施，Phase 1 仅校验字段）"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=1.0)
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json={
                **_enrich_payload(),
                "user_question": "特征值和 PCA 的关系？",
                "mode": "answer",
            },
        )

    assert response.status_code == 200


def test_enrich_context_rejects_invalid_mode(client):
    """P1.4 — mode 限制在 'preload' / 'answer'，其他值 422"""
    response = client.post(
        "/api/v1/chat/enrich-context",
        json={**_enrich_payload(), "mode": "invalid_mode"},
    )
    assert response.status_code == 422


# ====================================================================
# P0-C (2026-05-12 hotfix): enrich-context cold-start lazy init verification.
# ====================================================================


def test_enrich_context_answer_mode_uses_lazy_init_path(client):
    """P0-C: answer + user_question triggers _get_supp_lancedb_client(init_timeout=5.0)."""
    from unittest.mock import AsyncMock

    enrich_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=1.0)
    captured_lazy = AsyncMock()
    captured_lazy.side_effect = lambda *a, **kw: None

    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=enrich_result,
        ),
        patch(
            "app.api.v1.endpoints.chat._get_supp_lancedb_client",
            captured_lazy,
        ),
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json={
                **_enrich_payload(),
                "user_question": "what is admissible heuristic?",
                "mode": "answer",
            },
        )

    assert response.status_code == 200
    assert captured_lazy.called
    call_obj = captured_lazy.call_args
    init_timeout = call_obj.kwargs.get("init_timeout") or (call_obj.args[0] if call_obj.args else None)
    assert init_timeout == 5.0


def test_enrich_context_preload_mode_skips_supplementary(client):
    """P0-C inverse: preload mode (no user_question) skips lazy init path."""
    from unittest.mock import AsyncMock

    enrich_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=1.0)
    captured_lazy = AsyncMock()
    captured_lazy.side_effect = lambda *a, **kw: None

    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=enrich_result,
        ),
        patch(
            "app.api.v1.endpoints.chat._get_supp_lancedb_client",
            captured_lazy,
        ),
    ):
        response = client.post(
            "/api/v1/chat/enrich-context",
            json={**_enrich_payload(), "mode": "preload"},
        )

    assert response.status_code == 200
    assert not captured_lazy.called


# ════════════════════════════════════════════════════════════════════
# Wave-2 P0-2 漏修-1 (2026-05-12) — rag_enrich_hook lazy-init path.
# 旧 bug: 裸读 _supp_lancedb_singleton 绕过 lazy init, cold-start 期间永远跳过
# 注入. 修法: 走 _get_supp_lancedb_client(init_timeout=0.5) 统一入口.
# ════════════════════════════════════════════════════════════════════


def test_rag_enrich_hook_uses_lazy_init(client):
    """Hook 必须调 _get_supp_lancedb_client (非裸读 module singleton)."""
    from unittest.mock import AsyncMock

    captured_lazy = AsyncMock()
    captured_lazy.return_value = None  # ready 与否本测试不关心, 只验证调用路径

    with patch(
        "app.api.v1.endpoints.chat._get_supp_lancedb_client",
        captured_lazy,
    ):
        response = client.post(
            "/api/v1/chat/rag/enrich-hook",
            json={
                "session_id": "test-session",
                "prompt": "How do I prove linear independence?",
            },
        )

    assert response.status_code == 200
    assert captured_lazy.called, (
        "rag_enrich_hook 未调 _get_supp_lancedb_client → Leak-1 回归 (裸读 _supp_lancedb_singleton 绕开 lazy init)"
    )
    # 验证 init_timeout 是 hook 专用的短预算 (0.5s) — 不阻塞用户对话
    call_obj = captured_lazy.call_args
    init_timeout = call_obj.kwargs.get("init_timeout") or (call_obj.args[0] if call_obj.args else None)
    assert init_timeout == 0.5, f"hook 应用 init_timeout=0.5 (非阻塞), 实际 {init_timeout}"


def test_rag_enrich_hook_short_prompt_skips_lazy_init(client):
    """Hook 短 prompt (< 5 char) 直接 early-return, 不应触发 lazy init."""
    from unittest.mock import AsyncMock

    captured_lazy = AsyncMock()
    captured_lazy.return_value = None

    with patch(
        "app.api.v1.endpoints.chat._get_supp_lancedb_client",
        captured_lazy,
    ):
        response = client.post(
            "/api/v1/chat/rag/enrich-hook",
            json={"session_id": "test-session", "prompt": "hi"},
        )

    assert response.status_code == 200
    assert not captured_lazy.called, "短 prompt 应在 lazy init 前 early-return"


def test_rag_enrich_hook_lazy_init_returns_none_injects_degraded_marker(client):
    """Lazy init 拿到 None (cold-start 未 ready) → RAG-S2 T5 降级失明修复:
    不再静默空 context, 注入 degraded 标注 (lancedb_unavailable) 让 Claude
    区分「检索降级」与「vault 真无相关材料」。"""
    from unittest.mock import AsyncMock

    captured_lazy = AsyncMock()
    captured_lazy.return_value = None  # singleton 未 ready

    with patch(
        "app.api.v1.endpoints.chat._get_supp_lancedb_client",
        captured_lazy,
    ):
        response = client.post(
            "/api/v1/chat/rag/enrich-hook",
            json={
                "session_id": "test-session",
                "prompt": "What is admissible heuristic?",
            },
        )

    assert response.status_code == 200
    ctx = response.json()["hookSpecificOutput"]["additionalContext"]
    assert 'degraded="true"' in ctx
    assert "lancedb_unavailable" in ctx
    assert 'confidence="none"' in ctx
