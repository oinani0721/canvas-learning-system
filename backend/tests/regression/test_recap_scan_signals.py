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
import re
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
    ledger_seed = "- SeedA — 批注 2 条"
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
    assert "未闭合 HTML 注释" in r.stdout


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
    assert "尾部说明夹带第二组计数" in r.stdout


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
    assert "尾部说明夹带第二组计数" in r.stdout


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
    assert "尾部说明夹带第二组计数" in r.stdout


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
        f"---\ntype: whiteboard\n---\n\n# {bad}\n\n## Concepts\n\n- [[节点/SeedA]]\n", encoding="utf-8"
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
