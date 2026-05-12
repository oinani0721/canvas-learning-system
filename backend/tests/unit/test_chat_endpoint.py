"""Story 2.1 Task 5.3 — POST /api/v1/chat/enrich-context endpoint 测试。

覆盖：
- happy path (graph 已 built, 返回 enriched context)
- 降级路径 (graph not built, degraded=True + fallback context)
- 输入验证 (空 node_path → 400)
- max_hops 边界 (1/2/3 接受 / 0/4 拒绝)
"""

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.services.wikilink_context_service import (
    EnrichmentResult,
    WikilinkNeighborContext,
)


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _enrich_payload(
    node_path: str = "节点/Eigenvalues.md",
    content: str = "特征值是核心概念。",
    fm: dict[str, Any] | None = None,
    max_hops: int = 2,
    vault_id: str = "test_vault",
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
                "vault_id": "test_vault",  # Multi-vault P0-1: 必填
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


# ════════════════════════════════════════════════════════════════════
# Story 2.2+2.9 Global-Search (2026-05-12) — POST /chat/global-search
# 不依赖节点的 vault 全域 RAG 搜索
# ════════════════════════════════════════════════════════════════════


def _global_search_payload(
    user_question: str = "如何求 Linear Independence?",
    vault_id: str = "test_vault",
    **kwargs,
) -> dict[str, Any]:
    return {
        "user_question": user_question,
        "vault_id": vault_id,
        **kwargs,
    }


def test_global_search_endpoint_returns_xml(client):
    """全局搜索 happy path — mock lancedb_client, 返回 200 + supplementary XML."""
    stub_supp_result = {
        "materials": [
            {
                "title": "Linear Independence Lecture",
                "snippet": "Vectors v1..vn are linearly independent iff...",
                "wikilink": "[[lectures/lec03#Linear-Independence]]",
                "source_path": "lectures/lec03.md",
                "source_type": "lecture",
                "score": 0.85,
            }
        ],
        "degraded": False,
        "reason": None,
    }
    with (
        patch(
            "app.api.v1.endpoints.chat._get_supp_lancedb_client",
            return_value="stub_client",
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            return_value=stub_supp_result,
        ),
    ):
        response = client.post(
            "/api/v1/chat/global-search",
            json=_global_search_payload(),
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "enriched_context" in body
    # manifest 必须含 vault / query / sources
    assert "Global Search Manifest" in body["enriched_context"]
    assert "test_vault" in body["enriched_context"]
    assert body["supplementary_count"] >= 1
    assert body["supplementary_degraded"] is False
    assert body["elapsed_ms"] >= 0
    # XML body 应含 supplementary_materials 标签
    assert "supplementary_materials" in body["enriched_context"]


def test_global_search_endpoint_rejects_empty_question(client):
    """空 user_question → 422 (Pydantic min_length=1)."""
    response = client.post(
        "/api/v1/chat/global-search",
        json=_global_search_payload(user_question=""),
    )
    assert response.status_code == 422


def test_global_search_endpoint_degrades_on_lancedb_none(client):
    """lancedb 不可用 (singleton None) → degraded=True + reason=lancedb_unavailable."""
    # _get_supp_lancedb_client 返回 None → search_supplementary 内部短路返回 degraded
    stub_degraded_result = {
        "materials": [],
        "degraded": True,
        "reason": "lancedb_unavailable",
    }
    with (
        patch(
            "app.api.v1.endpoints.chat._get_supp_lancedb_client",
            return_value=None,
        ),
        patch(
            "app.api.v1.endpoints.chat.search_supplementary",
            return_value=stub_degraded_result,
        ),
    ):
        response = client.post(
            "/api/v1/chat/global-search",
            json=_global_search_payload(),
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["supplementary_degraded"] is True
    assert body["supplementary_count"] == 0
    assert body["supplementary_reason"] == "lancedb_unavailable"
    # manifest 应明示 degradation reason
    assert "lancedb_unavailable" in body["enriched_context"]


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
    init_timeout = call_obj.kwargs.get("init_timeout") or (
        call_obj.args[0] if call_obj.args else None
    )
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
        "rag_enrich_hook 未调 _get_supp_lancedb_client → "
        "Leak-1 回归 (裸读 _supp_lancedb_singleton 绕开 lazy init)"
    )
    # 验证 init_timeout 是 hook 专用的短预算 (0.5s) — 不阻塞用户对话
    call_obj = captured_lazy.call_args
    init_timeout = call_obj.kwargs.get("init_timeout") or (
        call_obj.args[0] if call_obj.args else None
    )
    assert init_timeout == 0.5, (
        f"hook 应用 init_timeout=0.5 (非阻塞), 实际 {init_timeout}"
    )


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


def test_rag_enrich_hook_lazy_init_returns_none_skips_injection(client):
    """Lazy init 拿到 None (cold-start 未 ready) → 静默 additionalContext=''."""
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
    body = response.json()
    assert body["hookSpecificOutput"]["additionalContext"] == ""
