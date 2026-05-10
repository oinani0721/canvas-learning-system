"""Story 2.3 Phase 1 — /api/v1/chat/enrich-context mode='deep' 行为测试。

study-question Skill 通过 plugin Cmd+Shift+Q 触发，调 backend 同一 endpoint
但用 mode='deep' 参数。本测试覆盖 deep 与 answer / preload 的关键参数差异：

- mode='deep' 接受（之前 Literal 只有 preload/answer）
- mode='deep' + user_question → supplementary search 用激进参数（top_k_max=30 / hard_cap=20）
- mode='deep' 无 user_question → 不搜（与 preload 一致）
- mode='answer' 仍用快问快答参数（top_k_max=20 / hard_cap=15）— 不被 deep 改动污染
- 非法 mode 被 Pydantic 拒绝（422）
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.wikilink_context_service import EnrichmentResult


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _payload(
    mode: str | None = None,
    user_question: str | None = None,
    vault_id: str = "test_vault",
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
