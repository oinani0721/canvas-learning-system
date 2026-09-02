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

# 第二层防线: 消费前复用校验器本体。与写点手写的 8 条准入判据**完全重合**
# (2026-09-02 逐形态实测: rating 自洽 / 整秒字面 / rating 与 grade_norm 完整性 /
# event_type / concept_id / vault_id / 两时刻同瞬间 —— 校验器全部都拦)。
# 只删手写那一层, 校验器仍拦住 ⇒ 门不变红 ⇒ 会被误判成「假门」。
# 挂上它, 变异才是「**两层都没了**」, 门重新有鉴别力。
# 见 MEMORY: reference_mutation_must_disable_all_layers。
LAYER2_ALSO = (
    (
        SKILL,
        "    _vio_, _warn_ = validate_record_full(_o, vault_id=_vid, manifest=_GOLDEN_MF)\n",
        "    _vio_, _warn_ = [], []  # MUTANT: 同时禁掉校验器那层\n",
    ),
)


#: round-6 新增的两道前置门（BOM / 空行）排在账本解码与尾行判据**之前**，
#: 会把针对它们的变异先兜住。要证「那两道旧门仍承重」，必须同时禁掉这两道。
LAYER3_ALSO = (
    (
        SKILL,
        '    if _raw_bytes.startswith(b"\\xef\\xbb\\xbf"):\n',
        "    if False:  # MUTANT: 同时禁掉 BOM 门\n",
    ),
    (
        SKILL,
        "    if _blank_at:\n",
        "    if False:  # MUTANT: 同时禁掉空行门\n",
    ),
)

MUTATIONS = [
    (
        # ⚠️ round-8 重绑: candidate 的 payload 已不含时刻键（时刻面移到顶层
        # scored_at）。变异仍打「candidate 从 durable spread」这个原缺陷形态。
        "M1-R1-candidate-spread",
        SKILL,
        '        "payload": {"schema_ext": "review/1", "vault_id": _vid, "concept_id": node_id,\n',
        '        "payload": {**{k: v for k, v in _dpl.items() if k not in ("fsrs_library_version", "fsrs_params_hash", "review_time", "scored_at")},\n'
        '                    "schema_ext": "review/1", "vault_id": _vid, "concept_id": node_id,\n',
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
        "    elif _fsrs_applied or f1:\n        _att_expect = _att_now - _after_applied\n",
        "    elif _fsrs_applied or f1:\n        _att_expect = _att_now  # MUTANT\n",
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
        LAYER2_ALSO,
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
        LAYER2_ALSO,
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
        LAYER2_ALSO,
    ),
    (
        "M14-N3-drop-duplicate-key-hook",
        SKILL,
        "json.loads(_line, object_pairs_hook=_no_dup_keys,\n                                          parse_constant=_reject_json_constant)",
        "json.loads(_line)",
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
        LAYER2_ALSO,
    ),
    (
        "M20-B1-drop-gradenorm-completeness",
        SKILL,
        "    if isinstance(_gn_, bool) or not isinstance(_gn_, (int, float)) or not (0.0 <= float(_gn_) <= 1.0):\n",
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
        LAYER2_ALSO,
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
        LAYER3_ALSO,
    ),
    (
        "M23-C1-drop-event-type-gate",
        SKILL,
        '    if _o.get("event_type") not in ("answer_scored", "answer_abandoned"):\n',
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
        LAYER2_ALSO,
    ),
    (
        "M24-C1-drop-concept-id-gate",
        SKILL,
        '    if _pl.get("concept_id") != node_id:\n',
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
        LAYER2_ALSO,
    ),
    (
        "M25-C1-drop-vault-id-gate",
        SKILL,
        '    if _pl.get("vault_id") != _vid:\n',
        "    if False:  # MUTANT\n",
        "test_internal_audit_findings",
        LAYER2_ALSO,
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
        "    a_, b_ = update_after_idle(a_, b_, GN2 if gn is None else float(gn), days_idle)\n",
        "    a_, b_ = update_after_idle(a_, b_, GN if gn is None else float(gn), days_idle)  # MUTANT\n",
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
        LAYER3_ALSO,
    ),
]


# ── Codex round-3 的 BLOCKER/HIGH 修复的承重变异
MUTATIONS += [
    (
        "M29-R3-drop-event-version-gate",
        SKILL,
        '    if isinstance(_o.get("event_version"), bool) or _o.get("event_version") != 1:\n',
        "    if False:  # MUTANT\n",
        "test_round3_findings",
    ),
    (
        "M30-R3-drop-two-instant-consistency",
        SKILL,
        '    if _instant_only(_ea_, _ctx + " 的 effective_at") != _rt_inst_:\n',
        "    if False:  # MUTANT\n",
        "test_round3_findings",
        LAYER2_ALSO,
    ),
    (
        "M31-R3-drop-attempt-required",
        SKILL,
        "    if isinstance(_n0_, bool) or not isinstance(_n0_, int) or _n0_ < 1:\n",
        "    if False:  # MUTANT\n",
        "test_round3_findings",
    ),
    (
        # ⚠️ round-5 重绑: 原锚点「payload 类型门排在归属判断之前」那一行已被
        # 删除 —— 它正是误拒合法别节点 v2 记录的根因。新结构里等价的门是归属
        # 之后的「本节点缺 payload 即拒」。
        "M32-R3-drop-payload-object-gate",
        SKILL,
        '    if not isinstance(_pl, dict):\n        raise SystemExit(f"[quiz-answer] 账本第 {_ln} 行 (本节点) 缺 payload',
        '    if False:  # MUTANT\n        raise SystemExit(f"[quiz-answer] 账本第 {_ln} 行 (本节点) 缺 payload',
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
        "    if isinstance(_o, dict) and (not isinstance(_nid_, str) or not _nid_.strip() or _nid_ != _nid_.strip()):\n",
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


# ── 「复放评分链副作用」与 attempt 单调性的承重变异
MUTATIONS += [
    (
        # 用 max() 抹平差异 ⇒ 非法低序数被伪装成「单调不减」放过去
        "M38b-attempt-expectation-masked-by-max",
        SKILL,
        "        if _n_ != _exp_n_:\n",
        "        if _n_ != max(_n_, _exp_n_):  # MUTANT: 用 max 抹平\n",
        "test_round3_findings",
    ),
    (
        # F1 在复放 calibration **之后**求值 ⇒ 恒为真 ⇒ attempt 期望值选错档
        "M43-f1-evaluated-after-calibration-replay",
        SKILL,
        "    _already_ = _fm_has_event_compat(fm, _rid_, _ALL_LEDGER_IDS)\n",
        "    _already_ = True  # MUTANT: 恒当作已应用\n",
        "test_round3_findings",
    ),
    (
        # 抹掉 marker 的降级行被当历史行跳过（复用 validator 判定被摘掉）
        "M44-drop-looks-like-review-ext",
        SKILL,
        '        if "schema_ext" in _pl or _looks_like_review_ext(_pl):\n',
        '        if "schema_ext" in _pl:  # MUTANT: 只看 marker 在不在\n',
        "test_round3_findings",
        LAYER2_ALSO,
    ),
    (
        # current dup 与 foreign 同处 pending ⇒ 两阶段永久不收敛
        "M45-allow-dup-and-foreign-same-round",
        SKILL,
        "if _foreign_replayed and len(_foreign_replayed) != len(pending):\n",
        "if False:  # MUTANT: 允许 dup 与 foreign 同轮\n",
        "test_round3_findings",
    ),
    (
        # YAML 单引号标量的 '' 转义不还原 ⇒ F1 假阴性 ⇒ 副作用重复
        "M46-yaml-single-quote-escape",
        SKILL,
        '                v = v[1:-1].replace("\'\'", "\'")\n',
        "                v = v[1:-1]  # MUTANT: 不还原 '' 转义\n",
        # ⚠️ 绑错门的实例: 原绑 test_f1_detection_survives_obsidian_renormalization,
        # 但那道门用的是**裸词**形态 (event_id: xxx 无引号), 走不到单引号分支,
        # 变异当然杀不动 —— SURVIVED 是「门与变异不匹配」, 不是「门是假的」。
        # 测 '' 转义的是 test_round3_findings 的子场景⑬。
        "test_round3_findings",
        LAYER3_ALSO,
    ),
    (
        # 不容单引号 —— YAML 单引号标量是合法形态，Obsidian Properties 会写它
        "M39-attempt-regex-rejects-single-quote",
        SKILL,
        "_ATT_RE = r'^attempt_count:\\s*[\\'\"]?(\\d+)[\\'\"]?\\s*$'\n",
        "_ATT_RE = r'^attempt_count:\\s*\"?(\\d+)\"?\\s*$'  # MUTANT\n",
        "test_round3_findings",
    ),
]


MUTATIONS += []


MUTATIONS += [
    (
        # 未标 out_of_order 的迟到/同秒行被静默放过 ⇒ 那次复习永久漏算
        "M42-late-unmarked-row-silently-skipped",
        SKILL,
        '    if W_inst is None or _inst_ > W_inst or _o_.get("event_id") == evid:\n',
        "    if True:  # MUTANT: 迟到行一律放过\n",
        "test_round2_lead_followups",
    ),
]


# ── 重构后重新锚定（_already_ 抽出、判据合并）
MUTATIONS += [
    (
        "M36b-replay-drops-mastery",
        SKILL,
        '    if _o.get("event_id") != evid and not _already_:\n        _o2_, _A2_, _B2_, _n2_ = _apply_mastery',
        "    if False:  # MUTANT: 不复放 mastery\n        _o2_, _A2_, _B2_, _n2_ = _apply_mastery",
        "test_round3_findings",
    ),
    (
        "M37c-replay-includes-dup-double-eats-ema",
        SKILL,
        '    if _o.get("event_id") != evid and not _already_:\n',
        "    if True:  # MUTANT: 复放也算上 dup 自己\n",
        "test_degraded_legacy_retry_restores_fsrs_without_double_ema",
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


# ── round-4 HIGH/MEDIUM 修复的承重变异（消费前复用校验器本体）
MUTATIONS += [
    (
        # 不复用校验器本体 ⇒ 「缺 payload」「event_version: true」「时刻带空白」
        # 等形态写点放行而校验器拒 —— round-4 报的漏网方向原样复现
        "M47-skip-validator-record-check",
        SKILL,
        "    _vio_, _warn_ = validate_record_full(_o, vault_id=_vid, manifest=_GOLDEN_MF)\n",
        "    _vio_, _warn_ = [], []  # MUTANT: 不复用校验器本体\n",
        "test_round4_writer_validator_verdict_parity",
    ),
    (
        # 归属判断退回「缺 payload 就跳过」之后 ⇒ 本节点缺 payload 的行被静默漏算
        "M48-attribution-check-after-payload-skip",
        SKILL,
        # ⚠️ round-5 重绑: 归属与 payload 检查之间现在隔着版本门与事件类型门,
        # 原来的连续两行锚点不再相邻。变异改为让归属判断**失效**(恒不跳过),
        # 等价复现「别节点的行也被当本节点消费」的旧缺陷面。
        '    if _o.get("node_id") != node_id:\n        continue\n',
        "    if False:  # MUTANT: 归属判断失效\n        continue\n",
        "test_round4_writer_validator_verdict_parity",
    ),
    (
        # 不排除 bool ⇒ `event_version: true` 因 `True == 1` 被当成 v1 消费
        "M49-event-version-accepts-bool",
        SKILL,
        '    if isinstance(_o.get("event_version"), bool) or _o.get("event_version") != 1:\n',
        '    if _o.get("event_version") != 1:  # MUTANT: 不排除 bool\n',
        "test_round4_writer_validator_verdict_parity",
        LAYER2_ALSO,
    ),
    (
        # 顶层非 object 的行退回静默跳过 ⇒ 写点 rc=0 而校验器 rc=1
        "M50-non-object-line-silently-skipped",
        SKILL,
        """    if not isinstance(_o, dict):
        raise SystemExit(f"[quiz-answer] 账本第 {_ln} 行的顶层不是 JSON object""",
        """    if False:  # MUTANT: 顶层非 object 静默跳过
        raise SystemExit(f"[quiz-answer] 账本第 {_ln} 行的顶层不是 JSON object""",
        "test_round4_writer_validator_verdict_parity",
        LAYER2_ALSO,
    ),
]


MUTATIONS += [
    (
        # 行级 .strip() 洗值 ⇒ `\x0c` 被当空白吃掉, 写点放行而校验器判 Extra data
        "M51-line-strip-washes-nonjson-whitespace",
        SKILL,
        "            _rows.append((_ln, json.loads(_line, object_pairs_hook=_no_dup_keys,\n"
        "                                          parse_constant=_reject_json_constant)))\n",
        "            _rows.append((_ln, json.loads(_line.strip(), object_pairs_hook=_no_dup_keys,\n"
        "                                          parse_constant=_reject_json_constant)))  # MUTANT\n",
        "test_round4_writer_validator_verdict_parity",
        LAYER2_ALSO,
    ),
]


MUTATIONS += [
    (
        # 校准写入退回剥前缀 ⇒ `quiz:K` 与 `K` 撞成同一个键 ⇒ 一次复习静默消失
        "M52-calibration-strips-quiz-prefix",
        SKILL,
        '        _e_id = str(ev.get("event_id") or "")\n',
        '        _raw_id = str(ev.get("event_id") or "")  # MUTANT\n'
        '        _e_id = _raw_id[5:] if _raw_id.startswith("quiz:") else _raw_id\n',
        "test_round5_calibration_key_prefix_collision",
    ),
    (
        # F1 查询退回「只查剥前缀形态」⇒ 同一个碰撞从查询侧复现
        "M53-f1-query-strips-prefix-only",
        SKILL,
        "    if _fm_has_event(fm_text, ev_id):\n        _cands.append(ev_id)\n",
        "    if _fm_has_event(fm_text, ev_id[5:] if ev_id.startswith('quiz:') else ev_id):  # MUTANT\n        _cands.append(ev_id)\n",
        "test_round5_calibration_key_prefix_collision",
    ),
]


# ── round-5 修复的承重变异
MUTATIONS += [
    (
        # f1 退回按裸 eid 判 ⇒ 本次 quiz:K 撞上别的事件写下的裸键 K 条目
        "M54-f1-uses-bare-eid",
        SKILL,
        "f1 = bool(eid) and _fm_has_event_compat(fm, evid, _EARLY_LEDGER_IDS)\n",
        "f1 = bool(eid) and _fm_has_event(fm, eid)  # MUTANT\n",
        "test_round5_calibration_key_prefix_collision",
        (
            (
                SKILL,
                "    if _sources and _sources != {ev_id}:\n",
                "    if False:  # MUTANT: 同时禁掉唯一性证明那层\n",
            ),
        ),
    ),
    (
        # 裸键回落不证唯一性 ⇒ 歧义时猜一个, 另一个静默不入账
        "M55-fallback-without-uniqueness-proof",
        SKILL,
        "    if _sources and _sources != {ev_id}:\n",
        "    if False:  # MUTANT: 不证唯一性\n",
        "test_round5_calibration_key_prefix_collision",
    ),
    (
        # 完整校验退回 marker/乱序分流之后 ⇒ 「先放行再校验」
        "M56-full-validation-after-branching",
        SKILL,
        "    _vio_, _warn_ = validate_record_full(_o, vault_id=_vid, manifest=_GOLDEN_MF)\n",
        "    _vio_, _warn_ = [], []  # MUTANT: 分流前不校验\n",
        "test_round5_routing_order_and_input_literal",
    ),
    (
        # 不传 manifest ⇒ 算法身份真值绑定没执行
        "M57-validate-without-golden-manifest",
        SKILL,
        "manifest=_GOLDEN_MF)\n",
        "manifest=None)  # MUTANT\n",
        "test_round5_routing_order_and_input_literal",
    ),
    (
        # 输入 ts 不做字面校验 ⇒ 写点自己产出不合规的账本行
        "M58-input-ts-not-literally-checked",
        SKILL,
        "if not isinstance(_ts_in, str) or not _TS_RE.fullmatch(_ts_in):\n",
        "if False:  # MUTANT: 输入 ts 不校验\n",
        "test_round5_routing_order_and_input_literal",
    ),
]


MUTATIONS += [
    (
        # 序数回推漏计 §6.3 历史行 ⇒ 算出错的期望值并伪装成 envelope 冲突
        "M59-ordinal-ignores-legacy-scored-rows",
        SKILL,
        "    if _legacy_after:\n",
        "    if False:  # MUTANT: 漏计历史行\n",
        "test_round5_legacy_scored_rows_break_ordinal_proof",
    ),
]


# ── round-6 修复的承重变异
MUTATIONS += [
    (
        # ⛔ 正常路径退回存裸 eid ⇒ 与 foreign 路径写的键不是同一个东西
        "M60-normal-path-stores-bare-eid",
        SKILL,
        "        _e_id, _e_pl = evid, p\n",
        "        _e_id, _e_pl = eid, p  # MUTANT\n",
        "test_round6_findings",
    ),
    (
        # durable event_id 首尾空白不做全账本扫描 ⇒ 同一次评分算两遍
        "M61-durable-eid-whitespace-not-scanned",
        SKILL,
        "if _ws_ids:\n",
        "if False:  # MUTANT: 不扫 durable eid 空白\n",
        "test_round6_findings",
    ),
    (
        # node_id 只判类型 ⇒ 空串/纯空白被当别节点静默跳过
        "M62-node-id-type-only",
        SKILL,
        "if isinstance(_o, dict) and (not isinstance(_nid_, str) or not _nid_.strip() or _nid_ != _nid_.strip()):\n",
        "if isinstance(_o, dict) and not isinstance(_nid_, str):  # MUTANT\n",
        "test_round6_findings",
    ),
    (
        # match 而非 fullmatch ⇒ 末尾换行穿透
        "M63-ts-match-not-fullmatch",
        SKILL,
        "if not isinstance(_ts_in, str) or not _TS_RE.fullmatch(_ts_in):\n",
        "if not isinstance(_ts_in, str) or not _TS_RE.match(_ts_in):  # MUTANT\n",
        "test_round6_findings",
    ),
    (
        # 输出侧不禁 NaN ⇒ 程序自己产出不合规的行
        "M64-dumps-allows-nan",
        SKILL,
        "json.dumps(rec, ensure_ascii=False, allow_nan=False)",
        "json.dumps(rec, ensure_ascii=False)  # MUTANT",
        "test_round6_findings",
    ),
    (
        # 读取侧不禁 NaN ⇒ 与严格校验器分叉
        "M65-loads-allows-nan",
        SKILL,
        "                                          parse_constant=_reject_json_constant)))\n",
        "                                          )))  # MUTANT: 读取侧不禁 NaN\n",
        "test_round6_findings",
    ),
    (
        # 同 ID 的合法 §6.3 历史行退回无条件拒 ⇒ 违反 A4.5 幂等
        "M66-legacy-same-id-rejected",
        SKILL,
        "        if isinstance(_dpl, dict) and not _looks_like_review_ext(_dpl):\n",
        "        if False:  # MUTANT: 同 ID 历史行无条件拒\n",
        "test_round6_findings",
    ),
    (
        # inline 空列表不规范化 ⇒ 产出非法 YAML 且永久不收敛
        "M67-inline-calibration-not-normalized",
        SKILL,
        "    fm_text = _normalize_inline_calibration(fm_text)\n",
        "    pass  # MUTANT: 不规范化 inline 空列表\n",
        "test_round6_findings",
    ),
    (
        # 空行不拒 ⇒ 与校验器分叉
        "M68-blank-lines-tolerated",
        SKILL,
        "    if _blank_at:\n",
        "    if False:  # MUTANT: 空行放行\n",
        "test_round6_findings",
    ),
    (
        # BOM 不拒 ⇒ 与校验器分叉
        "M69-bom-tolerated",
        SKILL,
        '    if _raw_bytes.startswith(b"\\xef\\xbb\\xbf"):\n',
        "    if False:  # MUTANT: BOM 放行\n",
        "test_round6_findings",
    ),
]


MUTATIONS += [
    (
        # 序数退回只按 W 判 ⇒ degraded 落账的后继事件不算，误拒合法历史重试
        "M70-ordinal-w-only-not-calibration",
        SKILL,
        '        and _fm_has_event_compat(fm, str(_o4.get("event_id") or ""), _ALL_LEDGER_IDS)\n',
        "        and (W_inst is not None and _i <= W_inst)  # MUTANT: 只按 W 判\n",
        "test_round6_ordinal_evidence",
    ),
    (
        # 不用账本可证的序数 ⇒ 带合法 attempt_count 的历史行也被无条件拒
        "M71-ignore-provable-legacy-ordinal",
        SKILL,
        "    if _prov is not None:\n",
        "    if False:  # MUTANT: 不用账本可证序数\n",
        "test_round6_ordinal_evidence",
    ),
]


# ── round-7 修复的承重变异
MUTATIONS += [
    (
        # exact 命中直接返回 ⇒ 绕过歧义检查
        "M72-exact-hit-bypasses-ambiguity",
        SKILL,
        "    _cands = []\n    if _fm_has_event(fm_text, ev_id):\n        _cands.append(ev_id)\n",
        "    _cands = []\n    if _fm_has_event(fm_text, ev_id):\n        return True  # MUTANT\n",
        "test_round7_findings",
    ),
    (
        # 全账迟到扫描退回分诊之后 ⇒ 幂等早退绕过它
        "M73-late-scan-after-early-exit",
        SKILL,
        'for _inst_, _ln_, _o_ in _applicable:\n    if W_inst is None or _inst_ > W_inst or _o_.get("event_id") == evid:\n        continue\n',
        'for _inst_, _ln_, _o_ in []:  # MUTANT: 扫描失效\n    if W_inst is None or _inst_ > W_inst or _o_.get("event_id") == evid:\n        continue\n',
        "test_round7_findings",
    ),
    (
        # candidate 抄 durable 的业务时刻 ⇒ 同 ID 换时刻看不出
        # ⚠️ round-8 重绑: 时刻面已统一到顶层 scored_at（此前分散在 effective_at
        # 与 payload.review_time 两处）。变异打「candidate 抄 durable 时刻」这个
        # 原缺陷形态 —— 抄了就无法识别「同 ID 换了业务时刻」。
        "M74-candidate-copies-durable-rt",
        SKILL,
        '        "scored_at": _SCORED_AT,\n        "payload": {"schema_ext"',
        '        "scored_at": _their_scored,  # MUTANT\n        "payload": {"schema_ext"',
        "test_round7_findings",
    ),
    (
        # W 兜底回来 ⇒ calibration 判据形同虚设
        # ⚠️ 挂第二层: 删掉后继事件的校准条目后, **前移的全账迟到扫描**(B② 的
        # 修复)会先拦下来 —— 那是纵深, 不是「W 兜底没用」。要证 W 兜底确实会
        # 掩盖 calibration 判据, 必须同时禁掉那道扫描。
        "M75-w-fallback-restored",
        SKILL,
        '        and _fm_has_event_compat(fm, str(_o4.get("event_id") or ""), _ALL_LEDGER_IDS)\n',
        '        and (_fm_has_event_compat(fm, str(_o4.get("event_id") or ""), _ALL_LEDGER_IDS)\n             or (W_inst is not None and _i <= W_inst))  # MUTANT\n',
        "test_round7_findings",
        (
            (
                SKILL,
                'for _inst_, _ln_, _o_ in _applicable:\n    if W_inst is None or _inst_ > W_inst or _o_.get("event_id") == evid:\n        continue\n',
                'for _inst_, _ln_, _o_ in []:  # MUTANT: 同时禁掉全账迟到扫描\n    if W_inst is None or _inst_ > W_inst or _o_.get("event_id") == evid:\n        continue\n',
            ),
        ),
    ),
    (
        # 本次事件自身的 node_id 门失效
        "M76-self-node-id-gate-dropped",
        SKILL,
        "if not isinstance(node_id, str) or not node_id.strip() or node_id != node_id.strip():\n",
        "if False:  # MUTANT: 自身 node_id 不校验\n",
        "test_round7_ordinal_gap_and_self_node_id",
    ),
    (
        # 序数证明固定减 1，不按 gap 折算
        "M77-ordinal-fixed-minus-one",
        SKILL,
        "                _prov = (_l3, _n3 - _gap)\n",
        "                _prov = (_l3, _n3)  # MUTANT: 不折算 gap\n",
        "test_round7_ordinal_gap_and_self_node_id",
    ),
]


# ── round-8 修复的承重变异
MUTATIONS += [
    (
        # ⚠️ 这条变异**打不出缺陷**（第五种成因: 变异没把缺陷完整放回来）。
        # round-8 把 scored_at 独立记录、envelope 比它之后，「首写传哪个时刻给
        # bridge」只影响 **A3 采用值**，恢复能力不再依赖它 —— 实测变异后崩溃
        # 续跑仍 rc=0。要复现原缺陷必须**同时**让 scored_at 也退回 p["ts"]。
        "M78-first-write-uses-run-ts",
        SKILL,
        "_out, _err = _bridge(fm, GN2, abandoned, _SCORED_AT, rating=rating)\n",
        '_out, _err = _bridge(fm, GN2, abandoned, p["ts"], rating=rating)  # MUTANT\n',
        "test_round8_stable_scored_at",
        (
            (
                SKILL,
                '                       "scored_at": _SCORED_AT,\n',
                '                       "scored_at": p["ts"],  # MUTANT: 同时退回运行时刻\n',
            ),
        ),
    ),
    (
        # 缺稳定时刻回抄 durable ⇒ 整条修复被架空
        "M79-missing-scored-at-falls-back",
        SKILL,
        "if not isinstance(_SCORED_AT, str) or not _TS_RE.fullmatch(_SCORED_AT):\n",
        "if False:  # MUTANT: 缺稳定时刻不拦\n",
        "test_round8_stable_scored_at",
    ),
    (
        # envelope 比 A3 采用值而非原始时刻 ⇒ A3 生效时续跑必冲突
        "M80-envelope-compares-adopted-rt",
        SKILL,
        '        "scored_at": _SCORED_AT,\n        "payload": {"schema_ext": "review/1", "vault_id": _vid,',
        '        "scored_at": _dpl.get("review_time"),  # MUTANT: 比 A3 采用值\n        "payload": {"schema_ext": "review/1", "vault_id": _vid,',
        "test_round8_stable_scored_at",
    ),
    (
        # 无 marker 历史行的 out_of_order 被赋予契约语义 ⇒ 序数正反颠倒
        "M81-legacy-out-of-order-honored",
        SKILL,
        '            if _pl3.get("schema_ext") == "review/1" and _pl3.get("out_of_order") is True:\n',
        '            if _pl3.get("out_of_order") is True:  # MUTANT\n',
        "test_round8_high_findings",
    ),
    (
        # 校准 header 正则不容尾注释 ⇒ F1 假阴性、两阶段永久停住
        "M82-calibration-header-no-comment",
        SKILL,
        "    mcal = re.search(r'^calibration_log:[ \\t]*(?:#[^\\n]*)?$', fm_text, re.M)\n",
        "    mcal = re.search(r'^calibration_log:[ \\t]*$', fm_text, re.M)  # MUTANT\n",
        "test_round8_high_findings",
    ),
    (
        # 空白 id 门退回全账 ⇒ 别节点的合法存量行阻塞整个 vault
        "M83-whitespace-id-gate-global",
        SKILL,
        '                  and _r.get("node_id") == node_id\n',
        "                  and True  # MUTANT: 退回全账\n",
        "test_round8_high_findings",
    ),
]


# ⛔ 执行块必须包在 main() 里 (2026-09-02 事故):
# 此前它是**模块顶层**代码, 于是任何 `import g32b_mutation_gates`
# (探针脚本 / 锚点体检脚本想复用 MUTATIONS 表时都会这么做) 都会**立刻跑全套
# 变异并改写生产文件**。实测代价: 两个 import 各触发一次全套变异, 与前台那次
# **并行**跑, 三方交错互相把对方的变异体当「第三方改动」存证再还原到自己的快照
# ⇒ SKILL.md 留下 M42 的变异体、契约文件留下 M7 的变异体, 而每条变异各自的
# 「还原后字节相同」自检**全部显示通过**(它比的是自己的快照)。
# 见 MEMORY: reference_mutation_script_serial_only / reference_parallel_session_file_collision。
def main():
    failures = []
    for _m in MUTATIONS:
        # 第 6 元素 (可选): [(old, new), ...] —— **同时**施加的其它防线变异。
        # ⛔ 为什么需要它 (MEMORY reference_mutation_must_disable_all_layers):
        # 本卡消费前复用了校验器本体 validate_record_full(), 它与写点手写的 8 条
        # 准入判据**完全重合** (2026-09-02 逐形态实测: rating 自洽 / 整秒字面 /
        # rating 与 grade_norm 完整性 / event_type / concept_id / vault_id /
        # 两时刻同瞬间, 校验器**全部都拦**)。只删手写那一层, 校验器仍拦住 ⇒ 门不
        # 变红 ⇒ 被误判成「假门」。真正要证的是「**两层都没了**才会漏」。
        tag, path, old, new, gate = _m[:5]
        # 第 6 元素的每项是 (target_path, old, new) —— **跨文件**, 因为第二层防线
        # (SKILL.md 里的 validate_record_full 调用) 未必与主变异同一个文件
        # (如 M5 的主变异在 fsrs_bridge.py)。
        also = _m[5] if len(_m) > 5 else ()
        edits = [(path, old, new)] + [tuple(x) for x in also]
        originals = {}
        for _p, _, _ in edits:
            if _p not in originals:
                originals[_p] = _p.read_bytes()
        texts = {p: b.decode("utf-8") for p, b in originals.items()}
        _anchor_bad = False
        for _p, _o, _n in edits:
            c = texts[_p].count(_o)
            if c != 1:
                which = "变异" if (_p, _o, _n) == edits[0] else "同层"
                failures.append(f"{tag}: {which}锚点在 {_p.name} 命中 {c} 次 (须恰 1) — 未变异, 跳过")
                print(f"[{tag}] ✗ {which}锚点在 {_p.name} 命中 {c} 次, 跳过")
                _anchor_bad = True
                break
            texts[_p] = texts[_p].replace(_o, _n, 1)
        if _anchor_bad:
            continue
        mutated = {p: t.encode("utf-8") for p, t in texts.items()}
        try:
            for _p, _b in mutated.items():
                _p.write_bytes(_b)
            r = run_gate(gate)
            killed, why = is_killed(r, gate)
        finally:
            # 并发编辑防护: 还原写的是**读时快照**, 若变异窗口内有人改了这个文件,
            # 无条件写回会**静默丢掉他的改动**, 而「还原后字节相同」自检比的是自己
            # 的快照, 恒相同、看不见这件事。窗口最长 900s × 多条变异, 不是理论风险。
            # ⚠️ 并行下这道自检**是自证** —— 2026-09-02 三个变异进程交错跑, 每条各自
            # 都显示「还原成功」, 却在生产文件里留下了别人的变异体。外部锚点
            # (grep MUTANT + 与已知良好 sha 比对) 才是证据。见 MEMORY:
            # reference_mutation_script_module_level_side_effects。
            for _p, _b in mutated.items():
                now = _p.read_bytes()
                if now != _b:
                    # ⛔ 首版这里 sys.exit(3) 且**不还原** —— 那是致命的方向错误: 变异体
                    # 会被留在生产文件里。实测代价: 一次触发后 `if False:  # MUTANT` 在
                    # SKILL.md 里活了整整一轮, 差点被 commit(靠 grep MUTANT 才抓到)。
                    # 正确顺序是「先把第三方内容存证, 再无条件还原」—— 变异体绝不能留,
                    # 而第三方改动也不能无声蒸发。
                    stash = pathlib.Path(f"/private/tmp/g32b-mutation-thirdparty-{tag}-{_p.name}.bak")
                    stash.write_bytes(now)
                    print(
                        f"[{tag}] ⚠️ 变异窗口内 {_p.name} 被第三方改动 — 其内容已存证到 {stash}; "
                        f"仍按快照还原(变异体不得留在生产文件里), 请人工核对是否需要合并回去"
                    )
                _p.write_bytes(originals[_p])  # 逐字节还原 (finally 无条件 = EXIT trap 等价)
        _drift = [
            _p.name
            for _p in originals
            if hashlib.sha256(_p.read_bytes()).hexdigest() != hashlib.sha256(originals[_p]).hexdigest()
        ]
        if _drift:
            print(f"[{tag}] ✗✗ 还原后字节不同: {', '.join(_drift)} — 立即停")
            sys.exit(2)
        sha_after = sha(path)
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


if __name__ == "__main__":
    main()
