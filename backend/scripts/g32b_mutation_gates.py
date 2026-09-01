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
        "M14-N3-drop-duplicate-key-hook",
        SKILL,
        "json.loads(_line.strip(), object_pairs_hook=_no_dup_keys)",
        "json.loads(_line.strip())",
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


MUTATIONS += []


# ── 内部对抗审查 7 条修复的承重变异
MUTATIONS += [
    (
        "M19-B1-drop-rating-completeness",
        SKILL,
        "    if isinstance(_rt_, bool) or not isinstance(_rt_, int) or _rt_ not in (1, 2, 3, 4):\n",
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
    ),
    (
        "M20-B1-drop-gradenorm-completeness",
        SKILL,
        "    if isinstance(_gn_, bool) or not isinstance(_gn_, (int, float)) or not (0.0 <= float(_gn_) <= 1.0):\n",
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
    ),
    (
        "M21-B2-drop-attempt-sync-on-replay",
        SKILL,
        "    if isinstance(_n_, int) and not isinstance(_n_, bool) and _n_ >= 0:\n",
        "    if False:  # MUTANT: A2 重放不同步 attempt\n",
        "test_internal_audit_findings",
    ),
    (
        "M22-B3-whole-file-decode",
        SKILL,
        '            _line = _bline.decode("utf-8-sig" if _ln == 1 else "utf-8")\n',
        '            _line = _bline.decode("utf-8")  # MUTANT: 不剥 BOM\n',
        "test_internal_audit_findings",
    ),
    (
        "M23-C1-drop-event-type-gate",
        SKILL,
        '    if _o.get("event_type") not in ("answer_scored", "answer_abandoned"):\n',
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
    ),
    (
        "M24-C1-drop-concept-id-gate",
        SKILL,
        '    if _pl.get("concept_id") != node_id:\n',
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
    ),
    (
        "M25-C1-drop-vault-id-gate",
        SKILL,
        '    if _pl.get("vault_id") != _vid:\n',
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
    ),
    (
        "M26-C2-drop-eid-whitespace-gate",
        SKILL,
        "if isinstance(eid, str) and eid != eid.strip():\n",
        "if False:  # MUTANT\n",
        "test_internal_audit_findings",
    ),
    (
        "M28-C4-mastery-uses-unrounded-gn",
        SKILL,
        "    a_, b_ = update_after_idle(a_, b_, GN2, days_idle)\n",
        "    a_, b_ = update_after_idle(a_, b_, GN, days_idle)  # MUTANT\n",
        "test_internal_audit_findings",
    ),
]


# ── 账本读取块改为「按字节切行 + 逐行 decode」后，这几条重新锚定到新实现的等价位置
MUTATIONS += [
    (
        # R7：坏行判据（json 解析分支那处，注意 decode 分支也有同形一行）
        "M6b-R7-tail-ignores-lf-state",
        SKILL,
        "            if _ln == _n_lines and not _ends_with_lf:\n"
        '                print(f"[quiz-answer] 账本第 {_ln} 行为截断尾行 (崩溃产物: 非 JSON 且无终止 LF)',
        "            if _ln == _n_lines:  # MUTANT: 忽略 LF 状态\n"
        '                print(f"[quiz-answer] 账本第 {_ln} 行为截断尾行 (崩溃产物: 非 JSON 且无终止 LF)',
        "test_r7_corrupt_tail_line_with_lf_is_not_truncation",
    ),
    (
        # N2：判据必须落在字节上（文本模式的 universal newlines 会把裸 CR 读成 LF）
        "M13b-N2-text-mode-read",
        SKILL,
        '    _raw_bytes = open(EV, "rb").read()\n    _byte_lines = _raw_bytes.split(b"\\n")\n',
        '    _raw_bytes = open(EV, "rb").read()\n'
        '    _byte_lines = [x.encode("utf-8", "surrogateescape") for x in '
        'open(EV, encoding="utf-8", errors="surrogateescape").read().split("\\n")]  # MUTANT: 文本模式\n',
        "test_round1_followups_n1_to_n5",
    ),
    (
        # N4：非 UTF-8 字节必须 clean fail-closed，不是静默替换
        "M15b-N4-decode-with-replace",
        SKILL,
        '            _line = _bline.decode("utf-8-sig" if _ln == 1 else "utf-8")\n',
        '            _line = _bline.decode("utf-8", errors="replace")  # MUTANT\n',
        "test_round1_followups_n1_to_n5",
    ),
    (
        # R7-blank：判据必须是「最后一个非空行」而不是「文件末尾」
        "M18b-R7blank-judge-file-end-not-last-line",
        SKILL,
        "    _last_idx = max((i for i, x in enumerate(_byte_lines) if x.strip()), default=-1)\n"
        "    _ends_with_lf = _last_idx >= 0 and _last_idx < len(_byte_lines) - 1\n",
        '    _ends_with_lf = _raw_bytes.endswith(b"\\n")  # MUTANT: 退回文件末尾判据\n',
        "test_round2_lead_followups",
    ),
    (
        # C3：attempt 正则容引号 —— 打**正常路径**那一处（门㊲⑥ 走的正是它）
        "M27b-C3-attempt-regex-rejects-quotes",
        SKILL,
        "\nmo_att = re.search(r'^attempt_count:\\s*\"?(\\d+)\"?\\s*$', fm, re.M)\n",
        "\nmo_att = re.search(r'^attempt_count:\\s*(\\d+)', fm, re.M)  # MUTANT\n",
        "test_internal_audit_findings",
    ),
]


# ── Codex round-3 的 BLOCKER/HIGH 修复的承重变异
MUTATIONS += [
    (
        "M29-R3-drop-event-version-gate",
        SKILL,
        '    if _o.get("event_version") != 1:\n',
        "    if False:  # MUTANT\n",
        "test_round3_findings",
    ),
    (
        "M30-R3-drop-two-instant-consistency",
        SKILL,
        '    if _instant_only(_ea_, _ctx + " 的 effective_at") != _rt_inst_:\n',
        "    if False:  # MUTANT\n",
        "test_round3_findings",
    ),
    (
        "M31-R3-drop-attempt-required",
        SKILL,
        "    if isinstance(_n0_, bool) or not isinstance(_n0_, int) or _n0_ < 1:\n",
        "    if False:  # MUTANT\n",
        "test_round3_findings",
    ),
    (
        "M32-R3-drop-payload-object-gate",
        SKILL,
        '    if isinstance(_o, dict) and "payload" in _o and not isinstance(_pl, dict):\n',
        "    if False:  # MUTANT\n",
        "test_round3_findings",
    ),
    (
        "M33-R3-merge-recovery-and-append",
        SKILL,
        "if _foreign_replayed:\n",
        "if False:  # MUTANT: 恢复与新写混在一次运行里\n",
        "test_round3_findings",
    ),
    (
        "M34-R3-drop-routing-envelope-gate",
        SKILL,
        '    if isinstance(_o, dict) and not isinstance(_o.get("node_id"), str):\n',
        "    if False:  # MUTANT\n",
        "test_round2_lead_followups",
    ),
]


MUTATIONS += [
    (
        # effective_at 若套上 review_time 的严格字面门就比契约严一档
        "M35-R3-effective-at-over-strict",
        SKILL,
        '    if _instant_only(_ea_, _ctx + " 的 effective_at") != _rt_inst_:\n',
        '    if _durable_instant(_ea_, _ctx + " 的 effective_at") != _rt_inst_:  # MUTANT: 过严\n',
        "test_round3_findings",
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


def is_killed(proc, gate):
    """KILLED = **指定的那道门真的失败了**，不是「某处有失败」。

    pytest 的退出码里只有 1 表示「测试失败」：4 = 用法错误（门名打错、nodeid
    不存在），5 = 一个都没收集到，2 = 中断，3 = 内部错误。这些非 1 的码在
    `rc != 0` 判据下会被当成 KILLED —— 门名一打错，整份变异报告就全绿而毫无
    意义。这正是 MEMORY 里「rc=5 不算红」那条教训的同族。
    """
    if proc.returncode != 1:
        return False, f"rc={proc.returncode}（非 1 = 不是测试失败；4=门名/用法错误 5=零收集）"
    tail = proc.stdout.strip().splitlines()
    summary = tail[-1] if tail else ""
    if "1 failed" not in summary:
        return False, f"rc=1 但摘要不是「1 failed」: {summary[:80]!r}"
    return True, summary[:80]


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
    mutated = text.replace(old, new, 1).encode("utf-8")
    try:
        path.write_bytes(mutated)
        r = run_gate(gate)
        killed, why = is_killed(r, gate)
    finally:
        # 并发编辑防护: 还原写的是**读时快照**, 若变异窗口内有人改了这个文件,
        # 无条件写回会**静默丢掉他的改动**, 而「还原后字节相同」自检比的是自己
        # 的快照, 恒相同、看不见这件事。窗口最长 900s × 多条变异, 不是理论风险。
        now = path.read_bytes()
        third_party = now != mutated
        if third_party:
            # ⛔ 首版这里 sys.exit(3) 且**不还原** —— 那是致命的方向错误: 变异体
            # 会被留在生产文件里。实测代价: 一次触发后 `if False:  # MUTANT` 在
            # SKILL.md 里活了整整一轮, 差点被 commit(靠 grep MUTANT 才抓到)。
            # 正确顺序是「先把第三方内容存证, 再无条件还原」—— 变异体绝不能留,
            # 而第三方改动也不能无声蒸发。
            stash = pathlib.Path(f"/private/tmp/g32b-mutation-thirdparty-{tag}.bak")
            stash.write_bytes(now)
            print(
                f"[{tag}] ⚠️ 变异窗口内 {path.name} 被第三方改动 — 其内容已存证到 {stash}; "
                f"仍按快照还原(变异体不得留在生产文件里), 请人工核对是否需要合并回去"
            )
        path.write_bytes(original)  # 逐字节还原 (finally 无条件执行 = EXIT trap 等价)
    sha_after = sha(path)
    if sha_after != sha_before:
        print(f"[{tag}] ✗✗ 还原后字节不同 ({sha_before[:12]} → {sha_after[:12]}) — 立即停")
        sys.exit(2)
    status = f"KILLED ({why})" if killed else f"SURVIVED ⇒ 假门 ({why})"
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
