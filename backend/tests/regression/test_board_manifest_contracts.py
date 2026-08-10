"""Board Manifest 契约锁定 (RAG-S2.5-2026-08-10)。

组 A: 成员解析 + wikilink 归一化 (结构检索是完整性契约, P=R=1.00)
组 B: 四 schema 归一化 + is_stub + role/relation + exam 摘句
组 C: dual_source_gap / orphans / 路径穿越 / 单节点解析失败不熄火
组 N: pick_hint 与 vault decay_beta.py 真相源 1e-9 数值等价 (禁漂移)

惯例对齐 test_daily_review_pick / test_rag_stage2_*: tmp_path 造 vault, 零网络。
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.services.board_manifest_service import (
    PLACEHOLDER,
    build_manifest,
    compute_generation,
    resolve_node_id,
    validate_path_component,
)

#: decay_beta 单一真相源 (与 test_decay_beta_convergence 同一路径解析)
VAULT_SCRIPTS = Path(__file__).resolve().parents[3] / "canvas-vault" / ".claude" / "scripts"

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


# ── 造数 helpers ──


def _write(vault: Path, rel: str, content: str) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _board_md(board_name: str | None = None, doc_count: int | None = None, concepts: list[str] | None = None) -> str:
    fm = ["type: whiteboard"]
    if board_name:
        fm.append(f"board_name: {board_name}")
    if doc_count is not None:
        fm.append(f"doc_count: {doc_count}")
    body = ["# 板", "", "## Concepts", ""]
    body += [f"- [[节点/{c}]] — seed note" for c in (concepts or [])]
    body += ["", "## Recent Activity", "", "- created"]
    return "---\n" + "\n".join(fm) + "\n---\n" + "\n".join(body) + "\n"


def _node_md(fm_lines: list[str], body: str = "真实内容。") -> str:
    return "---\n" + "\n".join(fm_lines) + "\n---\n" + body + "\n"


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    for d in ("节点", "原白板", "检验白板"):
        (v / d).mkdir(parents=True)
    return v


# ══ 组 A: 成员解析 + 归一化 ══


def test_membership_grouping_and_wikilink_normalization(vault):
    _write(vault, "原白板/甲板.md", _board_md(concepts=["n1", "n2", "n3"]))
    _write(vault, "原白板/乙板.md", _board_md(concepts=["n4"]))
    _write(vault, "节点/n1.md", _node_md(['source_board: "[[原白板/甲板]]"']))
    _write(vault, "节点/n2.md", _node_md(['source_board: "[[原白板/甲板|我的别名]]"']))
    _write(vault, "节点/n3.md", _node_md(["source_board: 甲板"]))
    _write(vault, "节点/n4.md", _node_md(['source_board: "[[原白板/乙板]]"']))

    m = build_manifest(vault, board_id="甲板", now=NOW)
    assert {n["node_id"] for n in m["nodes"]} == {"n1", "n2", "n3"}
    assert m["board"]["member_count_actual"] == 3
    m2 = build_manifest(vault, board_id="乙板", now=NOW)
    assert {n["node_id"] for n in m2["nodes"]} == {"n4"}


def test_empty_board_returns_empty_members_not_error(vault):
    _write(vault, "原白板/空板.md", _board_md())
    m = build_manifest(vault, board_id="空板", now=NOW)
    assert m["nodes"] == [] and m["board"]["member_count_actual"] == 0


def test_list_mode_returns_board_summaries(vault):
    _write(vault, "原白板/甲板.md", _board_md(board_name="别名板", doc_count=5))
    _write(vault, "节点/n1.md", _node_md(['source_board: "[[原白板/甲板]]"']))
    m = build_manifest(vault, now=NOW)
    assert m["board"] is None and m["nodes"] == []
    (b,) = m["boards"]
    assert b["board_id"] == "甲板" and b["board_name"] == "别名板"
    assert b["board_name_mismatch"] is True
    assert b["doc_count_declared"] == 5 and b["member_count_actual"] == 1


def test_orphans_reported_with_reasons(vault):
    _write(vault, "原白板/甲板.md", _board_md())
    _write(vault, "节点/无归属.md", _node_md(["type: concept"]))
    _write(vault, "节点/指错板.md", _node_md(['source_board: "[[原白板/不存在板]]"']))
    m = build_manifest(vault, board_id="甲板", now=NOW)
    by_id = {o["node_id"]: o for o in m["orphans"]}
    assert set(by_id) == {"无归属", "指错板"}
    # Code-Review H1: reason 只许定长枚举文案 (不插值 untrusted 值)
    assert by_id["无归属"]["reason"] == "无 source_board"
    assert by_id["指错板"]["reason"] == "source_board 指向不存在的白板"
    assert "不存在板" in by_id["指错板"]["source_board_raw"]


def test_orphan_channel_no_unbounded_content_echo(vault):
    """Code-Review H1 复现锁: source_board 塞 300 字定义 → 只回显截断 120 字,
    reason 不插值 — orphans 不得成为 exam 视图第三条自由文本泄漏通道。"""
    _write(vault, "原白板/甲板.md", _board_md())
    poison = "特征向量的完整定义是满足Av=λv的非零向量这是答案内容" * 12  # ~300 字
    _write(vault, "节点/毒孤儿.md", _node_md([f"source_board: {poison}"]))
    m = build_manifest(vault, board_id="甲板", now=NOW)
    (o,) = m["orphans"]
    assert o["reason"] == "source_board 指向不存在的白板"
    assert len(o["source_board_raw"]) <= 120
    from app.models.board_manifest import project_manifest

    exam_json = str(project_manifest(m, "exam").model_dump())
    assert poison not in exam_json  # 全文绝不出现 (只允许 ≤120 前缀)


def test_parse_error_messages_bounded_and_content_free(vault):
    """Code-Review H2/M5 复现锁: parse_errors 去内容化 — 坏 YAML 只报异常类型+
    行号 (纯 Python loader 的 str(e) 会引用原文行), 坏 last_examined 截断 80。"""
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/坏yaml.md", "---\ncorrection: 反例 diag(-1,-1) 行列式为 1 但负定\n: [炸\n---\n正文\n")
    _write(
        vault,
        "节点/坏日期.md",
        _node_md(
            [
                'source_board: "[[原白板/板]]"',
                "mastery_a: 2.0",
                "mastery_b: 3.0",
                f"last_examined: {'这不是日期' * 60}",
            ]
        ),
    )
    m = build_manifest(vault, board_id="板", now=NOW)
    assert m["parse_errors"], "两个坏文件必须有上报"
    for e in m["parse_errors"]:
        assert len(e["error"]) <= 200
        assert "diag(-1,-1)" not in e["error"]  # YAML 出错行原文绝不回显


def test_resolve_node_id_variants():
    assert resolve_node_id("[[节点/base-case]]") == "base-case"
    assert resolve_node_id("[[源笔记|别名]]") == "源笔记"
    assert resolve_node_id("base-case.md") == "base-case"
    assert resolve_node_id("[[原白板/CS 61B]]") == "CS 61B"
    assert resolve_node_id(None) == ""


# ══ 组 B: 四 schema + is_stub + relation + exam 摘句 ══


def _four_schema_vault(vault):
    _write(vault, "原白板/板.md", _board_md(concepts=["富", "标准", "遗留", "种子"]))
    _write(
        vault,
        "节点/富.md",
        _node_md(
            [
                "type: concept",
                "mastery_score: 0.01",
                "mastery_a: 2.0",
                "mastery_b: 3.0",
                "attempt_count: 2",
                "last_examined: 2026-08-01T12:00:00Z",
                'source_board: "[[原白板/板]]"',
            ]
        ),
    )
    _write(
        vault,
        "节点/标准.md",
        _node_md(
            [
                "type: concept",
                "mastery_score: 0.30",
                "created_from: ai_linked_doc",
                'source_note: "[[种子]]"',
                'source_board: "[[原白板/板]]"',
                "relationships:",
                "  - type: extends",
                '    target: "[[种子]]"',
                "    derived_at: 2026-07-23T14:30:43Z",
                "    description: 因为我不理解想单独讨论",
            ]
        ),
    )
    _write(
        vault,
        "节点/遗留.md",
        _node_md(
            [
                "subject: x",
                "mastery: 0.30",
                'source_board: "[[原白板/板]]"',
            ]
        ),
    )
    _write(vault, "节点/种子.md", _node_md(["type: concept", 'source_board: "[[原白板/板]]"']))


def test_mastery_four_state_normalization(vault):
    _four_schema_vault(vault)
    m = build_manifest(vault, board_id="板", now=NOW)
    by_id = {n["node_id"]: n for n in m["nodes"]}
    rich = by_id["富"]["mastery"]
    assert rich["source"] == "beta" and rich["a"] == 2.0 and rich["b"] == 3.0
    assert rich["score"] == 0.01  # 显式 mastery_score 优先于 μ
    assert by_id["标准"]["mastery"] == {"score": 0.30, "a": None, "b": None, "source": "score_only"}
    assert by_id["遗留"]["mastery"]["source"] == "legacy_v2"
    assert by_id["遗留"]["mastery"]["score"] == 0.30
    absent = by_id["种子"]["mastery"]
    assert absent["source"] == "absent" and absent["score"] is None
    # absent 也有 pick_hint (先验 Beta, 从未考 σ 大自动优先), days_idle=None
    assert by_id["种子"]["pick_hint"] is not None
    assert by_id["种子"]["pick_hint"]["days_idle"] is None
    assert by_id["富"]["pick_hint"]["days_idle"] == pytest.approx(9.0)


def test_mastery_level_maps_to_legacy_v2(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/n.md", _node_md(["mastery_level: 0.5", 'source_board: "[[原白板/板]]"']))
    m = build_manifest(vault, board_id="板", now=NOW)
    assert m["nodes"][0]["mastery"]["source"] == "legacy_v2"


def test_role_and_relation_extraction(vault):
    _four_schema_vault(vault)
    m = build_manifest(vault, board_id="板", now=NOW)
    by_id = {n["node_id"]: n for n in m["nodes"]}
    assert by_id["种子"]["role"] == "seed" and by_id["种子"]["relation"] is None
    std = by_id["标准"]
    assert std["role"] == "derived"
    assert std["relation"]["type"] == "extends"
    assert std["relation"]["target_node_id"] == "种子"
    assert std["relation"]["derived_reason"] == "因为我不理解想单独讨论"
    assert std["relation"]["derived_at"].startswith("2026-07-23")


def test_derived_reason_hard_truncated_500(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(
        vault,
        "节点/长因.md",
        _node_md(
            [
                'source_board: "[[原白板/板]]"',
                "relationships:",
                "  - type: extends",
                '    target: "[[种子]]"',
                f"    description: {'长' * 900}",
            ]
        ),
    )
    m = build_manifest(vault, board_id="板", now=NOW)
    assert len(m["nodes"][0]["relation"]["derived_reason"]) == 500


def test_is_stub_placeholder_detection(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/占位.md", _node_md(['source_board: "[[原白板/板]]"'], body=f"> {PLACEHOLDER}"))
    _write(vault, "节点/真实.md", _node_md(['source_board: "[[原白板/板]]"']))
    m = build_manifest(vault, board_id="板", now=NOW)
    by_id = {n["node_id"]: n for n in m["nodes"]}
    assert by_id["占位"]["is_stub"] is True and by_id["真实"]["is_stub"] is False


def test_exam_history_and_question_digests(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/概念甲.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(
        vault,
        "检验白板/板-2026-08-01-0100.md",
        "\n".join(
            [
                "---",
                "type: exam_board",
                'source_board: "[[原白板/板]]"',
                'created_at: "2026-08-01T01:00:00Z"',
                "status: done",
                "selected_node: 概念甲",
                "questions:",
                "  - id: q1",
                "    concept: 概念甲",
                '    concept_path: "节点/概念甲.md"',
                '    self_confidence: "不懂"',
                "    score: 1.00",
                "---",
                "# 检验白板 · 板",
                "",
                "> [!exam_question]+ Q1 · 概念甲",
                "> 请推导 **det(A - λI) = 0** 的来历，" + "很长的题面。" * 40,
                "",
                "**答：**",
            ]
        )
        + "\n",
    )
    m = build_manifest(vault, board_id="板", now=NOW)
    (hist,) = m["exam_history"]
    assert hist["exam_board_id"] == "板-2026-08-01-0100"
    assert hist["question_count"] == 1 and hist["status"] == "done"
    (node,) = m["nodes"]
    (dg,) = node["past_question_digests"]
    assert dg["qid"] == "q1" and dg["score"] == 1.0
    assert dg["self_confidence"] == "不懂"
    assert dg["digest"] and len(dg["digest"]) <= 160
    assert "det(A - λI) = 0" in dg["digest"]


# ══ 组 P: pick_rank 板内候选秩 (RAG-S2.6 — 替代消费侧自行对浮点数排序) ══


def _rank_vault(vault):
    """4 成员: 占位节点 pick_score 最低 (若不排除会篡夺 rank=1) + 三个真实节点。"""
    _write(vault, "原白板/板.md", _board_md())
    for node_id, mastery in (("低分", 0.1), ("中分", 0.5), ("高分", 0.9)):
        _write(vault, f"节点/{node_id}.md", _node_md([f"mastery_score: {mastery}", 'source_board: "[[原白板/板]]"']))
    _write(
        vault,
        "节点/占位.md",
        _node_md(["mastery_score: 0.05", 'source_board: "[[原白板/板]]"'], body=f"> {PLACEHOLDER}"),
    )


def test_pick_rank_orders_by_pick_score_and_excludes_stubs(vault):
    """秩只覆盖可考察候选 — 占位节点即便 pick_score 最低也恒 rank=None。

    这是消费侧「过滤 is_stub → 取 rank==1」的成立前提: 若占位节点占掉
    rank=1, 过滤后就没有 1 了 (start-exam-board Step 3 直接扑空)。
    """
    _rank_vault(vault)
    m = build_manifest(vault, board_id="板", now=NOW)
    by_id = {n["node_id"]: n for n in m["nodes"]}
    assert by_id["占位"]["pick_hint"]["pick_score"] < by_id["低分"]["pick_hint"]["pick_score"]
    assert by_id["占位"]["pick_hint"]["pick_rank"] is None, "占位节点不得进候选秩"
    assert by_id["低分"]["pick_hint"]["pick_rank"] == 1
    assert by_id["中分"]["pick_hint"]["pick_rank"] == 2
    assert by_id["高分"]["pick_hint"]["pick_rank"] == 3
    # 恒等式: 过滤占位后 rank==1 必然存在且唯一
    live = [n for n in m["nodes"] if not n["is_stub"]]
    assert [n["node_id"] for n in live if n["pick_hint"]["pick_rank"] == 1] == ["低分"]


def test_pick_rank_does_not_reorder_nodes_and_ties_break_by_node_id(vault):
    """⛔ nodes[] 契约恒为文件名序; 并列由 node_id 字典序破 (manifest 无「段内位置」)。"""
    _write(vault, "原白板/板.md", _board_md())
    for node_id, mastery in (("a并列", 0.5), ("b并列", 0.5), ("z最低", 0.1)):
        _write(vault, f"节点/{node_id}.md", _node_md([f"mastery_score: {mastery}", 'source_board: "[[原白板/板]]"']))
    m = build_manifest(vault, board_id="板", now=NOW)
    assert [n["node_id"] for n in m["nodes"]] == ["a并列", "b并列", "z最低"], "返回顺序必须仍是文件名序"
    by_id = {n["node_id"]: n["pick_hint"] for n in m["nodes"]}
    assert by_id["a并列"]["pick_score"] == pytest.approx(by_id["b并列"]["pick_score"])
    assert by_id["z最低"]["pick_rank"] == 1  # 秩与文件序不同 → 排序真的生效了
    assert by_id["a并列"]["pick_rank"] == 2 and by_id["b并列"]["pick_rank"] == 3


def test_pick_rank_survives_degraded_snapshot_path(vault):
    """降级态也必须有秩 — 2.6 之前写下的历史快照没有本字段, 故秩在 serve 侧算。"""
    from app.services.board_manifest_service import snapshot_file

    _rank_vault(vault)
    _serve(vault, now=NOW)  # 写出快照
    # 模拟历史快照: 把已落盘快照里的 pick_rank 全部抹掉
    snap = snapshot_file(vault)
    import json as _json

    raw = _json.loads(snap.read_text(encoding="utf-8"))
    for b in raw["boards"].values():
        for mem in b["members"]:
            (mem.get("pick_hint") or {}).pop("pick_rank", None)
    snap.write_text(_json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    (vault / "节点").rename(vault / "节点-改名")  # 逼降级
    m = _serve(vault, board_id="板", now=NOW)
    assert m["degraded"] is True and m["source_status"] == "snapshot"
    by_id = {n["node_id"]: n["pick_hint"] for n in m["nodes"]}
    assert by_id["低分"]["pick_rank"] == 1 and by_id["占位"]["pick_rank"] is None


def _exam_md(*question_lines: str, board: str = "板") -> str:
    """检验白板造数 (RAG-S2.6 score_scale 用): questions[] 逐行外部给。"""
    return (
        "\n".join(
            [
                "---",
                "type: exam_board",
                f'source_board: "[[原白板/{board}]]"',
                'created_at: "2026-08-01T01:00:00Z"',
                "status: done",
                "questions:",
                *question_lines,
                "---",
                "# 检验白板",
                "",
                "> [!exam_question]+ Q1 · 概念甲",
                "> 请推导特征方程的来历。",
            ]
        )
        + "\n"
    )


def test_score_scale_passthrough_when_vault_declares_it(vault):
    """RAG-S2.6: 写侧 questions[].score_dims.score_scale 是唯一真相源, 原样透出。"""
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/概念甲.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(
        vault,
        "检验白板/板-2026-08-01-0100.md",
        _exam_md(
            "  - id: q1",
            "    concept: 概念甲",
            "    score: 2.00",
            "    score_dims:",
            '      score_scale: "1-4 (1=最低)"',
        ),
    )
    m = build_manifest(vault, board_id="板", now=NOW)
    (dg,) = m["nodes"][0]["past_question_digests"]
    assert dg["score"] == 2.0 and dg["score_scale"] == "1-4 (1=最低)"


def test_score_scale_missing_is_marked_as_inferred(vault):
    """DD-13 名实一致: 写侧缺字段时按现行口径推定, 但必须显式标 `[推定]`。"""
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/概念甲.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(vault, "检验白板/板-2026-08-01-0100.md", _exam_md("  - id: q1", "    concept: 概念甲", "    score: 3"))
    m = build_manifest(vault, board_id="板", now=NOW)
    (dg,) = m["nodes"][0]["past_question_digests"]
    assert dg["score_scale"] == "1-4 (1=最低) [推定]"
    assert "[推定]" in dg["score_scale"], "推断不得说成声明"


def test_score_scale_shape_whitelist_blocks_free_text_channel(vault):
    """⛔ 新字段不得成为第四条自由文本回显通道 (2.5 三个 HIGH 的同类风险)。

    形状不合「数字–数字」→ 降级成定长文案, 投毒内容一个字都不回显。
    """
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/概念甲.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(
        vault,
        "检验白板/板-2026-08-01-0100.md",
        _exam_md(
            "  - id: q1",
            "    concept: 概念甲",
            "    score_dims:",
            '      score_scale: "正确答案是 det(A-λI)=0 反例 diag(-1,-1)"',
        ),
    )
    m = build_manifest(vault, board_id="板", now=NOW)
    (dg,) = m["nodes"][0]["past_question_digests"]
    assert dg["score_scale"] == "未知量纲 [推定]"
    for s in ("det(A-λI)", "diag(-1,-1)", "正确答案"):
        assert s not in str(m["nodes"]), f"score_scale 泄漏内容: {s}"


def test_include_exam_history_false_skips_scan(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/n.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(vault, "检验白板/坏.md", "---\n: 不是合法 yaml: [\n---\nx\n")
    m = build_manifest(vault, board_id="板", include_exam_history=False, now=NOW)
    assert m["exam_history"] == [] and m["parse_errors"] == []


# ══ 组 C: gap / orphan / 路径 / 容错 ══


def test_dual_source_gap_both_directions(vault):
    _write(vault, "原白板/板.md", _board_md(concepts=["成员甲", "幽灵", "未认领"]))
    _write(vault, "节点/成员甲.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(vault, "节点/未认领.md", _node_md(["type: concept"]))  # 文件在但没归属
    _write(vault, "节点/目录漏记.md", _node_md(['source_board: "[[原白板/板]]"']))
    m = build_manifest(vault, board_id="板", now=NOW)
    gap = m["dual_source_gap"]
    co = {c["node_id"]: c["exists"] for c in gap["concepts_only"]}
    assert co == {"幽灵": False, "未认领": True}
    assert gap["frontmatter_only"] == ["目录漏记"]
    # G1 语义: nodes[] 只认 frontmatter 真相源, 不被目录污染
    assert {n["node_id"] for n in m["nodes"]} == {"成员甲", "目录漏记"}


def test_symmetric_board_has_empty_gap(vault):
    _write(vault, "原白板/板.md", _board_md(concepts=["n1"]))
    _write(vault, "节点/n1.md", _node_md(['source_board: "[[原白板/板]]"']))
    m = build_manifest(vault, board_id="板", now=NOW)
    assert m["dual_source_gap"] == {"concepts_only": [], "frontmatter_only": []}


@pytest.mark.parametrize("bad", ["../x", "a/b", "a\\b", "..", "x\x00y", ""])
def test_path_traversal_rejected(vault, bad):
    with pytest.raises(ValueError):
        build_manifest(vault, board_id=bad, now=NOW)
    with pytest.raises(ValueError):
        validate_path_component(bad)


def test_unknown_board_raises_keyerror(vault):
    _write(vault, "原白板/板.md", _board_md())
    with pytest.raises(KeyError):
        build_manifest(vault, board_id="没这板", now=NOW)


def test_single_broken_node_does_not_kill_run(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/好.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(vault, "节点/坏.md", "---\n: [无法解析: {\n---\n正文\n")
    m = build_manifest(vault, board_id="板", now=NOW)
    assert {n["node_id"] for n in m["nodes"]} == {"好"}
    assert any("坏.md" in e["path"] for e in m["parse_errors"])


def test_negative_beta_params_reported_not_silent(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/脏.md", _node_md(["mastery_a: -3", "mastery_b: 2", 'source_board: "[[原白板/板]]"']))
    m = build_manifest(vault, board_id="板", now=NOW)
    (node,) = m["nodes"]
    assert node["pick_hint"] is None
    assert any("非正" in e["error"] for e in m["parse_errors"])


def test_pathological_last_examined_does_not_crash(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(
        vault,
        "节点/病理.md",
        _node_md(
            ["mastery_a: 2.0", "mastery_b: 3.0", "last_examined: 0001-01-01T00:00:00Z", 'source_board: "[[原白板/板]]"']
        ),
    )
    m = build_manifest(vault, board_id="板", now=NOW)
    (node,) = m["nodes"]
    assert node["pick_hint"] is not None  # 1e-150 下溢防护, 不崩
    assert node["pick_hint"]["pick_score"] == node["pick_hint"]["pick_score"]  # 非 NaN


def test_generation_changes_on_member_touch(vault):
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/n.md", _node_md(['source_board: "[[原白板/板]]"']))
    g1 = compute_generation(vault)
    _write(vault, "节点/n.md", _node_md(['source_board: "[[原白板/板]]"'], body="改了"))
    g2 = compute_generation(vault)
    assert g1 != g2 and len(g1) == 12


# ══ 组 N: pick_hint 与 decay_beta.py 真相源 1e-9 数值等价 ══


def test_pick_hint_numerically_locked_to_decay_beta(vault):
    sys.path.insert(0, str(VAULT_SCRIPTS))
    try:
        import decay_beta as dbeta
    finally:
        sys.path.remove(str(VAULT_SCRIPTS))

    from app.services import board_manifest_service as svc

    assert svc.PRIOR_A == dbeta.PRIOR_A and svc.PRIOR_B == dbeta.PRIOR_B
    assert svc.GAMMA_DAILY == dbeta.GAMMA_DAILY
    assert svc.BETA_EXPLORE == dbeta.BETA_EXPLORE

    grid_ab = [(0.9, 2.1), (0.05, 4.33), (2.0, 3.0), (9.0, 1.0), (0.05, 0.05)]
    grid_days = [0.0, 0.5, 1.0, 10.0, 69.0, 365.0, 740000.0]
    for a, b in grid_ab:
        for d in grid_days:
            ours = svc._beta_effective(a, b, d)
            theirs = dbeta.effective(a, b, d)
            assert ours[0] == pytest.approx(theirs[0], abs=1e-9)
            assert ours[1] == pytest.approx(theirs[1], abs=1e-9)
            assert svc._beta_mu(*ours) == pytest.approx(dbeta.mu(*theirs), abs=1e-9)
            assert svc._beta_sigma(*ours) == pytest.approx(dbeta.sigma(*theirs), abs=1e-9)
            assert svc._beta_pick_score(*ours) == pytest.approx(dbeta.pick_score(*theirs), abs=1e-9)
    for score in [0.0, 0.01, 0.3, 0.5, 1.0]:
        assert svc._beta_from_legacy(score) == pytest.approx(dbeta.from_legacy(score), abs=1e-9)


# ══ 组 D: exam 视图禁项 = 模型结构性缺字段 (T2) ══

#: 计划 T2 逐键断言清单: 这些键名在 ExamNodeEntry 及其嵌套模型上不得存在
FORBIDDEN_EXAM_KEYS = [
    "tips",
    "errors",
    "error_candidates",
    "misconception",
    "correction",
    "raw_dialog_excerpt",
    "evidence_turns",
    "ai_reason",
    "title",
    "aliases",
    "source_note",
    "body",
    "calibration_log",
    "calibration_count",
    "next_review",
    "created_at",
    "created_from",
]


def _all_keys(obj) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys |= _all_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            keys |= _all_keys(item)
    return keys


def _poisoned_raw_node() -> dict:
    """合成极端节点: 批注者把定义/纠错塞进一切能塞的槽位。"""
    return {
        "node_id": "毒",
        "exists": True,
        "role": "derived",
        "is_stub": False,
        "relation": {
            "type": "extends",
            "target_node_id": "种子",
            "derived_reason": "我不理解",
            "derived_at": None,
            "misconception": "泄漏的误解",
            "correction": "泄漏的更正",
        },
        "mastery": {"score": 0.3, "a": None, "b": None, "source": "score_only"},
        "attempt_count": 1,
        "last_examined": None,
        "pick_hint": None,
        "past_question_digests": [],
        "title": "泄漏标题",
        "aliases": ["泄漏别名"],
        "created_at": "2026-01-01",
        "created_from": "ai_linked_doc",
        "source_note": "种子",
        "tips": [{"text": "泄漏的 tips 正文", "tag": "question"}],
        "errors": [{"description": "泄漏的错误"}],
        "error_candidates": [
            {
                "misconception": "认为 det>0 即正定",
                "correction": "反例 diag(-1,-1)",
                "raw_dialog_excerpt": "原话摘录",
                "ai_reason": "AI 推断",
                "evidence_turns": [],
            }
        ],
        "next_review": "2026-09-01",
        "calibration_count": 4,
    }


def test_exam_entry_forbidden_keys_structurally_absent():
    from app.models.board_manifest import (
        ExamNodeEntry,
        MasteryOut,
        PickHintOut,
        QuestionDigestOut,
        RelationOut,
    )

    for key in FORBIDDEN_EXAM_KEYS:
        assert key not in ExamNodeEntry.model_fields, f"exam 禁项泄漏: {key}"
    # 嵌套模型白名单集合相等 (比逐键更强: 新增字段也会被抓)
    assert set(RelationOut.model_fields) == {"type", "target_node_id", "derived_reason", "derived_at"}
    assert set(MasteryOut.model_fields) == {"score", "a", "b", "source"}
    assert set(PickHintOut.model_fields) == {"mu", "sigma", "pick_score", "days_idle", "pick_rank"}
    assert set(QuestionDigestOut.model_fields) == {
        "exam_board_id",
        "qid",
        "asked_at",
        "score",
        "score_scale",
        "self_confidence",
        "digest",
    }
    assert set(ExamNodeEntry.model_fields) == {
        "node_id",
        "exists",
        "role",
        "is_stub",
        "relation",
        "mastery",
        "attempt_count",
        "last_examined",
        "pick_hint",
        "past_question_digests",
    }


def test_exam_projection_drops_poisoned_fields_at_any_depth():
    from app.models.board_manifest import ExamNodeEntry

    dumped = ExamNodeEntry.model_validate(_poisoned_raw_node()).model_dump()
    leaked = _all_keys(dumped) & set(FORBIDDEN_EXAM_KEYS)
    assert leaked == set(), f"exam 投影泄漏键: {leaked}"
    text = str(dumped)
    for s in ("泄漏", "det>0", "diag(-1,-1)", "原话摘录", "AI 推断"):
        assert s not in text, f"exam 投影泄漏内容: {s}"
    # 白名单槽位保留 (派生原因是 exam 合法上下文)
    assert dumped["relation"]["derived_reason"] == "我不理解"


def test_study_projection_keeps_learning_fields():
    from app.models.board_manifest import StudyNodeEntry

    node = StudyNodeEntry.model_validate(_poisoned_raw_node())
    assert node.title == "泄漏标题" and node.tips[0]["text"] == "泄漏的 tips 正文"
    assert node.error_candidates[0]["misconception"] == "认为 det>0 即正定"
    assert node.calibration_count == 4


def test_digest_and_reason_hard_limits_enforced_by_model():
    import pydantic

    from app.models.board_manifest import QuestionDigestOut, RelationOut

    with pytest.raises(pydantic.ValidationError):
        QuestionDigestOut(exam_board_id="x", digest="超" * 161)
    with pytest.raises(pydantic.ValidationError):
        RelationOut(type="extends", derived_reason="超" * 501)


def test_project_manifest_both_views_from_live(vault):
    from app.models.board_manifest import project_manifest

    _four_schema_vault(vault)
    raw = build_manifest(vault, board_id="板", now=NOW)
    exam = project_manifest(raw, "exam")
    study = project_manifest(raw, "study")
    assert exam.view == "exam" and study.view == "study"
    assert exam.source == "live" and exam.annotation_trust == "untrusted_user_data"
    assert {n.node_id for n in exam.nodes} == {"富", "标准", "遗留", "种子"}
    leaked = _all_keys(exam.model_dump()) & set(FORBIDDEN_EXAM_KEYS)
    assert leaked == set()
    with pytest.raises(ValueError):
        project_manifest(raw, "别的")


# ══ 组 E: JSON 快照兜底 + freshness + 降级三态 (T2) ══


def _serve(vault, **kw):
    from app.services.board_manifest_service import serve_manifest

    return serve_manifest(vault, **kw)


def _basic_vault(vault):
    _write(vault, "原白板/板.md", _board_md(concepts=["n1"]))
    _write(vault, "节点/n1.md", _node_md(['source_board: "[[原白板/板]]"']))


def test_serve_live_writes_snapshot_once_per_generation(vault):
    from app.services.board_manifest_service import snapshot_file

    _basic_vault(vault)
    m = _serve(vault, board_id="板", now=NOW)
    assert m["source"] == "live" and m["source_status"] == "ok" and m["degraded"] is False
    snap = snapshot_file(vault)
    assert snap.exists() and not snap.with_name(snap.name + ".tmp").exists()
    mtime1 = snap.stat().st_mtime_ns
    _serve(vault, board_id="板", now=NOW)  # 同 generation → 不重写
    assert snap.stat().st_mtime_ns == mtime1
    _write(vault, "节点/n2.md", _node_md(['source_board: "[[原白板/板]]"']))
    _serve(vault, board_id="板", now=NOW)  # generation 变更 → 重写
    assert snap.stat().st_mtime_ns != mtime1


def test_fallback_to_snapshot_when_vault_structure_gone(vault):
    _basic_vault(vault)
    _serve(vault, now=NOW)  # 先写出快照
    (vault / "节点").rename(vault / "节点-改名")  # 模拟 vault 结构不可达
    m = _serve(vault, board_id="板", now=NOW)
    assert m["source"] == "local_json" and m["source_status"] == "snapshot"
    assert m["degraded"] is True and "live 扫描失败" in m["degraded_reason"]
    assert {n["node_id"] for n in m["nodes"]} == {"n1"}  # last known good
    assert m["freshness"]["stale"] is False  # 刚生成, 未过阈值
    # 改回 → 恢复 live (mini-UAT ③ 语义)
    (vault / "节点-改名").rename(vault / "节点")
    assert _serve(vault, board_id="板", now=NOW)["source"] == "live"


def test_snapshot_stale_marked_after_threshold(vault):
    from datetime import timedelta

    _basic_vault(vault)
    _serve(vault, now=NOW)
    (vault / "节点").rename(vault / "节点-改名")
    later = NOW + timedelta(days=2)
    m = _serve(vault, board_id="板", stale_after_s=86400, now=later)
    assert m["freshness"]["stale"] is True
    assert m["freshness"]["lag_seconds"] == pytest.approx(2 * 86400, abs=1)


def test_error_state_when_no_snapshot_honest_empty(vault):
    m = _serve(vault / "根本不存在", board_id=None, now=NOW)
    assert m["source_status"] == "error" and m["degraded"] is True
    assert m["nodes"] == [] and m["boards"] is None and m["freshness"] is None
    assert "无可用快照" in m["degraded_reason"]


def test_corrupt_snapshot_falls_to_error_state(vault):
    from app.services.board_manifest_service import snapshot_file

    _basic_vault(vault)
    _serve(vault, now=NOW)
    snapshot_file(vault).write_text("{损坏的 json", encoding="utf-8")
    (vault / "节点").rename(vault / "节点-改名")
    m = _serve(vault, board_id="板", now=NOW)
    assert m["source_status"] == "error" and m["nodes"] == []


def test_single_node_parse_failure_stays_live_not_fallback(vault):
    _basic_vault(vault)
    _write(vault, "节点/坏.md", "---\n: [无法解析: {\n---\n正文\n")
    m = _serve(vault, board_id="板", now=NOW)
    assert m["source"] == "live"  # 单文件炸不触发兜底 (进 parse_errors)
    assert any("坏.md" in e["path"] for e in m["parse_errors"])


def test_snapshot_roundtrip_projection_identical_shape(vault):
    """live 与快照 serve 过同一套投影 — 泄漏控制点唯一 (计划 T2)。"""
    from app.models.board_manifest import project_manifest

    _four_schema_vault(vault)
    live = _serve(vault, board_id="板", now=NOW)
    (vault / "节点").rename(vault / "节点-改名")
    snap = _serve(vault, board_id="板", now=NOW)
    exam_live = project_manifest(live, "exam").model_dump()
    exam_snap = project_manifest(snap, "exam").model_dump()
    for m in (exam_live, exam_snap):
        assert _all_keys(m) & set(FORBIDDEN_EXAM_KEYS) == set()
    # 除 source/degraded/freshness 三组诚实信号外, 结构与内容一致
    for k in ("board", "nodes", "dual_source_gap", "orphans"):
        assert exam_live[k] == exam_snap[k]


def test_board_not_found_raises_in_snapshot_mode_too(vault):
    _basic_vault(vault)
    _serve(vault, now=NOW)
    (vault / "节点").rename(vault / "节点-改名")
    with pytest.raises(KeyError):
        _serve(vault, board_id="没这板", now=NOW)


def test_passthrough_datetime_fields_json_safe(vault):
    """live 实测 BUG-361BD6FC: YAML 把 tips[].added_at 等解析成 datetime 对象,
    快照 json.dumps 直接 TypeError → 500。透传字段必须深度 JSON-safe。"""
    import json as _json

    from app.services.board_manifest_service import snapshot_file

    _write(vault, "原白板/板.md", _board_md())
    _write(
        vault,
        "节点/带日期.md",
        _node_md(
            [
                'source_board: "[[原白板/板]]"',
                "next_review: 2026-04-21",
                "tips:",
                "  - text: 提示",
                "    added_at: 2026-07-25T08:25:03.871Z",  # YAML → datetime 对象
                "error_candidates:",
                "  - id: c1",
                "    created_at: 2026-07-13 05:09:32+00:00",  # YAML → datetime 对象
            ]
        ),
    )
    m = _serve(vault, board_id="板", now=NOW)
    assert m["source"] == "live"
    _json.dumps(m)  # 整棵树必须 JSON 原生
    assert snapshot_file(vault).exists()  # 快照写入未被 TypeError 打断
    (node,) = m["nodes"]
    assert isinstance(node["tips"][0]["added_at"], str)
    assert isinstance(node["error_candidates"][0]["created_at"], str)


def test_digest_stops_at_adjacent_callout_boundary(vault):
    """Code-Review M4 复现锁: 题面后紧跟的 [!feedback]/[!hint] callout (可含
    正确答案) 是摘句边界, 绝不吸入 digest 白名单槽位。"""
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/n1.md", _node_md(['source_board: "[[原白板/板]]"']))
    _write(
        vault,
        "检验白板/板-2026-08-01-0100.md",
        "\n".join(
            [
                "---",
                "type: exam_board",
                'source_board: "[[原白板/板]]"',
                'created_at: "2026-08-01T01:00:00Z"',
                "questions:",
                "  - id: q1",
                "    concept: n1",
                "---",
                "> [!exam_question]+ Q1 · n1",
                "> 题面正常内容。",
                "> [!feedback] 评分反馈",
                "> 正确答案是 det(A-λI)=0 这里是答案内容",
            ]
        )
        + "\n",
    )
    m = build_manifest(vault, board_id="板", now=NOW)
    (node,) = m["nodes"]
    (dg,) = node["past_question_digests"]
    assert "题面正常内容" in dg["digest"]
    assert "正确答案" not in dg["digest"] and "答案内容" not in dg["digest"]


def test_untrusted_scalars_do_not_crash_projection(vault):
    """Code-Review H3 复现锁: `doc_count: 大约五个` / `title: 2026` 等类型脏值
    必须被归一, 不得 ValidationError 500 整个端点 (含列板模式)。"""
    from app.models.board_manifest import project_manifest

    _write(vault, "原白板/板.md", "---\ntype: whiteboard\ndoc_count: 大约五个\nboard_name: 2026\n---\n# 板\n")
    _write(
        vault,
        "节点/n1.md",
        _node_md(
            [
                'source_board: "[[原白板/板]]"',
                "title: 2026",
                "created_from: 12345",
            ]
        ),
    )
    listing = build_manifest(vault, now=NOW)
    project_manifest(listing, "study")  # 列板模式不炸
    (b,) = listing["boards"]
    assert b["doc_count_declared"] is None and b["board_name"] == "2026"
    single = build_manifest(vault, board_id="板", now=NOW)
    study = project_manifest(single, "study")  # 单板双视图不炸
    project_manifest(single, "exam")
    assert study.nodes[0].title == "2026"


def test_wikilink_anchor_and_case_insensitive_board_match(vault):
    """Code-Review M6 复现锁: #heading 锚点与大小写差异不得判成假孤儿
    (假孤儿会把 untrusted 值送进 orphans 回显通道)。"""
    _write(vault, "原白板/Board.md", _board_md())
    _write(vault, "节点/带锚点.md", _node_md(['source_board: "[[原白板/Board#小节]]"']))
    _write(vault, "节点/大小写.md", _node_md(['source_board: "[[原白板/BOARD]]"']))
    m = build_manifest(vault, board_id="Board", now=NOW)
    assert {n["node_id"] for n in m["nodes"]} == {"带锚点", "大小写"}
    assert m["orphans"] == []


def test_include_exam_history_false_strips_digests_from_snapshot(vault):
    _basic_vault(vault)
    _write(
        vault,
        "检验白板/板-2026-08-01-0100.md",
        "\n".join(
            [
                "---",
                "type: exam_board",
                'source_board: "[[原白板/板]]"',
                'created_at: "2026-08-01T01:00:00Z"',
                "status: done",
                "questions:",
                "  - id: q1",
                "    concept: n1",
                "---",
                "> [!exam_question]+ Q1 · n1",
                "> 题面。",
            ]
        )
        + "\n",
    )
    _serve(vault, now=NOW)
    (vault / "节点").rename(vault / "节点-改名")
    m = _serve(vault, board_id="板", include_exam_history=False, now=NOW)
    assert m["exam_history"] == []
    assert all(n["past_question_digests"] == [] for n in m["nodes"])
    m2 = _serve(vault, board_id="板", include_exam_history=True, now=NOW)
    assert m2["nodes"][0]["past_question_digests"] != []
