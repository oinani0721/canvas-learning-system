"""P0-SYNC-ISO-2026-08-17 R10 (读侧) — verification_service by-name Cypher vault 隔离.

背景 (外部对抗审查 P1-06): _get_graph_context_for_concept 的两条 Cypher 按
CanvasBoard.name / CanvasNode.title 串库匹配, 无 group 过滤 — 两个 vault 的
同名白板/同名概念 (如都有 "递归") 会互相污染验证上下文。

教训锁 (同 test_sync_group_isolation.py): 全部是**行为断言** — 检查 stub
neo4j client 实际收到的 Cypher 文本 + 参数绑定, 禁止 hasattr 式静态断言。

覆盖矩阵:
1. fetch_connected Cypher: b/n/m 三个 alias 全带 group 过滤 (= 或 STARTS WITH)
2. fetch_siblings Cypher: b/n 双 alias 全带 group 过滤
3. 绑定参数是物理格式 (vault__ 双下划线, 无冒号) — 防漏 to_physical_group_id
4. subject 二级组输入收敛到 vault 级 (跨 subject ≠ 跨 vault, 前缀放行)
5. 前缀带尾 "__": vault__cs_61b 不误配 vault__cs_61b_v2 (STARTS WITH 语义护栏)
6. group_id 缺省时 ContextVar (get_current_subject_id) 兜底
7. 双 vault 同名白板: 绑定的 group 参数互不相同
8. _get_enriched_context 把 group_id 线程化传到图查询
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

import pytest

from app.core.subject_config import (
    DEFAULT_SUBJECT_ID,
    set_current_subject_id,
)
from app.services.verification_service import (
    VerificationService,
    _vault_scope_params,
)


def _norm(query: str) -> str:
    """折叠空白, 让 Cypher 文本断言不受缩进/换行影响."""
    return re.sub(r"\s+", " ", query).strip()


class _StubNeo4jClient:
    """记录 run_query 收到的 Cypher 文本与参数绑定 (行为断言基建)."""

    def __init__(self) -> None:
        self.run_calls: List[Tuple[str, Dict[str, Any]]] = []

    async def run_query(self, query: str, **kwargs: Any):
        self.run_calls.append((query, kwargs))
        return []


class _StubGraphitiClient:
    """最小 Graphiti stub: 暴露 neo4j_client 给 _get_neo4j_client."""

    def __init__(self, neo4j: _StubNeo4jClient) -> None:
        self.neo4j_client = neo4j

    async def search_nodes(self, **kwargs: Any):
        return []


def _make_service() -> Tuple[VerificationService, _StubNeo4jClient]:
    neo4j = _StubNeo4jClient()
    svc = VerificationService(graphiti_client=_StubGraphitiClient(neo4j))
    return svc, neo4j


def _connected_call(neo4j: _StubNeo4jClient) -> Tuple[str, Dict[str, Any]]:
    for query, kwargs in neo4j.run_calls:
        if "CANVAS_EDGE" in query:
            return _norm(query), kwargs
    raise AssertionError(f"fetch_connected query not issued; got: {[q for q, _ in neo4j.run_calls]}")


def _siblings_call(neo4j: _StubNeo4jClient) -> Tuple[str, Dict[str, Any]]:
    for query, kwargs in neo4j.run_calls:
        if "sibling" in query:
            return _norm(query), kwargs
    raise AssertionError(f"fetch_siblings query not issued; got: {[q for q, _ in neo4j.run_calls]}")


@pytest.fixture(autouse=True)
def _reset_subject_contextvar():
    """每个测试后把 ContextVar 复位到默认, 防跨测试污染."""
    yield
    set_current_subject_id(DEFAULT_SUBJECT_ID)


# ---------------------------------------------------------------------------
# 1+2: 两条 Cypher 文本全部 alias 带 group 过滤
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_connected_cypher_filters_all_three_aliases():
    svc, neo4j = _make_service()
    await svc._get_graph_context_for_concept("递归", "board.canvas", group_id="vault:vault_a")
    query, _ = _connected_call(neo4j)
    for alias in ("b", "n", "m"):
        assert f"{alias}.group_id = $groupVault" in query, f"alias '{alias}' 缺 group 等值过滤: {query}"
        assert f"{alias}.group_id STARTS WITH $groupVaultPrefix" in query, f"alias '{alias}' 缺 vault 前缀放行: {query}"


@pytest.mark.asyncio
async def test_fetch_siblings_cypher_filters_board_and_node():
    svc, neo4j = _make_service()
    await svc._get_graph_context_for_concept("递归", "board.canvas", group_id="vault:vault_a")
    query, _ = _siblings_call(neo4j)
    for alias in ("b", "n"):
        assert f"{alias}.group_id = $groupVault" in query, f"alias '{alias}' 缺 group 等值过滤: {query}"
        assert f"{alias}.group_id STARTS WITH $groupVaultPrefix" in query, f"alias '{alias}' 缺 vault 前缀放行: {query}"


# ---------------------------------------------------------------------------
# 3: 绑定参数物理格式 (vault__ 双下划线, 无冒号)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_group_bindings_are_physical_format():
    svc, neo4j = _make_service()
    await svc._get_graph_context_for_concept("递归", "board.canvas", group_id="vault:vault_a")
    assert len(neo4j.run_calls) == 2, "connected + siblings 两条查询都应发出"
    for query, kwargs in neo4j.run_calls:
        assert kwargs["groupVault"] == "vault__vault_a"
        assert kwargs["groupVaultPrefix"] == "vault__vault_a__"
        assert ":" not in kwargs["groupVault"], "逻辑格式直绑 = 假过滤"
        assert kwargs["groupVault"].startswith("vault__")


# ---------------------------------------------------------------------------
# 4: subject 二级组收敛到 vault 级 (跨 subject ≠ 跨 vault)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subject_level_group_collapses_to_vault_scope():
    svc, neo4j = _make_service()
    await svc._get_graph_context_for_concept("递归", "board.canvas", group_id="vault:cs_61b:algorithms")
    _, kwargs = _connected_call(neo4j)
    assert kwargs["groupVault"] == "vault__cs_61b"
    assert kwargs["groupVaultPrefix"] == "vault__cs_61b__"


# ---------------------------------------------------------------------------
# 5: 前缀尾 "__" 护栏 — 相似 vault 名不误配 (STARTS WITH 语义)
# ---------------------------------------------------------------------------


def test_prefix_guard_no_false_match_on_similar_vault_name():
    scope = _vault_scope_params("vault:cs_61b")
    assert scope["groupVaultPrefix"] == "vault__cs_61b__"
    other_vault = "vault__cs_61b_v2"  # 另一 vault 的物理组
    # 复现 Cypher 过滤语义: = groupVault OR STARTS WITH groupVaultPrefix
    assert other_vault != scope["groupVault"]
    assert not other_vault.startswith(scope["groupVaultPrefix"]), (
        "vault__cs_61b_v2 被 vault__cs_61b 前缀误配 — 前缀必须带尾部 '__'"
    )
    # 本 vault 的 subject 子组必须放行
    assert "vault__cs_61b__algorithms".startswith(scope["groupVaultPrefix"])


def test_scope_params_idempotent_on_physical_input():
    scope = _vault_scope_params("vault__vault_a")
    assert scope["groupVault"] == "vault__vault_a"
    assert scope["groupVaultPrefix"] == "vault__vault_a__"


# ---------------------------------------------------------------------------
# 6: ContextVar 兜底 (endpoint 层 resolve_vault_group_id 注入)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_contextvar_fallback_when_group_id_omitted():
    svc, neo4j = _make_service()
    set_current_subject_id("vault:vault_b")
    await svc._get_graph_context_for_concept("递归", "board.canvas")
    for _, kwargs in neo4j.run_calls:
        assert kwargs["groupVault"] == "vault__vault_b"
        assert kwargs["groupVaultPrefix"] == "vault__vault_b__"


@pytest.mark.asyncio
async def test_no_context_fails_closed_not_open():
    """无请求上下文: 绑定收敛为 vault__general (不存在的组) → 查询空.

    关键: 查询仍然带过滤 (fail-closed), 而不是退化成无过滤全库扫描。
    """
    svc, neo4j = _make_service()
    await svc._get_graph_context_for_concept("递归", "board.canvas")
    assert neo4j.run_calls, "查询应照常发出 (带过滤), 不是跳过"
    for query, kwargs in neo4j.run_calls:
        assert "$groupVault" in query
        assert kwargs["groupVault"].startswith("vault__")
        assert ":" not in kwargs["groupVault"]


# ---------------------------------------------------------------------------
# 7: 双 vault 同名白板 → 绑定参数互不相同
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_two_vaults_same_board_name_bind_distinct_groups():
    svc_a, neo4j_a = _make_service()
    svc_b, neo4j_b = _make_service()
    await svc_a._get_graph_context_for_concept("递归", "同名白板.canvas", group_id="vault:vault_a")
    await svc_b._get_graph_context_for_concept("递归", "同名白板.canvas", group_id="vault:vault_b")
    _, kwargs_a = _connected_call(neo4j_a)
    _, kwargs_b = _connected_call(neo4j_b)
    assert kwargs_a["canvasName"] == kwargs_b["canvasName"] == "同名白板.canvas"
    assert kwargs_a["groupVault"] != kwargs_b["groupVault"]
    assert kwargs_a["groupVault"] == "vault__vault_a"
    assert kwargs_b["groupVault"] == "vault__vault_b"


# ---------------------------------------------------------------------------
# 8: _get_enriched_context 线程化传递 group_id 到图查询
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enriched_context_threads_group_id_to_graph_query():
    svc, neo4j = _make_service()
    await svc._get_enriched_context("递归", "board.canvas", group_id="vault:vault_a")
    assert neo4j.run_calls, "图查询应被发出"
    for _, kwargs in neo4j.run_calls:
        assert kwargs["groupVault"] == "vault__vault_a"
