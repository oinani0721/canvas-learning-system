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
) -> dict[str, Any]:
    return {
        "node_path": node_path,
        "current_note_content": content,
        "current_note_frontmatter": fm or {"type": "concept", "mastery_score": 0.5},
        "max_hops": max_hops,
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
            },
        )
    assert response.status_code == 200


def test_enrich_context_response_includes_elapsed_ms(client):
    fake_result = EnrichmentResult(
        neighbors=[], degraded=False, elapsed_ms=12.3456
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
    assert response.json()["enrichment_elapsed_ms"] == 12.35
