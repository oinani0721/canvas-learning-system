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


MUTATIONS += [
    (
        "M10-R2-value-not-literal",
        SKILL,
        "    if not _WHOLE_SECOND_RE.match(rt.strip()):\n",
        "    if False and not _WHOLE_SECOND_RE.match(rt.strip()):  # MUTANT: 退回只看解析后的值\n",
        "test_r2_non_whole_second_durable_review_time_fail_closed",
    ),
]


# ── round-1 后续 N1-N5 的承重变异（每条精确退回修复前形态）
MUTATIONS += [
    (
        "M11-N1-drop-out-of-order-semantic-gate",
        SKILL,
        "        if W_inst is None or _oo_inst > W_inst:\n",
        "        if False and (W_inst is None or _oo_inst > W_inst):  # MUTANT\n",
        "test_round1_followups_n1_to_n5",
    ),
    (
        "M12-N1-drop-out-of-order-shape-gate",
        SKILL,
        '        if _pl["out_of_order"] is not True:\n',
        '        if False and _pl["out_of_order"] is not True:  # MUTANT\n',
        "test_round1_followups_n1_to_n5",
    ),
    (
        # ⚠️ 首版 M13 打在 `endswith(b"\\n")` 上并**存活** —— 那不是承重点:
        # bytes.decode() 不做 universal newlines, 只有文本模式 open(encoding=)
        # 做。真正的承重点是「二进制读 vs 文本模式读」, 变异必须打在那一处。
        "M13-N2-text-mode-read",
        SKILL,
        '    _raw_bytes = open(EV, "rb").read()\n'
        "    try:\n"
        '        _raw_text = _raw_bytes.decode("utf-8")\n'
        "    except UnicodeDecodeError as _ue:\n",
        '    _raw_text = open(EV, encoding="utf-8").read()  # MUTANT: 退回文本模式读\n'
        "    if False:\n"
        "        _ue = None\n"
        "    elif False:\n",
        "test_round1_followups_n1_to_n5",
    ),
    (
        "M14-N3-drop-duplicate-key-hook",
        SKILL,
        "json.loads(_line.strip(), object_pairs_hook=_no_dup_keys)",
        "json.loads(_line.strip())",
        "test_round1_followups_n1_to_n5",
    ),
    (
        "M15-N4-decode-with-replace",
        SKILL,
        '        _raw_text = _raw_bytes.decode("utf-8")\n',
        '        _raw_text = _raw_bytes.decode("utf-8", errors="replace")  # MUTANT\n',
        "test_round1_followups_n1_to_n5",
    ),
    (
        "M16-N5-hard-compute-attempt-across-pending",
        SKILL,
        "        if _before_pending:\n",
        "        if False and _before_pending:  # MUTANT: 退回硬算\n",
        "test_round1_followups_n1_to_n5",
    ),
]


MUTATIONS += [
    (
        "M17-N1-schema-drops-writer-side-clause",
        SCHEMA,
        "写点（在线 A2）侧同款语义门",
        "写点侧不另作要求",
        "test_r6_schema_declares_identity_key_integrity_owner",
    ),
]


MUTATIONS += [
    (
        # 判据退回「文件末尾有无 LF」——末尾多一个纯空白行就让它失真。
        "M18-R7blank-judge-file-end-not-last-line",
        SKILL,
        "    _last_idx = max((i for i, x in enumerate(_raw_lines) if x.strip()), default=-1)\n"
        "    _ends_with_lf = _last_idx >= 0 and _last_idx < len(_raw_lines) - 1\n",
        '    _ends_with_lf = _raw_bytes.endswith(b"\\n")  # MUTANT: 退回文件末尾判据\n',
        "test_round2_lead_followups",
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
