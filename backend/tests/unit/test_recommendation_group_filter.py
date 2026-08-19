"""P0-SYNC-ISO-2026-08-17 R10 — RecommendationService 读侧 vault 隔离行为测试.

背景: 写侧 (sync_service / canvas_projection_sync) 已用 {id, group_id} 复合键
隔离, 但 recommendation_service 的 5 条读 Cypher 全部裸查 CanvasNode/CANVAS_EDGE
仅按 canvasId 过滤 — 两个 vault 同名 canvas (canvasId 碰撞) 时, 推荐分析会把
另一 vault 的节点/边当作本 vault 数据 (读取面跨 vault 泄漏, 外部审查 P1-06)。

教训锁 (同 test_sync_group_isolation): 全部**行为断言** — 检查 stub client
实际收到的 Cypher 文本含 group 过滤 + 绑定参数是 vault__ 物理格式。
禁止 hasattr 式静态断言。

覆盖矩阵:
1. 全管道 5 条 Cypher 文本全部含 group_id (花括号 pattern / WHERE 子句)
2. 所有调用 kwargs 绑定物理格式 group (vault__ 前缀, 防漏 to_physical_group_id)
3. ContextVar 兜底: endpoint 层 resolve_vault_group_id 注入的逻辑格式
   (vault:x) 被服务转成物理格式绑定
4. 显式 group_id 参数优先于 ContextVar
5. 双 vault 场景: 不同 context → 绑定值互不相同 (隔离行为)
6. 2-hop 中间节点 shared 也被 group 约束 (防跨 vault 借证据)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

import pytest

from app.core.subject_config import DEFAULT_SUBJECT_ID, set_current_subject_id
from app.services.recommendation_service import RecommendationService

LOGICAL_GID_A = "vault:vault_a"
LOGICAL_GID_B = "vault:vault_b"
PHYSICAL_GID_A = "vault__vault_a"
PHYSICAL_GID_B = "vault__vault_b"


def _norm(query: str) -> str:
    """折叠空白, 让 Cypher 文本断言不受缩进/换行影响."""
    return re.sub(r"\s+", " ", query).strip()


class _StubNeo4jClient:
    """记录 run_query 收到的 Cypher 文本 + 绑定参数, 按查询语义回放数据.

    回放数据驱动 _generate_internal 走完整管道 (count>=5 → unconnected>=2 →
    L2 → titles → labels), 确保 5 条 Cypher 全部发射。
    """

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def run_query(self, query: str, **params: Any) -> List[Dict[str, Any]]:
        self.calls.append({"query": query, "params": dict(params)})
        q = _norm(query)
        if "count(n) AS cnt" in q:
            return [{"cnt": 10}]
        if "n.content AS content" in q:
            return [
                {"id": "n1", "title": "Graph", "content": "BFS"},
                {"id": "n2", "title": "Tree", "content": "DFS"},
            ]
        if "shared_neighbors" in q:
            return [{"source_id": "n1", "target_id": "n2", "shared_neighbors": 3}]
        if "n.title AS title" in q:
            return [{"id": "n1", "title": "Graph"}, {"id": "n2", "title": "Tree"}]
        if "e.label AS label" in q:
            return [{"label": "相关概念", "cnt": 2}]
        return []


async def _no_l1(nodes: List[Dict]) -> List:
    """替身 L1 — 不打真实 embedding 服务 (L1 无 Cypher, 不在被测面)."""
    return []


def _make_service() -> tuple[RecommendationService, _StubNeo4jClient]:
    client = _StubNeo4jClient()
    svc = RecommendationService(client)
    svc._compute_text_similarity = _no_l1  # type: ignore[method-assign]
    return svc, client


@pytest.fixture(autouse=True)
def _reset_context_group() -> Any:
    """每个测试后把 ContextVar 还原为默认, 防止跨测试串 group."""
    yield
    set_current_subject_id(DEFAULT_SUBJECT_ID)


async def _run_full_pipeline(
    *, explicit_group: str | None = None, context_group: str | None = None
) -> _StubNeo4jClient:
    if context_group is not None:
        set_current_subject_id(context_group)
    svc, client = _make_service()
    response = await svc.generate_recommendations(canvas_id="c1", dismissed_pairs=[], group_id=explicit_group)
    # 管道必须真正跑通 (5 条 Cypher 全部发射), 否则查询断言是空集真值
    assert len(client.calls) == 5, [_norm(c["query"])[:60] for c in client.calls]
    assert response.canvas_id == "c1"
    return client


# ---------------------------------------------------------------------------
# 1+2: 五条 Cypher 全部含 group 过滤 + 绑定物理格式
# ---------------------------------------------------------------------------


class TestRecommendationCypherGroupFilter:
    """5 条读 Cypher 的 CanvasNode pattern 必须含 group_id, 参数必须物理格式."""

    async def test_every_query_binds_physical_group(self) -> None:
        client = await _run_full_pipeline(explicit_group=LOGICAL_GID_A)
        for call in client.calls:
            query = _norm(call["query"])
            assert "$group_id" in query, f"query without group binding: {query}"
            assert call["params"]["group_id"] == PHYSICAL_GID_A
            assert call["params"]["group_id"].startswith("vault__")
            # 逻辑冒号格式直接绑定 = 假过滤, 必须被物理化
            assert ":" not in call["params"]["group_id"]

    async def test_count_nodes_pattern_carries_group(self) -> None:
        client = await _run_full_pipeline(explicit_group=LOGICAL_GID_A)
        query = _norm(client.calls[0]["query"])
        assert "MATCH (n:CanvasNode {canvasId: $canvas_id, group_id: $group_id})" in query
        assert "count(n) AS cnt" in query

    async def test_unconnected_nodes_pattern_carries_group(self) -> None:
        client = await _run_full_pipeline(explicit_group=LOGICAL_GID_A)
        query = _norm(client.calls[1]["query"])
        assert "MATCH (n:CanvasNode {canvasId: $canvas_id, group_id: $group_id})" in query
        # P1-05c (F-02): 模式谓词升级为 EXISTS 子查询 — "已连接"只认 live 边
        # (墓碑边不算连接, 否则孤立节点被幽灵边挡出推荐面)
        assert "NOT EXISTS" in query
        assert "e.invalidated_at IS NULL" in query

    async def test_graph_pattern_both_anchors_and_shared_carry_group(self) -> None:
        """2-hop 查询: 两个锚点 a/b + 中间节点 shared 三处都必须限定 group."""
        client = await _run_full_pipeline(explicit_group=LOGICAL_GID_A)
        query = _norm(client.calls[2]["query"])
        assert "(a:CanvasNode {canvasId: $canvas_id, group_id: $group_id})" in query
        assert "(b:CanvasNode {canvasId: $canvas_id, group_id: $group_id})" in query
        assert "shared.group_id = $group_id" in query

    async def test_node_titles_pattern_carries_group(self) -> None:
        client = await _run_full_pipeline(explicit_group=LOGICAL_GID_A)
        query = _norm(client.calls[3]["query"])
        assert "MATCH (n:CanvasNode {canvasId: $canvas_id, group_id: $group_id})" in query
        assert "n.title AS title" in query

    async def test_edge_labels_both_endpoints_carry_group(self) -> None:
        """边 label 查询: 两端 CanvasNode 都必须限定 group — 防跨 vault 借边."""
        client = await _run_full_pipeline(explicit_group=LOGICAL_GID_A)
        query = _norm(client.calls[4]["query"])
        assert (
            "(:CanvasNode {canvasId: $canvas_id, group_id: $group_id})"
            "-[e:CANVAS_EDGE]-(:CanvasNode {group_id: $group_id})" in query
        )


# ---------------------------------------------------------------------------
# 3+4: group 来源优先级 (显式参数 > ContextVar 兜底) + 物理化
# ---------------------------------------------------------------------------


class TestGroupSourceResolution:
    async def test_contextvar_fallback_binds_physical_form(self) -> None:
        """endpoint 层注入逻辑格式 vault:x → 服务绑定必须是 vault__x."""
        client = await _run_full_pipeline(context_group=LOGICAL_GID_A)
        for call in client.calls:
            assert call["params"]["group_id"] == PHYSICAL_GID_A

    async def test_explicit_group_overrides_contextvar(self) -> None:
        client = await _run_full_pipeline(explicit_group=LOGICAL_GID_B, context_group=LOGICAL_GID_A)
        for call in client.calls:
            assert call["params"]["group_id"] == PHYSICAL_GID_B

    async def test_already_physical_group_is_idempotent(self) -> None:
        """to_physical_group_id 幂等 — 传物理格式不得二次转换损坏."""
        client = await _run_full_pipeline(explicit_group=PHYSICAL_GID_A)
        for call in client.calls:
            assert call["params"]["group_id"] == PHYSICAL_GID_A


# ---------------------------------------------------------------------------
# 5: 双 vault 隔离行为 — 同 canvas_id 不同 vault, 绑定互不相同
# ---------------------------------------------------------------------------


class TestTwoVaultIsolation:
    async def test_same_canvas_id_different_vault_binds_different_group(self) -> None:
        """canvasId 碰撞场景: vault_a / vault_b 各自请求, group 绑定必须分流."""
        client_a = await _run_full_pipeline(context_group=LOGICAL_GID_A)
        set_current_subject_id(DEFAULT_SUBJECT_ID)
        client_b = await _run_full_pipeline(context_group=LOGICAL_GID_B)

        groups_a = {c["params"]["group_id"] for c in client_a.calls}
        groups_b = {c["params"]["group_id"] for c in client_b.calls}
        assert groups_a == {PHYSICAL_GID_A}
        assert groups_b == {PHYSICAL_GID_B}
        assert groups_a.isdisjoint(groups_b)
