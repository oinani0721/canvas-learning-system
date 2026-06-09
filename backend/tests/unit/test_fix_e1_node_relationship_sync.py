"""Fix-E1 回归测试: 节点 frontmatter relationships[] → Neo4j CANVAS_EDGE 同步。

GAP-E: 用户拉新节点标的原因写在 md frontmatter relationships[].description, 但降级后
无路径进 Neo4j → question_generator._get_edge_reasons (读 CANVAS_EDGE.label) 永远空。

verify_targeted_exam_chain.py Layer 3 已做真实 Neo4j 端到端 (frontmatter→CANVAS_EDGE→
_get_edge_reasons); 本文件用 capture 双 + 临时 md 做 CI 友好的纯逻辑回归 (无需 Neo4j)。
"""

from pathlib import Path

import pytest

from app.services.node_relationship_sync_service import (
    NodeRelationshipSyncService,
    _resolve_node_id,
)


class CaptureNeo4j:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def run_query(self, query: str, **params):
        self.calls.append((query, params))
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# _resolve_node_id — wikilink / 别名 / 路径 / 纯文本
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("[[base-case]]", "base-case"),
        ("[[节点/base-case]]", "base-case"),
        ("[[base-case|基线情况]]", "base-case"),
        ("[[节点/base-case.md]]", "base-case"),
        ("base-case", "base-case"),
        ("", ""),
    ],
)
def test_resolve_node_id(raw, expected):
    assert _resolve_node_id(raw) == expected


# ═══════════════════════════════════════════════════════════════════════════════
# sync — frontmatter relationships → CANVAS_EDGE{label=原因}
# ═══════════════════════════════════════════════════════════════════════════════


def _write_node_md(vault: Path, stem: str, body: str) -> None:
    (vault / f"{stem}.md").write_text(body, encoding="utf-8")


async def test_sync_writes_edge_with_reason_as_label(tmp_path, monkeypatch):
    svc = NodeRelationshipSyncService()
    cap = CaptureNeo4j()
    monkeypatch.setattr(svc, "_client", lambda: cap)

    _write_node_md(
        tmp_path,
        "recursion-base-case",
        "---\n"
        "type: concept\n"
        "relationships:\n"
        "  - type: prerequisite\n"
        '    target: "[[recursion]]"\n'
        "    description: base case 是 recursion 的前置 — 我为此拉出这个节点\n"
        "---\n\n正文。\n",
    )

    result = await svc.sync(str(tmp_path))
    assert result == {
        "nodes_with_relationships": 1,
        "edges_synced": 1,
        "failed": 0,
    }
    assert len(cap.calls) == 1
    query, params = cap.calls[0]
    assert "MERGE (s)-[e:CANVAS_EDGE" in query
    # 边方向: 持有 frontmatter 的节点 → target; label = 原因 (description)
    assert params["source_id"] == "recursion-base-case"
    assert params["target_id"] == "recursion"
    assert params["label"] == "base case 是 recursion 的前置 — 我为此拉出这个节点"
    assert params["rel_type"] == "prerequisite"


async def test_sync_falls_back_to_type_when_no_description(tmp_path, monkeypatch):
    svc = NodeRelationshipSyncService()
    cap = CaptureNeo4j()
    monkeypatch.setattr(svc, "_client", lambda: cap)
    _write_node_md(
        tmp_path,
        "n1",
        '---\nrelationships:\n  - type: depends_on\n    target: "[[n2]]"\n---\n',
    )
    await svc.sync(str(tmp_path))
    # 无 description → label 退到 rel_type (保证非空, 否则 _get_edge_reasons 过滤掉)
    assert cap.calls[0][1]["label"] == "depends_on"


async def test_sync_skips_md_without_relationships(tmp_path, monkeypatch):
    svc = NodeRelationshipSyncService()
    cap = CaptureNeo4j()
    monkeypatch.setattr(svc, "_client", lambda: cap)
    _write_node_md(tmp_path, "plain", "---\ntype: concept\n---\n\n无 relationships。\n")
    _write_node_md(tmp_path, "noyaml", "# 纯 markdown 无 frontmatter\n")
    result = await svc.sync(str(tmp_path))
    assert result["nodes_with_relationships"] == 0
    assert len(cap.calls) == 0


async def test_sync_skips_self_loop_and_empty_target(tmp_path, monkeypatch):
    svc = NodeRelationshipSyncService()
    cap = CaptureNeo4j()
    monkeypatch.setattr(svc, "_client", lambda: cap)
    _write_node_md(
        tmp_path,
        "x",
        "---\n"
        "relationships:\n"
        '  - type: related_to\n    target: "[[x]]"\n'  # 自环 → skip
        "    description: 自己指自己\n"
        '  - type: related_to\n    target: ""\n'  # 空 target → skip
        "    description: 无目标\n"
        '  - type: refines\n    target: "[[y]]"\n'  # 正常
        "    description: 细化 y\n"
        "---\n",
    )
    result = await svc.sync(str(tmp_path))
    assert result["edges_synced"] == 1
    assert cap.calls[0][1]["target_id"] == "y"


async def test_sync_multiple_relationships_one_node(tmp_path, monkeypatch):
    svc = NodeRelationshipSyncService()
    cap = CaptureNeo4j()
    monkeypatch.setattr(svc, "_client", lambda: cap)
    _write_node_md(
        tmp_path,
        "hub",
        "---\n"
        "relationships:\n"
        '  - type: prerequisite\n    target: "[[a]]"\n    description: 因为 a\n'
        '  - type: example_of\n    target: "[[b]]"\n    description: 因为 b\n'
        "---\n",
    )
    result = await svc.sync(str(tmp_path))
    assert result["edges_synced"] == 2
    targets = {c[1]["target_id"] for c in cap.calls}
    assert targets == {"a", "b"}


async def test_sync_nonexistent_vault_returns_zero(monkeypatch):
    svc = NodeRelationshipSyncService()
    cap = CaptureNeo4j()
    monkeypatch.setattr(svc, "_client", lambda: cap)
    result = await svc.sync("/nonexistent/vault/path/xyz")
    assert result["edges_synced"] == 0
    assert len(cap.calls) == 0


async def test_merge_edge_deterministic_id(tmp_path, monkeypatch):
    """同一 (source, type, target) → 同 edge_id → MERGE 幂等。"""
    svc = NodeRelationshipSyncService()
    cap = CaptureNeo4j()
    await svc._merge_edge(cap, "s", "t", "prerequisite", "原因")
    await svc._merge_edge(cap, "s", "t", "prerequisite", "原因改了")
    assert cap.calls[0][1]["edge_id"] == cap.calls[1][1]["edge_id"]
    assert cap.calls[0][1]["edge_id"] == "rel-s-prerequisite-t"
