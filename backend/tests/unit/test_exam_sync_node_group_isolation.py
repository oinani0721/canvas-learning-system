"""P0-SYNC-ISO-2026-08-17 审查 F1 — exam sync-node 的 group 隔离行为.

独立对抗审查 (2026-08-17) 确认的 HIGH: edge_query 端点 MATCH 限定 group 后,
跨 group 端点从「静默借用」变空匹配 — run_query 空结果不抛异常, 修复前
代码零边写入却返回 edge_created=True (DD-13 名实不一致)。

本文件是行为断言: 检查 fake client 收到的实际 Cypher 与参数, 以及空匹配
时 edge_created 的如实上报。
"""

from __future__ import annotations

from typing import Any

import pytest

from app.models.exam_models import ExamNodeSyncRequest
from app.services.exam_service_ext import sync_node_to_source_canvas


class _FakeClient:
    """run_query 按 Cypher 文本分发, 记录全部调用 (query + params)."""

    def __init__(
        self,
        edge_rows: list[dict[str, Any]],
        node_rows: list[dict[str, Any]] | None = None,
        use_json_fallback: bool = False,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self._edge_rows = edge_rows
        self._node_rows = node_rows
        self._use_json_fallback = use_json_fallback

    async def run_query(self, query: str, **params: Any) -> list[dict[str, Any]]:
        self.calls.append({"query": query, "params": params})
        if "EXAM_DISCOVERED" in query and "MERGE" in query:
            return self._edge_rows
        if "MERGE (n:CanvasNode" in query:
            if self._node_rows is not None:
                return self._node_rows
            return [{"id": params.get("node_id")}]
        return []


class _FakeExamService:
    """sync_node_to_source_canvas 的 self 依赖面: get_session + _sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Any] = {}

    async def get_session(self, exam_id: str) -> None:
        return None


def _make_request() -> ExamNodeSyncRequest:
    return ExamNodeSyncRequest(
        exam_id="E1",
        source_canvas_id="cv-1",
        node_id="discovered-1",
        node_text="new concept",
        source_node_id="src-1",
    )


@pytest.fixture
def patch_client(monkeypatch):
    def _install(
        edge_rows: list[dict[str, Any]],
        node_rows: list[dict[str, Any]] | None = None,
        use_json_fallback: bool = False,
    ) -> _FakeClient:
        client = _FakeClient(edge_rows, node_rows=node_rows, use_json_fallback=use_json_fallback)
        import app.clients.neo4j_client as neo4j_client_module

        monkeypatch.setattr(neo4j_client_module, "get_neo4j_client", lambda: client)
        return client

    return _install


class TestExamSyncNodeGroupIsolation:
    @pytest.mark.asyncio
    async def test_node_and_edge_cypher_carry_physical_group(self, patch_client) -> None:
        client = patch_client([{"rel_type": "EXAM_DISCOVERED"}])
        resp = await sync_node_to_source_canvas(_FakeExamService(), _make_request(), group_id="vault:canvas_vault")

        assert resp.edge_created is True
        node_call = next(c for c in client.calls if "MERGE (n:CanvasNode" in c["query"])
        # 键含 group + 参数是物理格式 (vault: → vault__)
        assert "{id: $node_id, group_id: $group_id}" in node_call["query"]
        assert node_call["params"]["group_id"] == "vault__canvas_vault"
        edge_call = next(c for c in client.calls if "EXAM_DISCOVERED" in c["query"] and "MERGE" in c["query"])
        assert "{id: $source_node_id, group_id: $group_id}" in edge_call["query"]
        assert edge_call["params"]["group_id"] == "vault__canvas_vault"

    @pytest.mark.asyncio
    async def test_empty_edge_match_reports_edge_created_false(self, patch_client) -> None:
        """审查 F1 核心: 跨 group 端点 → MATCH 空 → 必须如实报 False.

        修复前: run_query 返回空 list 不抛异常, edge_created 保持 True —
        零边写入却报成功。R10 P1-03 追加: 整体 status 必须是 partial,
        不许无条件 "ok"。
        """
        patch_client([])  # edge_query 空匹配 (端点在另一 group)
        resp = await sync_node_to_source_canvas(_FakeExamService(), _make_request(), group_id="vault:canvas_vault")

        assert resp.edge_created is False
        assert resp.synced_to_neo4j is True  # 节点本身写入成功, 只有边失败
        assert resp.status == "partial"
        assert resp.message  # 必须解释哪里没成

    @pytest.mark.asyncio
    async def test_happy_path_status_ok(self, patch_client) -> None:
        patch_client([{"rel_type": "EXAM_DISCOVERED"}])
        resp = await sync_node_to_source_canvas(_FakeExamService(), _make_request(), group_id="vault:canvas_vault")
        assert resp.status == "ok"
        assert resp.edge_created is True

    @pytest.mark.asyncio
    async def test_empty_node_write_reports_error(self, patch_client) -> None:
        """R10 P1-03 核心: node MERGE+RETURN 空行 = 静默降级/失败 —
        修复前把所有查询结果设为空仍返回 synced_to_neo4j=True status=ok."""
        patch_client([], node_rows=[])
        resp = await sync_node_to_source_canvas(_FakeExamService(), _make_request(), group_id="vault:canvas_vault")

        assert resp.synced_to_neo4j is False
        assert resp.synced_to_canvas is False
        assert resp.edge_created is False
        assert resp.status == "error"
        assert "no rows" in resp.message

    @pytest.mark.asyncio
    async def test_json_fallback_mode_refuses_write(self, patch_client) -> None:
        """R10 P1-03: JSON fallback 不支持 CanvasNode 写 — 写路径禁止
        静默降级, 直接拒绝。"""
        client = patch_client([{"rel_type": "EXAM_DISCOVERED"}], use_json_fallback=True)
        resp = await sync_node_to_source_canvas(_FakeExamService(), _make_request(), group_id="vault:canvas_vault")

        assert resp.status == "error"
        assert resp.synced_to_neo4j is False
        assert "fallback" in resp.message.lower()
        assert client.calls == []  # 一条写查询都不许发
