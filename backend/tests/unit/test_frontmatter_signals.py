"""P1 (A+-prime 2026-06-26): 节点当前态信号读取单测。

验证 ACP 当前态从 frontmatter 真相源读 (非 Graphiti active 边):
- tips[] 按 tag 分流 (error → errors, 其余 → tips)
- relationships[].description → edge_reasons
- 删除的批注不在 frontmatter → 不返回 (幽灵记忆根治)
"""

from __future__ import annotations

import frontmatter
import pytest

import app.services.frontmatter_signals as fs


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """构造临时 vault, 把 CANVAS_BASE_PATH 指向它。"""
    (tmp_path / "节点").mkdir()
    monkeypatch.setattr(fs.settings, "CANVAS_BASE_PATH", str(tmp_path), raising=False)
    return tmp_path


def _write_node(vault, node_id: str, metadata: dict, body: str = "正文"):
    post = frontmatter.Post(body, **metadata)
    (vault / "节点" / f"{node_id}.md").write_text(
        frontmatter.dumps(post), encoding="utf-8"
    )


def test_reads_tips_split_by_tag(vault):
    _write_node(
        vault,
        "递归",
        {
            "tips": [
                {"id": "cb-1", "text": "先想 base case", "tag": "tips"},
                {"id": "cb-2", "text": "忘了终止条件", "tag": "error"},
                {"id": "cb-3", "text": "这里是关键", "tag": "keypoint"},
            ]
        },
    )
    sig = fs.read_node_frontmatter_signals("递归")
    assert sig["tips"] == ["先想 base case", "这里是关键"]  # 非 error
    assert len(sig["errors"]) == 1
    assert sig["errors"][0]["description"] == "忘了终止条件"


def test_reads_edge_reasons_from_relationships(vault):
    _write_node(
        vault,
        "代理函数",
        {
            "relationships": [
                {
                    "type": "refines",
                    "target": "[[lecture 2]]",
                    "description": "我想单独讨论",
                },
                {"type": "related_to", "target": "[[效用]]"},  # 无 description → 跳过
            ]
        },
    )
    sig = fs.read_node_frontmatter_signals("代理函数")
    assert sig["edge_reasons"] == ["我想单独讨论"]


def test_missing_file_returns_empty(vault):
    sig = fs.read_node_frontmatter_signals("不存在的节点")
    assert sig == {"tips": [], "errors": [], "edge_reasons": []}


def test_deleted_tip_not_returned_ghost_memory_fixed(vault):
    """用户删 callout → frontmatter tips[] 不含它 → 当前态不返回 (P1 核心)。"""
    # 初始 2 条
    _write_node(
        vault,
        "n",
        {
            "tips": [
                {"id": "cb-a", "text": "保留的批注", "tag": "tips"},
                {"id": "cb-b", "text": "将被删除的批注", "tag": "tips"},
            ]
        },
    )
    assert len(fs.read_node_frontmatter_signals("n")["tips"]) == 2
    # 用户删掉 cb-b (frontmatter 完全覆盖语义)
    _write_node(
        vault, "n", {"tips": [{"id": "cb-a", "text": "保留的批注", "tag": "tips"}]}
    )
    sig = fs.read_node_frontmatter_signals("n")
    assert sig["tips"] == ["保留的批注"]  # 删掉的不再出现 = 幽灵记忆根治


def test_empty_text_skipped(vault):
    _write_node(vault, "n", {"tips": [{"id": "x", "text": "  ", "tag": "tips"}]})
    assert fs.read_node_frontmatter_signals("n")["tips"] == []


def test_no_frontmatter_returns_empty(vault):
    (vault / "节点" / "plain.md").write_text(
        "没有 frontmatter 的正文", encoding="utf-8"
    )
    assert fs.read_node_frontmatter_signals("plain") == {
        "tips": [],
        "errors": [],
        "edge_reasons": [],
    }
