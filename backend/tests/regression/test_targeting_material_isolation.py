"""批次1'② targeting-material 隔离回归 (MEM-FLYWHEEL-2026-07-22)。

对抗审查 C1 实锤: 测试种子 (UAT-2.5.X, errors[] 缺 group_id) 走「老记录
无 group_id 放行」通道泄漏进真实出题链。本套件锁定 fail-closed 契约:

  - errors[] 缺 group_id → 拒收 (缺失放行只准存在于离线迁移工具, ChatGPT R1 三层防线裁决)
  - Cypher 邻居/节点谓词严格相等 (不再 IS NULL 放行), 且带确定性 ORDER BY
  - degraded 四态可区分: neo4j_unavailable / node_not_found / no_neighbors / no_neighbor_errors
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import targeting_material_service as tms

GROUP = "vault:cs_61b"


def _write_node_md(tmp_path, node_id: str, front: str) -> None:
    (tmp_path / f"{node_id}.md").write_text(
        f"---\n{front}---\n\n正文\n", encoding="utf-8"
    )


def _patch_md_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(
        tms,
        "_node_md_path",
        lambda nid: p if (p := tmp_path / f"{nid}.md").exists() else None,
    )


# ── _read_neighbor_errors: fail-closed 契约 ──


def test_errors_without_group_id_rejected(monkeypatch, tmp_path):
    """C1 泄漏通道: 缺 group_id 的 errors[] 必须拒收 (原行为=放行)。"""
    _write_node_md(
        tmp_path,
        "neighbor-a",
        "errors:\n  - description: 学生混淆了 admissibility 和 consistency\n",
    )
    _patch_md_dir(monkeypatch, tmp_path)
    assert tms._read_neighbor_errors("neighbor-a", group_id=GROUP) == []


def test_errors_with_matching_group_id_accepted(monkeypatch, tmp_path):
    _write_node_md(
        tmp_path,
        "neighbor-b",
        f"errors:\n  - description: 误认为 heap 是有序的\n    group_id: '{GROUP}'\n",
    )
    _patch_md_dir(monkeypatch, tmp_path)
    assert tms._read_neighbor_errors("neighbor-b", group_id=GROUP) == [
        "误认为 heap 是有序的"
    ]


def test_errors_with_foreign_group_id_rejected(monkeypatch, tmp_path):
    _write_node_md(
        tmp_path,
        "neighbor-c",
        "errors:\n  - description: CS188 测试种子\n    group_id: 'vault:cs188_test'\n",
    )
    _patch_md_dir(monkeypatch, tmp_path)
    assert tms._read_neighbor_errors("neighbor-c", group_id=GROUP) == []


def test_tips_error_channel_still_works(monkeypatch, tmp_path):
    """tips[] 无 group_id 字段, 节点级隔离由 Cypher 谓词负责 — 通道保持可用。"""
    _write_node_md(
        tmp_path,
        "neighbor-d",
        "tips:\n  - tag: error\n    text: 把 base case 写成了 n==1\n",
    )
    _patch_md_dir(monkeypatch, tmp_path)
    assert tms._read_neighbor_errors("neighbor-d", group_id=GROUP) == [
        "把 base case 写成了 n==1"
    ]


def test_misconception_preferred_over_description(monkeypatch, tmp_path):
    """P5 泄题防御回归: misconception 优先, 更正半句永不进素材。"""
    _write_node_md(
        tmp_path,
        "neighbor-e",
        f"errors:\n  - misconception: 以为 DFS 一定找到最短路\n"
        f"    description: 更正后的完整解释\n    group_id: '{GROUP}'\n",
    )
    _patch_md_dir(monkeypatch, tmp_path)
    assert tms._read_neighbor_errors("neighbor-e", group_id=GROUP) == [
        "以为 DFS 一定找到最短路"
    ]


# ── collect_targeting_material: Cypher 契约 + 四态 degraded ──


def _mock_client(records):
    client = MagicMock()
    client.run_query = AsyncMock(return_value=records)
    return client


async def _collect_with(records):
    client = _mock_client(records)
    with patch("app.clients.neo4j_client.get_neo4j_client", return_value=client):
        result = await tms.collect_targeting_material("node-x", GROUP)
    return result, client.run_query.call_args


async def test_cypher_is_fail_closed_and_ordered():
    """谓词严格相等 (无 IS NULL 放行) + 确定性 ORDER BY + n 侧也滤 group。"""
    _, call = await _collect_with([])
    cypher = call.args[0]
    assert "IS NULL" not in cypher
    assert "ORDER BY" in cypher
    assert cypher.count("group_id = $group_id") >= 3  # n 侧 + 边 + m 侧


async def test_degraded_node_not_found():
    result, _ = await _collect_with([])
    assert result["degraded"] is True
    assert result["degraded_reason"] == "node_not_found"
    assert result["materials"] == []


async def test_degraded_no_neighbors():
    result, _ = await _collect_with([{"neighbor_id": None, "reason": None}])
    assert result["degraded"] is True
    assert result["degraded_reason"] == "no_neighbors"


async def test_degraded_no_neighbor_errors(monkeypatch, tmp_path):
    _patch_md_dir(monkeypatch, tmp_path)  # 邻居 md 不存在 → 无素材
    result, _ = await _collect_with([{"neighbor_id": "ghost", "reason": "相关"}])
    assert result["degraded"] is True
    assert result["degraded_reason"] == "no_neighbor_errors"


async def test_degraded_neo4j_unavailable():
    client = MagicMock()
    client.run_query = AsyncMock(side_effect=ConnectionError("boom"))
    with patch("app.clients.neo4j_client.get_neo4j_client", return_value=client):
        result = await tms.collect_targeting_material("node-x", GROUP)
    assert result["degraded"] is True
    assert result["degraded_reason"].startswith("neo4j_unavailable")


async def test_happy_path_not_degraded(monkeypatch, tmp_path):
    _write_node_md(
        tmp_path,
        "real-neighbor",
        f"errors:\n  - description: 混淆入栈出栈顺序\n    group_id: '{GROUP}'\n",
    )
    _patch_md_dir(monkeypatch, tmp_path)
    result, _ = await _collect_with(
        [{"neighbor_id": "real-neighbor", "reason": "因为都用栈"}]
    )
    assert result["degraded"] is False
    assert result["degraded_reason"] is None
    assert result["materials"] == [
        {
            "source_node": "real-neighbor",
            "relation_reason": "因为都用栈",
            "kind": "error",
            "text": "混淆入栈出栈顺序",
        }
    ]
