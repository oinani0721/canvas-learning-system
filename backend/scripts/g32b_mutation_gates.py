#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CARD-G3-2b 变异验证 (串行, 逐字节还原)。

判据 (MEMORY reference_gate_design_pitfalls / reference_mutation_script_serial_only):
  - 每个变异把生产代码**精确退回旧实现形态** (同构复现审查者的绕过, 非弱变异);
  - **指定的那道门**必须变红 (不是「某处有失败」);
  - 还原后必须与变异前**逐字节相同**, 否则立即停。
"""

import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = ROOT / "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
BRIDGE = ROOT / "canvas-vault/.claude/scripts/fsrs_bridge.py"
SCHEMA = ROOT / "docs/learning-events-schema-v1.md"
TESTF = "tests/regression/test_g3_2_review_ledger.py"

MUTATIONS = [
    (
        "M1-R1-candidate-spread",
        SKILL,
        '        "payload": {"schema_ext": "review/1", "vault_id": _vid, "concept_id": node_id,\n'
        '                    "rating": rating, "grade_norm": GN2, "review_time": _dup_rt,\n',
        '        "payload": {**{k: v for k, v in _dpl.items() if k not in ("fsrs_library_version", "fsrs_params_hash")},\n'
        '                    "schema_ext": "review/1", "vault_id": _vid, "concept_id": node_id,\n'
        '                    "rating": rating, "grade_norm": GN2, "review_time": _dup_rt,\n',
        "test_r1_unknown_durable_payload_key_conflicts",
    ),
    (
        "M2a-R2-drop-subsecond-check",
        SKILL,
        "    if _dt.microsecond:\n",
        "    if False and _dt.microsecond:\n",
        "test_r2_non_whole_second_durable_review_time_fail_closed",
    ),
    (
        "M2b-R2-drop-utc-offset-check",
        SKILL,
        "    if _dt.tzinfo is None or _dt.utcoffset() != timedelta(0):\n",
        "    if _dt.tzinfo is None:\n",
        "test_r2_non_whole_second_durable_review_time_fail_closed",
    ),
    (
        "M3-R3-attempt-uses-tip",
        SKILL,
        "    if _fsrs_applied or f1:\n        _att_expect = _att_now - _after_applied\n",
        "    if _fsrs_applied or f1:\n        _att_expect = _att_now\n",
        "test_r3_historical_event_replay_is_noop_not_conflict",
    ),
    (
        "M4-R4-normal-path-uses-payload-ts",
        SKILL,
        "\nold, A, B, new = _apply_mastery(fm, review_time)\n",
        '\nold, A, B, new = _apply_mastery(fm, p["ts"])\n',
        "test_r4_recovery_byte_identical_with_idle_and_a3_bump",
    ),
    (
        "M5-R5-drop-rating-consistency",
        BRIDGE,
        "        _expect = rating_from_grade(grade_norm, abandoned)\n"
        "        if rating != _expect:\n"
        "            raise ValueError(\n"
        '                f"显式 rating {rating} 与评分事实不自洽 "\n'
        '                f"(grade_norm={grade_norm!r}, abandoned={abandoned!r} ⇒ 契约值 {_expect})"\n'
        "            )\n",
        "        if abandoned and rating != 1:\n"
        '            raise ValueError(f"abandoned=true 时 rating 恒为 1 (弃答一票否决), 实为 {rating!r}")\n',
        "test_r5_inconsistent_scored_rating_rejected_before_apply",
    ),
    (
        "M6-R7-tail-ignores-lf-state",
        SKILL,
        "            if _ln == _n_lines and not _ends_with_lf:\n",
        "            if _ln == _n_lines:\n",
        "test_r7_corrupt_tail_line_with_lf_is_not_truncation",
    ),
    (
        "M7-R6-schema-drops-owner-clause",
        SCHEMA,
        "**golden manifest 绑定门**承担",
        "由某处承担",
        "test_r6_schema_declares_identity_key_integrity_owner",
    ),
]

MUTATIONS += [
    (
        "M8-6cell-cell4-allow-recovery",
        SKILL,
        '        raise SystemExit(f"[quiz-answer] 事件 {evid} 的 FSRS 已应用但 frontmatter 缺校准记录 — 恢复会引入顺序错乱, fail-closed 请人工核对 {NODE} 与账本")\n',
        "        pass  # MUTANT: 格4 放行 (原为人工裁定 fail-closed)\n",
        "test_six_cell_state_machine_closed",
    ),
    (
        "M9-6cell-cell2-drop-orphan-noop",
        SKILL,
        '    if f1:\n        print(f"[quiz-answer] {NODE}: event={eid} 已完整应用，幂等跳过（无任何改动）；账本无对应行',
        '    if False and f1:\n        print(f"[quiz-answer] {NODE}: event={eid} 已完整应用，幂等跳过（无任何改动）；账本无对应行',
        "test_six_cell_state_machine_closed",
    ),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate(name):
    return subprocess.run(
        [str(ROOT / "backend/.venv/bin/pytest"), f"{TESTF}::{name}", "-q", "-p", "no:cacheprovider", "--tb=no"],
        cwd=str(ROOT / "backend"),
        capture_output=True,
        text=True,
        timeout=900,
        env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


failures = []
for tag, path, old, new, gate in MUTATIONS:
    original = path.read_bytes()
    sha_before = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    n = text.count(old)
    if n != 1:
        failures.append(f"{tag}: 变异锚点命中 {n} 次 (须恰 1) — 未变异, 跳过")
        print(f"[{tag}] ✗ 锚点命中 {n} 次, 跳过")
        continue
    try:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        r = run_gate(gate)
        killed = r.returncode != 0
    finally:
        path.write_bytes(original)  # 逐字节还原 (EXIT 等价: finally 无条件执行)
    sha_after = sha(path)
    if sha_after != sha_before:
        print(f"[{tag}] ✗✗ 还原后字节不同 ({sha_before[:12]} → {sha_after[:12]}) — 立即停")
        sys.exit(2)
    status = "KILLED (门变红)" if killed else "SURVIVED (门未抓住 ⇒ 假门)"
    print(f"[{tag}] {gate} → {status}  [还原字节相同 {sha_after[:12]}]")
    if not killed:
        failures.append(f"{tag}: 门 {gate} 未抓住变异 (SURVIVED)")
        print("    ---- 门输出尾部 ----")
        print("    " + "\n    ".join(r.stdout.strip().split("\n")[-6:]))

print()
if failures:
    print("变异验证 FAIL:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"变异验证 PASS: {len(MUTATIONS)}/{len(MUTATIONS)} 全部被指定门杀死, 全部逐字节还原。")
