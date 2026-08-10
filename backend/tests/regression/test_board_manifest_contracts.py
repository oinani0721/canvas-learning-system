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
    assert by_id["无归属"]["reason"] == "无 source_board"
    assert "不存在板" in by_id["指错板"]["reason"]


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
