"""daily_review_pick 选板逻辑锁定 (DAILY-REVIEW-PUSH-2026-07-29, Code-Review M6)。

12 场景运行时矩阵之外的纯逻辑层: 病理日期不崩全轮 / wikilink 归一 /
占位符跳过 / tie-break 三级 / 脏数值进 corrupt / BOM 容忍。
"""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_pick as picker  # noqa: E402

NOW = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)


_seq = iter(range(1000))


def _build(tmp_path, nodes: dict, blr: dict | None = None):
    vault = tmp_path / f"vault{next(_seq)}"  # 同一测试可多次调用, 各建独立 vault
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for name, content in nodes.items():
        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    return picker.build_payload(vault, NOW, blr or {}, picker.load_decay(vault))


def _node(board="普通板", extra=""):
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def test_pathological_last_examined_does_not_kill_run(tmp_path):
    """Code-Review M2: 年份手滑成 0001 的节点不得崩掉整轮生成。"""
    payload, ranked = _build(
        tmp_path,
        {
            "病理": _node(extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 0001-01-01T00:00:00Z\n"),
            "正常": _node(),
        },
    )
    assert payload["stats"]["corrupt"] == 0 and len(ranked) == 1
    assert all(r["priority"] == r["priority"] for r in ranked)  # 无 NaN


def test_wikilink_board_normalization(tmp_path):
    payload, ranked = _build(tmp_path, {"甲": _node(board="我的板")})
    assert ranked[0]["board"] == "我的板"
    assert "node 甲" in picker.render_md(payload, ranked)


def test_placeholder_node_skipped_empty_notification(tmp_path):
    payload, ranked = _build(
        tmp_path,
        {
            "占位": _node(extra="").replace("真实内容。", "> 你的 1-2 句精准定义"),
        },
    )
    assert payload["stats"]["ineligible"] == 1
    assert ranked == [] and payload["notification"] is None


def test_tiebreak_prefers_least_recently_recommended(tmp_path):
    nodes = {"a节点": _node(board="A板"), "b节点": _node(board="B板")}
    _, ranked = _build(tmp_path, nodes, blr={"A板": "2026-07-29"})
    assert ranked[0]["board"] == "B板", "同分时从未被推荐的板优先"
    _, ranked2 = _build(tmp_path, nodes)
    assert ranked2[0]["board"] == "A板", "全无记录时按板名稳定排序"


def test_negative_mastery_counted_corrupt_not_silent(tmp_path):
    """Code-Review L5: mastery_a: -3 必须进 corrupt, 不得静默当无字段。"""
    payload, ranked = _build(
        tmp_path,
        {
            "脏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
        },
    )
    assert payload["stats"]["corrupt"] == 1 and ranked == []


def test_bom_frontmatter_tolerated(tmp_path):
    payload, _ = _build(
        tmp_path,
        {
            "带bom": "﻿" + _node(extra="mastery_a: 1.0\nmastery_b: 1.0\n"),
        },
    )
    assert payload["stats"]["new"] == 1


def test_unassigned_nodes_named_in_md(tmp_path):
    """Code-Review M3: 无 source_board 节点点名可见, 不再只是个数字。"""
    payload, ranked = _build(
        tmp_path,
        {
            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
            "正常": _node(),
        },
    )
    assert payload["unassigned_nodes"] == ["孤儿"]
    assert "孤儿" in picker.render_md(payload, ranked)
