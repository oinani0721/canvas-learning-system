"""Story 2.3 Phase 1 — /api/v1/chat/enrich-context mode='deep' 行为测试。

study-question Skill 通过 plugin Cmd+Shift+Q 触发，调 backend 同一 endpoint
但用 mode='deep' 参数。本测试覆盖 deep 与 answer / preload 的关键参数差异：

- mode='deep' 接受（之前 Literal 只有 preload/answer）
- mode='deep' + user_question → supplementary search 用激进参数（top_k_max=30 / hard_cap=20）
- mode='deep' 无 user_question → 不搜（与 preload 一致）
- mode='answer' 仍用快问快答参数（top_k_max=20 / hard_cap=15）— 不被 deep 改动污染
- 非法 mode 被 Pydantic 拒绝（422）
"""

from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.wikilink_context_service import EnrichmentResult


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
    (``vault_scope.py:166-176``)。本文件测的是 **mode 参数如何影响 top_k / hard_cap
    与是否触发检索**, 不是 vault 隔离; 不把 ``TEST_VAULT_ID`` 声明成 active vault,
    每条断言都会变成 409, 淹没真正要测的信号。桩的形态与理由同
    ``test_sync_batch_auth.py:81-84,98`` 的先例。

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


def _payload(
    mode: str | None = None,
    user_question: str | None = None,
    vault_id: str = TEST_VAULT_ID,
) -> dict[str, Any]:
    # Multi-vault P0-1: vault_id 必填，测试默认 'test_vault'
    p: dict[str, Any] = {
        "node_path": "节点/Eigenvalues.md",
        "current_note_content": "特征值是核心概念。",
        "current_note_frontmatter": {"type": "concept", "mastery_score": 0.5},
        "max_hops": 2,
        "vault_id": vault_id,
    }
    if mode is not None:
        p["mode"] = mode
    if user_question is not None:
        p["user_question"] = user_question
    return p


# ─────────────────────────────────────────────────────────────
# mode='deep' acceptance — Literal 现在含 deep
# ─────────────────────────────────────────────────────────────


def test_mode_deep_accepted_by_request_model(client):
    """Story 2.3: mode='deep' 应被 Pydantic 接受（不再 422）。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with patch(
        "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
        return_value=fake_result,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(mode="deep", user_question="什么是 admissibility"),
        )
    assert resp.status_code == 200, (
        f"deep mode 应被接受，实际 {resp.status_code}: {resp.text[:200]}"
    )


def test_mode_invalid_rejected_by_pydantic(client):
    """非法 mode（如 'shallow'）应被 Literal 校验拒绝。"""
    resp = client.post(
        "/api/v1/chat/enrich-context",
        json=_payload(mode="shallow"),
    )
    assert resp.status_code == 422


def test_mode_default_is_preload(client):
    """不传 mode 应默认 preload — 不触发 supplementary search。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch("app.api.v1.endpoints.chat.search_supplementary") as mock_search,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(),  # no mode
        )
    assert resp.status_code == 200
    # default = preload → 即使有 user_question 也不该触发；本 case 没 user_question
    mock_search.assert_not_called()


# ─────────────────────────────────────────────────────────────
# deep 参数差异 — top_k_max / hard_cap
# ─────────────────────────────────────────────────────────────


def _setup_search_mock(mock_search):
    """Mock search_supplementary 返回最小合法 result."""
    mock_search.return_value = {
        "materials": [],
        "degraded": False,
        "reason": None,
    }


def test_mode_deep_uses_top_k_30_and_hard_cap_20(client):
    """Story 2.3 §4.3 关键参数对比：deep mode → top_k_max=30 / hard_cap=20。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            new_callable=AsyncMock,
        ) as mock_search,
    ):
        _setup_search_mock(mock_search)
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(mode="deep", user_question="什么是 admissibility"),
        )

    assert resp.status_code == 200
    mock_search.assert_awaited_once()
    call_kwargs = mock_search.await_args.kwargs
    assert call_kwargs["top_k_max"] == 30, (
        f"deep mode 应用 top_k_max=30，实际 {call_kwargs['top_k_max']}"
    )
    assert call_kwargs["hard_cap"] == 20, (
        f"deep mode 应用 hard_cap=20，实际 {call_kwargs['hard_cap']}"
    )


def test_mode_answer_keeps_top_k_20_and_hard_cap_15(client):
    """answer mode（Cmd+Shift+E 快问快答）参数未被 deep 改动污染。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            new_callable=AsyncMock,
        ) as mock_search,
    ):
        _setup_search_mock(mock_search)
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(mode="answer", user_question="什么是 admissibility"),
        )

    assert resp.status_code == 200
    mock_search.assert_awaited_once()
    call_kwargs = mock_search.await_args.kwargs
    assert call_kwargs["top_k_max"] == 20, (
        f"answer mode 应保持 top_k_max=20（不被 deep 影响），实际 {call_kwargs['top_k_max']}"
    )
    assert call_kwargs["hard_cap"] == 15, (
        f"answer mode 应保持 hard_cap=15，实际 {call_kwargs['hard_cap']}"
    )


# ─────────────────────────────────────────────────────────────
# user_question 缺失行为
# ─────────────────────────────────────────────────────────────


def test_mode_deep_without_user_question_skips_search(client):
    """deep mode 无 user_question 仍跳过搜索（与 answer 一致：搜索需要 query 文本）。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            new_callable=AsyncMock,
        ) as mock_search,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(mode="deep"),  # 无 user_question
        )

    assert resp.status_code == 200
    mock_search.assert_not_called()


def test_mode_deep_empty_user_question_skips_search(client):
    """deep mode + 空白 user_question 也应跳过（防 garbage query）。"""
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            new_callable=AsyncMock,
        ) as mock_search,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(mode="deep", user_question="   "),
        )

    assert resp.status_code == 200
    mock_search.assert_not_called()


# ─────────────────────────────────────────────────────────────
# 行为一致性 — preload 永远不搜（即使 user_question 给了）
# ─────────────────────────────────────────────────────────────


def test_mode_preload_with_user_question_still_skips_search(client):
    """preload 表示 hotkey 预加载场景 — 即使带 user_question 也不该触发搜索。
    这是 hook 设计：preload 用于 Cmd+Shift+E 触发时 backend 先组装上下文，
    用户实际提问时才用 answer/deep 模式。
    """
    fake_result = EnrichmentResult(neighbors=[], degraded=False, elapsed_ms=10.0)
    with (
        patch(
            "app.api.v1.endpoints.chat.enrich_from_wikilink_graph",
            return_value=fake_result,
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            new_callable=AsyncMock,
        ) as mock_search,
    ):
        resp = client.post(
            "/api/v1/chat/enrich-context",
            json=_payload(mode="preload", user_question="什么是 admissibility"),
        )

    assert resp.status_code == 200
    mock_search.assert_not_called()
