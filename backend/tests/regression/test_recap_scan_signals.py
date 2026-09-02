"""G5-4 — 偏航 lint 一梯队信号裁判 (BATCH-2026-08-28-第五批 / CARD-G5-4)。

被测物: canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py

裁判覆盖 (卡片完成条件逐条):
  (a) scan JSON 加性新增 signals 块 — 四信号各含 value/denominator/
      percentile_ref (板内分位参考)/availability (实测|文件|推定|无据)/asof;
      ledger 行加性补 source_note; 既有 v1 键零破坏 (键回归)。
  (b) 0 阈值: signals 块无任何判定/合格线字段 — 判偏航留人。
  (c) 措辞两模式通杀: fallback 与 manifest 两版全量报告 (含信号标准行)
      均过自家 verifier — 不被派生词禁令与「偏离」禁词打死 (fixture 锁定)。
  (d) --verify 扩展: 篡改任一信号数字/档位 → exit 1; 缺行 → exit 1;
      无据错标 → exit 1; 旧 scan JSON (无 signals 键) → 兼容 PASS。
  零编造: denominator==0 → value=null + availability="无据"。
  零写侧: collect 运行前后 vault 全树 (sha256+mtime_ns) 逐字节一致。

fixtures 全部在 tmp_path 程序化构造 (与 test_split_preview.py 同惯例),
时间戳用相对当前时刻构造 (N 天 + 2h 前 → floor 年龄恰 N 天, 确定性)。
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "canvas-vault" / ".claude" / "skills" / "board-recap" / "scripts" / "recap_scan.py"

BOARD = "T板"

# ── v1 契约快照 (键回归基准; 破坏任一 = 消费面断裂) ──
V1_TOP_KEYS = {
    "board_exists",
    "board_stem",
    "board_name",
    "recap_date",
    "report_path",
    "data_mode",
    "manifest",
    "source_revision",
    "ledger",
    "counts",
    "tips_oldest3",
    "scale_gate",
    "concepts_members",
    "previous_recap",
    "unsafe_write_targets",
}
V1_COUNTS_KEYS = {
    "members",
    "seeds",
    "derived",
    "stubs",
    "never_examined",
    "tips_total",
    "tips_unanswered_upper_bound",
    "tips_understanding_open",
    "tips_undated",
    "body_callouts",
    "annotations",
    "relation_types",
    "error_candidates_pending",
}
SIGNAL_KEYS = {
    "unanswered_question_age",
    "source_coverage",
    "unsourced_conclusions",
    "duplicate_accumulation",
}
SIGNAL_REQUIRED_FIELDS = {
    "value",
    "denominator",
    "percentile_ref",
    "availability",
    "asof",
}


def _ts(days: int) -> str:
    """N 天 + 2h 前的 ISO 时间戳 → collect 时 floor 年龄恰 N 天。"""
    return (datetime.now(timezone.utc) - timedelta(days=days, hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_collect(vault: Path, board: str = BOARD, *extra: str) -> subprocess.CompletedProcess:
    if not SCRIPT.exists():  # 防「脚本不存在 → 非零退出 → 拒绝类断言假绿」
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault), "--board", board, *extra],
        capture_output=True,
        text=True,
        timeout=60,
    )


def run_verify(report: Path) -> subprocess.CompletedProcess:
    if not SCRIPT.exists():
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--verify", str(report)],
        capture_output=True,
        text=True,
        timeout=60,
    )


# ────────────────────────── fixture 构造器 ──────────────────────────


def write_node(
    vault: Path,
    name: str,
    *,
    source_note: str | None = None,
    derived_from: str | None = None,
    tips: list[dict] | None = None,
    stub: bool = False,
) -> None:
    fm = ["---", "type: concept", f'source_board: "[[原白板/{BOARD}]]"']
    if source_note:
        fm.append(f'source_note: "{source_note}"')
    if derived_from:
        fm.append(f'derived-from: "{derived_from}"')
    if tips:
        fm.append("tips:")
        for t in tips:
            fm.append(f"  - text: {t['text']}")
            if t.get("added_at"):
                fm.append(f"    added_at: {t['added_at']}")
            if t.get("understanding"):
                fm.append(f"    understanding: {t['understanding']}")
    fm.append("---")
    body = f"# {name}\n\n## 核心概念\n\n"
    body += "（你的 1-2 句精准定义。）\n" if stub else "已有正文。\n"
    (vault / "节点" / f"{name}.md").write_text("\n".join(fm) + "\n" + body, encoding="utf-8")


def build_vault(tmp_path: Path, members: list[str]) -> Path:
    vault = tmp_path / "vault"
    for sub in ("原白板", "节点", "outputs"):
        (vault / sub).mkdir(parents=True)
    links = "\n".join(f"- [[节点/{m}]]" for m in members)
    (vault / "原白板" / f"{BOARD}.md").write_text(
        f"---\ntype: whiteboard\nboard_name: {BOARD}\n---\n\n# {BOARD}\n\n## Concepts\n\n{links}\n",
        encoding="utf-8",
    )
    return vault


def standard_vault(tmp_path: Path) -> Path:
    """3 成员: 种子无 provenance + 派生带 source_note + 派生缺 source_note。"""
    vault = build_vault(tmp_path, ["SeedA", "DerivedB", "DerivedC"])
    write_node(
        vault,
        "SeedA",
        tips=[
            {"text": "What is X", "added_at": _ts(11)},
            {"text": "what   is x", "added_at": _ts(5)},
        ],
    )
    write_node(
        vault,
        "DerivedB",
        source_note="[[节点/SeedA|别名]]",
        derived_from="[[SeedA]]",
        tips=[
            {"text": "What is X", "added_at": _ts(2)},
            {"text": "unique question", "added_at": "not-a-date"},
        ],
        stub=True,
    )
    write_node(vault, "DerivedC", derived_from="[[SeedA]]")
    return vault


def collect_json(vault: Path, *extra: str) -> dict:
    r = run_collect(vault, BOARD, *extra)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def make_manifest(vault: Path) -> Path:
    """manifest 模式 fixture: 与 standard_vault 同板 3 成员。"""
    nodes = [
        {
            "node_id": "SeedA",
            "role": "seed",
            "is_stub": False,
            "source_note": None,
            "tips": [
                {"text": "What is X", "added_at": _ts(11)},
                {"text": "what   is x", "added_at": _ts(5)},
            ],
        },
        {
            "node_id": "DerivedB",
            "role": "derived",
            "is_stub": True,
            "source_note": "SeedA",
            # L1 (Codex round-2 fixture 忠实度): 真 frontmatter 只有
            # derived-from 单链 → _node_relation 走退路分支产 derived_from
            # 且 derived_reason/derived_at 为 None（原先手写成 extends 失真）
            "relation": {
                "type": "derived_from",
                "target_node_id": "SeedA",
                "derived_reason": None,
                "derived_at": None,
            },
            "tips": [{"text": "What is X", "added_at": _ts(2)}],
        },
        {
            "node_id": "DerivedC",
            "role": "derived",
            "is_stub": False,
            "source_note": None,
            # 镜像真 build_manifest: derived-from 单链 → relation 退路分支
            # (Codex round-1 指出手搓 manifest 漏此字段与真形状不符;
            #  round-2 L1 补 derived_reason/derived_at 两键)
            "relation": {
                "type": "derived_from",
                "target_node_id": "SeedA",
                "derived_reason": None,
                "derived_at": None,
            },
            "tips": [],
        },
    ]
    manifest = {
        "board": {"board_id": BOARD, "board_name": BOARD},
        "source_status": "ok",
        "source": "live",
        "nodes": nodes,
        "freshness": {"generated_at": _ts(0), "lag_seconds": 1, "stale": False},
    }
    p = vault / "outputs" / f".recap-manifest-{BOARD}.json"
    p.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return p


def vault_snapshot(vault: Path) -> dict[str, tuple[str, int]]:
    out: dict[str, tuple[str, int]] = {}
    for p in sorted(vault.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(vault))] = (
                hashlib.sha256(p.read_bytes()).hexdigest(),
                st.st_mtime_ns,
            )
    return out


# ────────────────────────── (a) 键回归 + signals 形状 ──────────────────────────


def test_v1_keys_regression_and_signals_shape(tmp_path):
    scan = collect_json(standard_vault(tmp_path))
    assert V1_TOP_KEYS <= set(scan), f"v1 顶层键缺失: {V1_TOP_KEYS - set(scan)}"
    assert set(scan["counts"]) == V1_COUNTS_KEYS, "counts 键面变化 (须加性且本卡未加)"
    assert "signals" in scan, "signals 块缺失"
    sig = scan["signals"]
    assert sig["signals_version"] == 1
    assert sig["policy"] == "zero_threshold"
    assert SIGNAL_KEYS <= set(sig)
    for key in SIGNAL_KEYS:
        missing = SIGNAL_REQUIRED_FIELDS - set(sig[key])
        assert not missing, f"signals.{key} 缺必备字段: {missing}"
        assert sig[key]["asof"] == scan["source_revision"]["scan_at_utc"]
    # ledger 行加性 source_note (fallback 从 frontmatter 抄录并归一 stem)
    rows = {r["node_id"]: r for r in scan["ledger"]["seeds"] + scan["ledger"]["derived"]}
    assert rows["DerivedB"]["source_note"] == "SeedA"  # [[节点/SeedA|别名]] → stem
    assert rows["SeedA"]["source_note"] is None
    assert rows["DerivedC"]["source_note"] is None


def test_zero_threshold_no_judgement_keys(tmp_path):
    """(b) 0 阈值: signals 块任何层级不得出现判定/合格线类键名。"""
    sig = collect_json(standard_vault(tmp_path))["signals"]
    # 注意避免误伤: source_coverage 含子串 over → 只列判定语义明确的词根
    banned = (
        "threshold",
        "exceed",
        "warn",
        "verdict",
        "judg",
        "grade",
        "breach",
        "violat",
    )

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k != "policy":  # policy 值声明 zero_threshold, 键名本身中性
                    assert not any(b in k.lower() for b in banned), f"判定类键: {path}.{k}"
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")

    walk(sig)


# ────────────────────────── 信号1 · 未答问题年龄 ──────────────────────────


def test_age_signal_values_and_percentiles(tmp_path):
    sig = collect_json(standard_vault(tmp_path))["signals"]["unanswered_question_age"]
    # dated ages = [2, 5, 11] (11d+2h / 5d+2h / 2d+2h 前); "not-a-date" 不参与
    assert sig["value"] == 11
    assert sig["denominator"] == 3
    assert sig["undated"] == 1
    assert sig["percentile_ref"] == {
        "p25_days": 2,
        "p50_days": 5,
        "p75_days": 11,
        "max_days": 11,
    }
    assert sig["availability"] == "文件"  # 时序封顶: manifest 也不升实测


def test_age_signal_nodata_when_no_dated_tips(tmp_path):
    vault = build_vault(tmp_path, ["SeedA"])
    write_node(vault, "SeedA", tips=[{"text": "q", "added_at": "garbage"}])
    sig = collect_json(vault)["signals"]["unanswered_question_age"]
    assert sig["value"] is None
    assert sig["denominator"] == 0
    assert sig["percentile_ref"] is None
    assert sig["availability"] == "无据"
    assert sig["undated"] == 1


def test_age_future_added_at_clamped_zero(tmp_path):
    vault = build_vault(tmp_path, ["SeedA"])
    future = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_node(vault, "SeedA", tips=[{"text": "q", "added_at": future}])
    sig = collect_json(vault)["signals"]["unanswered_question_age"]
    assert sig["value"] == 0  # 未来时间戳按 0 天计, 不产出负年龄
    assert sig["availability"] == "文件"


# ────────────────────────── 信号2/3 · 覆盖率与无来源结论 ──────────────────────────


def test_coverage_and_unsourced_fallback(tmp_path):
    """F1 后: fallback 把 derived-from 认作来源锚点 (对齐 manifest 退路分支)。"""
    sig = collect_json(standard_vault(tmp_path))["signals"]
    cov = sig["source_coverage"]
    # DerivedB (source_note+derived-from) + DerivedC (derived-from) 均有锚
    assert (cov["value"], cov["denominator"]) == (2, 3)
    assert cov["availability"] == "文件"
    assert cov["percentile_ref"] is None  # 二值信号无分位, 板内参考=by_role
    assert cov["by_role"]["derived"] == {"with_provenance": 2, "total": 2}
    assert cov["by_role"]["seed"] == {"with_provenance": 0, "total": 1}
    uns = sig["unsourced_conclusions"]
    assert (uns["value"], uns["denominator"]) == (0, 2)
    assert uns["node_ids"] == []
    assert uns["availability"] == "推定"  # fallback role 是本地推定


def test_coverage_and_unsourced_manifest_measured(tmp_path):
    vault = standard_vault(tmp_path)
    mpath = make_manifest(vault)
    scan = collect_json(vault, "--manifest", str(mpath))
    assert scan["data_mode"] == "manifest"
    sig = scan["signals"]
    cov = sig["source_coverage"]
    assert (cov["value"], cov["denominator"]) == (2, 3)  # B (note+rel) + C (rel)
    assert cov["availability"] == "实测"
    uns = sig["unsourced_conclusions"]
    assert (uns["value"], uns["denominator"]) == (0, 2)
    assert uns["node_ids"] == []
    assert uns["availability"] == "实测"
    # ledger 行加性 source_note (manifest 透传)
    rows = {r["node_id"]: r for r in scan["ledger"]["derived"]}
    assert rows["DerivedB"]["source_note"] == "SeedA"


def test_cross_mode_signal_consistency_real_manifest(tmp_path):
    """F1 回归锁 (Codex G5-4 round-1 复现路径): 同一 vault 用**真**
    board_manifest_service.build_manifest 产 manifest, 两模式的来源覆盖/
    无来源结论 value/denominator 必须全等 — fallback 不得比 manifest 多报
    「无来源」假警报。"""
    from app.services.board_manifest_service import build_manifest

    vault = standard_vault(tmp_path)
    fallback = collect_json(vault)
    manifest = build_manifest(vault, board_id=BOARD, include_exam_history=True)
    mp = vault / "outputs" / "real-manifest.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    measured = collect_json(vault, "--manifest", str(mp))
    assert measured["data_mode"] == "manifest"
    for key in ("source_coverage", "unsourced_conclusions"):
        f, m = fallback["signals"][key], measured["signals"][key]
        assert (f["value"], f["denominator"]) == (m["value"], m["denominator"]), (
            f"两模式信号分叉 {key}: fallback={f['value']}/{f['denominator']} manifest={m['value']}/{m['denominator']}"
        )


@pytest.mark.parametrize("key", ["derived-from", "derived_from"])
def test_role_and_anchor_accept_both_spellings(tmp_path, key):
    """H1/W1 回归锁: 连字符与下划线两种拼写同口径 — role 与 relation_target
    必须一致（原先 role 只认连字符 → seed 却带 relation_target 自相矛盾，
    且与后端 _node_role 分叉）。"""
    vault = build_vault(tmp_path, ["SeedA", "D"])
    write_node(vault, "SeedA")
    (vault / "节点" / "D.md").write_text(
        f'---\ntype: concept\nsource_board: "[[原白板/{BOARD}]]"\n{key}: "[[节点/SeedA]]"\n---\n# D\n正文。\n',
        encoding="utf-8",
    )
    scan = collect_json(vault)
    rows = {r["node_id"]: r for r in scan["ledger"]["seeds"] + scan["ledger"]["derived"]}
    assert rows["D"]["role"] == "derived", f"{key} 拼写未被识别为派生"
    assert rows["D"]["relation_target"] == "SeedA"
    # 恒等式: relation_types 聚合数不得超过 derived 计数
    assert scan["counts"]["relation_types"].get("derived_from", 0) <= scan["counts"]["derived"]


def test_empty_key_does_not_fabricate_anchor(tmp_path):
    """W2 回归锁 (workflow round-1 复现): 空 `derived-from:` 键不得把**下一行**
    当成自己的值（_fm_scalar 的 \\s* 曾跨换行 → 凭空捏造来源锚点/掌握度）。"""
    vault = build_vault(tmp_path, ["E"])
    (vault / "节点" / "E.md").write_text(
        f'---\ntype: concept\nsource_board: "[[原白板/{BOARD}]]"\n'
        "derived-from:\nmastery_score: 0.5\n---\n# E\n正文。\n",
        encoding="utf-8",
    )
    scan = collect_json(vault)
    row = (scan["ledger"]["derived"] + scan["ledger"]["seeds"])[0]
    assert row["relation_target"] is None, f"空键捏造了锚点: {row['relation_target']!r}"
    assert row["mastery_score"] == 0.5, "同行标量抄录被误伤"
    # round-3 H1: 空/null 值的 derived-from 按后端 truthiness 判 seed
    # （board_manifest_service._node_role 对 falsy 值不算派生痕迹）→
    # 该节点不进派生分母，无来源结论信号如实无据
    assert row["role"] == "seed", "空 derived-from 仍被当派生（与后端分叉）"
    uns = scan["signals"]["unsourced_conclusions"]
    assert (uns["value"], uns["denominator"]) == (None, 0)
    assert uns["availability"] == "无据"


def test_role_not_flipped_by_frontmatter_text_mention(tmp_path):
    """W3 回归锁: frontmatter **值**里提到 'derived-from' 一词（如批注正文）
    不得把节点翻成 derived — 否则信号 3 会点名一个毫无派生元数据的节点。"""
    vault = build_vault(tmp_path, ["T"])
    (vault / "节点" / "T.md").write_text(
        f'---\ntype: concept\nsource_board: "[[原白板/{BOARD}]]"\n'
        "tips:\n  - text: 这个概念和 derived-from 机制有关吗\n"
        "    added_at: 2026-08-20T00:00:00Z\n---\n# T\n正文。\n",
        encoding="utf-8",
    )
    scan = collect_json(vault)
    rows = {r["node_id"]: r for r in scan["ledger"]["seeds"] + scan["ledger"]["derived"]}
    assert rows["T"]["role"] == "seed", "正文提及关键词导致角色误判"
    uns = scan["signals"]["unsourced_conclusions"]
    assert uns["availability"] == "无据" and uns["node_ids"] == []


@pytest.mark.parametrize(
    "fm_extra",
    [
        "derived-from: null\n",
        "derived-from:\n",
        'derived-from: ""\n',
        "created_from: ai_linked_doc # 派生自插件\n",
        "created_from: manual\n",
    ],
)
def test_role_matches_backend_node_role_exactly(tmp_path, fm_extra):
    """H1 回归锁 (round-3): fallback 的 role 必须与后端 _node_role 对同一
    frontmatter 给出**相同**结论——null/空值按 truthiness 判 seed，
    带行尾注释的 created_from 仍判 derived。"""
    from app.services.board_manifest_service import _node_role
    import yaml

    vault = build_vault(tmp_path, ["N"])
    fm_text = f'type: concept\nsource_board: "[[原白板/{BOARD}]]"\n{fm_extra}'
    (vault / "节点" / "N.md").write_text(f"---\n{fm_text}---\n# N\n正文。\n", encoding="utf-8")
    scan = collect_json(vault)
    rows = {r["node_id"]: r for r in scan["ledger"]["seeds"] + scan["ledger"]["derived"]}
    backend_role = _node_role(yaml.safe_load(fm_text))
    assert rows["N"]["role"] == backend_role, f"fallback role={rows['N']['role']} 与后端 _node_role={backend_role} 分叉"


def test_manifest_note_normalization_is_idempotent(tmp_path):
    """M1 回归锁 (round-3): 后端 resolve 过的裸 stem 在 manifest 侧不得被
    二次判 null——'null' 这个合法节点名两模式必须同值。"""
    vault = standard_vault(tmp_path)
    mpath = vault / "outputs" / "m.json"
    mpath.write_text(
        json.dumps(
            {
                "board": {"board_id": BOARD, "board_name": BOARD},
                "source_status": "ok",
                "nodes": [
                    {
                        "node_id": "X",
                        "role": "derived",
                        # 后端 resolve_node_id("[[节点/null]]") 的输出形态
                        "source_note": "null",
                        "relation": {"type": "derived_from", "target_node_id": "null"},
                        "tips": [],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    scan = collect_json(vault, "--manifest", str(mpath))
    row = scan["ledger"]["derived"][0]
    assert row["source_note"] == "null", "后端已归一的 stem 被二次判成 null 清除"
    assert row["relation_target"] == "null"
    cov = scan["signals"]["source_coverage"]
    assert (cov["value"], cov["denominator"]) == (1, 1)


def test_strip_note_ref_idempotent_on_wikilinked_null_name(tmp_path):
    """M1 回归锁 (Codex round-2): 名为 null 的节点用 wikilink 引用时必须
    归一为 stem 'null'（不能当 YAML null 清掉）——保证两模式/两次归一幂等；
    裸 null 字面量仍按空处理。"""
    vault = build_vault(tmp_path, ["A", "B"])
    (vault / "节点" / "A.md").write_text(
        f'---\ntype: concept\nsource_board: "[[原白板/{BOARD}]]"\nsource_note: "[[节点/null]]"\n---\n# A\n正文。\n',
        encoding="utf-8",
    )
    (vault / "节点" / "B.md").write_text(
        f'---\ntype: concept\nsource_board: "[[原白板/{BOARD}]]"\nsource_note: null\n---\n# B\n正文。\n',
        encoding="utf-8",
    )
    rows = {r["node_id"]: r for r in collect_json(vault)["ledger"]["seeds"] + collect_json(vault)["ledger"]["derived"]}
    assert rows["A"]["source_note"] == "null", "合法 wikilink 节点名被当 YAML null 清除"
    assert rows["B"]["source_note"] is None, "裸 null 字面量被当成锚点"


def test_null_literal_provenance_not_counted(tmp_path):
    """F4 + round-3 H1 回归锁: YAML null 字面量既不算来源锚点，也不算派生
    痕迹 —— 与后端 _node_role 的 truthiness 语义一致（falsy ⇒ seed）。"""
    vault = build_vault(tmp_path, ["SeedA", "DerivedNull"])
    write_node(vault, "SeedA")
    (vault / "节点" / "DerivedNull.md").write_text(
        "---\ntype: concept\n"
        'source_board: "[[原白板/T板]]"\n'
        "source_note: null\n"
        "derived-from: null\n"
        "---\n# DerivedNull\n正文。\n",
        encoding="utf-8",
    )
    scan = collect_json(vault)
    rows = {r["node_id"]: r for r in scan["ledger"]["seeds"] + scan["ledger"]["derived"]}
    assert rows["DerivedNull"]["source_note"] is None, "null 字面量被算成 source_note"
    assert rows["DerivedNull"]["relation_target"] is None
    assert rows["DerivedNull"]["role"] == "seed", "null 派生键被当派生痕迹（与后端分叉）"
    # 全板无派生角色成员 → 无来源结论如实无据（零编造）
    uns = scan["signals"]["unsourced_conclusions"]
    assert (uns["value"], uns["denominator"]) == (None, 0)
    assert uns["availability"] == "无据"


def test_unsourced_nodata_when_no_derived(tmp_path):
    vault = build_vault(tmp_path, ["SeedA"])
    write_node(vault, "SeedA")
    uns = collect_json(vault)["signals"]["unsourced_conclusions"]
    assert uns["value"] is None
    assert uns["denominator"] == 0
    assert uns["availability"] == "无据"


def test_empty_board_all_signals_nodata(tmp_path):
    vault = build_vault(tmp_path, [])
    sig = collect_json(vault)["signals"]
    for key in SIGNAL_KEYS:
        assert sig[key]["value"] is None, key
        assert sig[key]["availability"] == "无据", key


# ────────────────────────── 信号4 · 重复堆积 ──────────────────────────


def test_duplicate_accumulation_normalized_groups(tmp_path):
    scan = collect_json(standard_vault(tmp_path))
    dup = scan["signals"]["duplicate_accumulation"]
    # "What is X" / "what   is x" / "What is X" 归一同组 (3 条) → 冗余 2
    assert dup["value"] == 2
    assert dup["denominator"] == 4
    assert dup["percentile_ref"] == {
        "p50_group_size": 3,
        "max_group_size": 3,
        "group_count": 1,
    }
    assert dup["groups"][0]["count"] == 3
    assert dup["availability"] == "文件"


def test_duplicate_zero_with_unique_tips_is_measured_zero(tmp_path):
    vault = build_vault(tmp_path, ["SeedA"])
    write_node(vault, "SeedA", tips=[{"text": "q1"}, {"text": "q2"}])
    dup = collect_json(vault)["signals"]["duplicate_accumulation"]
    assert dup["value"] == 0  # 实测得 0, 不是无据
    assert dup["denominator"] == 2
    assert dup["percentile_ref"] is None
    assert dup["availability"] == "文件"


def test_duplicate_nodata_when_no_tips(tmp_path):
    vault = build_vault(tmp_path, ["SeedA"])
    write_node(vault, "SeedA")
    dup = collect_json(vault)["signals"]["duplicate_accumulation"]
    assert dup["value"] is None
    assert dup["availability"] == "无据"


# ────────────────────────── 零写侧 ──────────────────────────


def test_collect_readonly_no_write_side(tmp_path):
    vault = standard_vault(tmp_path)
    before = vault_snapshot(vault)
    collect_json(vault)
    assert vault_snapshot(vault) == before, "collect 运行改动了 vault 文件"


# ────────────────────────── (c)(d) --verify 信号绑定 ──────────────────────────


def signal_lines(sig: dict) -> str:
    lines = []
    a = sig["unanswered_question_age"]
    if a["availability"] == "无据":
        lines.append("> - 未答问题年龄：无据（无带时间戳批注）")
    else:
        pr = a["percentile_ref"]
        lines.append(
            f"> - 未答问题年龄：最老 {a['value']} 天（参与统计 {a['denominator']} 条，"
            f"p25/p50/p75 = {pr['p25_days']}/{pr['p50_days']}/{pr['p75_days']} 天）【{a['availability']}】"
        )
    for key, label, tail in (
        ("source_coverage", "来源覆盖率", "成员含来源锚点"),
        ("unsourced_conclusions", "无来源结论", "派生角色成员缺来源锚点"),
        ("duplicate_accumulation", "重复堆积", "条批注为重复条目"),
    ):
        s = sig[key]
        if s["availability"] == "无据":
            lines.append(f"> - {label}：无据（分母为零）")
        else:
            lines.append(f"> - {label}：{s['value']}/{s['denominator']} {tail}【{s['availability']}】")
    return "\n".join(lines)


def render_report(scan: dict) -> str:
    """按 SKILL.md Step 5 模板渲染最小合规报告 (两模式通用)。"""
    c = scan["counts"]
    fallback = scan["data_mode"] == "fallback_local"
    sha = scan["source_revision"]["board_sha256"]
    header_mode = "⚠ FALLBACK 本地扫描" if fallback else "manifest（1 次调用）"
    fresh = (
        "**⚠ FALLBACK：manifest 不可用（未提供 --manifest），本报告基于本地只读扫描，role/掌握度均为推定**\n"
        if fallback
        else ""
    )
    recon_tail = (
        "- 待定纠错候选 0 条 · 孤儿/双源差集/检验历史：无据（fallback）"
        if fallback
        else "- 待定纠错候选 0 条 · 孤儿 0 · 双源差集 无 · 检验历史 0 板"
    )
    # ⛔ 维护卡 B: 这里原本**硬编码** `- SeedA — 批注 2 条`，不随 scan 变——
    # 在 standard_vault 下恰好等于真值所以一直没露馅，在空 tips 板上就是一条
    # 「形状合法、数字无据」的行。新增的种子行绑值门第一次跑就把它抓了出来
    # （这正是本卡要的效果：形状对不等于数字有据）。改为按 scan 的 ledger 渲染。
    ledger_seed = "\n".join(
        f"- {r['node_id']} — " + (f"批注 {r['tips_count']} 条" if r.get("tips_count") else "无批注")
        for r in (scan.get("ledger") or {}).get("seeds", [])
    )
    ledger_derived = "- DerivedB — 占位 · mastery 未记录 · tips 未闭环 2 条\n- DerivedC — 已剖析 · mastery 未记录"
    return f"""---
type: recap
board: "{scan["board_stem"]}"
board_name: "{scan["board_name"]}"
recap_date: {scan["recap_date"]}
data_mode: {scan["data_mode"]}
board_sha256: "{sha}"
generated_by: board-recap v1.1-signals
---

# 回顾 · {scan["board_name"]} · {scan["recap_date"]}

> [!info]+ 规模自陈
> {c["members"]} 成员（{c["seeds"]} 种子 + {c["derived"]} 派生，{c["stubs"]} 占位）/ {c["annotations"]} 批注 /
> 数据面：{header_mode} / 无截断

## 数据来源与新鲜度
{fresh}- 板文件 SHA-256：`{sha[:12]}…` · 板文件 mtime：{scan["source_revision"]["board_mtime_utc"]}
- manifest：无
- 扫描时刻：{scan["source_revision"]["scan_at_utc"]}

## 本段新增（上次回顾 → 现在）
首次回顾，无对照基线。

## 你现在可以做的
1. 板上批注 {c["tips_total"]} 条【文件】——再跑一次 /board-recap {scan["board_stem"]}（数据更新后复盘）

## 台账（种子/派生）
### 种子
{ledger_seed}
### 派生
{ledger_derived}

## AI 侧对账
- tips 批注共 {c["tips_total"]} 条【未确认-无法判定已答】，其中理解度未闭环 {c["tips_understanding_open"]} 条
- 最老 3 条原话（added_at = 最后变更时间，非首次批注）：略
{recon_tail}

## 三维审查
### ① 有没有漏掉的
批注为零的成员共 1 个。
### ② 靠不靠谱
数据为本地文件抄录，角色为推定档。
### ③ 方向（与推定基准的距离，仅供参考）
{signal_lines(scan["signals"])}

方向叙述：来源锚点缺失集中在派生角色成员，关联声明以既有数据为准。
"""


def write_report(vault: Path, scan: dict) -> Path:
    outputs = vault / "outputs"
    (outputs / f".recap-scan-{BOARD}.json").write_text(json.dumps(scan, ensure_ascii=False), encoding="utf-8")
    report = outputs / f"回顾-{BOARD}-{scan['recap_date']}.md"
    report.write_text(render_report(scan), encoding="utf-8")
    return report


def test_verify_pass_fallback_wording_survives(tmp_path):
    """(c) fallback 全量报告 (含信号行) 过自家 verifier — 派生词禁令/「偏离」禁词零命中。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert scan["data_mode"] == "fallback_local"
    report = write_report(vault, scan)
    r = run_verify(report)
    assert r.returncode == 0, f"fallback 报告未过 verifier:\n{r.stdout}"
    assert "VERIFY PASS" in r.stdout


def test_verify_pass_manifest_wording(tmp_path):
    """(c) manifest 模式同款措辞同样通杀。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault, "--manifest", str(make_manifest(vault)))
    assert scan["data_mode"] == "manifest"
    report = write_report(vault, scan)
    r = run_verify(report)
    assert r.returncode == 0, f"manifest 报告未过 verifier:\n{r.stdout}"


@pytest.mark.parametrize(
    "label",
    ["未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"],
)
def test_verify_tamper_signal_number_fails(tmp_path, label):
    """(d) 篡改任一信号数字 → exit 1。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if label in ln)
    m = re.search(r"\d+", line)
    tampered = line[: m.start()] + str(int(m.group(0)) + 7) + line[m.end() :]
    report.write_text(text.replace(line, tampered), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"篡改 {label} 数字未被拦截:\n{r.stdout}"
    assert "数字终核" in r.stdout


def test_verify_missing_signal_line_fails(tmp_path):
    """(d) scan JSON 含 signals 而报告缺信号行 → exit 1 (fail-closed)。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    text = "\n".join(ln for ln in text.splitlines() if "重复堆积" not in ln)
    report.write_text(text, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "缺信号行 重复堆积" in r.stdout


def test_verify_availability_tag_tamper_fails(tmp_path):
    """(d) 档位造假 (推定 → 实测) → exit 1。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "无来源结论" in ln)
    report.write_text(text.replace(line, line.replace("【推定】", "【实测】")), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "未整行匹配标准式" in r.stdout


def test_verify_nodata_mismatch_fails_both_ways(tmp_path):
    """(d) 无据错标双向拦截: 有数报无据 / 无据硬给数。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    # 有数 → 报无据 (隐瞒)
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "来源覆盖率" in ln)
    report.write_text(text.replace(line, "> - 来源覆盖率：无据（数据被隐瞒）"), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "报告行却标了无据" in r.stdout
    # 无据 → 硬给数 (编造): 改 scan JSON 让年龄无据, 报告保留数字行
    scan2 = json.loads(json.dumps(scan))
    scan2["signals"]["unanswered_question_age"].update(
        {
            "value": None,
            "denominator": 0,
            "percentile_ref": None,
            "availability": "无据",
        }
    )
    (vault / "outputs" / f".recap-scan-{BOARD}.json").write_text(
        json.dumps(scan2, ensure_ascii=False), encoding="utf-8"
    )
    report.write_text(render_report(scan), encoding="utf-8")  # 报告仍带数字行
    r2 = run_verify(report)
    assert r2.returncode == 1
    assert "无据行未整行匹配标准式" in r2.stdout


def test_verify_nodata_lines_pass(tmp_path):
    """无据信号如实写「无据」→ PASS (空 tips 板)。"""
    vault = build_vault(tmp_path, ["SeedA", "DerivedB"])
    write_node(vault, "SeedA")
    write_node(vault, "DerivedB", derived_from="[[SeedA]]")
    scan = collect_json(vault)
    assert scan["signals"]["unanswered_question_age"]["availability"] == "无据"
    report = write_report(vault, scan)
    r = run_verify(report)
    assert r.returncode == 0, r.stdout


def test_verify_old_scan_json_without_signals_compat(tmp_path):
    """(d) 旧 scan JSON (无 signals 键) + 无信号行报告 → 兼容 PASS。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    old_scan = {k: v for k, v in scan.items() if k != "signals"}
    (vault / "outputs" / f".recap-scan-{BOARD}.json").write_text(
        json.dumps(old_scan, ensure_ascii=False), encoding="utf-8"
    )
    text = render_report(scan)
    # 剔除信号行 (旧版报告形态)
    text = "\n".join(
        ln
        for ln in text.splitlines()
        if not any(
            w in ln
            for w in (
                "未答问题年龄",
                "来源覆盖率",
                "无来源结论",
                "重复堆积",
                "一梯队信号",
            )
        )
    )
    report = vault / "outputs" / f"回顾-{BOARD}-{scan['recap_date']}.md"
    report.write_text(text, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 0, f"旧 scan JSON 兼容性破坏:\n{r.stdout}"


def test_verify_unclosed_html_comment_fails(tmp_path):
    """F2 回归锁 (Codex round-1 复现): 信号行前插未闭合 <!-- — 渲染视图会
    隐藏其后内容而正则校验照常看见 → 必须 FAIL 而非 PASS。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    report.write_text(
        text.replace("> - 未答问题年龄：", "<!--\n> - 未答问题年龄：", 1),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode == 1, "未闭合 HTML 注释未被拦截 (渲染隐藏面)"
    # ⚠️ 维护卡 B：拦截行为不变（仍 exit 1），但**理由合并了**。
    # 原实现「先剥闭合注释、再查残留 `<!--`」有个致命顺序问题：两个标记都被剥掉后
    # 那道残留检查恒不触发，于是把标记包成 code span 就能让整段正文对**全部**检查隐身
    # （实测连 HARD-R4 禁词都能这样藏进去并 VERIFY PASS）。改为在**原始文本**上
    # 一次判死：闭合与否、是否在代码跨度内，一律算「正文含 HTML 注释标记」。
    assert "HTML 注释标记" in r.stdout


def test_verify_nodata_line_with_numbers_fails(tmp_path):
    """F3 回归锁: 无据信号行夹带编造的 X/N 计数 → FAIL (无据不出数)。"""
    vault = build_vault(tmp_path, ["SeedA", "DerivedB"])
    write_node(vault, "SeedA")
    write_node(vault, "DerivedB", derived_from="[[SeedA]]")
    scan = collect_json(vault)
    assert scan["signals"]["duplicate_accumulation"]["availability"] == "无据"
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "重复堆积" in ln)
    report.write_text(
        text.replace(line, "> - 重复堆积：3/7 条批注为重复条目（无据）"),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode == 1
    assert "无据行未整行匹配标准式" in r.stdout


@pytest.mark.parametrize(
    "bogus",
    [
        "> - 重复堆积：无据（最老 999 天）",  # 数字在括号里
        "> - 重复堆积：无据（共有 99 条）",
        "> - 重复堆积：无据（3／7 条）",  # 全角斜线
        "> - 重复堆积：无据（约七十七条）",  # 中文数字
        "> - 重复堆积：无据（共有两条）",  # round-3 H2: 表量字「两」
        "> - 重复堆积：无据（俩条）",
        "> - 重复堆积：无据（共有壹条）",  # round-4 H2: 大写汉字数字
        "> - 重复堆积：无据（共有٩条）",  # Arabic-Indic
        "> - 重复堆积：无据（共有⁹条）",  # 上标
        "> - 重复堆积：无据（共有Ⅶ条）",  # 罗马数字 (Nl)
        "> - 重复堆积：无据（共有½条）",  # 分数 (No)
    ],
)
def test_verify_nodata_line_number_variants_fail(tmp_path, bogus):
    """H2 回归锁 (Codex round-2): 无据行夹带数字的四种变体全部 FAIL —
    原先只拦 ASCII X/N 与完整年龄式，括号数字/全角斜线/中文数字可绕过。"""
    vault = build_vault(tmp_path, ["SeedA", "DerivedB"])
    write_node(vault, "SeedA")
    write_node(vault, "DerivedB", derived_from="[[SeedA]]")
    scan = collect_json(vault)
    assert scan["signals"]["duplicate_accumulation"]["availability"] == "无据"
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "重复堆积" in ln)
    report.write_text(text.replace(line, bogus), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"无据行变体未被拦: {bogus}"
    assert "无据行未整行匹配标准式" in r.stdout


def test_verify_merged_signal_line_fails(tmp_path):
    """H3 回归锁 (Codex round-2): 四信号合并成一行 → 档位可互相借用，
    必须 FAIL（每信号独占一行）。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    lines = text.splitlines()
    sig_lines = [ln for ln in lines if any(lb in ln for lb in ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"))]
    merged = "> " + " · ".join(ln.lstrip("> -").strip() for ln in sig_lines)
    out = [ln for ln in lines if ln not in sig_lines]
    idx = out.index(next(ln for ln in out if ln.startswith("### ③"))) + 1
    out.insert(idx, merged)
    report.write_text("\n".join(out), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "合并信号行未被拦"
    assert "独占一行" in r.stdout


def test_verify_signal_lines_outside_section3_fail(tmp_path):
    """M3 回归锁 (Codex round-2): 信号行搬到 ③ 段之后的 ## 段里 →
    ③ 段抽取必须止于下一个 ##，判缺行 FAIL。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    sig_lines = [ln for ln in lines if any(lb in ln for lb in ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"))]
    out = [ln for ln in lines if ln not in sig_lines]
    out += ["", "## 附录", ""] + sig_lines
    report.write_text("\n".join(out), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "③ 段外的信号行被当成段内"
    assert "缺信号行" in r.stdout


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda s: {"availability": "无据"}, id="仅剩availability"),
        pytest.param(lambda s: {**s, "availability": "神谕"}, id="availability非法枚举"),
        pytest.param(lambda s: {**s, "availability": "无据"}, id="标无据却带数值"),
        pytest.param(
            lambda s: {k: v for k, v in s.items() if k != "denominator"},
            id="缺denominator",
        ),
    ],
)
def test_verify_signal_subobject_schema_fail_closed(tmp_path, mutate):
    """M2 回归锁 (Codex round-2): signals 子对象 schema 不合契约 → FAIL
    （顶层是 dict 不足以放行——削成 {"availability":"无据"} 曾能蒙混）。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    bad = json.loads(json.dumps(scan))
    bad["signals"]["source_coverage"] = mutate(bad["signals"]["source_coverage"])
    (vault / "outputs" / f".recap-scan-{BOARD}.json").write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    report = vault / "outputs" / f"回顾-{BOARD}-{scan['recap_date']}.md"
    report.write_text(render_report(scan), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "子对象 schema 违规未被拦"
    assert "数字终核" in r.stdout


def test_verify_trailing_second_number_group_fails(tmp_path):
    """H3 回归锁 (round-3): 正确数字之后追加第二组错误数字与档位 →
    整行严格模板匹配必须 FAIL（原先只查首个匹配 + 档位"出现过"）。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "来源覆盖率" in ln)
    report.write_text(text.replace(line, line + " 99/99【实测】"), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "行尾追加的第二组数字未被拦"
    assert "未整行匹配标准式" in r.stdout


def test_verify_trailing_number_in_tail_text_fails(tmp_path):
    """round-4 回归锁: 有数信号行的尾部说明段禁数字——
    「2/3 成员含来源锚点 99/99」曾被 `[^【】]*` 通配放行。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "来源覆盖率" in ln)
    tampered = line.replace("【文件】", "99/99【文件】")
    report.write_text(text.replace(line, tampered), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "尾部说明段的第二组数字未被拦"
    # ⛔ 维护卡 B · H-3: 拦截行为不变（仍 exit 1），但**失败理由变了**——
    # 尾部从「先开放再排除」（黑名单：禁数值字符/禁 X/N 形态）改成正向允许式
    # （只许标准尾部文案 + 锚 `$`），于是这类夹带在整行 fullmatch 处就被拒，
    # 不再走那条已删除的字符表分支。断言随之改锚新理由。
    assert "未整行匹配标准式" in r.stdout


@pytest.mark.parametrize(
    "tail",
    ["九九/九九", "٩٩/٩٩", "⁹⁹/⁹⁹", "另有壹处"],
)
def test_verify_trailing_unicode_numerals_fail(tmp_path, tail):
    """round-4 H3 回归锁: 尾部说明段夹带**任意语系**数字都拦
    （字符黑名单曾放行汉字/Arabic-Indic/上标）。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "来源覆盖率" in ln)
    report.write_text(
        text.replace(line, line.replace("【文件】", f"{tail}【文件】")),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode == 1, f"尾部 {tail} 未被拦"
    # ⛔ 维护卡 B · H-3: 拦截行为不变（仍 exit 1），但**失败理由变了**——
    # 尾部从「先开放再排除」（黑名单：禁数值字符/禁 X/N 形态）改成正向允许式
    # （只许标准尾部文案 + 锚 `$`），于是这类夹带在整行 fullmatch 处就被拒，
    # 不再走那条已删除的字符表分支。断言随之改锚新理由。
    assert "未整行匹配标准式" in r.stdout


@pytest.mark.parametrize(
    "bogus_line",
    [
        "- SeedA — 批注 2 条，后代节点数量为零。",  # round-4 H4: 换词绕过
        "- SeedA — 批注 2 条（尚未长出下一层）",
        "SeedA 这个种子还很空。",
    ],
)
def test_verify_seed_section_template_whitelist(tmp_path, bogus_line):
    """round-4 H4 回归锁: 种子段改**整行模板白名单** —— 任何模板外的行
    （无论用什么词说派生）一律 FAIL，同义改写竞赛结构性终结。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    report.write_text(text.replace("- SeedA — 批注 2 条", bogus_line), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"模板外的种子行未被拦: {bogus_line}"
    assert "存在模板外的行" in r.stdout


@pytest.mark.parametrize("heading", ["##", "##\t附录", "## 附录"])
def test_verify_section3_boundary_variants(tmp_path, heading):
    """round-4 M3 回归锁: 空标题 `##` 与 tab 标题同样终止 ③ 段。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    sig = [ln for ln in lines if any(lb in ln for lb in ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"))]
    out = [ln for ln in lines if ln not in sig] + ["", heading, ""] + sig
    report.write_text("\n".join(out), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"标题 {heading!r} 未终止 ③ 段"
    assert "缺信号行" in r.stdout


def test_verify_signal_lines_in_code_block_fail(tmp_path):
    """round-4 M3 回归锁: 信号行藏在 fenced/缩进代码块里不算数
    （代码块渲染为字面文本，与报告陈述分叉）。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    sig = [ln for ln in lines if any(lb in ln for lb in ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"))]
    idx = lines.index(sig[0])
    out = lines[:idx] + ["```"] + sig + ["```"] + lines[idx + len(sig) :]
    report.write_text("\n".join(out), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "代码块里的信号行被当成有效信号行"
    assert "缺信号行" in r.stdout


def test_verify_percentile_ref_null_rejected(tmp_path):
    """round-4 回归锁: 年龄信号有数档但 percentile_ref 为 null →
    schema fail-closed（原先报告写 None/None/None 也能通过）。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    bad = json.loads(json.dumps(scan))
    bad["signals"]["unanswered_question_age"]["percentile_ref"] = None
    (vault / "outputs" / f".recap-scan-{BOARD}.json").write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    report = vault / "outputs" / f"回顾-{BOARD}-{scan['recap_date']}.md"
    report.write_text(render_report(scan), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "percentile_ref" in r.stdout


@pytest.mark.parametrize(
    "falsy",
    ["false", "0", '""', "{}", "[]", "Null"],
)
def test_falsy_derived_from_matches_backend(tmp_path, falsy):
    """round-4 H1 回归锁: YAML falsy 全集（不只 null/~）都按后端语义判 seed。"""
    from app.services.board_manifest_service import _node_role
    import yaml

    vault = build_vault(tmp_path, ["N"])
    fm_text = f'type: concept\nsource_board: "[[原白板/{BOARD}]]"\nderived-from: {falsy}\n'
    (vault / "节点" / "N.md").write_text(f"---\n{fm_text}---\n# N\n正文。\n", encoding="utf-8")
    scan = collect_json(vault)
    rows = {r["node_id"]: r for r in scan["ledger"]["seeds"] + scan["ledger"]["derived"]}
    backend_role = _node_role(yaml.safe_load(fm_text))
    assert rows["N"]["role"] == backend_role, (
        f"derived-from: {falsy} → fallback={rows['N']['role']} ≠ 后端={backend_role}"
    )


@pytest.mark.parametrize(
    "bogus",
    [
        "> - 重复堆积：无据（共有仨条）",  # round-5: 罕见汉字数字
        "> - 重复堆积：无据（共有皕条）",
        "> - 重复堆积：无据（共有零条）",  # 「零」不在数字黑名单里
        "> - 重复堆积：无据（我编的原因）",  # 白名单外的自由文案
        "> - 重复堆积：无据",  # 缺括号原因
    ],
)
def test_verify_nodata_reason_whitelist(tmp_path, bogus):
    """round-5 H2 结构性终结回归锁: 无据行改**整行固定模板白名单** ——
    原因只能取自 _NODATA_REASONS，任何自由文案（含罕见汉字数字）一律 FAIL。"""
    vault = build_vault(tmp_path, ["SeedA", "DerivedB"])
    write_node(vault, "SeedA")
    write_node(vault, "DerivedB", derived_from="[[SeedA]]")
    scan = collect_json(vault)
    assert scan["signals"]["duplicate_accumulation"]["availability"] == "无据"
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "重复堆积" in ln)
    report.write_text(text.replace(line, bogus), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"无据行变体未被拦: {bogus}"
    assert "无据行未整行匹配标准式" in r.stdout


@pytest.mark.parametrize("tail", ["仨/仨", "皕/皕", "零/零"])
def test_verify_trailing_slash_pair_fails(tmp_path, tail):
    """round-5 H3 回归锁: 尾部的 X/N **结构**本身即第二组计数，
    即便用黑名单外的字符（仨/皕/零）也拦。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "来源覆盖率" in ln)
    report.write_text(
        text.replace(line, line.replace("【文件】", f"{tail}【文件】")),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode == 1, f"尾部 {tail} 未被拦"
    # ⛔ 维护卡 B · H-3: 拦截行为不变（仍 exit 1），但**失败理由变了**——
    # 尾部从「先开放再排除」（黑名单：禁数值字符/禁 X/N 形态）改成正向允许式
    # （只许标准尾部文案 + 锚 `$`），于是这类夹带在整行 fullmatch 处就被拒，
    # 不再走那条已删除的字符表分支。断言随之改锚新理由。
    assert "未整行匹配标准式" in r.stdout


@pytest.mark.parametrize(
    "where,bogus",
    [
        (
            "### 派生",
            "- DerivedB — 占位 · mastery 未记录 · tips 未闭环 2 条，它没有派生出东西。",
        ),
        ("### ① 有没有漏掉的", "批注为零的成员共 1 个。SeedA 一个派生也没有。"),
    ],
)
def test_verify_derivation_assertion_outside_seed_section(tmp_path, where, bogus):
    """round-5 H4 回归锁: 派生断言写在种子段**之外**（派生段/①段）同样 FAIL ——
    全局『派生』行白名单，不再靠段内规则。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert scan["data_mode"] == "fallback_local"
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith(where))
    lines.insert(idx + 1, bogus)
    report.write_text("\n".join(lines), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"{where} 内的派生断言未被拦"
    assert "模板外的『派生』表述" in r.stdout


def test_verify_blockquote_fence_hides_nothing(tmp_path):
    """round-5 M3 回归锁: 引用块内的围栏（`> ```）同样识别为代码块，
    藏在里面的信号行等同缺行。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    sig = [ln for ln in lines if any(lb in ln for lb in ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"))]
    idx = lines.index(sig[0])
    out = lines[:idx] + ["> ```"] + sig + ["> ```"] + lines[idx + len(sig) :]
    report.write_text("\n".join(out), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "引用块内围栏未被识别"
    assert "缺信号行" in r.stdout


def test_verify_legitimate_nested_list_not_stripped(tmp_path):
    """round-5 误伤回归锁: 合法的四空格缩进三级列表**不得**被当代码块删除
    （曾导致「③段缺信号行」误报）。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith("### ① "))
    lines[idx + 1 : idx + 1] = [
        "- 一级列表",
        "  - 二级列表",
        "    - 三级列表（四空格缩进，合法 Markdown）",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 0, f"合法嵌套列表被误判:\n{r.stdout}"


def test_verify_zero_width_chars_fail(tmp_path):
    """round-4 回归锁: 零宽/双向控制字符（渲染不可见但改变匹配与阅读顺序）
    一律 FAIL。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    report.write_text(text.replace("## 三维审查", "##​ 三维审查"), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "零宽" in r.stdout


@pytest.mark.parametrize(
    "rel_block,expect_derived",
    [
        ("relationships:\n", False),  # 空值 → 后端 falsy → seed
        ("relationships: null\n", False),
        ("relationships: []\n", False),
        ('relationships:\n  - type: extends\n    target: "[[节点/S]]"\n', True),
    ],
)
def test_relationships_truthiness_matches_backend(tmp_path, rel_block, expect_derived):
    """round-4 回归锁: relationships 也走 truthiness（键存在不等于有内容）——
    与后端 _node_role 逐形态对拍。"""
    from app.services.board_manifest_service import _node_role
    import yaml

    vault = build_vault(tmp_path, ["N"])
    fm_text = f'type: concept\nsource_board: "[[原白板/{BOARD}]]"\n{rel_block}'
    (vault / "节点" / "N.md").write_text(f"---\n{fm_text}---\n# N\n正文。\n", encoding="utf-8")
    scan = collect_json(vault)
    rows = {r["node_id"]: r for r in scan["ledger"]["seeds"] + scan["ledger"]["derived"]}
    backend_role = _node_role(yaml.safe_load(fm_text))
    assert backend_role == ("derived" if expect_derived else "seed")
    assert rows["N"]["role"] == backend_role, (
        f"relationships 形态 {rel_block!r}: fallback={rows['N']['role']} ≠ 后端={backend_role}"
    )


def test_verify_tab_heading_section3_boundary(tmp_path):
    """M3 回归锁 (round-3): `##\\t附录`（tab 分隔的合法 Markdown 标题）同样
    终止 ③ 段——信号行搬到其后即判缺行。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    sig_lines = [ln for ln in lines if any(lb in ln for lb in ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"))]
    out = [ln for ln in lines if ln not in sig_lines] + ["", "##\t附录", ""] + sig_lines
    report.write_text("\n".join(out), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "tab 标题未终止 ③ 段"
    assert "缺信号行" in r.stdout


def test_verify_bool_value_rejected(tmp_path):
    """M2 回归锁 (round-3): JSON true 是 Python bool（int 子类），
    配报告 "1/N" 曾整条通过 → 必须 FAIL。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    bad = json.loads(json.dumps(scan))
    bad["signals"]["source_coverage"]["value"] = True
    (vault / "outputs" / f".recap-scan-{BOARD}.json").write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    report = vault / "outputs" / f"回顾-{BOARD}-{scan['recap_date']}.md"
    report.write_text(render_report(scan), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "非整数" in r.stdout


def test_verify_fallback_seed_section_derivation_words_fail(tmp_path):
    """H4 回归锁 (round-3 结构化): fallback 台账「种子」小节出现任何「派生」
    表述即 FAIL——同义句改写（「派生数量为零」）不再能绕过词表。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert scan["data_mode"] == "fallback_local"
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    report.write_text(
        text.replace("- SeedA — 批注 2 条", "- SeedA — 批注 2 条，派生数量为零。"),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode == 1, "种子段的派生同义断言未被拦"
    assert "存在模板外的行" in r.stdout


def test_verify_fallback_no_derivation_synonym_fails(tmp_path):
    """H4 回归锁 (Codex round-2): fallback 报告写「无派生」= 无据断言，
    必须 0 命中（派生子女在 fallback 恒无据）。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert scan["data_mode"] == "fallback_local"
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    report.write_text(
        text.replace("- SeedA — 批注 2 条", "- SeedA — 批注 2 条，无派生。"),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode == 1
    # round-6: 「无派生」已从子串词表移除（它是白名单无据文案的真子串），
    # 改由「含派生的行必须整行匹配白名单」这条结构规则拦截
    assert "模板外的『派生』表述" in r.stdout


def test_verify_signals_key_wrong_shape_fails(tmp_path):
    """F5 回归锁: scan JSON 的 signals 键存在但非对象 → fail-closed
    (不得静默跳过绑定); 键完全缺失才走兼容路径。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    bad = json.loads(json.dumps(scan))
    bad["signals"] = []
    (vault / "outputs" / f".recap-scan-{BOARD}.json").write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    report = vault / "outputs" / f"回顾-{BOARD}-{scan['recap_date']}.md"
    report.write_text(render_report(scan), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "形状损坏" in r.stdout


# ────────────────── round-6 终裁复核 (BLOCKER + HIGH) ──────────────────


@pytest.mark.parametrize(
    "suffix",
    ["x", ".", "：", " ·", " 本轮"],  # ⛔ 「（本轮）」是设计内合法补充，不在此列
)
def test_verify_section_heading_suffix_cannot_disable_bindings(tmp_path, suffix):
    """round-6 BLOCKER 回归锁（终裁复核实测）: 给 `## AI 侧对账` 加任意后缀
    曾让 _verify_numbers 提前 return → tips 绑定与**整块 signals 绑定**全部
    跳过（信号行可整体删除仍 PASS）。根因是段落存在性检查用前缀匹配、
    下游定位用整行正则，两者不一致。现在必须 FAIL。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    # 改标题 + 删光四条信号行 + 篡改 tips 两数
    text = text.replace("## AI 侧对账", f"## AI 侧对账{suffix}")
    text = "\n".join(
        ln
        for ln in text.splitlines()
        if not any(lb in ln for lb in ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积"))
    )
    text = re.sub(r"tips 批注共 \d+ 条", "tips 批注共 999 条", text)
    report.write_text(text, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"标题后缀 {suffix!r} 关闭了全部数字绑定"
    # 必须同时报出「段落标题不精确」与「信号行缺失」——证明绑定没被跳过
    assert "AI 侧对账" in r.stdout
    assert "缺信号行" in r.stdout, "signals 绑定被跳过了"


def test_verify_actions_heading_suffix_still_checked(tmp_path):
    """round-6 同源回归锁: `## 你现在可以做的` 加后缀同样不得逃逸
    （动作段白名单曾因整行正则匹配不上而整体跳过）。"""
    vault = standard_vault(tmp_path)
    report = write_report(vault, collect_json(vault))
    text = report.read_text(encoding="utf-8")
    text = text.replace("## 你现在可以做的", "## 你现在可以做的 本轮")
    report.write_text(text, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1
    assert "你现在可以做的" in r.stdout


def test_verify_scale_decoy_line_rejected(tmp_path):
    """round-6 HIGH 回归锁（终裁复核实测）: 规模自陈五元组曾用 re.search 取
    **首个**匹配 → 在更早处放一行带真数字的诱饵，可见 callout 就能写假数字。
    现在全文所有五元组逐条校验且必须恰好一条。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    c = scan["counts"]
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    honest = (
        f"{c['members']} 成员（{c['seeds']} 种子 + {c['derived']} 派生，{c['stubs']} 占位）/ {c['annotations']} 批注"
    )
    lie = "120 成员（80 种子 + 40 派生，0 占位）/ 350 批注"
    # 诱饵放在标题后（更早），可见 callout 改成假数字
    lines = text.splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith("# 回顾"))
    lines.insert(idx + 1, f"本轮基线：{honest}。")
    text = "\n".join(lines).replace(honest, lie, 1) if False else "\n".join(lines)
    text = text.replace(f"> {honest} /", f"> {lie} /")
    report.write_text(text, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, "诱饵行让假的规模自陈通过了"
    assert "规模自陈" in r.stdout


# ══════════════════ CARD-M11M7 · M7 板名/节点名字符拒绝集 ══════════════════
# unsafe_name_chars() 是 _contained_md 的字符判据（一处判定），拒绝集从 C0 扩到
# DEL + C1 + 行分隔符。⛔ 边界最容易写错（<0x20 / <=0x9F 任一端 off-by-one 都会
# 让实现悄悄放行或误伤），所以这里逐个边界字符正反双向锁。


def _load_recap_scan():
    """按被测脚本自身的零写侧约定导入它（不落 __pycache__）。"""
    import importlib.util

    if not SCRIPT.exists():
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("recap_scan_ut", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    return mod


@pytest.mark.parametrize(
    "ch,expected,why",
    [
        ("\x1f", True, "U+001F 是 C0 末位 — 原判据 ord<0x20 的上边界内"),
        (" ", False, "U+0020 空格 — 边界外, 合法板名常有"),
        ("~", False, "U+007E — DEL 的前一位, 必须放行"),
        ("\x7f", True, "U+007F DEL — 实测致 PyYAML ReaderError"),
        ("\x80", True, "U+0080 — C1 首位"),
        ("\x85", True, "U+0085 NEL — 实测致 exam_history.board_id=null"),
        ("\x9f", True, "U+009F — C1 末位"),
        ("\xa0", False, "U+00A0 NBSP — C1 的后一位, 是合法可打印空白必须放行"),
        ("\u2028", True, "U+2028 行分隔符 — splitlines 会在此断行"),
        ("\u2029", True, "U+2029 段分隔符"),
        ("\u200b", False, "U+200B 零宽空格 — 不属本判据（verifier 另有正文零宽检查）"),
        ("中", False, "CJK"),
        ("①", False, "带圈数字"),
        ("é", False, "带音标拉丁字母"),
        ("🎯", False, "emoji（星平面字符）"),
    ],
    ids=lambda v: None,
)
def test_m7_unsafe_name_chars_boundaries(ch, expected, why):
    """拒绝集的正反双向边界锁 — 每个「拒」的紧邻位都配了一个「放」。"""
    rs = _load_recap_scan()
    got = bool(rs.unsafe_name_chars(f"板{ch}名"))
    assert got is expected, f"{why}: 期望{'拒绝' if expected else '放行'}, 实际{'拒绝' if got else '放行'}"


def test_m7_unsafe_name_chars_reports_all_codepoints_deduped():
    """诊断面: 返回全部命中码位、去重保序（拒绝原因要能点名到具体字符）。"""
    rs = _load_recap_scan()
    assert rs.unsafe_name_chars("干净的板名") == []
    assert rs.unsafe_name_chars("板\x85名\x7f尾\x85") == ["U+0085", "U+007F"]


def test_m7_containment_rejects_control_char_names(tmp_path):
    """_contained_md 侧: 控制字符名一律拒绝，且**不因文件真实存在而放行**。"""
    rs = _load_recap_scan()
    base = tmp_path / "原白板"
    base.mkdir(parents=True)
    for stem in ("板\x7f甲", "板\x85乙", "板\u2028丙"):
        (base / f"{stem}.md").write_text("x", encoding="utf-8")  # 文件真实存在
        assert rs._contained_md(base, stem) is None, f"控制字符名被放行: {stem!r}"
    ok = "板一"
    (base / f"{ok}.md").write_text("x", encoding="utf-8")
    assert rs._contained_md(base, ok) == base / f"{ok}.md", "合法板名被误拒"


def test_m7_collect_refuses_control_char_board(tmp_path):
    """CLI 级: collect 对控制字符板名走 containment 拒绝分支（exit 0 + board_exists false）。"""
    vault = build_vault(tmp_path, ["SeedA"])
    bad = f"{BOARD}\x85尾"
    (vault / "原白板" / f"{bad}.md").write_text(
        f"---\ntype: whiteboard\n---\n\n# {bad}\n\n## Concepts\n\n- [[节点/SeedA]]\n",
        encoding="utf-8",
    )
    r = run_collect(vault, bad)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["board_exists"] is False, f"控制字符板名被当成正常板扫描: {out.get('board_stem')!r}"
    assert "containment" in out["refusal_reason"], out["refusal_reason"]
    # Codex round-1 LOW: 原文案一律说"路径分隔符/父目录引用或越界" —— 对控制字符
    # 板名而言那句话是**错的**，用户按它去查路径永远查不出问题。必须点名码位。
    assert "U+0085" in out["refusal_reason"], f"字符类拒绝被误述为路径问题: {out['refusal_reason']!r}"
    assert "路径分隔符" not in out["refusal_reason"], f"字符类拒绝仍在说路径: {out['refusal_reason']!r}"


def test_m7_collect_path_traversal_still_says_path(tmp_path):
    """反向锁: **真正的**路径越界仍报路径原因（别把两个成因合并成一句）。"""
    vault = build_vault(tmp_path, ["SeedA"])
    out = json.loads(run_collect(vault, "../外部板").stdout)
    assert out["board_exists"] is False
    assert "路径分隔符" in out["refusal_reason"], out["refusal_reason"]
    assert "U+" not in out["refusal_reason"], out["refusal_reason"]


def test_m7_collect_normal_board_still_works(tmp_path):
    """放行门: 收紧后正常板名的 collect 全链不变（防误伤整条第一刀）。"""
    scan = collect_json(standard_vault(tmp_path))
    assert scan["board_exists"] is True
    assert scan["counts"]["members"] == 3


# ══════════════ 维护卡 B · 数字治理域双向门（BATCH-2026-08-31-第七批） ══════════════
# 治理域裁定见卡文 §零（按位置/结构划分，不按字符）。
# ⛔ 拦截门与放行门**同权重**：round-5 那 4 个误伤输入就是只有拦截门时漏掉的。
# 下列反例全部来自 round-6 定向复核的**实测**记录，本卡开工前逐条重测过现状
# （不采信台账——round-6 存在的理由正是「台账称已处置但实测未处置」）。

LIVE_FIXTURES = Path(__file__).parent / "fixtures" / "recap_live_reports"


def _mutate_report(tmp_path: Path, mutate) -> subprocess.CompletedProcess:
    """在标准 fixture 报告上施加一处变异后跑 --verify。"""
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    base = run_verify(report)
    assert base.returncode == 0, f"基线报告本身就不过 verifier:\n{base.stdout}"
    before = report.read_text(encoding="utf-8")
    after = mutate(before, scan)
    # ⛔ MEMORY `reference_gate_design_pitfalls`: `str.replace` 不命中**不报错**——
    # 变异没打上去、报告没变、verifier 当然 exit 0，而拦截门会把这读成"未被拦"，
    # 或者更糟：某天实现修好了，这条门却因为构造失效而恒绿。变异必须真的改到东西。
    assert after != before, "变异未命中：报告一字未改，这条门测的是空气"
    report.write_text(after, encoding="utf-8")
    return run_verify(report)


def _sig_line(text: str, label: str = "来源覆盖率") -> str:
    return next(ln for ln in text.splitlines() if label in ln)


# ── 拦截门（round-6 实证反例，逐条先红后绿） ────────────────────────────


def test_domain_block_four_fence_short_close(tmp_path):
    """E1: 四反引号开栏 + 三反引号「短闭合」后塞信号行 —— round-6 实测 exit 0。

    CommonMark 规定闭合围栏须同字符且**不短于**开栏；原实现只存 `bare[:3]` 并用
    startswith 判闭合，于是块被误判为已结束，藏在 <pre><code> 里的信号行仍被
    verifier 当成在场陈述。
    """

    def m(text, scan):
        sig = _sig_line(text)
        return text.replace(sig, f"````\n```\n{sig}", 1)

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"四反引号短闭合仍被放行:\n{r.stdout}"


def test_domain_block_blockquote_indented_code(tmp_path):
    """E1 邻域: 引用内缩进代码形态的信号行不得被当成合法在场。

    ⚠️ 如实记录：round-6 报告称此例 exit 0，本卡开工前**实测为 exit 1**
    （被信号行模板的整行匹配拦下）。构造差异或代码已变，两说；
    本用例锁的是**结果面**——这种形态不得被当成合法信号行。
    """

    def m(text, scan):
        sig = _sig_line(text)
        return text.replace(sig, f">     {sig.lstrip('> ').lstrip()}", 1)

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"引用内缩进代码形态被当成合法信号行:\n{r.stdout}"


def test_domain_block_scale_line_tail_append(tmp_path):
    """H-2 前半: 正确规模行**尾部追加**任意文字 —— 原式缺 `$`，match() 只认前缀。

    ⛔ R3 round-8 追加文本更换（负验证实测暴露）：原用「，SeedA 的派生子女共有仨个」，
    但 round-8 把 `仨` 加进定界集、并放宽了句式门之后，这句话会**先被数字绑定**
    独立拦下（`仨` → 无法解析）⇒ 去掉行尾锚 `$` 不再产生泄漏，`survivor-2`
    当场变成不承重。那不是门坏了，是**同一场景多了一道独立防线**。
    按 negverify 铁律「变体必须禁掉该性质的**全部**防线」，正确修法是让这道门
    **只测一个性质**：追加文本改为**不含任何数词**，于是唯一能拦它的就是
    「模板外『派生』表述」——也就是行尾锚 `$` 真正守的那条。
    """

    def m(text, scan):
        line = next(ln for ln in text.splitlines() if "成员（" in ln)
        return text.replace(line, line + "，SeedA 的派生子女如上", 1)

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"规模行尾部追加未被拦:\n{r.stdout}"
    assert "模板外的『派生』表述" in r.stdout, f"应由『行尾锚失效 ⇒ 白名单不再匹配』拦下，而不是别的防线:\n{r.stdout}"


def test_domain_block_seed_ledger_fake_count(tmp_path):
    """H-2 后半: 种子行「批注 999 条」形状合法但值无据 —— 白名单只管句式不管出处。"""

    def m(text, scan):
        line = next(ln for ln in text.splitlines() if ln.startswith("- SeedA — 批注"))
        return text.replace(line, "- SeedA — 批注 999 条", 1)

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"种子行伪计数未被拦:\n{r.stdout}"
    assert "tips_count" in r.stdout, f"未点名绑定字段:\n{r.stdout}"


def test_domain_block_signal_tail_append(tmp_path):
    """H-3: 覆盖率行**标准尾部之后**追加「另有仨条」——「仨」在任何字符表之外。"""

    def m(text, scan):
        line = _sig_line(text)
        return text.replace(line, line.replace("【", "另有仨条【", 1), 1)

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"信号行尾部夹带未被拦:\n{r.stdout}"


def test_domain_block_bare_count_in_prose(tmp_path):
    """D2（本卡原始命题）: 叙述段里**无出处**的裸计数必须被拦。

    ⚠️ 如实记录一处能力边界：卡文/goal 举的例子是「99 个子节点」，但在当前池语义下
    **99 恰好可由 scan 的数值一阶推出**（池 = 数值 ∪ 两两和差），所以它拦不住——
    而这个池语义又是必需的：live 报告实测有合法推算
    「7 个派生点中仅 2 个带 derived_at……其余 5 个无据」（5 = 7−2）。
    ⇒ 拦截力与「不误伤合法算术」用同一套值域匹配**无法兼得**。
    本用例因此改用不可由一阶推算得到的 987654，并把这条边界写进验收单裁决点：
    D2 真正能拦的是「罕见的、推不出来的大数」，对常见小数值形同虚设。
    """

    def m(text, scan):
        return text.replace("## 三维审查", "## 三维审查\n\n- 本板共有 987654 个子节点。【实测】", 1)

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"域内裸计数未被拦:\n{r.stdout}"
    assert "找不到同值来源" in r.stdout, f"未点名无出处:\n{r.stdout}"


# ── 放行门（与拦截门同权重） ────────────────────────────────────────────


@pytest.mark.parametrize(
    "prose",
    [
        "说明十分清楚。",  # round-5 误伤: 含「十」的正常中文
        "统计口径尚未一致。",  # round-5 误伤: 含「一」的正常中文
        "数据来自 2026-08-27 的扫描。",  # E4 日期形态
        "参见 [[节点/Lecture 14]] 的记录。",  # E3 wikilink 内自带数字
    ],
    ids=["shifen", "yizhi", "date", "wikilink"],
)
def test_domain_allow_legit_prose(tmp_path, prose):
    """放行门: 合法叙述不得被收紧误伤（五类合法语料各一组）。"""
    r = _mutate_report(
        tmp_path,
        lambda text, scan: text.replace("## 三维审查", f"## 三维审查\n\n- {prose}【实测】", 1),
    )
    assert r.returncode == 0, f"合法语料被误伤 ({prose}):\n{r.stdout}"


def test_domain_allow_skill_hotkey_action_line(tmp_path):
    """放行门: SKILL HARD-CONSTRAINTS 的白名单动作句（含 `Cmd+Shift+D` 与「派生」）。

    ⚠️ 这条第一次写时用了 `- ` 前缀而红——白名单要求的是**有序列表**形态
    （`## 你现在可以做的` 段的模板就是有序列表）。是语料构造不真实，不是实现误伤；
    如实改测试而不是放宽实现。行内代码跨度由 E2 豁免，序号由 E5 豁免。
    """
    r = _mutate_report(
        tmp_path,
        lambda text, scan: text.replace(
            "## 你现在可以做的\n",
            "## 你现在可以做的\n2. 在原白板选中相关文本 `Cmd+Shift+D` 派生新节点【实测】\n",
            1,
        ),
    )
    assert r.returncode == 0, f"SKILL 白名单动作句被误伤:\n{r.stdout}"


def test_domain_allow_legit_nested_list(tmp_path):
    """放行门: 合法三级列表（四空格缩进）不得被当缩进代码块删掉致误报缺信号行。"""
    r = _mutate_report(
        tmp_path,
        lambda text, scan: text.replace("## 三维审查", "## 三维审查\n\n- 一级\n  - 二级\n    - 三级缩进项\n", 1),
    )
    assert r.returncode == 0, f"合法三级列表被误伤:\n{r.stdout}"


@pytest.mark.parametrize(
    "report_name",
    [
        "回顾-递归与分治 (Recursion & Divide-Conquer)-2026-08-27.md",
        "回顾-特征值与特征向量-2026-08-27.md",
        "回顾-CS 61B-2026-08-27.md",
        "回顾-CS188 lecture 2-2026-08-27.md",
    ],
    ids=["recursion", "eigen", "cs61b", "cs188"],
)
def test_domain_allow_live_real_reports(tmp_path, report_name):
    """⛔ 最重要的放行门: **live vault 的四份真报告**整篇 --verify 必须仍 exit 0。

    fixture 是 live 原件的逐字节拷贝（连同各自的 .recap-scan-*.json）。
    合成 fixture 再像也覆盖不到真实语料的全部形态——真报告里有 mastery 0.01、
    量表 1-4、ISO 时间戳、引用用户原话（含 `[03:21]`、作答「111」）、
    board_name_mismatch 说明等等，这些正是"多禁一点"最容易打到的地方。
    """
    work = tmp_path / "outputs"
    work.mkdir(parents=True)
    for src in LIVE_FIXTURES.iterdir():
        shutil.copy2(src, work / src.name)
    r = run_verify(work / report_name)
    assert r.returncode == 0, f"live 真报告被收紧误伤:\n{r.stdout}"


def test_live_fixtures_are_byte_identical_to_source():
    """诚实性门: fixture 必须是 live 原件的**逐字节**拷贝，不是"整理过"的版本。

    否则放行门就成了自证——用一份为了通过而修饰过的语料去证明"没有误伤"。
    live 侧只读：本用例只算哈希，不写 live vault。
    """
    live_dir = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs")
    if not live_dir.is_dir():
        pytest.skip("live vault 不在本机此路径（CI/他机）")
    checked = 0
    for fx in LIVE_FIXTURES.iterdir():
        src = live_dir / fx.name
        if not src.is_file():
            pytest.fail(f"fixture 在 live 侧找不到同名原件: {fx.name}")
        assert hashlib.sha256(fx.read_bytes()).hexdigest() == hashlib.sha256(src.read_bytes()).hexdigest(), (
            f"fixture 与 live 原件不逐字节相同: {fx.name}"
        )
        checked += 1
    assert checked == 8, f"应有 4 报告 + 4 scan JSON，实际 {checked}"


# ── Codex round-1 整改：门覆盖缺口（每一条都对应一个实测 survivor/BLOCKER） ──


@pytest.mark.parametrize("section", ["你现在可以做的", "三维审查"], ids=["actions", "review3"])
def test_domain_block_bare_count_in_each_d2_section(tmp_path, section):
    """D2 的**每个段**都要有自己的门。

    ⛔ Codex 实测 survivor：把 `_D2_SECTIONS` 砍成只剩「三维审查」，套件仍 142 passed
    ——因为原来的拦截门只往「三维审查」插探针，域的另一半根本没人看着。
    这是「门覆盖不全」的典型：域声明了两段，门只守了一段。
    """
    r = _mutate_report(
        tmp_path,
        lambda text, scan: text.replace(
            f"## {section}\n",
            f"## {section}\n- 本板共有 987654 个隐藏节点。【实测】\n",
            1,
        ),
    )
    assert r.returncode != 0, f"『{section}』段的裸计数未被拦:\n{r.stdout}"


@pytest.mark.parametrize("suffix", ["", "（本轮）"], ids=["exact", "with_suffix"])
def test_domain_block_survives_section_title_suffix(tmp_path, suffix):
    """⛔ BLOCKER-2: 给段标题加后缀不得关掉整个域。

    报告别处用**宽松**段名口径（允许 `## 三维审查（本轮）`），D2 却用精确标题定位——
    于是加四个字就能整段关掉 D2。单变量对照实测：精确标题 exit 1、加后缀 exit 0。
    这是「存在性与下游定位口径不一致」的同型复发。
    """

    def m(text, scan):
        text = text.replace("## 三维审查", f"## 三维审查{suffix}", 1)
        return text.replace(
            f"## 三维审查{suffix}",
            f"## 三维审查{suffix}\n\n- 本板共有 987654 个隐藏节点。【实测】",
            1,
        )

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"标题后缀 {suffix!r} 关掉了 D2:\n{r.stdout}"


def test_domain_block_seed_count_tamper_on_real_manifest_line(tmp_path):
    """⛔ BLOCKER-3: 种子绑值门必须在**真实 manifest 台账行**上生效。

    真报告的种子行带后续字段（`- cs-61b-csm — 批注 2 条；未派生…· mastery 0.3…`），
    原正则要求「批注 N 条」后直接行尾 ⇒ 整行不匹配 ⇒ 被 continue 跳过 ⇒
    把 2 改成 999 照样 exit 0。**门在真实语料上完全不生效**。

    而放行门只证明了「真报告 PASS」，没证明「真报告被篡改后 FAIL」——
    这正是假绿的经典形态：正例过了就以为门在工作。本用例补的就是这半边。
    """
    work = tmp_path / "outputs"
    work.mkdir(parents=True)
    for src in LIVE_FIXTURES.iterdir():
        shutil.copy2(src, work / src.name)
    report = work / "回顾-CS 61B-2026-08-27.md"
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if ln.startswith("- cs-61b-csm — 批注"))
    assert "批注 2 条" in line, f"前提失效，真报告形态已变: {line}"
    report.write_text(
        text.replace(line, line.replace("批注 2 条", "批注 999 条", 1), 1),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode != 0, f"真实 manifest 台账行的伪计数未被拦:\n{r.stdout}"


def test_domain_block_fence_close_needs_trailing_blank_only(tmp_path):
    """⛔ BLOCKER-1: 闭栏标记之后只能有空白（CommonMark），带 info string 的不是闭栏。

    实测：` ```` text` 开栏 + ` ````not-a-valid-close` 后跟信号行 → 原实现判块已闭合，
    信号行"看起来在块外"照样在场；而 CommonMark 渲染里它们全在 <pre><code> 内。
    """

    def m(text, scan):
        sig = _sig_line(text)
        return text.replace(sig, f"````text\n````not-a-valid-close\n{sig}", 1)

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"带 info string 的伪闭栏被当成闭栏:\n{r.stdout}"


@pytest.mark.parametrize(
    "prose",
    ["从 2~3 个节点里挑一个复盘。", "覆盖 1-2 个薄弱点。", "建议再看 2 到 3 个例子。"],
    ids=["tilde", "hyphen", "cjk"],
)
def test_domain_allow_range_expression(tmp_path, prose):
    """放行门（E7）: 范围表达的端点不是独立计数。

    ⛔ Codex 实测：`2~3 个` 在「递归与分治」报告 FAIL、在 CS 61B 报告 PASS——
    因为后者的 scan 里恰好有个无关的整数 3。**合法与否取决于另一块板的偶然数字**，
    这是明确的误伤，按结构豁免整段区间。
    """
    r = _mutate_report(
        tmp_path,
        lambda text, scan: text.replace("## 三维审查", f"## 三维审查\n\n- {prose}【实测】", 1),
    )
    assert r.returncode == 0, f"范围表达被误伤 ({prose}):\n{r.stdout}"


def test_domain_number_pool_excludes_string_derived_digits(tmp_path):
    """⛔ D2 池只收**数值型**，不从字符串抽数。

    Codex 实测：`544 个子节点` 通过（544 只来自 board_sha256 片段）、
    `111 个子节点` 通过（111 只来自用户作答原话）。池被哈希与原话污染后，
    "有出处"这个语义就空了——罕见大数拦得住，常见小数值形同虚设。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    sha = scan["source_revision"]["board_sha256"]
    frag = next((sha[i : i + 4] for i in range(len(sha) - 3) if sha[i : i + 4].isdigit()), None)
    if frag is None:
        pytest.skip("本次 fixture 的 sha 里没有 4 位纯数字片段")
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    report.write_text(
        text.replace(
            "## 三维审查",
            f"## 三维审查\n\n- 本板共有 {int(frag)} 个隐藏节点。【实测】",
            1,
        ),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode != 0, f"来自 SHA 字符串的数字 {int(frag)} 被当成了「有出处」:\n{r.stdout}"


# ── Codex round-1 HIGH「D1 仍只是少量枚举」整改：域倒转为 default-deny 后的逐条门 ──
# 下列每一条都是复核者实测 **exit 0** 的越界探针；域从「点名两段」改成
# 「默认全域 + 显式例外」后应全部拦下。


@pytest.mark.parametrize(
    "anchor,inject",
    [
        # 台账『派生』行（原来只有『种子』行有 binder）
        ("### 派生", "- 本板共有 987654 条未闭环 tips。\n"),
        # AI 侧对账段的其余数字（原来只绑 tips 两式）
        ("## AI 侧对账", "- 本板共有 987654 条待定纠错候选。\n"),
        # 「本段新增」段
        ("## 本段新增", "- 本板共有 987654 个隐藏节点。【实测】\n"),
        # 自造的新段落——加个标题就该逃出治理，正是 default-deny 要堵的
        ("## 三维审查", "## 附录\n\n- 本板共有 987654 个隐藏节点。【实测】\n\n"),
    ],
    ids=["ledger_derived", "ai_recon", "new_section", "appendix"],
)
def test_domain_default_deny_covers_every_section(tmp_path, anchor, inject):
    """⛔ 域倒转（default-deny）后，这些位置都不再是「没人管」的缝隙。

    原实现 `_D2_SECTIONS = ("你现在可以做的", "三维审查")` 是**点名两段的允许式**，
    于是复核者只要把伪数字写在别处（甚至新开一个 `## 附录`）就能 exit 0。
    「加一个标题就能逃出治理」——那不是域，是几个段名。
    """

    def m(text, scan):
        if inject is None:  # 规模 callout：改模板里那个「1 次调用」
            return text.replace("manifest（1 次调用）", "manifest（987654 次调用）", 1)
        return (
            text.replace(anchor, anchor + "\n" + inject if anchor.startswith("##") else anchor, 1)
            if anchor.startswith("###") is False and inject.startswith("##")
            else text.replace(anchor, anchor + "\n" + inject, 1)
        )

    r = _mutate_report(tmp_path, m)
    assert r.returncode != 0, f"{anchor} 处的越界数字未被拦:\n{r.stdout}"


def test_domain_exempt_section_is_explicit_not_accidental(tmp_path):
    """反向锁: 唯一出域的段（数据来源与新鲜度）是**显式**豁免，不是碰巧扫不到。

    这条锁的是"例外表"本身——如果哪天有人往 `_D2_EXEMPT_SECTIONS` 里加东西，
    这条会提醒他：出域是一个需要写下来的决定，不是实现细节。
    """
    mod_src = (
        Path(__file__).resolve().parents[3] / "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py"
    ).read_text(encoding="utf-8")
    assert "_D2_EXEMPT_SECTIONS = (" in mod_src
    exempt_block = mod_src.split("_D2_EXEMPT_SECTIONS = (", 1)[1].split("\n)", 1)[0]
    # ⚠️ 只数**非注释行**的条目——第一版直接 count('"') 把注释里的引号也数进去了（4 != 2）。
    entries = [ln.strip() for ln in exempt_block.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    assert entries == ['"数据来源与新鲜度",'], f"例外表变了却没人复核——出域必须是显式决定，不是实现细节: {entries}"


def test_domain_covers_scale_callout_preamble(tmp_path):
    """⛔ 规模自陈 callout 在**首个 `##` 之前**——原实现按 `##` 段定位，根本扫不到它。

    复核者实测：manifest 模式报告里把「manifest（1 次调用）」改成「987654 次调用」exit 0。
    default-deny 切段时必须把 preamble 也当成一段。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault, "--manifest", str(make_manifest(vault)))
    assert scan["data_mode"] == "manifest", "前提失效：需要 manifest 模式才有那句 callout"
    report = write_report(vault, scan)
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"
    text = report.read_text(encoding="utf-8")
    assert "manifest（1 次调用）" in text, f"前提失效，callout 形态已变:\n{text[:400]}"
    # ⚠️ 判据从"值在池里"改为"句式 + 值"后（见 _D2_CLAIM_RE 的说明），
    # 模板里的「manifest（N 次调用）」不再由 D2 管——它没有自称全板规模，
    # 且该数由 D1 的 data_mode 绑定面负责。这里锁的是 **preamble 段确实在域内**：
    # 往 callout 里塞一句自称全板规模的假计数，必须被拦。
    report.write_text(
        text.replace("> 数据面：", "> 本板共有 987654 个子节点。\n> 数据面：", 1),
        encoding="utf-8",
    )
    r = run_verify(report)
    assert r.returncode != 0, f"规模 callout（preamble）里的越界数字未被拦:\n{r.stdout}"


# ══════ 多智能体对抗审查（ultracode workflow）整改门 · 8 条实证发现 ══════
# 5 路探针（结构 / 数字形态 / 误伤 / 门覆盖 / 名实一致）× 三视角证伪。
# 下列每条都由探针在**四份 live 真报告**上实测 exit 0，全部先红后绿。


def _live_probe(tmp_path: Path, extra: str, report="回顾-CS 61B-2026-08-27.md"):
    """在 live 真报告尾部追加一段后跑 --verify（fixture 逐字节拷贝，live 只读）。"""
    work = tmp_path / "outputs"
    work.mkdir(parents=True)
    for src in LIVE_FIXTURES.iterdir():
        shutil.copy2(src, work / src.name)
    rp = work / report
    base = run_verify(rp)
    assert base.returncode == 0, f"基线真报告本身就不过 verifier:\n{base.stdout}"
    rp.write_text(rp.read_text(encoding="utf-8") + extra, encoding="utf-8")
    return run_verify(rp)


def test_audit_code_span_html_comment_cannot_hide_content(tmp_path):
    """⛔ BLOCKER: code span 包住 `<!--` / `-->`，可让**渲染可见**的正文对全部检查隐身。

    原实现「先无条件剥闭合注释、再查残留 `<!--`」——两个标记都被吃掉，残留检查恒不触发。
    在 Obsidian 里 `` `<!--` `` 渲染成字面文本，读者看得见那段字，verifier 却先把它删了。
    影响面远不止 D2：探针实测连 HARD-R4 禁词「偏离」都能这样藏进去并 VERIFY PASS。
    """
    r = _live_probe(tmp_path, "\n- 注释语法 `<!--` 起，本板共有 987654 个子节点，`-->` 止。\n")
    assert r.returncode != 0, f"code-span 包裹的注释标记让计数隐身:\n{r.stdout}"
    r2 = _live_probe(tmp_path / "b", "\n- 语法 `<!--` 起，你的理解偏离了材料主线，`-->` 止。\n")
    assert r2.returncode != 0, f"同一构造还能藏 HARD-R4 禁词:\n{r2.stdout}"


@pytest.mark.parametrize(
    "extra",
    [
        "\n### 数据来源与新鲜度（补充）\n\n- 本板共有 987654 个子节点。\n",
        "\n## 附录（数据来源与新鲜度）\n\n- 本板共有 987654 个子节点。\n",
        "\n```\n## 板级数据来源与新鲜度\n```\n\n- 本板共有 987654 个子节点。\n",
    ],
    ids=["h3_heading", "suffix_in_title", "fake_heading_in_fence"],
)
def test_audit_exempt_section_match_is_prefix_anchored(tmp_path, extra):
    """⛔ BLOCKER: 出域判定曾用**子串**匹配，且切段正则连 `###` 一起当段首。

    于是「把豁免段名塞进任意标题的非开头位置」或「加个三级标题」就能整段出域——
    这正是 Codex round-1 已推翻过一次的缺陷（「加一个标题就能逃出治理」）换条路复活。
    第三个构造更隐蔽：围栏**里**的假标题被切段正则当成真标题，而读者只看到一段灰底代码。
    ⚠️ 我原来那道守卫测试只锁了例外表的**字面量**，没锁**匹配语义**——守卫守错了东西。
    """
    r = _live_probe(tmp_path, extra)
    assert r.returncode != 0, f"出域匹配被绕过:\n{r.stdout}"


def test_audit_number_pool_excludes_scale_gate_constants(tmp_path):
    """⛔ BLOCKER: 数值池混入 `scale_gate` 的源码常量（30/100/10），任何板都有。

    后果：100−1=99 恒在池内 ⇒ **卡文与 goal 的旗舰反例「99 个子节点」在四份真报告上
    全部放行**，而验收单 §一 当时还写着「拦下」。门槛常量不是「这块板的数据」，
    拿它当出处等于给池注水。
    """
    r = _live_probe(tmp_path, "\n- 本板共有 99 个子节点。【实测】\n")
    assert r.returncode != 0, f"99 仍被当成「有出处」（池里还有 scale_gate 常量？）:\n{r.stdout}"


@pytest.mark.parametrize(
    "extra,ids",
    [
        ("\n- 本板共有 `987654` 个子节点。【实测】\n", "inline_code"),
        ("\n- 详见 [[节点/x|本板共有 987654 个子节点]]。\n", "wikilink_alias"),
        ("\n- 本板共有 **987654** 个子节点。【实测】\n", "bold"),
        ("\n- 本板共有 <span>987654</span> 个子节点。\n", "html_span"),
        ("\n- 本板共有 987654&nbsp;个子节点。\n", "nbsp"),
        ("\n- 本板共有 0.987654 个子节点。【实测】\n", "decimal_prefix"),
    ],
    ids=lambda v: v if isinstance(v, str) and not v.startswith("\n") else None,
)
def test_audit_visible_number_forms_are_counted(tmp_path, extra, ids):
    """⛔ 渲染**可见**的计数不得因排版而免检。

    - 行内代码 / wikilink 别名：挖空的是读者看得见的正文，`` `987654` 个子节点 ``
      的渲染结果与裸写等价地在断言一个计数；
    - 加粗 / `<span>` / `&nbsp;`：原式要求数字与量词**紧邻**（只容 `\\s`），
      任一排版插入即漏检——而加粗数字正是 LLM 写报告的常见排版；
    - `0.` 前缀：`(?<![0-9.])` 的本意是不切开小数，实际效果是任何数字补个 `0.` 就退出治理。
    """
    r = _live_probe(tmp_path, extra)
    assert r.returncode != 0, f"{ids}: 可见计数因排版免检:\n{r.stdout}"


@pytest.mark.parametrize(
    "extra,ids",
    [
        ("\n```\n本板共有 987654 个子节点\n```\n", "fenced_code"),
        ("\n- 用 `/node-chat 节点/cs-61b-csm` 继续剖析。\n", "cmd_inline_code"),
        ("\n- 考分量表 `1-4 (1=最低)` 为数据字段自带的推定值。\n", "scale_inline_code"),
        ("\n- 详见 [[节点/Lecture 14]] 的记录。\n", "wikilink_target"),
    ],
    ids=lambda v: v if isinstance(v, str) and not v.startswith("\n") else None,
)
def test_audit_legit_forms_still_pass_on_live_report(tmp_path, extra, ids):
    """放行门（与上一条同权重）：收紧不得误伤真实语料里的合法形态。

    ⚠️ E1 的缺失曾是**双向**的：D2 从不调用 `_strip_code_blocks`，
    既让围栏里的字面文本被当成报告的陈述（误伤），又让围栏里的假标题开出出域段（绕过）。
    这四条锁的是误伤那一侧——命令示例、量表、wikilink 目标在 live 报告里大量出现。
    """
    r = _live_probe(tmp_path, extra)
    assert r.returncode == 0, f"{ids}: 合法形态被误伤:\n{r.stdout}"


def _verdicts_on_all_boards(tmp_path: Path, prose: str) -> dict:
    """同一句话追加到四份 live 真报告，返回各自的 exit code。"""
    out = {}
    for i, name in enumerate(sorted(p.name for p in LIVE_FIXTURES.glob("*.md"))):
        work = tmp_path / f"b{i}" / "outputs"
        work.mkdir(parents=True)
        for src in LIVE_FIXTURES.iterdir():
            shutil.copy2(src, work / src.name)
        rp = work / name
        rp.write_text(rp.read_text(encoding="utf-8") + f"\n- {prose}【实测】\n", encoding="utf-8")
        out[name[:12]] = run_verify(rp).returncode
    return out


@pytest.mark.parametrize(
    "prose",
    [
        "你说「我做了 5 个练习」，这条批注未闭环。",
        "承接第 4 条动作建议继续推进。",
        "以上 4 条建议按优先级排序。",
        "建议覆盖 4 个到 5 个节点。",
        "有 5 处值得注意。",
        "详见 [共 987 个例子](节点/x.md)。",
    ],
    ids=["quote", "ordinal", "self_ref", "range_alt", "synonym_quant", "md_link"],
)
def test_audit_verdict_is_board_independent(tmp_path, prose):
    """⛔ BLOCKER: 同一句合法叙述，在**四块板上必须判决一致**。

    这是本卡最深的一处修正。原判据是「值落在 scan 数值池里 = 有出处」——
    那是个**碰撞判据**：池里有 0/1/2/3 时几乎任何小计数都"碰巧有出处"，
    池小的板（「递归与分治」只有 `[0,1]`）则合法叙述全被拒。
    对抗审查实测：上列每一句在 CS 61B / 特征值 / CS188 放行，在「递归与分治」FAIL。
    **同一句话的对错取决于另一组数据**——这不是覆盖面问题，是判据不可用。

    ⇒ D2 收窄为只查**明确自称全板规模**的句式（`_D2_CLAIM_RE`），
    普通叙述（引用原话 / 序数 / 自指 / 同义量词 / 链接文本）不再被牵连。
    宁可少管，不可乱判。
    """
    v = _verdicts_on_all_boards(tmp_path, prose)
    assert len(set(v.values())) == 1, f"同一句话在不同板上判决不同: {v}"
    assert set(v.values()) == {0}, f"合法叙述被误伤: {v}"


@pytest.mark.parametrize(
    "prose",
    [
        "本板共有 987654 个子节点。",
        "这块板共有 99 个子节点。",
        "全板总共 987654 条批注。",
    ],
    ids=["ben_ban", "zhe_kuai_ban", "quan_ban"],
)
def test_audit_scale_claims_blocked_on_every_board(tmp_path, prose):
    """反向：**自称全板规模**的假计数，在四块板上必须一致地被拦下。

    与上一条同权重——收窄不能收成"什么都不管"。
    """
    v = _verdicts_on_all_boards(tmp_path, prose)
    assert all(v.values()), f"自称全板规模的假计数未被拦: {v}"


# ── 对抗审查第 3/4 路（数字形态面 / 门覆盖面）整改门 ──
# ⚠️ 工作流在 verify 阶段撞上周限额中断，**没有三视角证伪结果**——
# 下列每条都是我自己在四份 live 真报告上逐条复现后才动手的，如实记录该证据缺口。


@pytest.mark.parametrize(
    "prose,ids",
    [
        ("本板共有 ９８７６５４ 个子节点。", "fullwidth"),
        ("本板共有九十八万个子节点。", "cjk_numeral"),
        ("本板共有 987654 名成员。", "quant_outside_table"),
        ("本板共有 987654 组关系。", "quant_zu"),
        ("本板共有 987654 多个子节点。", "modifier_duo"),
        ("本板共有 987654 余条批注。", "modifier_yu"),
        ("本板共有 1-987654 个子节点。", "range_laundering"),
        ("本板共有 987654 `条` 批注。", "quant_in_code_span"),
        ("本板共有 999,016 个子节点。", "thousands_sep"),
    ],
    ids=lambda v: v if isinstance(v, str) and "共有" not in v else None,
)
def test_audit_number_form_bypasses_are_closed(tmp_path, prose, ids):
    """⛔ 数字/量词识别面的九条绕过，四板一致地拦下。

    - **全角与中文数字**（BLOCKER）：原来 D2 的数字是 `[0-9]+`，于是
      「本板共有九十八万个子节点」这种**完全虚构**的规模自陈整域免检。
      scan 的计数都是 ASCII 整数，报告换个写法不该换来免检 ⇒ 归一后照常比对。
    - **表外量词**：11 字封闭表被 21 个常用量词（名/位/台/件/组…）绕过 ⇒ 扩表。
      ⚠️ 仍是封闭表——如实登记的边界，不宣称"位置承担了一切"。
    - **修饰字**（多/余/来/几/约/近/超）：插一个字就断开数字与量词的紧邻关系。
    - **E7 洗钱通道**：范围豁免原为**无条件**整段挖空 ⇒ 写个 `1-` 前缀，
      任意量级都不受检。现在只有**两端都有出处**才算合法区间。
    - **量词包进 code span**：挖空量词会让前面的数字失去锚点 ⇒ 纯量词跨度不再豁免。
    """
    v = _verdicts_on_all_boards(tmp_path, prose)
    assert len(set(v.values())) == 1, f"{ids}: 四板判决不一致: {v}"
    assert all(v.values()), f"{ids}: 未被拦下: {v}"


@pytest.mark.parametrize(
    "prose,ids",
    [
        ("建议覆盖 2~3 个节点。", "legit_range"),
        ("覆盖 4 个到 5 个节点。", "legit_range_cjk"),
        ("量表 `1-4 (1=最低)` 为数据字段自带的推定值。", "legit_scale_code"),
        ("统计口径尚未一致。", "cjk_yi_in_prose"),
        ("说明十分清楚。", "cjk_shi_in_prose"),
    ],
    ids=lambda v: v if isinstance(v, str) and "。" not in v else None,
)
def test_audit_number_form_fixes_do_not_overreach(tmp_path, prose, ids):
    """放行门（同权重）：数字形态收紧不得反噬合法语料。

    ⚠️ 特别是最后两条——`统计口径尚未一致` / `说明十分清楚` 含「一」「十」，
    正是 round-5 那次翻车的原始误伤输入。中文数字解析器上线后必须重新验一遍：
    中文数字只有**紧跟量词**时才算计数，散落在正常中文里的数字字不算。
    """
    v = _verdicts_on_all_boards(tmp_path, prose)
    assert len(set(v.values())) == 1, f"{ids}: 四板判决不一致: {v}"
    assert not any(v.values()), f"{ids}: 合法语料被误伤: {v}"


# ══════════ CARD-维护B-R2 · survivor 承重门（BATCH-2026-09-01-第八批） ══════════
# 第七批复核裁定 F-4: 在隔离拷贝上重放 round-6 的 survivor，S1/S3/S4 变异后
# **全套件 passed/failed 集合与原版逐字相同** = 门没锁住；验收单「survivor 5 条
# 全部如期变红」那一行不实（那 5 条锁的是别的性质）。
# 本节为三个 survivor + 一个旧 survivor 各配**先红后绿**的承重门。
# ⛔ 每道门写明「它证明什么、不证明什么」——不写比门宽的话。

SIGNAL_LABELS = ("未答问题年龄", "来源覆盖率", "无来源结论", "重复堆积")
SKILL_MD = SCRIPT.parent.parent / "SKILL.md"


def _parse_skill_nodata_reasons(skill_text: str) -> list[str]:
    """从 SKILL.md ③段铁律里解析五条无据原因（顺序保留）。

    ⛔ 解析必须真的读文件：返回常量的"解析器"会让同步锁恒绿（假门）。
    锚点是铁律原文「原因只能逐字取自下列」，其后**第一条**全部由反引号项
    与 `/` 组成的行即原因表行；找不到就返回空表（让比对失败并点名），
    ⛔ 不静默回退成"就当它们相等"。
    """
    idx = skill_text.find("原因只能逐字取自下列")
    if idx < 0:
        return []
    for line in skill_text[idx:].splitlines()[1:]:
        if re.fullmatch(r"\s*`[^`\n]+`(?:\s*/\s*`[^`\n]+`)+\s*", line):
            return re.findall(r"`([^`\n]+)`", line)
    return []


def _parse_skill_tail_notes(skill_text: str) -> list[str]:
    """从 SKILL.md ③段铁律里解析**信号行尾部注记**封闭表（CARD-维护B-R2 (e)）。"""
    idx = skill_text.find("附注只许")
    if idx < 0:
        return []
    for line in skill_text[idx:].splitlines()[1:]:
        toks = re.findall(r"`([^`\n]+)`", line)
        if toks:
            return toks
    return []


# ── (b) S1: `_NODATA_REASONS` 增一条即放宽，无任何测试锁表 ──────────────


def test_domain_skill_sync_nodata_reasons_table():
    """b1 · S1 承重门①「SKILL 同步锁」: 代码表与 SKILL.md 铁律表必须**全等**。

    survivor 实证: 往 `_NODATA_REASONS` 里加第六项「任意原因」，
    既有门 `test_verify_nodata_reason_whitelist` 只喂固定 bogus 串，
    表多一条只放宽那一个字面 —— 全套件 196 passed 无新增红。
    代码注释写着「新增文案必须两处同改」，但那只是**注释约定**，没有门。

    **它证明什么**: 代码的五条原因与 SKILL.md 文档面逐字同序一致；
    单侧增删（代码侧或文档侧）立刻变红。
    **它不证明什么**: 不证明这五条原因本身是"对的"文案，也不证明
    verifier 在运行时真的按这张表拦截（那是 b2 的行为门的事）。
    """
    rs = _load_recap_scan()
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    parsed = _parse_skill_nodata_reasons(skill_text)
    assert len(parsed) == 5, f"SKILL.md 原因表解析异常（应 5 条，得 {parsed}）"
    assert tuple(parsed) == rs._NODATA_REASONS, (
        f"代码与 SKILL.md 的无据原因表不同步:\n  代码 = {rs._NODATA_REASONS}\n  SKILL = {tuple(parsed)}"
    )
    # ⛔ 篡改门（MEMORY `reference_positive_gate_needs_tamper_test`）:
    # 只验「真语料 PASS」不证明门在工作 —— 必须证明它对**不同步**会报警。
    # 三种篡改都从**文档侧文本**下手，因此同时证明解析器真的在读 SKILL.md、
    # 不是返回一个与代码常量同源的副本。
    reason_line = next(
        ln
        for ln in skill_text[skill_text.find("原因只能逐字取自下列") :].splitlines()[1:]
        if re.fullmatch(r"\s*`[^`\n]+`(?:\s*/\s*`[^`\n]+`)+\s*", ln)
    )
    tampers = {
        "多一项": reason_line + " / `任意原因`",
        "少一项": " / ".join(reason_line.strip().split(" / ")[:-1]),
        "改顺序": " / ".join(reversed(reason_line.strip().split(" / "))),
    }
    for name, bad_line in tampers.items():
        bad = skill_text.replace(reason_line, bad_line, 1)
        assert bad != skill_text, f"{name}: 篡改未命中，这条篡改门测的是空气"
        assert tuple(_parse_skill_nodata_reasons(bad)) != rs._NODATA_REASONS, (
            f"{name} 后同步锁仍判「一致」—— 该锁不承重"
        )


@pytest.mark.parametrize(
    "reason",
    ["任意原因", "其他", "略", "见上文", "分母为零（补充）"],
    ids=["renyi", "qita", "lve", "jianshangwen", "fenmu_suffix"],
)
def test_domain_block_nodata_reason_outside_table(tmp_path, reason):
    """b2 · S1 承重门②「表外原因行为门」: 表外原因必须被 verifier 实际拦下。

    与 b1 互补: b1 锁"表的内容"，b2 锁"表在运行时真的封闭"。
    `分母为零（补充）` 一条专打**前缀式**放行——它以合法原因开头，
    只有整行锚定（`$`）才拦得住。

    **它证明什么**: 这五个表外原因写进无据行时 exit 1 且点名「未整行匹配标准式」。
    **它不证明什么**: 不证明表内五条原因**都**能放行（那由既有的
    `test_verify_nodata_lines_pass` 与本套件的真语料门覆盖），
    也不证明穷尽了所有表外写法——表外是无限集，本门取五个代表。
    """
    vault = build_vault(tmp_path, ["SeedA", "DerivedB"])
    write_node(vault, "SeedA")
    write_node(vault, "DerivedB", derived_from="[[SeedA]]")
    scan = collect_json(vault)
    assert scan["signals"]["duplicate_accumulation"]["availability"] == "无据"
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "重复堆积" in ln)
    bogus = f"> - 重复堆积：无据（{reason}）"
    assert bogus != line, "构造与原行相同，这条门测的是空气"
    report.write_text(text.replace(line, bogus, 1), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"表外原因「{reason}」被放行:\n{r.stdout}"
    assert "无据行未整行匹配标准式" in r.stdout, f"拦截理由不是白名单:\n{r.stdout}"
    assert "VERIFY PASS" not in r.stdout


# ── (c) S3: 多层引用前缀下围栏只剥一层 ──────────────────────────────


def _wrap_signals_in_fence(text: str, prefix: str) -> str:
    """把四条信号行整体包进 `<prefix>``` … <prefix>``` `，信号行同层前缀。"""
    lines = text.splitlines()
    idx = [i for i, ln in enumerate(lines) if any(lb in ln for lb in SIGNAL_LABELS)]
    start, end = idx[0], idx[-1]
    body = [prefix + re.sub(r"^[>\s]*", "", lines[i]) for i in range(start, end + 1)]
    out = lines[:start] + [prefix + "```"] + body + [prefix + "```"] + lines[end + 1 :]
    return "\n".join(out)


@pytest.mark.parametrize("prefix", ["> > ", "> > > ", ">>"], ids=["depth2", "depth3", "no_space"])
def test_domain_block_multilevel_blockquote_fence(tmp_path, prefix):
    """c1 · S3 承重门①「多层引用围栏行为门」: 任意层引用前缀下的围栏都必须识别。

    survivor 实证: `_strip_code_blocks` 的 `^[>\\s]*` 改成 `^>?[^\\S\\n]*`（只剥一层）后
    全套件 196 passed 无新增红。既有门 `test_verify_blockquote_fence_hides_nothing`
    只构造**一层** `> ```；`grep -c "> > " 测试文件` = 0。
    而 `> > - 信号行` 恰好落在信号行前缀允许式 `[>\\-*·\\s]{0,6}`（6 字符）里
    ⇒ 变异体下 VERIFY PASS，可 Obsidian 把它渲染成**引用内代码块**（读者看到灰底代码）。

    **它证明什么**: 二层/三层/无空格三种前缀下，藏进围栏的信号行都不被当成在场，
    且拦截理由是"代码块相关"而非碰巧撞上别的规则。
    **它不证明什么**: 不证明所有 CommonMark 引用嵌套形态都覆盖（如引用内列表内围栏），
    也不证明围栏识别对 `~~~` 与反引号的所有交叉组合都正确（同族另配 old-1 门）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    base = run_verify(report)
    assert base.returncode == 0, f"基线报告本身就不过 verifier:\n{base.stdout}"
    before = report.read_text(encoding="utf-8")
    after = _wrap_signals_in_fence(before, prefix)
    assert after != before, "变异未命中：报告一字未改，这条门测的是空气"
    report.write_text(after, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode != 0, f"{prefix!r} 层引用内的围栏未被识别:\n{r.stdout}"
    assert "代码块内出现信号名" in r.stdout or "缺信号行" in r.stdout, (
        f"拦截理由与「信号行藏在代码块里」无关（可能撞上了别的规则）:\n{r.stdout}"
    )
    assert "VERIFY PASS" not in r.stdout


def test_domain_block_list_item_fence_hides_signals(tmp_path):
    """round-2 线索门 + round-3 BLOCKER-1/2 修复门: 列表容器内的围栏。

    渲染语义（CommonMark，round-3 与 Codex 双向确认）:
      · `- ``` ` 开栏 + **缩进 ≥ 内容列** 的内容行 → 内容渲染在代码块内（灰底），
        verifier 必须剥 ⇒ 藏信号 = 缺行/代码块内信号名;
      · `- ``` ` 开栏后 **marker 行**（缩进不足的同级 `- 内容`）→ 是**新的 sibling
        列表项，渲染为可见正文** ⇒ verifier 必须保留 ⇒ 可见伪计数由 D2 拦
        （round-3 BLOCKER-1: 无容器边界跟踪时它被误剥成代码内容，D2 漏拦）;
      · **有序 marker** `1. ``` `（round-3 BLOCKER-2）与无序同语义。

    先红证据: `evidence-maintb-r2/codex-hint-repro.txt`（round-2 形态）、
    `round3-repro.txt`（BLOCKER-1 实测 exit 0）、`round3-v2-probe4.txt`（整改后 19 项行为矩阵）。

    **它证明什么**: 上述三形态的「剥/留」判定与下游拦截各就各位。
    **它不证明什么**: 不证明所有 CommonMark 容器嵌套（引用内列表内列表等）都覆盖
    ——以「模板允许的前缀形态 + 常见列表容器」为封闭集。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    base = run_verify(report)
    assert base.returncode == 0, f"基线报告本身就不过 verifier:\n{base.stdout}"
    text = report.read_text(encoding="utf-8")
    lines = text.splitlines()
    idx = [i for i, ln in enumerate(lines) if any(lb in ln for lb in SIGNAL_LABELS)]
    start, end = idx[0], idx[-1]

    # ① 列表项围栏 + 缩进内容（真代码）→ 剥 → 拦
    body = ["> - ```"] + [">   " + re.sub(r"^[>\s]*-\s*", "", lines[i]) for i in range(start, end + 1)] + [">   ```"]
    out = lines[:start] + body + lines[end + 1 :]
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    r = run_verify(report)
    assert r.returncode != 0, f"列表项围栏(缩进内容)仍被放行:\n{r.stdout}"
    assert "代码块内出现信号名" in r.stdout or "缺信号行" in r.stdout, f"拦截理由与围栏无关:\n{r.stdout}"

    # ② 有序列表围栏 + 缩进内容（round-3 BLOCKER-2）→ 剥 → 拦
    body = ["1. ```"] + ["   " + re.sub(r"^[>\s]*-\s*", "", lines[i]) for i in range(start, end + 1)] + ["1. ```"]
    out = lines[:start] + body + lines[end + 1 :]
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    r = run_verify(report)
    assert r.returncode != 0, f"有序列表围栏仍被放行:\n{r.stdout}"
    assert "代码块内出现信号名" in r.stdout or "缺信号行" in r.stdout, f"拦截理由与围栏无关:\n{r.stdout}"

    # ③ sibling marker 行 = 可见正文（round-3 BLOCKER-1）→ 保留 → D2 拦伪计数
    r = _mutate_report(
        tmp_path / "sibling",
        lambda t, s: t.replace(
            "## 三维审查",
            "## 三维审查\n\n- ```\n- 本板共有 987654 个子节点\n- ```\n",
            1,
        ),
    )
    assert r.returncode != 0, f"sibling 列表项可见伪计数被放行:\n{r.stdout}"
    assert "找不到同值来源" in r.stdout, f"拦截理由不是 D2:\n{r.stdout}"

    # ④ sibling marker 行放合规信号 = 可见且合规 → 放行（渲染语义锁，防过剥）
    r = _mutate_report(
        tmp_path / "sibling_ok",
        lambda t, s: t.replace(
            "## 三维审查",
            "## 三维审查\n\n- ```\n- 本报告信号与数据快照一致\n- ```\n",
            1,
        ),
    )
    assert r.returncode == 0, f"sibling 列表项可见正文被误伤:\n{r.stdout}"


def test_domain_strip_code_blocks_unit_contract():
    """c2 · S3 承重门②「`_strip_code_blocks` 单元契约门」: 直接调函数验双向行为。

    行为门（c1/列表围栏门）走整条 verifier，误伤面与拦截面都可能被别的规则掩盖；
    这道单元门把契约钉在函数本身（round-3 重写为渲染语义三分类）:
      · **剥空**（真代码内容，渲染为灰底）: 任意层引用围栏 / 列表项围栏 +
        缩进达内容列的内容 / 有序列表围栏；
      · **保留**（sibling marker 行 = 可见正文，round-3 BLOCKER-1 的语义反转）:
        `- ``` ` 开栏后缩进不足的同级 `- 内容` 行——围栏行剥空但内容行原样；
      · **零改动**: 合法列表 / thematic break / 无围栏结构。

    **它证明什么**: 上述三分类的逐形态行为。
    **它不证明什么**: 不证明调用方（`_verify_signal_lines` / `_verify_prose_counts`）
    正确使用了它——那是行为门的事；也不穷尽 CommonMark 容器嵌套。
    """
    rs = _load_recap_scan()

    def mid_kept(got: str, src: str) -> bool:
        """围栏行剥空 + **内容行**（第 2 行）原样保留 = sibling 可见正文语义。"""
        g, s = got.split("\n"), src.split("\n")
        return len(g) == len(s) and g[1] == s[1] and not g[0].strip() and not g[2].strip()

    # ── 剥空（真代码内容）──
    for name, src in (
        ("两层引用围栏", "> > ```\n> > x\n> > ```"),
        (
            "列表围栏+缩进内容",
            "> - ```\n>   未答问题年龄：无据（无带时间戳批注）\n>   ```",
        ),
        (
            "无引用列表围栏+缩进内容",
            "- ```\n  未答问题年龄：无据（无带时间戳批注）\n- ```",
        ),
        (
            "有序列表围栏+缩进内容",
            "1. ```\n   > - 来源覆盖率：0/3 成员含来源锚点【实测】\n1. ```",
        ),
        ("普通围栏", "```\n本板共有 987654 个子节点\n```"),
    ):
        got = rs._strip_code_blocks(src)
        # ⚠️ 必须用 split("\n") 不能用 splitlines(): 三行全空时结果是 "\n\n",
        # splitlines() 只给两项——第一次写就踩了，如实留注。
        assert all(not x.strip() for x in got.split("\n")), f"{name} 未整块剥空: {src!r} → {got!r}"

    # ── 保留（sibling marker 行 = 可见正文）──
    for name, src in (
        (
            "引用内 sibling",
            "> - ```\n> - 未答问题年龄：无据（无带时间戳批注）\n> - ```",
        ),
        ("无引用 sibling", "- ```\n- 本板共有 987654 个子节点\n- ```"),
    ):
        got = rs._strip_code_blocks(src)
        assert mid_kept(got, src), f"{name}: 内容行应保留（可见正文）却被剥: {got!r}"

    # ── 零改动 ──
    for name, legit in (
        ("thematic break", "---\n正文\n---"),
        ("合法二级引用列表", "> > - 合法二级引用列表"),
        (
            "合法三级列表",
            "- 一级\n  - 二级\n    - 三级列表（四空格缩进，合法 Markdown）",
        ),
    ):
        assert rs._strip_code_blocks(legit) == legit, f"{name} 被误剥: {legit!r}"
    # 三层引用围栏仍剥空
    p = "> > > "
    got = rs._strip_code_blocks(f"{p}```\n{p}藏起来的正文\n{p}```")
    assert all(not x.strip() for x in got.split("\n")), f"三层引用围栏未剥空: {got!r}"


def test_domain_block_fence_close_must_be_same_char(tmp_path):
    """old-1 承重门: 闭栏的「同字符」条件是承重的（`~~~` 不得关掉 ``` 开的围栏）。

    ⛔ 本卡新发现（不在 goal 点名的三个 survivor 内）: (a) 重放实测，
    单独删掉闭栏的「同字符」判据后全套件 196 passed 无新增红——**它也是 survivor**。
    验收单原写「变异脚本的 survivor-1 已把 E1 两条判据一起禁，现如期变红 2/2」，
    但那条变体是把**同字符 + 长度 + 尾随空白**三条一起禁；
    只禁同字符这一条时套件全绿 ⇒ 那句话比证据宽。

    **它证明什么**: 用 `~~~` 伪闭合一个 ``` 围栏时，其后的信号行仍被当作在块内。
    **它不证明什么**: 不证明 CommonMark 围栏规则被完整实现（长度/缩进/info string
    另有 `test_domain_block_four_fence_short_close` 等门）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    base = run_verify(report)
    assert base.returncode == 0, f"基线报告本身就不过 verifier:\n{base.stdout}"
    before = report.read_text(encoding="utf-8")
    first_sig = next(ln for ln in before.splitlines() if SIGNAL_LABELS[0] in ln)
    after = before.replace(first_sig, "> ```\n> 无关正文\n> ~~~\n" + first_sig, 1)
    assert after != before, "变异未命中：报告一字未改，这条门测的是空气"
    report.write_text(after, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode != 0, f"`~~~` 伪闭合了 ``` 围栏，信号行被当成在场:\n{r.stdout}"
    assert "代码块内出现信号名" in r.stdout or "缺信号行" in r.stdout, f"拦截理由与围栏无关:\n{r.stdout}"


# ── (d) S4: fallback「派生」允许式加一条自由叙述即放宽 ────────────────

D1_NEGATIVES = [
    "备注：SeedA 的派生子女数为 3 个。",
    "注：SeedA 的派生子女数为 3 个。",
    "说明：SeedA 的派生子女数为 3 个。",
    "补充：SeedA 的派生子女数为 3 个。",
    "PS：SeedA 的派生子女数为 3 个。",
    "> 备注：SeedA 的派生子女数为 3 个。",
    "- 备注：SeedA 的派生子女数为 3 个。",
    "SeedA 派生了 3 个子节点。",
]


@pytest.mark.parametrize(
    "bogus",
    D1_NEGATIVES,
    ids=[
        "beizhu",
        "zhu",
        "shuoming",
        "buchong",
        "ps",
        "quote_beizhu",
        "list_beizhu",
        "bare",
    ],
)
def test_domain_block_freeform_derivation_note(tmp_path, bogus):
    """d1 · S4 承重门①「自由叙述行为门」: 模板外的「派生」表述必须被拦。

    survivor 实证: 往允许式里加一条 `^\\s*备注[：:].*派生.*$` 后全套件 196 passed
    无新增红 —— 既有门 `test_verify_derivation_assertion_outside_seed_section`
    只喂**对全部模式都不匹配**的句子，往表里加一条模式除非恰好有测试喂那条模式
    的句子，否则不可见。

    ⚠️ 语料刻意避开 `_D2_CLAIM_RE`（无「本板/全板 + 共有」）与 fallback 禁词表，
    否则拦截会来自别的规则、变异体下仍红 ⇒ 门看着绿其实不承重。

    **它证明什么**: 七种前缀 + 一句裸叙述写进 fallback 报告 ①段时 exit 1，
    且理由是「模板外的『派生』表述」。
    **它不证明什么**: 不证明允许式表本身完备（合法形态另由放行门与 d2 覆盖），
    也不覆盖 manifest 模式（该检查是 fallback 专属）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert scan["data_mode"] == "fallback_local"
    report = write_report(vault, scan)
    base = run_verify(report)
    assert base.returncode == 0, f"基线报告本身就不过 verifier:\n{base.stdout}"
    lines = report.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith("### ① "))
    lines.insert(idx + 1, bogus)
    report.write_text("\n".join(lines), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"模板外派生叙述被放行: {bogus}\n{r.stdout}"
    assert "模板外的『派生』表述" in r.stdout, (
        f"拦截理由不是派生白名单（可能撞上了别的规则，那样这条门就不承重）:\n{r.stdout}"
    )


# SKILL Step 5 模板 / live 真报告里**合法**的「派生」行形态（d2 的正例集）
D2_SKILL_POSITIVES = [
    "> 3 成员（1 种子 + 2 派生，0 占位）/ 3 批注 /",
    "## 台账（种子/派生）",
    "### 派生",
    "> - 无来源结论：1/2 派生角色成员缺来源锚点【文件】",
    "> - 无来源结论：无据（本板无派生角色成员）",
    "> - 关系类型分布：derived_from 1 · extends 1",
    "2. 在原白板选中相关文本 `Cmd+Shift+D` 派生新节点【实测】",
    "2 个派生角色成员缺来源锚点。",
    "方向叙述：来源锚点缺失集中在派生角色成员，关联声明以既有数据为准。",
]


def test_domain_derive_allow_entries_are_grounded(tmp_path):
    """d2 · S4 承重门②「允许式绑定结构门」: 每条允许式都必须有**可验证的依据**。

    d1 拦的是"表外的句子"，d2 拦的是"往表里塞一条没有依据的模式"——
    后者才是 survivor 的实际形态（改的是实现，不是报告）。
    逐条判据:
      · `scan:<路径>` → 该路径必须能在**真实** scan JSON 里解析到；
      · `md:heading`  → 模式必须以 `^#{1,6}` 起（真的是在匹配标题结构）；
      · `skill:action-verb` → 模式必须含 SKILL HARD-CONSTRAINTS 白名单动词之一；
      · `skill:③段固定句式` → 归口 SKILL.md ③段模板/叙述句式；
      · 且**每条**模式至少匹配一条 SKILL 模板正例、且**不匹配** d1 反例集里的任何一行。

    最后一条是关键: 「备注：…派生…」这类自由允许式无论挂什么依据，
    都会因为"匹配到了 d1 反例"而变红。

    **它证明什么**: 表内 8 条允许式各有可解析的依据、都在匹配真实模板形态、
    且没有一条会顺带放行 d1 的越界语料。
    **它不证明什么**: 不证明这 8 条**穷尽**了合法形态（漏一条合法形态表现为误伤，
    由 live/合成真语料放行门守）；`skill:③段固定句式` 的依据是**语义归口**，
    不是与 SKILL.md 的逐字比对（SKILL.md:203 原文无「角色」二字，逐字锁会锁错）。
    """
    rs = _load_recap_scan()
    scan = collect_json(standard_vault(tmp_path))
    table = rs._FALLBACK_DERIVE_ALLOW
    assert len(table) >= 8, f"允许式表条目数异常: {len(table)}"
    for pattern, basis in table:
        if basis.startswith("scan:"):
            node = scan
            for part in basis[len("scan:") :].split("."):
                assert isinstance(node, dict) and part in node, (
                    f"依据 {basis!r} 在真实 scan JSON 里解析不到（到 {part!r} 断链）"
                )
                node = node[part]
        elif basis == "md:heading":
            assert pattern.pattern.startswith("^#{1,6}"), f"依据声明为标题结构，模式却不是标题锚定: {pattern.pattern!r}"
        elif basis == "skill:action-verb":
            # ⚠️ 白名单动词在模式里是**正则转义**过的（`Cmd\+Shift\+D`），
            # 裸子串比对会恒假 —— 这条断言第一次写就因此变红，如实留注。
            assert any(v in pattern.pattern or re.escape(v) in pattern.pattern for v in rs._VERIFY_ACTION_VERBS), (
                f"依据声明为 SKILL 白名单动词，模式里却没有任何白名单动词: {pattern.pattern!r}"
            )
        elif basis == "skill:③段固定句式":
            assert "派生角色成员" in pattern.pattern, (
                f"依据声明为 ③段固定句式，模式却不含该句式的锚: {pattern.pattern!r}"
            )
        else:
            pytest.fail(f"未知依据类型 {basis!r} —— 新增允许式必须带可验证依据")
        assert any(pattern.match(p) for p in D2_SKILL_POSITIVES), (
            f"允许式 {pattern.pattern!r} 匹配不到任何 SKILL 模板正例（它在放行什么？）"
        )
        for neg in D1_NEGATIVES:
            assert not pattern.match(neg), f"允许式 {pattern.pattern!r}（依据 {basis}）放行了越界语料: {neg!r}"


def test_domain_derive_allow_covers_every_skill_positive(tmp_path):
    """d2 反向锁: 每条 SKILL 模板正例都必须被表里**某条**允许式放行。

    只验"允许式不放行反例"会让"把表删空"通过（空表不放行任何反例）。
    这条从另一侧钉住: 表不能收窄到打到合法模板。
    """
    rs = _load_recap_scan()
    for pos in D2_SKILL_POSITIVES:
        assert any(p.match(pos) for p, _ in rs._FALLBACK_DERIVE_ALLOW), (
            f"SKILL 模板正例被允许式表整体拒绝（误伤）: {pos!r}"
        )


@pytest.mark.parametrize(
    "bogus",
    [
        "派生角色成员的子女数为 987654 个。",
        "3 个派生角色成员的子女数合计 987654 个。",
        "本轮优化集中在派生角色成员的 987654 个子女上。",
    ],
    ids=["free_tail", "leading_count_free_tail", "jizhong_free_tail"],
)
def test_domain_block_derive_clause_free_tail(tmp_path, bogus):
    """D3 裁决（⑦ 自由段收紧）: 「派生角色成员」句式的自由尾段不得夹带子女数。

    ⛔ (a) 重放实测的**同族缺口**（不在三个 survivor 内）: ⑦ 原式
    `^[>\\s]*(?:\\d+\\s*个)?派生角色成员[^。\\n]*。?\\s*$` 的 `[^。\\n]*` 自由段
    让「派生角色成员的子女数为 987654 个。」在**原版**上 exit 0。
    收紧口径以 SKILL.md:267 信号行模板（`<value>/<denominator> 派生角色成员缺来源锚点`）
    + :203 叙述句式（原文「N 个派生成员缺来源锚点」，无「角色」二字——
    同步锁比**匹配语义**不比字面）为准: 谓语固定为「缺来源锚点」，尾段禁裸数字。

    **它证明什么**: 三种自由尾段形态现在 exit 1 且理由是派生白名单。
    **它不证明什么**: 不证明 fallback 下所有伪计数都被拦（D2 只管自称全板规模的句式，
    D1 只管模板行；两者未覆盖的位置仍留给人工判读——这是如实登记的边界）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert scan["data_mode"] == "fallback_local"
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith("### ③ "))
    lines.insert(idx + 1, bogus)
    report.write_text("\n".join(lines), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"⑦ 自由尾段仍放行: {bogus}\n{r.stdout}"
    assert "模板外的『派生』表述" in r.stdout, f"拦截理由不是派生白名单:\n{r.stdout}"


# ── (e) 「口径一致」封闭注记槽（第七批 §三 B-1 建议甲，默认执行、待用户裁决） ──


def _tail_note_line(text: str, label: str, note_form: str) -> tuple[str, str]:
    """把 label 信号行的档位标注前插入注记，返回 (原行, 新行)。"""
    line = _sig_line(text, label)
    return line, line.replace("【", note_form + "【", 1)


@pytest.mark.parametrize(
    "label,note_form",
    [
        ("来源覆盖率", "口径一致"),
        ("来源覆盖率", " · 口径一致"),
        ("无来源结论", "口径一致"),
    ],
    ids=["coverage_adjacent", "coverage_middot", "unsourced_adjacent"],
)
def test_domain_allow_signal_tail_note(tmp_path, label, note_form):
    """e1 放行门: 信号行尾部的**封闭表**注记「口径一致」必须放行。

    ⛔ 这是 goal 点名、round-5/6 一直挂着的输入。开工前实测（存档
    `evidence/e1-pre-implementation-red.txt`）: 紧接式与 ` · ` 分隔式**均 exit 1**
    （理由「未整行匹配标准式」）⇒ 本门先红后绿成立。

    处置口径 = 第七批复核裁定 §三 **B-1 建议甲（放宽规则）**，
    ⚠️ 与本卡上一版验收单裁决点 1 的甲/乙标签**相反**（那里甲 = 不许附注）：
    实现的是**封闭表注记槽**（`_SIGNAL_TAIL_NOTES`），不是自由文本槽——
    自由槽等于把 H-3 那条黑名单老路重开一遍。**仍待你裁决**。

    **它证明什么**: 表内短语在两种分隔形态下、在 X/N 型信号行上放行且整篇 VERIFY PASS。
    **它不证明什么**: 不证明"任意附注"放行（e2 反向锁），也不证明无据行可带附注
    （无据行不适用本槽，e2 末条锁）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    base = run_verify(report)
    assert base.returncode == 0, f"基线报告本身就不过 verifier:\n{base.stdout}"
    text = report.read_text(encoding="utf-8")
    old, new = _tail_note_line(text, label, note_form)
    assert new != old, "构造未命中，这条门测的是空气"
    report.write_text(text.replace(old, new, 1), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 0, f"封闭表注记被误伤 ({label}/{note_form!r}):\n{r.stdout}"
    assert "VERIFY PASS" in r.stdout


@pytest.mark.parametrize(
    "note_form",
    [
        "口径一致另有仨条",
        "另有仨条口径一致",
        "口径一致 2/3",
        "口径一致/3",
        "口径一致口径一致",
        "口径不一致",
    ],
    ids=[
        "note_then_smuggle",
        "smuggle_then_note",
        "note_then_pair",
        "note_then_slash",
        "note_twice",
        "not_in_table",
    ],
)
def test_domain_block_signal_tail_note_outside_table(tmp_path, note_form):
    """e2 拦截门: 注记槽是**封闭表**，不是自由文本槽。

    ⛔ 槽一旦写成 `[^【】]*` 之类的自由式，H-3 那条"先开放再排除"的黑名单老路
    立刻复活（「另有仨条」正是当年绕过的原话）。本门逐条钉死:
    表内短语的前后都不许夹带、不许重复、近似词（`口径不一致`）不算。

    **它证明什么**: 六种夹带/近似形态一律 exit 1 且理由是"未整行匹配标准式"。
    **它不证明什么**: 不证明穷尽了所有夹带写法（表外是无限集），
    只证明槽的**封闭性**在这六个代表形态上成立。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    old, new = _tail_note_line(text, "来源覆盖率", note_form)
    assert new != old, "构造未命中，这条门测的是空气"
    report.write_text(text.replace(old, new, 1), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"表外注记被放行: {note_form!r}\n{r.stdout}"
    assert "未整行匹配标准式" in r.stdout, f"拦截理由异常:\n{r.stdout}"
    assert "VERIFY PASS" not in r.stdout


def test_domain_block_nodata_line_takes_no_tail_note(tmp_path):
    """e2 补充: **无据行**不适用注记槽（它另有整行固定模板）。"""
    vault = build_vault(tmp_path, ["SeedA", "DerivedB"])
    write_node(vault, "SeedA")
    write_node(vault, "DerivedB", derived_from="[[SeedA]]")
    scan = collect_json(vault)
    assert scan["signals"]["duplicate_accumulation"]["availability"] == "无据"
    report = write_report(vault, scan)
    text = report.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "重复堆积" in ln)
    report.write_text(text.replace(line, line + "口径一致", 1), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"无据行带了注记却被放行:\n{r.stdout}"
    assert "无据行未整行匹配标准式" in r.stdout


def test_domain_skill_sync_signal_tail_notes_table():
    """e3 表锁: `_SIGNAL_TAIL_NOTES` 与 SKILL.md ③段铁律的附注表必须全等 + 篡改门。

    **它证明什么**: 代码侧注记表与文档侧逐字同序一致，单侧改动即红。
    **它不证明什么**: 不证明表内短语在运行时真的放行（e1）或表外真的被拦（e2）。
    """
    rs = _load_recap_scan()
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    parsed = _parse_skill_tail_notes(skill_text)
    assert parsed, "SKILL.md 里解析不到信号行附注表"
    assert tuple(parsed) == rs._SIGNAL_TAIL_NOTES, (
        f"代码与 SKILL.md 的附注表不同步:\n  代码 = {rs._SIGNAL_TAIL_NOTES}\n  SKILL = {tuple(parsed)}"
    )
    note_line = next(
        ln for ln in skill_text[skill_text.find("附注只许") :].splitlines()[1:] if re.findall(r"`([^`\n]+)`", ln)
    )
    for name, bad_line in {
        "多一项": note_line.replace("`口径一致`", "`口径一致` / `另有仨条`", 1),
        "改文案": note_line.replace("`口径一致`", "`口径不一致`", 1),
    }.items():
        bad = skill_text.replace(note_line, bad_line, 1)
        assert bad != skill_text, f"{name}: 篡改未命中，这条篡改门测的是空气"
        assert tuple(_parse_skill_tail_notes(bad)) != rs._SIGNAL_TAIL_NOTES, (
            f"{name} 后附注表同步锁仍判「一致」—— 该锁不承重"
        )


def test_domain_allow_note_as_independent_line(tmp_path):
    """e4 现状锁: 「口径一致」写成**下一条独立叙述行**始终放行（round-1 Codex 的建议形态）。

    开工前实测 exit 0；本门把它钉住，防止注记槽上线后反而把这条路堵死。
    """
    r = _mutate_report(
        tmp_path,
        lambda text, scan: text.replace("\n方向叙述：", "\n\n口径一致。\n\n方向叙述：", 1),
    )
    assert r.returncode == 0, f"独立叙述行形态被误伤:\n{r.stdout}"


# ── (f) 含 signals 的真语料放行门（第七批 §三 B-3 建议「补」，默认执行） ──

SYNTH_FIXTURES = Path(__file__).parent / "fixtures" / "recap_synthetic_signals"
SYNTH_REPORT = "回顾-CS 61B-2026-09-01.md"


def _synth_workdir(tmp_path: Path) -> Path:
    work = tmp_path / "outputs"
    work.mkdir(parents=True)
    for src in SYNTH_FIXTURES.iterdir():
        shutil.copy2(src, work / src.name)
    return work


def test_synthetic_signals_report_passes(tmp_path):
    """(f) 放行门: **含 signals 的真 scan** 渲染出的整篇报告必须 exit 0。

    ⛔ 证据边界（Codex round-1 MEDIUM 的直接整改）: 四份 live 真报告的 scan
    **都没有 `signals` 键**，生产代码会整块跳过信号行校验 ⇒ 它们能证明
    「D1/D2 不误伤真语料」，**不能**证明「信号行固定尾部不误伤」。

    本 fixture 的诚实口径 = **scan 真、③段渲染**（⛔ 不是「live 真报告」）:
      · scan JSON 是 live vault `CS 61B` 板的**只读** collect 真产物
        （执行前后 live outputs 8 份 shasum+mtime 逐字相同，证据在验收单）；
      · 报告③段的四条信号行按 SKILL.md Step 5 模板逐字渲染，
        其余散文取自 live 2026-08-27 真报告并按 fallback 口径去掉 manifest 专属陈述。
    ⚠️ synthetic 标记落在**目录名**上而非文件名: verifier 强制
    「文件名解析出的板名 == frontmatter board」，文件名带后缀会被判
    「绑定另一块板的 scan JSON」（实测）。

    **它证明什么**: 真 scan 的四条信号行（含一条无据行）在整篇报告里不被误伤。
    **它不证明什么**: 不证明这份报告是 LLM 真实产出的（③段是我按模板渲染的），
    也没有 live 侧的逐字节哈希门（scan 随时间变，钉不住）。
    """
    work = _synth_workdir(tmp_path)
    scan = json.loads((work / ".recap-scan-CS 61B.json").read_text(encoding="utf-8"))
    assert "signals" in scan, "fixture 的 scan 没有 signals 键，这条门测的是空气"
    assert scan["signals"]["source_coverage"]["availability"] != "无据", (
        "fixture 的信号全是无据档，证明不了 X/N 型固定尾部不误伤"
    )
    r = run_verify(work / SYNTH_REPORT)
    assert r.returncode == 0, f"含 signals 的真语料被误伤:\n{r.stdout}"
    assert "VERIFY PASS" in r.stdout


@pytest.mark.parametrize(
    "old,new",
    [
        ("最老 21 天", "最老 22 天"),
        ("参与统计 3 条", "参与统计 4 条"),
        ("p25/p50/p75 = 20/21/21 天", "p25/p50/p75 = 20/21/99 天"),
        ("0/2 成员含来源锚点", "1/2 成员含来源锚点"),
        ("0/3 条批注为重复条目", "1/3 条批注为重复条目"),
        (
            "无来源结论：无据（本板无派生角色成员）",
            "无来源结论：0/2 派生角色成员缺来源锚点【文件】",
        ),
    ],
    ids=[
        "age_value",
        "age_denom",
        "percentile",
        "coverage_value",
        "duplicate_value",
        "nodata_to_measured",
    ],
)
def test_synthetic_signals_tamper_fails(tmp_path, old, new):
    """(f) 篡改门（与放行门同权重）: 真语料**被篡改后**必须 FAIL。

    ⛔ Codex round-1 BLOCKER-3 的教训: 放行门只证明了「真报告 PASS」，
    **没有证明「真报告被篡改后 FAIL」**——正例过了就以为门在工作，是假绿的经典形态。
    六条各打一个信号字段（含把无据行改写成有数行）。
    """
    work = _synth_workdir(tmp_path)
    rp = work / SYNTH_REPORT
    before = rp.read_text(encoding="utf-8")
    after = before.replace(old, new, 1)
    assert after != before, f"篡改未命中「{old}」，这条门测的是空气"
    rp.write_text(after, encoding="utf-8")
    r = run_verify(rp)
    assert r.returncode == 1, f"信号数字被改却仍 PASS: {old} → {new}\n{r.stdout}"


# ── round-3 整改门（Codex round-3: BLOCKER-1/2 + HIGH-3/4/5/6；先红证据
#    evidence-maintb-r2/round3-repro.txt 与 round3-v2-probe4.txt）──────────


def test_domain_r3_eof_unclosed_fence_signal_caught(tmp_path):
    """HIGH-3: EOF 未闭合围栏的伪信号行必须被「代码块内出现信号名」逮住。

    原实现用 zip() 对齐原文/剥后文本——EOF 未闭合围栏把尾部剥空后 splitlines()
    行数差让最后一行原文不参与比较，伪信号逃过检查（实测 exit 0）。
    修复 = zip_longest 对齐。
    """
    r = _mutate_report(
        tmp_path,
        lambda t, s: t + "\n```\n> - 来源覆盖率：9/9 成员含来源锚点【实测】\n",
    )
    assert r.returncode != 0, f"EOF 未闭合围栏伪信号被放行:\n{r.stdout}"
    assert "代码块内出现信号名" in r.stdout, f"拦截理由异常:\n{r.stdout}"


def test_domain_r3_nodata_signal_line_only_in_section3(tmp_path):
    """HIGH-4: 「无来源结论」信号行只许出现在③段（附录同形行必拦）。

    fallback 措辞白名单 (#3/#4) 作用于全文——③段外的同形行不受信号绑定保护，
    实测附录 `987654/2` 伪信号与矛盾无据行都 VERIFY PASS。
    修复 = _verify_fallback_derive_numbers 限定 ③ 段。
    """
    for name, extra in (
        (
            "伪有数信号",
            "\n## 附录\n\n- 无来源结论：987654/2 派生角色成员缺来源锚点【实测】\n",
        ),
        ("矛盾无据信号", "\n## 附录\n\n> - 无来源结论：无据（分母为零）\n"),
    ):
        r = _mutate_report(tmp_path / name, lambda t, s, e=extra: t + e)
        assert r.returncode != 0, f"{name}: ③段外无来源结论行被放行:\n{r.stdout}"
        assert "只许出现在③段" in r.stdout, f"{name}: 拦截理由异常:\n{r.stdout}"


@pytest.mark.parametrize(
    "name,inject",
    [
        ("fullwidth_tail", "2 个派生角色成员缺来源锚点，另有９８７６５４个。"),
        ("cjk_tail", "2 个派生角色成员缺来源锚点，另有九十八万个。"),
        ("arbitrary_prefix", "9 个派生角色成员缺来源锚点。"),
    ],
    ids=["fullwidth_tail", "cjk_tail", "arbitrary_prefix"],
)
def test_domain_r3_derive_clause_numbers_bound(tmp_path, name, inject):
    """HIGH-5: 「派生角色成员缺来源锚点」句式的数字必须受控。

    · 前置 N 必须全等 signals.unsourced_conclusions.value（standard_vault 真值 0）；
    · 尾段数字禁令从 ASCII 扩到全角 + 中文数词（原 `[^。\\n0-9]*` 放行
      `９８７６５４` / `九十八万`）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert scan["data_mode"] == "fallback_local"
    assert scan["signals"]["unsourced_conclusions"]["value"] == 0, "fixture 真值变化，先改此门"
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith("### ③ "))
    lines.insert(idx + 1, inject)
    report.write_text("\n".join(lines), encoding="utf-8")
    r = run_verify(report)
    assert r.returncode == 1, f"{name}: 越界数字叙述被放行:\n{r.stdout}"
    assert "派生角色成员" in r.stdout or "模板外的『派生』表述" in r.stdout, f"{name}: 拦截理由异常:\n{r.stdout}"


def test_domain_r3_derive_allow_numbers_in_pool(tmp_path):
    """HIGH-6: fallback 允许式放行的行，行内数字必须在 scan 数值池。

    · `#### 派生子女 987654 个的说明`（四级标题，不截断③段）曾放行；
    · `- 关系类型分布：无 987654` 曾放行。
    反向: 无数字的合法标题/关系行、报告主标题年份不受牵连。
    """
    for name, inject, want in (
        ("标题夹伪计数", "\n#### 派生子女 987654 个的说明\n", 1),
        ("关系行夹伪计数", "\n- 关系类型分布：无 987654\n", 1),
        ("合法关系行无数字", "\n- 关系类型分布：无\n", 0),
    ):
        r = _mutate_report(
            tmp_path / name,
            lambda t, s, e=inject: t.replace("方向叙述：", f"{e}\n方向叙述：", 1) if e else t,
        )
        if want == 1:
            assert r.returncode != 0, f"{name}: 无出处数字被放行:\n{r.stdout}"
            assert "无出处" in r.stdout, f"{name}: 拦截理由异常:\n{r.stdout}"
        else:
            assert r.returncode == 0, f"{name}: 合法行被误伤:\n{r.stdout}"
    # 主标题年份不误伤（`# 回顾 · 板 · 2026-09-01` 不含「派生」，不在检查范围）
    # ——由上面「合法关系行无数字」与全套件的放行门共同覆盖；不单列空变异 case
    # （_mutate_report 的防空气断言会拒绝不改内容的变异）。


# ── round-4 整改门（Codex round-4 被 cyber 过滤器截断，无终裁；其 stderr
#    抢救探针 A/B/C 三缝隙由车道独立复现实锤后整改。先红证据
#    evidence-maintb-r2/round4-repro.txt，整改后 round4-after2.txt）──────────


def test_domain_r4_leading_space_blockquote_list_fence(tmp_path):
    """round-4 A: 前导空格的引用内列表围栏（` > - ``` `）藏信号必须拦。

    `_quote_width` 原来只从 `>` 起算——引用标记**前**的前导空白不计入时，
    内容列被算大，` >   信号行` 被误判「缩进不足→容器结束→可见正文」而放行；
    markdown-it 确认该形态渲染在 `<pre><code>` 内（Codex round-4 stderr 实证）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    lines = report.read_text(encoding="utf-8").splitlines()
    idx = [i for i, ln in enumerate(lines) if any(lb in ln for lb in SIGNAL_LABELS)]
    core = [lines[i].lstrip("> ").lstrip("- ").strip() for i in range(idx[0], idx[-1] + 1)]
    body = [" > - ```"] + [" >   " + x for x in core] + [" >   ```"]
    out = lines[: idx[0]] + body + lines[idx[-1] + 1 :]
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    r = run_verify(report)
    assert r.returncode != 0, f"前导空格引用内列表围栏藏信号被放行:\n{r.stdout}"
    assert "代码块内出现信号名" in r.stdout or "缺信号行" in r.stdout


def test_domain_r4_manifest_appendix_signal_in_section3_only(tmp_path):
    """round-4 B: 「无来源结论」限定③段对 **manifest 模式**同样生效。

    HIGH-4 的限定原本只挂在 fallback 分支——manifest 报告的附录伪信号
    `987654/2 派生角色成员缺来源锚点` 实测放行（Codex round-4 探针 B）。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault, "--manifest", str(make_manifest(vault)))
    assert scan["data_mode"] == "manifest"
    report = write_report(vault, scan)
    with report.open("a", encoding="utf-8") as f:
        f.write("\n## 附录\n\n- 无来源结论：987654/2 派生角色成员缺来源锚点【实测】\n")
    r = run_verify(report)
    assert r.returncode != 0, f"manifest 附录伪信号被放行:\n{r.stdout}"
    assert "只许出现在③段" in r.stdout


def test_domain_r4_derive_allow_cjk_numbers_in_pool(tmp_path):
    """round-4 C: 允许式行内的**中文数词**也必须入池比对。

    `#### 派生子女 九十八万个 的说明`——`\\d+` 抓不到中文数字，实测放行
    （Codex round-4 探针 C）。
    ⛔ round-5 定向复核 HIGH 整改: 多字数词**不再交给 _cjk_to_int**——提取
    字符集与映射表同集导致「解析失败」分支静态不可达，且连续数字字只留末位
    （「五四」得 4）可能按错值查池。现只认**单字**数词（值=映射，绝对确定），
    多字串一律「无法验证」fail-closed（模板/合成语料无多字合法用例，零误伤）。
    """
    # 多字数词 → 无法验证（round-5 HIGH 锁: 不许按错值查池后放行）
    for name, inject in (
        ("九十八万", "\n#### 派生子女 九十八万个 的说明\n"),
        ("五四_末位陷阱", "\n#### 派生子女 五四 个 的说明\n"),
    ):
        r = _mutate_report(
            tmp_path / name,
            lambda t, s, e=inject: t.replace("方向叙述：", f"{e}\n方向叙述：", 1),
        )
        assert r.returncode != 0, f"{name}: 中文数词绕过被放行:\n{r.stdout}"
        assert "无法验证" in r.stdout, f"{name}: 应走「无法验证」fail-closed（不许按解析值查池）:\n{r.stdout}"


# ══════════ CARD-维护B-R3 · 中文数词终态冻结（BATCH-2026-09-01-第九批） ══════════
# round-5 定向复核 HIGH（属实）: 「解析失败 fail-closed」分支**静态不可达**
# （提取字符集 == `_CJK_NUM ∪ _CJK_UNIT`，任何非空匹配必返回某个整数），且连续
# 数字字不校验文法、只反复覆盖 `digit` ⇒ 按**局部值**查池。
# c754b043 只在 fallback 允许式一侧改成「只认单字」；**D2 叙述段仍在调**多位
# 解析器 `_cjk_to_int` —— R3 开工在标准 fixture 上实测红证据:
#   `- 本板共有一零个子节点。【实测】` → exit **0 放行**
#   （`_cjk_to_int("一零") == 0`，而 0 恒在池内 `abs(a-a)`）⇒ 纯虚构的规模自陈
#   整域免检。证据: _bmad-output/审查/evidence-maintb-r3/b-prefix-red-repro.txt
# R3 终态（冻结，不得再引入多位解析器）: `_cjk_to_int` 整体退役，两处消费点共用
# `_cjk_single_to_int`（只认单字，值 = 映射，绝对确定）。


def test_domain_r5_cjk_single_char_only_unit_contract():
    """R3 判据契约: 只认单字数词；多字 / 单字量词 / 集合外一律 None。

    **它证明什么**: 判据函数本身的逐形态取值；提取字符类由 `_CJK_NUM ∪ _CJK_UNIT`
    **机械派生**（手抄两份字面量正是 D2 与 fallback 两侧此前分叉的成因）；
    多位解析器 `_cjk_to_int` 确已退役、不得复活。
    **它不证明什么**: 不证明调用方正确使用了它——那是下面三道门的事。
    """
    rs = _load_recap_scan()

    assert not hasattr(rs, "_cjk_to_int"), "多位中文数词解析器复活了——R3 冻结口径禁止重新引入（round-5 HIGH 的根因）"
    # ⛔ 期望值必须有**独立来源**: 第一版写成 `for ch, want in rs._CJK_NUM.items()`
    # ——期望值与被测值取自同一张表，把 `零/〇` 的映射改成 7 全套件照样 253 全绿
    # （车道对抗审查实测）。自抄期望 = 自证恒真 = 假门。这里逐字写死。
    EXPECT = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000, "亿": 100000000}
    assert rs._CJK_NUM == EXPECT, f"单字数词表被改动: {rs._CJK_NUM}"
    assert rs._CJK_UNIT == UNITS, f"量词表被改动: {rs._CJK_UNIT}"
    for ch, want in EXPECT.items():
        assert rs._cjk_single_to_int(ch) == want, f"单字数词 {ch} 取值错"
    for ch in UNITS:  # 十百千万亿 不在 _CJK_NUM ⇒ 单字量词同样无法确定
        assert rs._cjk_single_to_int(ch) is None, f"单字量词 {ch} 必须 fail-closed"
    for s in ("一零", "五四", "九十八万", "零一", "十二", "两三", "", "甲", "五个"):
        assert rs._cjk_single_to_int(s) is None, f"{s!r} 必须判「无法确定」（不猜）"

    # 提取面必须覆盖判据面: **抓得到才拒得掉**。提取面漏字 ⇒ 该字组成的串落到
    # 检查面之外 = 漏拦（不是 fail-closed）。
    assert set(rs._CJK_NUM_CHARS) == set(EXPECT) | set(UNITS)
    # ⛔ R3 round-3: 取数用的是**宽集合**（数词样字符），它只用于**定界**、不赋值。
    # 表外数词字（廿卅/大写金融数字）必须进得来——进不来 ⇒ `廿五个` 会从 `五`
    # 重锚按 5 查池而放行（Codex round-2 HIGH，车道实测 rc=0）。
    # ⛔ 精确相等而非子集包含（Codex round-3 属实指出：子集断言锁不住声明里的
    # `卌` 与各种异体，表少一个字就意味着那类写法会从尾片重锚）。
    assert set(rs._NUMERAL_LIKE_CHARS) == (
        set(rs._CJK_NUM_CHARS)
        | set("0123456789")
        | set(
            "廿卅卌壹贰貳叁參参肆伍陆陸柒捌玖拾佰仟萬亿億两兩兆京垓秭穰仨俩①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳〡〢〣〤〥〦〧〨〩〸〹〺"
        )
    ), f"定界集漂移: {rs._NUMERAL_LIKE_CHARS}"
    # 宽集合只定界不赋值：表外字符进来只会让整串"无法确定"，不会被猜成某个数。
    for s in ("廿五", "壹佰", "九十八万5", "五四", "一零"):
        assert rs._count_token_value(s) is None, f"{s!r} 不得被赋值"
    for s, want in (("980005", 980005), ("016", 16), ("五", 5), ("0", 0)):
        assert rs._count_token_value(s) == want, f"{s!r} 取值错"
    m = rs._NUM_RUN_RE.match("九十八万")
    assert m and m.group(0) == "九十八万", "提取面抓不到连续多字串 = 漏拦"
    # ⛔ 且必须**跨排版噪声/不可见字符**整体抓 —— 断开就只剩尾片，判据再「绝对
    # 确定」也没用（拿到的 token 不是那句话里的数）。这一条是 R3 round-2 的
    # BLOCKER：`九十八万**五**个` 渲染出来就是「九十八万五个」，实测曾 exit 0。
    for name, s in (
        ("粗体", "九十八万**五"),
        ("空白", "九十八万 五"),
        ("nbsp", "九十八万&nbsp;五"),
        ("零宽", "九十八万\u200b五"),
        ("空标签", "九十八万<span></span>五"),
        ("HTML注释", "九十八万<!--x-->五"),
    ):
        m = rs._NUM_RUN_RE.match(s)
        assert m and m.group(0) == s, f"{name}切断: 提取面只抓到 {m and m.group(0)!r}"
        assert rs._join_free(m.group(0)) == "九十八万五", f"{name}: 剥噪声后不是原数"
        assert rs._cjk_single_to_int(rs._join_free(m.group(0))) is None


def test_domain_r5_derive_allow_single_char_value_enters_pool():
    """R3 单元门: 单字数词必须**带着自己的值**进池比对；多字不得按局部值查池。

    ⚠️ 为什么用合成 scan 而不是标准 fixture: 标准 fixture 的数值池是 `[0..16, 22]`，
    **覆盖了 `_CJK_NUM` 的全部值（0-9）** ⇒ CLI 层根本构造不出「单字且值不在池」
    的用例，只写 `五` 放行会退化成**空洞证明**（没查池也 rc=0）。合成 scan 把池
    收窄到 `[0,1,2]`，`九` 才能证明 9 确实进了池比对。合成语料非 live 正文。

    **它证明什么**: 单字 → 按自身值查池（九→`行内数字 9 无出处` / 二→放行）；
    多字 → 走「无法验证」且**不产生任何按局部值的池诊断**（`一零` 的 0、
    `五四` 的 4、`九十八万` 的 980000 都不得出现在诊断里）。
    **它不证明什么**: 不证明整条 verifier 的段切分与白名单匹配——那是 CLI 门的事。
    """
    rs = _load_recap_scan()
    synth = {"data_mode": "fallback_local", "counts": {"members": 1, "seeds": 1}}
    pool = rs._derived_number_pool(synth)
    assert pool == {0, 1, 2}, f"合成池漂移，判别前提失效: {sorted(pool)}"

    def probs_for(tok: str) -> list[str]:
        out: list[str] = []
        rs._verify_fallback_derive_numbers(f"#### 派生子女 {tok} 个 的说明\n", synth, out)
        return out

    assert any("行内数字 9 无出处" in p for p in probs_for("九")), "单字未按自身值查池"
    assert probs_for("二") == [], "值在池的单字被误伤"
    for tok, leaked in (("一零", "0"), ("五四", "4"), ("九十八万", "980000")):
        got = probs_for(tok)
        assert any("无法验证" in p for p in got), f"{tok}: 多字未 fail-closed: {got}"
        assert not any("无出处" in p for p in got), f"{tok}: 仍按局部值查池: {got}"
        assert not any(leaked in p for p in got), f"{tok}: 诊断里泄出解析值 {leaked}: {got}"


def test_domain_r5_derive_allow_cjk_pool_collision_cli(tmp_path):
    """R3 行为门①: fallback 允许式行内多字数词一律 fail-closed，单字不误伤。

    **它证明什么**: 走完整 CLI（`--verify`）时，`一零`/`五四`（局部值**实测在池**，
    即碰撞前提成立）与 `九十八万`/`十` 全部 exit 1 且诊断为「无法验证」，
    诊断里不出现任何池比对结论；值在池的单字 `五` 放行。
    **它不证明什么**: 不证明「单字带自身值查池」——本 fixture 池覆盖 0-9，
    该性质由 test_domain_r5_derive_allow_single_char_value_enters_pool 证明。
    """
    rs = _load_recap_scan()
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    pool = rs._derived_number_pool(scan)
    # ⛔ 碰撞前提必须**实测**: 局部值真的在池里，这条门才是在测「按错值查池会放行」；
    # 前提不成立时它只是在测别的东西（MEMORY `reference_gate_design_pitfalls`）。
    assert {0, 4, 5} <= pool, f"碰撞前提失效（局部值不在池）: {sorted(pool)}"
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify_with(tok: str):
        text = base_text.replace("方向叙述：", f"\n#### 派生子女 {tok} 个 的说明\n\n方向叙述：", 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    for tok in ("一零", "五四", "九十八万", "十"):
        r = verify_with(tok)
        assert r.returncode != 0, f"{tok}: 中文数词绕过被放行:\n{r.stdout}"
        assert "无法验证" in r.stdout, f"{tok}: 应走「无法验证」fail-closed:\n{r.stdout}"
        assert "无出处" not in r.stdout, f"{tok}: 仍按局部/末位值查池:\n{r.stdout}"
    r = verify_with("五")
    assert r.returncode == 0, f"值在池的单字数词被误伤:\n{r.stdout}"


def test_domain_r5_prose_cjk_multichar_fail_closed_cli(tmp_path):
    """R3 行为门②: D2 叙述段的多字中文数词计数同样 fail-closed。

    ⛔ 这是 R3 开工实测的**漏拦**（不是假想）: c754b043 只封了 fallback 一侧，
    `- 本板共有一零个子节点。【实测】` 在开工 HEAD `c754b043` 上 **exit 0 放行**
    （`_cjk_to_int("一零") == 0`，0 恒在池内）。红证据:
    `_bmad-output/审查/evidence-maintb-r3/b-prefix-red-repro.txt`。

    **它证明什么**: 该形态现在 exit 1、诊断为「无法解析」，且不再产生按局部值的
    池比对结论；值在池的单字自陈（`共有五个`）不误伤。
    **它不证明什么**: 不证明 D2 对**所有**数字形态的绑定力——池碰撞判据的固有
    边界见 test_domain_block_bare_count_in_prose 的说明，本卡未改变它。
    """

    def prose_case(tok: str):
        def m(text, scan):
            return text.replace("## 三维审查", f"## 三维审查\n\n- 本板共有{tok}个子节点。【实测】", 1)

        return m

    for tok in ("一零", "五四", "九十八万", "十"):
        r = _mutate_report(tmp_path / f"d2-{tok}", prose_case(tok))
        assert r.returncode != 0, f"{tok}: D2 段多字数词自陈被放行:\n{r.stdout}"
        assert "无法解析" in r.stdout, f"{tok}: 应走「无法解析」fail-closed:\n{r.stdout}"
        assert "找不到同值来源" not in r.stdout, f"{tok}: 仍按局部值查池:\n{r.stdout}"
    r = _mutate_report(tmp_path / "d2-五", prose_case("五"))
    assert r.returncode == 0, f"值在池的单字自陈被误伤:\n{r.stdout}"


# ── R3 round-2：车道对抗审查（5 镜头 17 agent）确认的 1 BLOCKER + 4 HIGH ──────
# 全部同一根因：**提取面**在排版噪声/不可见字符处断开，匹配重锚到紧邻量词的尾片，
# 于是「判据绝对确定」变得无关紧要——判据拿到的 token 不是那句话里的数。
# ⛔ 归因如实：该性质在开工 HEAD `c754b043` 上**同样存在**（验证者用 git show 重放
# 实证），**不是 R3 引入的回归**；但 R3 的门与 docstring 宣称「多字中文数词一律
# fail-closed」，被一个 `**` 击穿 = 声明比证据宽，按本仓口径算真缺陷，必须闭合。


def test_domain_r5_noise_split_number_run_cli(tmp_path):
    """R3 round-2 行为门：排版噪声/不可见字符**不得**成为数串的断点。

    `- 本板共有九十八万**五**个子节点。【实测】` 在 Obsidian 里渲染成
    「本板共有九十八万五个子节点」（粗体的五），而验证器原先只抓到尾片 `五`，
    `_cjk_single_to_int('五')==5` 且 5 在池内 ⇒ 纯虚构的 980005 **exit 0 放行**。
    ASCII 侧同形：`980 005个`（空格千分位）只查到 `005`。

    **它证明什么**：数串跨连接字符（排版标记 / `&nbsp;` / 空白 / 短 HTML 标签与
    注释 / 零宽与双向控制）整体抓取并剥噪声后再判 —— D2 侧覆盖 CJK 与 ASCII，
    fallback 侧本门只覆盖 CJK；合法的单字/池内数值不受影响。
    ⚠️ 措辞收窄（Codex round-2 属实指出）：本门原写「CJK 与 ASCII × D2 与
    fallback 全覆盖」，但矩阵里 fallback 只喂了 CJK——而当时 fallback 的 ASCII
    侧**确实还是** ``re.findall(r"\\d+")`` 的碎片取数。该缺口由
    `test_domain_r6_cross_class_and_offtable_numeral_cli` 闭合并配门。
    **它不证明什么**：连接集是**封闭表**（与量词表同口径）。表外字符仍能切断数串
    （`九十八万x五个` / `九十八万、五个` / `[[x|]]` 的残留 `|]]`）——那些断点
    **渲染后可见**，读者不会读成一个连续的数；表外的**不可见**载体（如超长 HTML
    注释）是真残余，登记在验收单 §五之三，本门不宣称覆盖。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    pool = _load_recap_scan()._derived_number_pool(scan)
    # 前提实测：尾片值必须真的在池里，这条门才是在测「按尾片查池会放行」。
    assert {0, 4, 5} <= pool, f"前提失效（尾片值不在池）: {sorted(pool)}"
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify(anchor: str, injected: str):
        text = base_text.replace(anchor, injected, 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    def d2(line: str):
        return verify("## 三维审查", f"## 三维审查\n\n{line}")

    # ── 拦截面：渲染后连续、源码被切断 ──
    for name, line in (
        ("粗体", "- 本板共有九十八万**五**个子节点。【实测】"),
        ("空白", "- 本板共有九十八万 五个子节点。【实测】"),
        ("nbsp", "- 本板共有九十八万&nbsp;五个子节点。【实测】"),
        ("空标签", "- 本板共有九十八万<span></span>五个子节点。【实测】"),
        ("修饰字余", "- 本板共有九十八万余五个子节点。【实测】"),
        ("行内代码", "- 本板共有九十八万`x`五个子节点。【实测】"),
    ):
        r = d2(name and line)
        assert r.returncode != 0, f"CJK {name}切断被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, "无法解析", "九十八万五"), (
            f"CJK {name}: 诊断类别与完整数串未绑在同一条 problem:\n{r.stdout}"
        )
    for name, line, whole in (
        ("空格千分位", "- 本板共有980 005个子节点。【实测】", "980005"),
        ("粗体", "- 本板共有98765**4**个子节点。【实测】", "987654"),
        # ⛔ 与「前导零归一化」的交互：行级剥零会把 `1 000`(渲染=1000, SI 千分位)
        # 先剥成 `1 0` 再拼成 `10` 落进池内 ⇒ 放行。归一化必须作用在拼接后的
        # token 上（车道实测，本卡修复时自己踩出来的洞）。
        ("SI千分位+前导零", "- 本板共有1 000个子节点。【实测】", "1000"),
    ):
        r = d2(line)
        assert r.returncode != 0, f"ASCII {name}切断被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, "找不到同值来源", whole), (
            f"ASCII {name}: 诊断类别与完整数串未绑在同一条 problem:\n{r.stdout}"
        )
    # fallback 允许式侧同根（碎片逐片查池全部命中 ⇒ 整体虚构值放行）
    for tok, joined in (("九**五**", "九五"), ("九十八万**五**", "九十八万五")):
        r = verify("方向叙述：", f"\n#### 派生子女 {tok} 个 的说明\n\n方向叙述：")
        assert r.returncode != 0, f"fallback {tok} 碎片被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, "无法验证", joined), (
            f"fallback {tok}: 诊断类别与完整数串未绑在同一条 problem:\n{r.stdout}"
        )

    # ── 放行面（同权重）：合法形态不得被这道收紧反噬 ──
    for name, line in (
        ("单字在池", "- 本板共有五个子节点。【实测】"),
        ("ASCII 在池", "- 本板共有3个子节点。【实测】"),
        ("ASCII 在池 22", "- 本板共有22个子节点。【实测】"),
        ("前导零 016=16 在池", "- 本板共有016个子节点。【实测】"),
        ("round-5 原始误伤 十分", "- 说明十分清楚。【实测】"),
        ("round-5 原始误伤 一致", "- 统计口径尚未一致。【实测】"),
    ):
        r = d2(line)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"


def test_domain_r5_prose_single_char_value_enters_pool():
    """R3 round-2 单元门：D2 侧单字数词同样必须**带自身值**进池比对。

    ⚠️ 与 fallback 侧同因：标准 fixture 池 `[0..16,22]` 覆盖 `_CJK_NUM` 全部值
    （0-9），CLI 层构造不出「单字且值不在池」的用例，于是「值不在池」这条分支
    在 D2 侧**零门覆盖**（车道对抗审查实测：摘掉该分支 253 用例仍全绿）。
    合成 scan 把池收窄到 `[0,1,2]`，`九` 才能证明 9 确实进了池比对。

    **它证明什么**：D2 段内单字 → 按自身值查池（九→找不到同值来源 / 二→放行）；
    多字与被切断的数串 → 走「无法解析」，且诊断里出现的是**剥噪声后的完整数串**。
    **它不证明什么**：不证明段切分、豁免跨度剥离与句式门——那是 CLI 门的事。
    """
    rs = _load_recap_scan()
    synth = {"data_mode": "fallback_local", "counts": {"members": 1, "seeds": 1}}
    assert rs._derived_number_pool(synth) == {0, 1, 2}, "合成池漂移，判别前提失效"

    def probs(tok: str) -> list[str]:
        out: list[str] = []
        rs._verify_prose_counts(f"## 三维审查\n\n- 本板共有{tok}个子节点。【实测】\n", synth, out)
        return out

    got = probs("九")
    assert any("九(9)" in p and "找不到同值来源" in p for p in got), f"单字未按自身值查池: {got}"
    assert probs("二") == [], "值在池的单字被误伤"
    for tok, joined in (("一零", "一零"), ("九十八万**五", "九十八万五")):
        got = probs(tok)
        assert any("无法解析" in p and joined in p for p in got), (
            f"{tok}: 诊断类别与完整数串未绑在同一条 problem: {got}"
        )
        assert not any("找不到同值来源" in p for p in got), f"{tok}: 仍按局部值查池: {got}"


# ── R3 round-3：Codex round-2 报的 4 条 HIGH（车道逐条实测复现后闭合）──────────
# 根因是同一个结构病：取数按字符类分成 CJK / ASCII 两条循环，于是**跨类**或
# **表外**的数词字成了断点，匹配重锚到尾片。已合并为一条规则（宽集合定界 →
# 剥连接字符 → 只有「全 ASCII 数字」或「表内单字」给值，其余 fail-closed）。
# ⚠️ Codex 同轮还报了 `980,005个` 被切断——**实测不成立**（逗号归一化已覆盖，
# 按 980005 查池），本卡如实驳回，见验收单 §五。


def _one_problem_has(stdout: str, *needles: str) -> bool:
    """同一条诊断行里同时出现全部 needle。

    ⛔ Codex round-2 的测试批评（属实）：`assert "无法解析" in out` 与
    `assert "九十八万五" in out` 两条独立 `any`，理论上可由**两条不同的**
    problem 分别满足 —— 断言没有把「诊断类别」与「完整 token」绑在一起。
    """
    return any(all(n in ln for n in needles) for ln in stdout.splitlines())


def test_domain_r6_cross_class_and_offtable_numeral_cli(tmp_path):
    """R3 round-3 行为门：跨类 / 表外数词字 / CJK 小数都不得按尾片查池。

    四条实测反例（修前全部 exit 0）：
      · `本板共有九十八万5个子节点` —— CJK run 停在 `万`，ASCII 只取 `5`
      · `本板共有廿五个子节点` —— `廿` 表外，从 `五` 重锚按 5 查池（读者读 25）
      · `本板共有壹佰个子节点` —— 两字全表外，一个 token 都抽不出
      · `本板共有五点五个 / 5点5个` —— `点` 在量词表里，被拆成两个 5 分别碰池
      · fallback `#### 派生子女 1 000 个` —— `\\d+` 拆成碎片逐片碰池

    **它证明什么**：D2 与 fallback、CJK 与 ASCII 走**同一条**取数规则；
    诊断类别与还原后的完整 token 出现在**同一条** problem 里；
    合法形态（含 `3点建议` 里 `点` 的正当量词用法）不被反噬。
    **它不证明什么**：`_NUMERAL_LIKE_CHARS` 仍是**封闭表**（廿卅卌 + 大写金融
    数字 + 异体），表外的其它数词写法仍可能重锚；量词表同样封闭。见 §五之三。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    pool = _load_recap_scan()._derived_number_pool(scan)
    assert {5, 3, 16, 22} <= pool, f"放行面前提失效: {sorted(pool)}"
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify(anchor: str, injected: str):
        text = base_text.replace(anchor, injected, 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    def d2(line: str):
        return verify("## 三维审查", f"## 三维审查\n\n{line}")

    def fb(tok: str):
        return verify("方向叙述：", f"\n#### 派生子女 {tok} 个 的说明\n\n方向叙述：")

    # 拦截面：诊断必须同时点名「无法解析」与**还原后的完整 token**
    for name, line, token in (
        ("跨类混写", "- 本板共有九十八万5个子节点。【实测】", "九十八万5"),
        ("表外廿", "- 本板共有廿五个子节点。【实测】", "廿五"),
        ("表外大写金融数字", "- 本板共有壹佰个子节点。【实测】", "壹佰"),
        ("多字+切断", "- 本板共有九十八万**五**个子节点。【实测】", "九十八万五"),
    ):
        r = d2(line)
        assert r.returncode != 0, f"D2 {name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, "无法解析", token), (
            f"D2 {name}: 诊断类别与完整 token 未绑在同一条 problem:\n{r.stdout}"
        )
    # CJK/混写小数：与 ASCII 小数同口径恒 FAIL
    for name, line, token in (
        ("CJK 小数", "- 本板共有五点五个子节点。【实测】", "五点五"),
        ("混写小数", "- 本板共有5点5个子节点。【实测】", "5点5"),
    ):
        r = d2(line)
        assert r.returncode != 0, f"D2 {name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, "小数形态", token), f"D2 {name}: 未按小数形态点名:\n{r.stdout}"
    # fallback 侧 ASCII 也必须整串取（round-2 只补了 CJK 侧，是本轮 HIGH 之一）
    for name, tok, token in (
        ("ASCII SI千分位", "1 000", "1000"),
        ("ASCII 标记切断", "9**5", "95"),
    ):
        r = fb(tok)
        assert r.returncode != 0, f"fallback {name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, "无出处", token), f"fallback {name}: 未按整串值点名:\n{r.stdout}"
    r = fb("廿五")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "无法验证", "廿五"), (
        f"fallback 表外数词未 fail-closed:\n{r.stdout}"
    )

    # 放行面（同权重）
    for name, line in (
        ("单字在池", "- 本板共有五个子节点。【实测】"),
        ("ASCII 在池", "- 本板共有3个子节点。【实测】"),
        ("前导零 016=16", "- 本板共有016个子节点。【实测】"),
        ("池内 22", "- 本板共有22个子节点。【实测】"),
        ("`点` 的正当量词用法", "- 本板共有3点建议。【实测】"),
        ("round-5 原始误伤 十分", "- 说明十分清楚。【实测】"),
        ("round-5 原始误伤 一致", "- 统计口径尚未一致。【实测】"),
    ):
        r = d2(line)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"
    for name, tok in (("fallback 单字在池", "五"), ("fallback ASCII 在池", "3")):
        r = fb(tok)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"

    # Codex round-2 报的第五条：`980,005个` 声称被逗号切断 —— **实测不成立**，
    # 逗号归一化先于取数生效，按 980005 查池。这条门把「不成立」也钉住，
    # 防止后人照抄该判词去"修"一个不存在的问题。
    r = d2("- 本板共有980,005个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "找不到同值来源", "980005"), (
        # ⛔ 必须同时绑「找不到同值来源」——只断言出现 980005 的话，
        # 实现改成「无法解析 980005」这条门照样绿，就证不出"按 980005 **查池**"
        # 这件事（Codex round-3 属实指出）。
        f"千分位逗号形态应按完整量级 980005 **查池**:\n{r.stdout}"
    )


# ── R3 round-4：Codex round-3 报的 3 条 HIGH（车道逐条实测复现后闭合）──────────
# ⚠️ 轮次口径：round-1 被内容过滤器截断、**无终裁**（卡文判 UNVERIFIABLE），
# 故产出终裁的是 round-2 / round-3 两轮，本轮整改后仍有一轮送审额度。


def test_domain_r7_range_endpoints_and_fallback_seps_cli(tmp_path):
    """R3 round-4 行为门：区间两端都终核；fallback 也有小数/千分位防线。

    三条实测反例（修前全部 exit 0）：
      · `本板共有987654-0个子节点` —— 某端无出处时区间不挖空，而后面的循环只取
        **紧邻量词**的右端 `0`；任一非空池都由 `abs(a-a)` 生成 0 ⇒ 放行。
        既有门只测了反方向 `1-987654`（大数在右）。
      · fallback `#### 派生子女 0.0 个` / `零点零` / `1,005` —— 千分位归一与小数
        防线原先**只在 D2 路径**，fallback 直接对原行 findall 逐片入池。
      · `本板共有987654<b>.</b>0个子节点` —— 渲染成 `987654.0`，但小数式原要求
        数串与 `.` 直接相邻，两道防线全不命中；`987654，000个` 的全角逗号同理。

    **它证明什么**：区间两端都进池比对且**只在规模自陈句式内**报（非自陈句
    `建议覆盖 2~3 个节点` 不受伤——第一版把报错放在句式门之前，当场误伤）；
    千分位与小数防线在 D2 与 fallback **两侧都在**，且认全角逗号与被标签包住的
    小数点。
    **它不证明什么**：分隔符集合（`,`/`，`）与小数分隔符集合（`.`/`．`/`点`）
    仍是**封闭表**；其它千分位写法（空格已由连接集覆盖，撇号 `'` 等未覆盖）
    未验证。见验收单 §五之三。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    pool = _load_recap_scan()._derived_number_pool(scan)
    assert 0 in pool and 987654 not in pool, f"前提失效: {sorted(pool)}"
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify(anchor: str, injected: str):
        text = base_text.replace(anchor, injected, 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    def d2(line: str):
        return verify("## 三维审查", f"## 三维审查\n\n{line}")

    def fb(tok: str):
        return verify("方向叙述：", f"\n#### 派生子女 {tok} 个 的说明\n\n方向叙述：")

    # 区间：大数在左（本轮新反例）与在右（既有方向）都必须被点名
    for name, line in (
        ("大数在左", "- 本板共有987654-0个子节点。【实测】"),
        ("大数在右", "- 本板共有0-987654个子节点。【实测】"),
        ("到字式", "- 本板共有987654到0个子节点。【实测】"),
    ):
        r = d2(line)
        assert r.returncode != 0, f"区间 {name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, "区间端点", "987654"), f"区间 {name}: 未点名无出处的那一端:\n{r.stdout}"
    # fallback 侧小数与千分位
    for name, tok, needles in (
        ("小数 ASCII", "0.0", ("小数形态", "0.0")),
        ("小数 CJK", "零点零", ("小数形态", "零点零")),
        ("千分位", "1,005", ("无出处", "1005")),
    ):
        r = fb(tok)
        assert r.returncode != 0, f"fallback {name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, *needles), f"fallback {name}: 诊断未绑定:\n{r.stdout}"
    # D2 侧：标签包住小数点 / 全角逗号
    r = d2("- 本板共有987654<b>.</b>0个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "小数形态", "987654.0"), (
        f"标签包住小数点未被识别为小数:\n{r.stdout}"
    )
    r = d2("- 本板共有987654，000个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "找不到同值来源", "987654000"), (
        f"全角逗号千分位未按完整量级查池:\n{r.stdout}"
    )

    # 放行面（同权重）
    for name, line in (
        ("合法区间两端在池", "- 建议覆盖 2~3 个节点。【实测】"),
        ("单字在池", "- 本板共有五个子节点。【实测】"),
        ("`点` 的正当量词用法", "- 本板共有3点建议。【实测】"),
    ):
        r = d2(line)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"
    for name, tok in (("fallback 单字", "五"), ("fallback ASCII", "3")):
        r = fb(tok)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"


# ── R3 round-5：Codex round-4 报的 7 条 HIGH（车道 10 条探针逐条复现后闭合）──────
# ⚠️ 本轮送审已**超出卡文「最多 3 轮」上限**，需用户追认；代码侧仍按"发现即修"处理。


def test_domain_r8_entities_ranges_and_table_gaps_cli(tmp_path):
    """R3 round-5 行为门：HTML 实体 / 区间共用式 / 两张封闭表的补漏。

    七条实测反例（修前全部 exit 0，见 evidence-maintb-r3/m-round4-high-repro.txt）：
      1. `总计987654-0个…` —— 区间**先挖空、后判句式**，挖空后 `_D2_CLAIM_RE` 的
         「共有/总计 + 数字」分支失锚 ⇒ continue，已收集的坏端点不再报。
      2. `本板共有987654<b>-</b>0个…` —— 区间正则是裸 ASCII 窄路径，不复用数串式。
      3. `987654<b>,</b>000个` / fallback `1<b>,</b>005` —— 千分位只认紧邻逗号。
      4. `987654&#46;0个` / `987654&#20010;` —— HTML 字符实体未规范化。
      5. `.5个` / `．五个` —— 小数式要求分隔符两侧都有数串。
      6. `九兆五个` —— `兆` 不在定界集 ⇒ 从尾片重锚（与 `廿五` 同机制）。
      7. `987654层关系` —— `层` 不在量词表 ⇒ 整句零校验。

    **它证明什么**：句式判定取自**挖空之前**的行；区间端点走与普通计数**同一个**
    判值器（中文/混写端点不再免检）且两端都报；HTML 实体先解再核；小数左侧可缺；
    两张封闭表补入常用字符后对应形态被拦。
    **它不证明什么**：`_NUMERAL_LIKE_CHARS` 与 `_D2_QUANT` **仍是封闭表**——
    补的是"已知常用"，不是全集。`html.unescape` 也只覆盖标准实体。
    根本口径见验收单 §五之四：源码级归一化在对抗范式下不可清零。
    """
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    pool = _load_recap_scan()._derived_number_pool(scan)
    assert 0 in pool and 987654 not in pool, f"前提失效: {sorted(pool)}"
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify(anchor: str, injected: str):
        text = base_text.replace(anchor, injected, 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    def d2(line: str):
        return verify("## 三维审查", f"## 三维审查\n\n{line}")

    def fb(tok: str):
        return verify("方向叙述：", f"\n#### 派生子女 {tok} 个 的说明\n\n方向叙述：")

    # 1/2：区间。⛔ Codex 指出既有门都用「大数在一端 + 池内 0」，一个只检查
    # max(ends) 的实现仍会全绿 ⇒ 这里补「双端均坏、逐个报」与非 `个` 量词。
    for name, line, tokens in (
        ("裸『总计』句式", "- 总计987654-0个子节点。【实测】", ("987654",)),
        ("连接字符连字符", "- 本板共有987654<b>-</b>0个子节点。【实测】", ("987654",)),
        ("双端均坏", "- 本板共有987654-876543个子节点。【实测】", ("987654", "876543")),
        ("中文端点", "- 本板共有九十八万-0个子节点。【实测】", ("九十八万",)),
        ("非『个』量词（层）", "- 本板共有987654-0层关系。【实测】", ("987654",)),
    ):
        r = d2(line)
        assert r.returncode != 0, f"区间 {name} 被放行:\n{r.stdout}"
        for tok in tokens:
            assert _one_problem_has(r.stdout, "区间端点", tok), f"区间 {name}: 未逐个点名端点 {tok}:\n{r.stdout}"

    # 3：千分位跨连接字符（两个消费面）
    r = d2("- 本板共有987654<b>,</b>000个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "找不到同值来源", "987654000"), (
        f"D2 千分位跨连接字符未按完整量级查池:\n{r.stdout}"
    )
    r = fb("1<b>,</b>005")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "无出处", "1005"), (
        f"fallback 千分位跨连接字符未按完整量级查池:\n{r.stdout}"
    )

    # 4：HTML 字符实体
    r = d2("- 本板共有987654&#46;0个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "小数形态", "987654.0"), f"实体小数点未被识别:\n{r.stdout}"
    # ⛔ 「小数分隔符两侧容连接字符」这条性质，必须用 `_visible_text` **不移除**的
    # 连接字符来测（Codex round-8 + 负验证实测）：原门用 `<b>.</b>`，但 round-6 起
    # `_visible_text` 会先剥标签 ⇒ 该性质被**纵深遮蔽**，`survivor-38` 当场不承重。
    # 空白在连接集内、却不被 `_visible_text` 移除，正好只由这条性质接住。
    r = d2("- 本板共有987654 . 0个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "小数形态", "987654.0"), (
        f"空白分隔的小数未被识别（小数式必须容连接字符）:\n{r.stdout}"
    )
    r = d2("- 本板共有987654 点 0个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "小数形态", "987654点0"), (
        f"空白分隔的中文小数未被识别:\n{r.stdout}"
    )
    r = d2("- 本板共有987654&#20010;子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "找不到同值来源", "987654"), (
        f"实体量词未还原出锚点:\n{r.stdout}"
    )

    # 5：小数左侧可缺（含全角小数点——Codex 指出此前无输入门）
    for name, line, tok in (
        ("半角左缺", "- 本板共有.5个子节点。【实测】", ".5"),
        ("全角左缺", "- 本板共有．五个子节点。【实测】", "．五"),
    ):
        r = d2(line)
        assert r.returncode != 0 and _one_problem_has(r.stdout, "小数形态", tok), f"{name} 小数未被识别:\n{r.stdout}"

    # 6/7：两张封闭表补漏
    r = d2("- 本板共有九兆五个子节点。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "无法解析", "九兆五"), (
        f"定界集漏『兆』导致尾片重锚:\n{r.stdout}"
    )
    r = d2("- 本板共有987654层关系。【实测】")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "找不到同值来源", "987654"), (
        f"量词表漏『层』导致整句零校验:\n{r.stdout}"
    )

    # 放行面（同权重）
    for name, line in (
        ("合法区间两端在池", "- 建议覆盖 2~3 个节点。【实测】"),
        ("单字在池", "- 本板共有五个子节点。【实测】"),
        ("ASCII 在池", "- 本板共有3个子节点。【实测】"),
        ("`点` 的正当量词用法", "- 本板共有3点建议。【实测】"),
        ("round-5 原始误伤 十分", "- 说明十分清楚。【实测】"),
    ):
        r = d2(line)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"
    for name, tok in (("fallback 单字", "五"), ("fallback ASCII", "3")):
        r = fb(tok)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"


# ── R3 round-6：Codex round-5 八条实现 HIGH 的整改 + **一次假设检验** ──────────
# ⛔ 本轮最重要的产出不是修了 8 条，而是**证伪了车道自己的中心断言**。
# 车道在 round-5 收口时写下：「五轮全部 finding 在『先渲染再核数』的设计下会
# **同时消失**，因为它们共享『源码与渲染不一致』这一个前提」。
# round-6 把 `_visible_text()` 真正实现出来并实测：**10 条里只闭合 3 条**
# （标记/实体/千分位），其余 7 条与渲染无关——是**封闭表**（量词 `门`、区间
# 分隔符 `～`）、**判据正则过窄**（`总计五个` / `总计：`）、**负号**、
# **有意豁免**（inline-code）、**顺序问题**（wikilink 在归一前已被挖空）。
# ⇒ 那句「同时消失」是**未经检验就写进结论的断言**，已按实测更正为 3/10。


def test_domain_r9_visible_text_and_round5_closures_cli(tmp_path):
    """R3 round-6：渲染归一 + 六处非渲染缺口，逐条锁住。

    **它证明什么**：
      · `_visible_text()` 把 HTML 实体（含 `&#xff19;` 这类全角实体，**先解实体
        再转全角**，顺序反了就永远转不成 ASCII）、HTML 标签、无别名 wikilink 的
        显示文本、零宽字符、强调标记统一归一到"读者看到的文本"；
      · 句式门 `总计/合计/共有` 其后接**任一数词样字符**（原只认 ASCII 数字，
        `总计五个` / `总计：987654个` 整句不进检查面）；
      · 区间分隔符含全角波浪等变体；负数计数恒 FAIL；量词表补常用字。
    **它不证明什么**：三张表（数词/量词/分隔符）**仍是封闭表**；
    `_visible_text` **不是完整 markdown 渲染器**，是针对本域已知构造的收敛器；
    inline code 内容是**有意豁免**的字段值（E2 设计选择），本门不覆盖。
    """
    rs = _load_recap_scan()
    # 归一器单元契约：顺序错了 `&#xff19;` 就会停在全角 `９`（round-5 HIGH-3）
    assert rs._visible_text("&#xff19;&#xff18;") == "98", "解实体必须早于全角转换"
    assert rs._visible_text("987654<b>-</b>0") == "987654-0"
    assert rs._visible_text("[[987654]]") == "987654", "无别名 wikilink 的目标就是显示文本"
    assert rs._visible_text("[[节点/A|五]]") == "五", "有别名时显示的是别名"
    assert rs._visible_text("98​7") == "987", "零宽字符不得切断数串"
    # ⛔ round-6 自查回归（Codex round-6 HIGH-1，车道实测确认并含**误伤**）：
    # 第一版 `_VIS_EMPHASIS_RE = [*_~]` 无条件剥 `~`，而 `_visible_text` 跑在
    # `_D2_RANGE_RE` **之前** ⇒ 合法区间 `2~3个` 被拼成 `23`（池外）而 FAIL。
    # ⚠️ 这条门此前只用**全角 `～`**，恰好漏掉 ASCII `~`。
    assert rs._visible_text("987654~0") == "987654~0", "单个 ~ 是区间号，不得剥"
    assert rs._visible_text("98~~7~~6") == "9876", "成对 ~~ 是删除线，须剥"

    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    pool = _load_recap_scan()._derived_number_pool(scan)
    assert 5 in pool and 987654 not in pool, f"前提失效: {sorted(pool)}"
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def d2(line: str):
        text = base_text.replace("## 三维审查", f"## 三维审查\n\n{line}", 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    for name, line, needles in (
        (
            "实体全角数字",
            "- 本板共有&#xff19;&#xff18;&#xff17;&#xff16;&#xff15;&#xff14;个子节点。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "千分位后三位内部再切",
            "- 本板共有987654,0<b>0</b>0个子节点。【实测】",
            ("找不到同值来源", "987654000"),
        ),
        (
            "标记切断的裸『总计』",
            "- 总计**987654**个子节点。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "冒号式裸『总计』",
            "- 总计：987654个子节点。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "无别名 wikilink",
            "- 本板共有[[987654]]个子节点。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "全角波浪区间",
            "- 本板共有987654～0个子节点。【实测】",
            ("区间端点", "987654"),
        ),
        # ⛔ ASCII `~` 必须与全角同等对待（round-6 回归点）
        (
            "ASCII 波浪区间",
            "- 本板共有987654~0个子节点。【实测】",
            ("区间端点", "987654"),
        ),
        (
            "成对删除线（渲染=9876）",
            "- 本板共有98~~7~~6个子节点。【实测】",
            ("找不到同值来源", "9876"),
        ),
        ("负数计数", "- 本板共有-5个子节点。【实测】", ("负数形态", "-5")),
        (
            "量词表补『门』",
            "- 本板共有987654门课程。【实测】",
            ("找不到同值来源", "987654"),
        ),
        # 句式门真的进了检查面（而非恰好放行）——多字/表外都必须 fail-closed
        (
            "裸『总计』+多字数词",
            "- 总计九十八万个子节点。【实测】",
            ("无法解析", "九十八万"),
        ),
        ("裸『合计』+表外数词", "- 合计：廿五个子节点。【实测】", ("无法解析", "廿五")),
    ):
        r = d2(line)
        assert r.returncode != 0, f"{name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, *needles), f"{name}: 诊断未绑定 {needles}:\n{r.stdout}"

    # 放行面（同权重）：收紧不得反噬
    for name, line in (
        ("裸『总计』+值在池的单字", "- 总计五个子节点。【实测】"),
        ("单字在池", "- 本板共有五个子节点。【实测】"),
        ("ASCII 在池", "- 本板共有3个子节点。【实测】"),
        ("合法区间（非自陈句）", "- 建议覆盖 2~3 个节点。【实测】"),
        # ⛔ 自陈句内的合法 ASCII 区间 —— 回归的**误伤面**（曾被拼成 23 而 FAIL）
        ("自陈句内合法 ASCII 区间", "- 本板共有2~3个子节点。【实测】"),
        ("`点` 的正当量词用法", "- 本板共有3点建议。【实测】"),
        ("round-5 原始误伤 十分", "- 说明十分清楚。【实测】"),
        ("round-5 原始误伤 一致", "- 统计口径尚未一致。【实测】"),
    ):
        r = d2(line)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"


# ── R3 round-8：Codex round-6 八条中的其余七条（**5 实现 + 2 自证**，非全部实现）──
# ⛔ 本轮同时是一次**速率测量**：round-6 那一刀在闭合 3 条的同时自引 1 条回归，
# 车道据此判「修复速率 ≈ 引入速率、应停止」。但那只是**一个数据点**，而"再修会
# 引入更多"本身就是未经验证的断言。
# 实测（⚠️ 措辞按 Codex round-7 HIGH-8 收窄）：round-7 修 1 条（自引回归）、
# round-8 修 7 条；本轮拦截面 8/8 闭合，**已列举的 10 个放行样例**与**已运行的
# 全套件**未发现回归。⇒ 「再修必然引入回归」这一断言在本轮**未被支持**。
# ⚠️ 这**不等于**「零回归」——未被门覆盖的行为面没有被测，不能据此声称。


def test_domain_r10_ordering_and_render_closure_cli(tmp_path):
    """R3 round-8：三处**顺序耦合** + 渲染闭包缺口 + 三张闭表的便宜面。

    七条实测反例（修前全部 exit 0）：
      · `[[节点/A|987654]]个` —— D2 把 `[[目标` 挖空**跑在 `_visible_text` 之前**，
        只剩 `|987654]]个`，量词锚失效（顺序耦合）；
      · fallback `#### 派**生**子女 987654 个` —— 在**源码行**上判「含派生」与
        白名单匹配，`**` 隔开 `派`/`生` 整行不进检查面（顺序耦合）；
      · fallback `-5` —— 负数守卫原先**只在 D2 侧**（覆盖不全）；
      · `总[计](http://x)987654个` —— 标准 Markdown link 未取显示文本；
      · `98⁦⁩7654个` —— U+2066-2069 bidi isolate 不在不可见集；
      · `1'005个` / `987654笔` / `仨五个` —— 三张闭表的常见缺口。

    **它证明什么**：归一必须跑在**筛选与豁免挖空之前**（三处顺序已改）；
    `_visible_text` 覆盖 Markdown link 与 bidi isolate；负数守卫两侧同口径。
    **它不证明什么**：`_visible_text` **仍不是完整 renderer**，三张表**仍是闭表**
    —— 见验收单 §五之五 的分类（四类都**没有**被证明有限）。
    """
    rs = _load_recap_scan()
    assert rs._visible_text("总[计](http://x)987654个") == "总计987654个"
    # ⛔ round-12：reference-style link 同处理（Codex 三轮点名）。
    # ⚠️ 如实声明：`_visible_text` **仍不是完整 renderer** —— Obsidian highlight
    # `==x==`、math `$x$`、脚注 `[^1]` 等未覆盖。这是**又补一个已知构造**，不是闭包。
    assert rs._visible_text("总[计][r]987654个") == "总计987654个"
    assert rs._visible_text("98⁦⁩7") == "987", "bidi isolate 不得切断数串"
    assert rs._normalize_number_seps("1'005") == "1005", "撇号千分位"

    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert 987654 not in _load_recap_scan()._derived_number_pool(scan)
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify(anchor: str, injected: str):
        text = base_text.replace(anchor, injected, 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    def d2(line: str):
        return verify("## 三维审查", f"## 三维审查\n\n{line}")

    def fb_raw(raw: str):
        return verify("方向叙述：", f"\n{raw}\n\n方向叙述：")

    for name, line, needles in (
        (
            "有别名 wikilink（顺序耦合）",
            "- 本板共有[[节点/A|987654]]个子节点。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "Markdown link 显示文本（inline）",
            "- 总[计](http://x)987654个子节点。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "Markdown link 显示文本（reference-style，round-12 新增）",
            "- 总[计][r]987654个子节点。【实测】",
            ("找不到同值来源", "987654"),
        ),
        ("bidi isolate", "- 本板共有98⁦⁩七654个子节点。【实测】", ("无法解析",)),
        ("撇号千分位", "- 本板共有1'005个子节点。【实测】", ("找不到同值来源", "1005")),
        (
            "量词表『笔』",
            "- 本板共有987654笔支出。【实测】",
            ("找不到同值来源", "987654"),
        ),
        ("数词表『仨』", "- 本板共有仨五个子节点。【实测】", ("无法解析", "仨五")),
    ):
        r = d2(line)
        assert r.returncode != 0, f"{name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, *needles), f"{name}: 诊断未绑定:\n{r.stdout}"

    # fallback 侧：选行顺序 + 负数守卫
    r = fb_raw("#### 派**生**子女 987654 个 的说明")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "无出处", "987654"), (
        f"fallback 在源码行上选行 ⇒ 整行不进检查面:\n{r.stdout}"
    )
    r = fb_raw("#### 派生子女 -5 个 的说明")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "负数形态", "-5"), (
        f"fallback 负数未 fail-closed:\n{r.stdout}"
    )

    # 放行面（同权重）——本轮的**回归探测面**
    for name, line in (
        ("单字在池", "- 本板共有五个子节点。【实测】"),
        ("ASCII 在池", "- 本板共有3个子节点。【实测】"),
        ("自陈句内合法 ASCII 区间", "- 本板共有2~3个子节点。【实测】"),
        ("非自陈句区间", "- 建议覆盖 2~3 个节点。【实测】"),
        ("`点` 的正当量词用法", "- 本板共有3点建议。【实测】"),
        ("前导零 016=16", "- 本板共有016个子节点。【实测】"),
        ("round-5 原始误伤 十分", "- 说明十分清楚。【实测】"),
        ("round-5 原始误伤 一致", "- 统计口径尚未一致。【实测】"),
    ):
        r = d2(line)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"
    # ⛔ Codex round-8 HIGH-9：中文「负」原**只测 D2 侧**，而两侧守卫**不是共享常量**
    # ⇒ fallback 那份可以漂移。补 fallback 侧的中文负号行为门。
    r = fb_raw("#### 派生子女 负五 个 的说明")
    assert r.returncode != 0 and _one_problem_has(r.stdout, "负数形态", "-五"), (
        f"fallback 侧中文负号未 fail-closed:\n{r.stdout}"
    )

    for name, raw in (
        ("fallback 单字", "#### 派生子女 五 个 的说明"),
        ("fallback ASCII", "#### 派生子女 3 个 的说明"),
    ):
        r = fb_raw(raw)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"


# ── R3 round-9：Codex round-7 的实现侧真缺陷（逐条实测复现后闭合）────────────
# ⚠️ Codex round-7 报 5 实现 HIGH，车道逐条实测：**H1/H3/H4/H5 属实**，
# 而 H2 的两个具体例子（inline-code 藏 `笔`、⑦⑧手抄数词禁集）**不成立**
# ——它们分别被「`支` 已在量词表」与「信号行整行格式检查」拦下。机制或许仍在，
# 但**给出的反例不可复现**，如实驳回，不按它去改一个测不出来的东西。
# H4（reference-style link）与 H5（过度拼接不保值）**未修**，登记在 §五之三。


def test_domain_r11_fulltext_gate_and_visible_numerals_cli(tmp_path):
    """R3 round-9：全文『派生』门先归一 + 可见数字/量词/中文负号的闭表补漏。

    四条实测反例（修前 exit 0）：
      · `- 派**生**出 987654 个新节点` —— **全文**白名单门仍在**源码行**上判
        「含派生」；round-8 只把**局部**数字函数改成先归一，这道门漏了 ⇒ 整行
        既不进局部循环、也绕过全文门（**同一个顺序耦合，修了一处漏了另一处**）；
      · `本板共有⑤个子节点` —— 带圈数字不在定界集 ⇒ **一个 token 都抽不出**，
        整句零校验（比尾片重锚更彻底）；
      · `本板共有987654例记录` —— `例` 不在量词表 ⇒ 整句零校验；
      · `本板共有负五个子节点` —— 符号守卫只认五个西文符号，漏中文「负」。

    **它证明什么**：两道 fallback 门（全文/局部）**同口径**先归一；可见数字与
    常用量词进表后对应形态被拦；中文负号与西文负号同等对待。
    **它不证明什么**：三张表**仍是封闭表**——本轮补的是"已知可见形态"，不是全集。
    Unicode 里还有大量可渲染成数字的字符未纳入，见 §五之三。
    """
    rs = _load_recap_scan()
    assert rs._count_token_value("⑤") is None, "带圈数字应进定界面但**不赋值**"
    assert "⑤" in rs._NUMERAL_LIKE_CHARS and "〡" in rs._NUMERAL_LIKE_CHARS

    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert 987654 not in rs._derived_number_pool(scan)
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify(anchor: str, injected: str):
        text = base_text.replace(anchor, injected, 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    def d2(line: str):
        return verify("## 三维审查", f"## 三维审查\n\n{line}")

    def fb_raw(raw: str):
        return verify("方向叙述：", f"\n{raw}\n\n方向叙述：")

    # 全文『派生』门：必须由**模板外派生表述**拦下（不是被别的防线顺手接住）
    r = fb_raw("- 派**生**出 987654 个新节点")
    assert r.returncode != 0, f"全文门在源码行上判 ⇒ 整行逃出:\n{r.stdout}"
    assert "模板外的『派生』表述" in r.stdout, f"应由全文『派生』白名单门拦下:\n{r.stdout}"

    for name, line, needles in (
        ("带圈数字（可见但表外）", "- 本板共有⑤个子节点。【实测】", ("无法解析", "⑤")),
        (
            "表外量词『例』",
            "- 本板共有987654例记录。【实测】",
            ("找不到同值来源", "987654"),
        ),
        ("中文负号（D2 侧）", "- 本板共有负五个子节点。【实测】", ("负数形态", "-五")),
        # ⛔ Codex round-8 HIGH-9：量词表本轮补了 `例束艘架间`，原门只测 `例`
        # ⇒ 其余四字可漂移而无人发现。逐字补齐行为门。
        (
            "表外量词『束』",
            "- 本板共有987654束数据。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "表外量词『艘』",
            "- 本板共有987654艘记录。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "表外量词『架』",
            "- 本板共有987654架记录。【实测】",
            ("找不到同值来源", "987654"),
        ),
        (
            "表外量词『间』",
            "- 本板共有987654间记录。【实测】",
            ("找不到同值来源", "987654"),
        ),
    ):
        r = d2(line)
        assert r.returncode != 0, f"{name} 被放行:\n{r.stdout}"
        assert _one_problem_has(r.stdout, *needles), f"{name}: 诊断未绑定:\n{r.stdout}"

    # 放行面（同权重）——本轮的回归探测面
    for name, line in (
        ("单字在池", "- 本板共有五个子节点。【实测】"),
        ("ASCII 在池", "- 本板共有3个子节点。【实测】"),
        ("池内 22", "- 本板共有22个子节点。【实测】"),
        ("自陈句内合法区间", "- 本板共有2~3个子节点。【实测】"),
        ("非自陈句区间", "- 建议覆盖 2~3 个节点。【实测】"),
        ("`点` 的正当量词用法", "- 本板共有3点建议。【实测】"),
        ("前导零 016=16", "- 本板共有016个子节点。【实测】"),
        ("round-5 原始误伤 十分", "- 说明十分清楚。【实测】"),
        ("round-5 原始误伤 一致", "- 统计口径尚未一致。【实测】"),
    ):
        r = d2(line)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"
    for name, raw in (
        ("fallback 单字", "#### 派生子女 五 个 的说明"),
        ("fallback ASCII", "#### 派生子女 3 个 的说明"),
    ):
        r = fb_raw(raw)
        assert r.returncode == 0, f"合法形态被误伤（{name}）:\n{r.stdout}"


# ── R3 round-11：消掉一张手抄闭表副本 + 给另一张加漂移检测 ────────────────────
# ⛔ Codex 连续三轮点名「隐藏的手抄闭表」。本卡反复证明的那条原则是：
# **一个原则只有一个应用点**（判据分叉 / 双循环分类 / 预处理顺序耦合，
# 全是同一个病的不同实例）。所以这里不是再补一次表，而是：
#   · inline-code 守卫的量词副本 → **从 `_D2_QUANT` 机械派生**（副本消失）；
#   · ⑦⑧允许式的数词禁集在**定界集定义之前**，移动代码风险大 ⇒ 保留副本，
#     但加一道**漂移检测门**：它必须覆盖 `_NUMERAL_LIKE_CHARS` 的每一个字符。
#     ⚠️ 这不等于消除副本，只是**把静默分叉变成会被抓住的分叉**——如实登记。


def test_domain_r12_no_silent_table_copies():
    """R3 round-11：闭表副本要么派生，要么可检测。

    **它证明什么**：① inline-code 的量词守卫确实从 `_D2_QUANT` 派生（给主表加字，
    守卫自动跟上，`` `例` `` 不再被当普通 code span 挖空）；② ⑦⑧允许式的数词禁集
    覆盖定界集全集，任一方漂移都会被这道门抓住。
    **它不证明什么**：⑦⑧ 的副本**仍然存在**（只是不能再静默分叉）；
    三张主表本身**仍是封闭表**，本门不宣称覆盖表外形态。
    """
    rs = _load_recap_scan()
    quant = set(rs._D2_QUANT.strip("[]"))

    # ① inline-code 守卫必须与主量词表同步（派生 ⇒ 逐字覆盖）
    for ch in sorted(quant):
        assert rs._codespan_is_visible_count(ch), (
            f"量词 {ch!r} 单独写成 code span 时被挖空 ⇒ 前面的数字失去锚点；inline-code 守卫与 _D2_QUANT 已分叉"
        )
    # ⛔ round-14（冻结审查）：数字部分原先仍手写 `[0-9]+` ——「副本已消除」只对了
    # 一半，于是 `` `九十八万个` ``/`` `987654 个` `` 这类**完整可见计数**写进
    # code span 会被整体挖空、整域免检。现数字部分也派生自定界集。
    for span in ("987654 个", "九十八万个", "987654", "廿五个"):
        assert rs._codespan_is_visible_count(span), f"纯计数 code span `{span}` 被当字段值挖空 ⇒ 可见计数整域免检"
    # ⛔ round-17（冻结审查 §一.2）：判据从 raw 正则前瞻改为**先归一再判**的函数，
    # 符号/小数点/千分位/全角数字不再让守卫失效。
    for span in ("-5", "5.5个", "1,005个", "５５个"):
        assert rs._codespan_is_visible_count(span), f"可见计数 `{span}` 仍被当字段值挖空"
    for span in ("-", ".", " "):
        assert not rs._codespan_is_visible_count(span), f"纯符号 `{span}` 不该算计数（白丢 E2 豁免）"
    # 可见计数 span **只挖反引号**：反引号不在连接集里，原样留下会让量词锚失效。
    assert rs._D2_CODE_SPAN_RE.sub(rs._blank_inline_code, "共有`-5`个") == "共有 -5 个"
    # 字段值 span 整段挖空，且**等长**（行内偏移不能乱）——期望值算出来，不手数空格
    assert (
        rs._D2_CODE_SPAN_RE.sub(rs._blank_inline_code, "项 `mastery` 已改") == "项 " + " " * len("`mastery`") + " 已改"
    )
    # 负号集必须是**单一常量**（原先 D2/fallback 手抄两次）
    assert hasattr(rs, "_NEG_SIGN"), "负号集应提为单一常量，避免第三处副本"
    # ⛔ round-15（冻结审查）：全文零宽门原先**手抄**一份只到 U+2064 的集合，
    # 而 `_INVISIBLE_ONE` 覆盖到 U+2069 ⇒ bidi isolate U+2065-2069 能过全局门。
    # 又一处「同一原则两处定义」。现两处共用同一常量 —— 逐字符验证一致性。
    import re as _re

    _inv = _re.compile(rs._INVISIBLE_ONE)
    # 全文零宽门与归一集必须是**同一个**集合：逐字符比对两者判定。
    _globals_src = pathlib.Path(rs.__file__).read_text(encoding="utf-8")
    assert "if re.search(_INVISIBLE_ONE, text):" in _globals_src, (
        "全文零宽门未共用 _INVISIBLE_ONE —— 手抄副本会与归一集分叉"
    )
    for _cp in (0x2065, 0x2066, 0x2067, 0x2068, 0x2069):
        assert _inv.match(chr(_cp)), f"U+{_cp:04X} (bidi isolate) 不在不可见集内 —— 它能切断数串却过全局门"
    # 反面：非量词的 code span 仍应被挖空（否则豁免整个失效）
    assert not rs._codespan_is_visible_count("abc"), "普通 code span 应仍被豁免（字段值）"

    # ② ⑦⑧允许式的手抄数词禁集必须覆盖定界集全集（漂移即被抓）
    # ⚠️ 必须**按行为**检测，不能拿字符去子串匹配 pattern 源码 ——
    # `0-9` 在字符类里是**区间**，`"1" in pattern` 恒 False，会给出大批假阳性
    # （第一版就这么写的，当场报出 60+ 个"缺失"，其中 1-8 是假的）。
    pats = [p for p, _ in rs._FALLBACK_DERIVE_ALLOW if "缺来源锚点" in p.pattern or "集中在" in p.pattern]
    assert len(pats) == 2, f"⑦⑧允许式应恰有两条: {len(pats)}"
    p7, p8 = pats
    missing = set()
    for ch in rs._NUMERAL_LIKE_CHARS:
        if p7.match(f"2 个派生角色成员缺来源锚点{ch}。"):
            missing.add(ch)
        if p8.match(f"集中在派生角色成员{ch}。"):
            missing.add(ch)
    assert not missing, (
        f"⑦⑧的手抄数词禁集与定界集已分叉，未禁: {''.join(sorted(missing))}\n"
        "⇒ 这些字符写进③段固定句式的尾段可绕过数字禁令"
    )


def test_domain_r13_shortcut_link_and_crash_classifier(tmp_path):
    """R3 round-16（冻结审查 HIGH ×2）：shortcut link 渲染面 + 崩溃判据的假阴面。

    两条实测反例（修前）：
      · `总[计]987654个子节点` —— link 三形态只覆盖了 inline `[t](url)` 与
        reference `[t][r]`/`[t][]`，**shortcut** `[t]` 未覆盖；渲染后读者看到
        `总计987654个`，源码里 `总`/`计` 被方括号隔开，句式门失锚 ⇒ exit 0；
      · negverify 的崩溃判据**枚举**五个异常名、且只扫外层 pytest stdout ⇒
        `ValueError`/`KeyError` 崩溃、以及 **CLI 子进程**里的 traceback 全部
        记成「✅ 如期变红」。崩溃伪红是四种假绿里**唯一伪装成成功**的一种。

    **它证明什么**：shortcut link 的显示文本进入受检面且不误伤 callout/脚注；
    崩溃判据按**形态**（`E <Exc>` 非 AssertionError / traceback / INTERNALERROR /
    收集期 error）而非**名单**识别，两个已知假阴面各有一条正例。
    **它不证明什么**：`_visible_text` 仍不是完整 renderer（highlight/math/脚注
    未覆盖）；崩溃判据取的是「宁可误报不漏报」方向，可能把**故意**断言 traceback
    文本的门误判为崩溃（当前目标套件无此形态）。
    """
    rs = _load_recap_scan()

    # ① 渲染面：shortcut 取显示文本，且不吃掉 callout / 脚注
    assert rs._visible_text("总[计]987654个") == "总计987654个"
    assert rs._visible_text("总[计](http://x)987654个") == "总计987654个", (
        "inline 形态必须先于 shortcut 剥，否则只剩裸 url"
    )
    assert rs._visible_text("总[计][r]987654个") == "总计987654个"
    assert rs._visible_text("> [!question]+ 提问") == "> [!question]+ 提问", (
        "Obsidian callout 头不是链接语法，剥掉会改变段落语义"
    )
    assert rs._visible_text("脚注[^1]在此") == "脚注[^1]在此"

    # ② CLI：shortcut link 藏起来的可见计数必须被拦
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    assert 987654 not in rs._derived_number_pool(scan)
    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"
    text = base_text.replace(
        "## 三维审查",
        "## 三维审查\n\n- 本板总[计]987654个子节点。【实测】",
        1,
    )
    assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
    report.write_text(text, encoding="utf-8")
    r = run_verify(report)
    assert r.returncode != 0, "shortcut link 藏起来的可见计数被放行"
    assert _one_problem_has(r.stdout, "987654"), f"诊断未指向完整数串 987654:\n{r.stdout}"

    # ③ 崩溃判据：两个已知假阴面各一条正例 + 断言失败不得误判
    import importlib.util as _ilu

    _prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        _spec = _ilu.spec_from_file_location(
            "negverify_ut", pathlib.Path(__file__).with_name("recap_domain_negverify.py")
        )
        _nv = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_nv)
    finally:
        sys.dont_write_bytecode = _prev

    for out, want, why in (
        ("E       AssertionError: 期望 FAIL", False, "断言失败=判错，正是我们要的红"),
        ("E       assert 0 == 1", False, "裸 assert 同上"),
        ("1 failed, 260 passed", False, "纯失败摘要"),
        ("E       re.error: invalid group reference", True, "round-10 原案"),
        ("E       ValueError: too many values", True, "旧版枚举之外 ⇒ 假阴"),
        ("E       KeyError: 3", True, "旧版枚举之外 ⇒ 假阴"),
        (
            "  Traceback (most recent call last):\n    File 'x'",
            True,
            "CLI 子进程崩溃，外层无异常名 ⇒ 旧版假阴",
        ),
        ("INTERNALERROR> boom", True, "pytest 内部错"),
        ("1 error, 260 passed", True, "收集期 error"),
        # ⛔ round-17（冻结审查 §一.4）：上一版号称"从名单改形态"，其实只是把名单
        # 从**全名**换成了**后缀** `(?:[Ee]rror|Exception)` —— 仍是我手写的闭表。
        # 下面三个都不以 Error/Exception 结尾，旧判据全部漏掉。
        ("E       SystemExit: 2", True, "不以 Error/Exception 结尾 ⇒ 旧后缀表假阴"),
        ("E       subprocess.TimeoutExpired: t", True, "同上，且是点分名"),
        ("E       RecursionError: deep", True, "枚举五名单之外"),
        ("E       Failed: 被测脚本不存在", True, "pytest.fail = 夹具坏了，不是判错"),
        # ⛔ round-17 二修（实测 39/44 假阳）：第一版把判据放宽成「行首是个标识符」，
        # 但 pytest 给失败详情的**每一行**都加 `E ` 前缀 ⇒ 断言消息的**续行**被
        # 当成异常类型。**修严引入松、修松引入严** —— 两个方向必须同时锁。
        ("E     VERIFY FAIL (1 项) — 改写报告后重跑本命令", False, "断言消息续行，不是异常"),
        ("E     VERIFY PASS — 可以发回执", False, "同上"),
        ("E    +  where 0 = CompletedProcess(args=[...])", False, "assert 重写的 where 行"),
        ("E   AssertionError: 四反引号短闭合仍被放行:", False, "消息自己以冒号结尾，仍是断言"),
        ("E     E1 围栏闭合: 少一个反引号", False, "续行首词恰好像类名 ⇒ 必须靠缩进外的冒号规则排除"),
    ):
        assert _nv._looks_like_crash(out) is want, f"崩溃判据判错: {why} | {out!r}"

    # ④ transport：崩溃分析必须同时看 stderr。本域大量门跑 CLI 子进程，
    #    子进程 traceback 只落 stderr 时，外层只剩一个 AssertionError。
    assert not _nv._looks_like_crash("1 failed, 260 passed"), "前提：单看 stdout 不算崩溃"
    assert _nv._looks_like_crash(_nv._crash_text("1 failed, 260 passed", "Traceback (most recent call last):")), (
        "stderr 里的 traceback 被丢弃 ⇒ 生产崩溃会被当成正常判错变红"
    )
    assert _nv._crash_text("a", None) == "a\n", "stderr 为 None 时不得抛"


def test_domain_r14_range_left_edge_and_codespan_order_cli(tmp_path):
    """R3 round-17（冻结审查 §一.1/§一.2）：两处**顺序耦合**，六条实测反例。

    修前全部 exit 0：
      · `-2~3个` —— 区间端点用的 `_NUM_RUN_PAT` **不含符号**，匹配从负号之后
        重新起锚成 `2~3`；两端都在池 ⇒ 整段挖空，负号守卫再也看不到它；
      · `2.2~3个` —— 同理从小数点之后起锚；
      · `` `-5`个 `` / `` `5.5个` `` / `` `1,005个` `` / `` `５５个` `` ——
        inline-code 的「纯计数」豁免判据作用在 **raw** span 上，而它跑在
        `_visible_text` / `_normalize_number_seps` **之前**，于是符号/小数点/
        千分位/全角数字都不在 `_D2_COUNTISH_CHARS` 里 ⇒ 前瞻失败 ⇒ 整段按
        「字段值」挖空，后续所有数值门都看不见。

    **它证明什么**：区间首端紧邻负号/小数点时 fail-closed；code span 的豁免
    判据看的是**渲染后**内容，且可见计数只挖反引号（保住量词锚）。
    **它不证明什么**：`_D2_RANGE_RE` 的分隔符仍是**闭表**；「可见计数」判据
    仍依赖 `_D2_COUNTISH_CHARS` 这张闭表 —— 两者都如实登记在验收单 §五之三。
    """
    rs = _load_recap_scan()
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    pool = rs._derived_number_pool(scan)
    assert {2, 3, 5} <= pool, "前提：2/3/5 必须在池内，否则下面测的是别的东西"
    assert 55 not in pool and 1005 not in pool, "前提：55/1005 必须在池外"

    report = write_report(vault, scan)
    base_text = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    def verify(injected: str):
        text = base_text.replace("## 三维审查", f"## 三维审查\n\n{injected}", 1)
        assert text != base_text, "变异未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    # ① 必须拦：六条实测反例
    for line, needle, why in (
        ("- 本板共有-2~3个子节点。【实测】", "-2~3", "区间首端负号"),
        ("- 本板共有2.2~3个子节点。【实测】", "2.2~3", "区间首端小数"),
        ("- 本板共有`-5`个子节点。【实测】", "5", "负号在 code span 外"),
        ("- 本板共有`5.5个`子节点。【实测】", "5.5", "小数整体在 code span"),
        ("- 本板共有`1,005个`子节点。【实测】", "1005", "千分位整体在 code span"),
        ("- 本板共有`５５个`子节点。【实测】", "55", "全角数字在 code span（池外 55）"),
    ):
        r = verify(line)
        assert r.returncode != 0, f"{why}：放行了 —— {line!r}"
        assert _one_problem_has(r.stdout, needle), f"{why}：诊断未指向完整数串 {needle}\n{r.stdout}"

    # ② 不得误伤：E2 字段值豁免仍在，池内值与合法区间照常放行
    for line, why in (
        ("- 配置项 `mastery_score` 已更新。【实测】", "普通字段值 code span 仍豁免"),
        ("- 本板共有`５个`子节点。【实测】", "全角 ５=5 在池内，应放行"),
        ("- 建议覆盖2~3个节点。", "合法区间不受伤"),
    ):
        assert verify(line).returncode == 0, f"误伤：{why} —— {line!r}"


def test_domain_r15_signal_line_selection_is_visible_text_cli(tmp_path):
    """R3 round-18（冻结审查 §一.3）：③段信号行的**选行**必须在渲染后文本上做。

    实测反例（修前 exit 0）：保留一条合规信号行，再加一条**渲染等价但 label 被
    切开**的冲突行 —— `来源**覆盖**率：99/3…` / `来源<b>覆盖</b>率：99/3…`。
    原实现用 `re.findall(rf"^.*{label}.*$", s3)` 在 **raw** 行上选行，这两条
    根本进不了「逐条全查」，于是"一条合规一条私货"的双行逃逸成立。

    **它证明什么**：选行与后续整行 fullmatch 都在 `_visible_text()` 上做，
    与 D2 / fallback 两条主链同一个文本空间；零宽形态另有全文门兜底。
    **它不证明什么**：`_visible_text` 仍不是完整 renderer；seed ledger / 五元组 /
    tips / fallback ⑦ 四处 raw 专用绑定**本轮未修**（见验收单 §五之五）。
    """
    m = sys.modules[__name__]
    rs = _load_recap_scan()
    vault = standard_vault(tmp_path)
    scan = collect_json(vault)
    report = write_report(vault, scan)
    base = report.read_text(encoding="utf-8")
    assert run_verify(report).returncode == 0, "基线报告本身就不过 verifier"

    good = "> - 来源覆盖率：2/3 成员含来源锚点【文件】"
    assert good in base, "前提：标准报告必须含这条合规信号行"

    def with_extra(extra: str):
        text = base.replace(good, good + "\n" + extra, 1)
        assert text != base, "注入未命中：报告一字未改，这条门测的是空气"
        report.write_text(text, encoding="utf-8")
        return run_verify(report)

    for extra, why in (
        ("> - 来源覆盖率：99/3 成员含来源锚点【文件】", "对照：裸 label 冲突行"),
        ("> - 来源**覆盖**率：99/3 成员含来源锚点【文件】", "label 被强调标记切开"),
        ("> - 来源<b>覆盖</b>率：99/3 成员含来源锚点【文件】", "label 被 HTML 标签切开"),
        ("> - 来源\u200b覆盖率：99/3 成员含来源锚点【文件】", "label 被零宽切开（全文门兜底）"),
    ):
        assert with_extra(extra).returncode != 0, f"{why}：冲突信号行被放行 —— {extra!r}"

    # 不得误伤：把合规行本身写成渲染等价的强调形态，仍须通过
    report.write_text(
        base.replace(good, "> - 来源**覆盖**率：2/3 成员含来源锚点【文件】", 1),
        encoding="utf-8",
    )
    assert run_verify(report).returncode == 0, "渲染等价的合规行被误判"
