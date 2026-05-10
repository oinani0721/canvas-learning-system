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
