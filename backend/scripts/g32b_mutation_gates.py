#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CARD-G3-2b 变异验证 (串行, 逐字节还原)。

判据 (MEMORY reference_gate_design_pitfalls / reference_mutation_script_serial_only):
  - 每个变异把生产代码**精确退回旧实现形态** (同构复现审查者的绕过, 非弱变异);
  - **指定的那道门**必须变红 (不是「某处有失败」);
  - 还原后必须与变异前**逐字节相同**, 否则立即停。
"""

import collections
import hashlib
import pathlib
import re
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
        '        print(f"[quiz-answer] {NODE}: event={eid} 已完整应用（receipt 事实一致且调度已覆盖），幂等跳过（无任何改动）；账本无对应行',
        '        _ = (f"[quiz-answer] {NODE}: event={eid} 已完整应用（receipt 事实一致且调度已覆盖），幂等跳过（无任何改动）；账本无对应行',
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
    # ⛔ M22-B3-whole-file-decode 已**退役**（round-11b, 如实记录而非静默删除）:
    # 变异体是「per-line decode 不剥 BOM」。三态诊断实测**变异体单独跑门全绿** ——
    # 因为 round-6 起写点有一道**显式 BOM 门**(与校验器同口径拒收), 它排在解析之前,
    # BOM 输入根本走不到 decode 那一步。也就是说 `utf-8-sig` 那层已是**被取代的
    # 死纵深**, 不可能承重。原先它挂的两层(BOM 门 + 空行门)拆的正是被测防线本身,
    # 只加层门就红 ⇒ 假杀。BOM 行为由 M68/M69 与门㊳的 BOM 场景直接守着。
    (
        "M23-C1-drop-event-type-gate",
        SKILL,
        '    if _o.get("event_type") not in ("answer_scored", "answer_abandoned"):\n',
        "    if False:  # MUTANT\n",
        "test_round11b_c1_event_type_narrow",  # round-11b: 由粗门改绑窄门, 让击杀可独立归因
        LAYER2_ALSO,
    ),
    (
        "M24-C1-drop-concept-id-gate",
        SKILL,
        '    if _nkey(_pl.get("concept_id")) != _NODE_KEY:\n',
        "    if False:  # MUTANT\n",
        "test_round11b_c1_concept_id_narrow",  # round-11b: 由粗门改绑窄门, 让击杀可独立归因
        LAYER2_ALSO,
    ),
    (
        "M25-C1-drop-vault-id-gate",
        SKILL,
        '    if _pl.get("vault_id") != _vid:\n',
        "    if False:  # MUTANT\n",
        "test_round11b_c1_vault_id_narrow",  # round-11b: 由粗门改绑窄门, 让击杀可独立归因
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
        # ⚠️ round-11 重绑: _already_ 现由统一 resolver 决定（不再是布尔 presence）
        "    _already_ = _rcpt_fg is not None\n",
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
        # ⚠️ 三层: BOM 门 + 空行门（LAYER3）+ **YAML 回落**。改用 PyYAML 后，
        # 正则里的 '' 转义分支**根本走不到** —— 不强制回落就打不中这个缺陷面。
        LAYER3_ALSO
        + (
            (
                SKILL,
                "        import yaml  # F1 判定\n",
                "        raise ImportError('MUTANT: 同时强制走正则回落')\n",
            ),
        ),
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
        [str(ROOT / "backend/.venv/bin/pytest"), f"{TESTF}::{name}", "-q", "-p", "no:cacheprovider", "--tb=line"],
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
        '    if _nkey(_o.get("node_id")) != _NODE_KEY:\n        continue\n',
        "    if False:  # MUTANT: 归属判断失效\n        continue\n",
        "test_round4_writer_validator_verdict_parity",
    ),
    (
        # 不排除 bool ⇒ `event_version: true` 因 `True == 1` 被当成 v1 消费
        "M49-event-version-accepts-bool",
        SKILL,
        '    if isinstance(_o.get("event_version"), bool) or _o.get("event_version") != 1:\n',
        '    if _o.get("event_version") != 1:  # MUTANT: 不排除 bool\n',
        "test_round11b_parity_event_version_bool_narrow",  # round-11b: 粗门→窄门, 击杀可独立归因
        LAYER2_ALSO,
    ),
    (
        # 顶层非 object 的行退回静默跳过 ⇒ 写点 rc=0 而校验器 rc=1
        "M50-non-object-line-silently-skipped",
        SKILL,
        # ⚠️ 忠实形态是 **continue**（原缺陷正是「适用集静默跳过」），不是 `if False:` ——
        # 后者会让 `[]` 落到下面的 `_o.get(...)`, 在 list 上抛 AttributeError, 写点
        # 照样非零退出 ⇒ 缺陷根本没被放回来（成因⑤ 覆盖不完整），门当然抓不到。
        """    if not isinstance(_o, dict):
        raise SystemExit(f"[quiz-answer] 账本第 {_ln} 行的顶层不是 JSON object""",
        """    if not isinstance(_o, dict):
        continue  # MUTANT: 顶层非 object 静默跳过
        raise SystemExit(f"[quiz-answer] 账本第 {_ln} 行的顶层不是 JSON object""",
        "test_round11b_parity_toplevel_non_object_narrow",  # round-11b: 粗门→窄门, 击杀可独立归因
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
        # ⚠️ 原挂 LAYER2_ALSO（禁校验器）—— 三态诊断实测**变异体单独即可杀**,
        # 且失败身份与只加层时相同 ⇒ 层是多余的, 挂着只会把击杀归因搅浑。
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
        # ⚠️ round-11b: 该片段原先在 resolver 与 compat 里**各有一份**(本条变异
        # 存活正是发现者 —— 打了 resolver 那份, 而门的场景走 compat 那份)。
        # 统一到 `_cands_and_sources` 后, 锚点跟着搬到唯一实现上。
        "    _cands = []\n    if _fm_has_event(fm_text, ev_id):\n        _cands.append(ev_id)",
        "    _cands = []\n    if _fm_has_event(fm_text, ev_id[5:] if ev_id.startswith('quiz:') else ev_id):  # MUTANT\n        _cands.append(ev_id)",
        "test_round5_calibration_key_prefix_collision",
        # ⚠️ 原挂两层（禁 facts + 拆 compat 歧义证明）—— 后者**正是本门要测的那道
        # 防线**, 拆了它门必红, 于是变成假杀。三态诊断实测: 变异体单独即可杀
        # (败在验伪断言「正常场景回归」—— 漏放的那次复习正是原缺陷的表现)。
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
            # ⚠️ round-12 depth 层: `≤W` 全账扫描现在也走 resolver + 完整事实,
            # 它会先于本站点拦住同类缺陷 ⇒ 变异体单独杀不动。拆掉**那一道**(不是
            # 被测的这一道), 让 compat 侧成为唯一屏障。
            (
                SKILL,
                'for _inst_, _ln_, _o_ in _applicable:\n    if W_inst is None or _inst_ > W_inst or _o_.get("event_id") == evid:\n        continue\n',
                'for _inst_, _ln_, _o_ in []:  # MUTANT: 拆掉 ≤W 扫描这道纵深\n    if W_inst is None or _inst_ > W_inst or _o_.get("event_id") == evid:\n        continue\n',
            ),
            # ⛔ 补齐**同一条防线的其余站点**(不是拆别的防线): 「按完整 id 查、
            # 裸键仅在映射可证唯一时回落」这条判据有**三个**调用点。只打 f1 那个时,
            # 迟到扫描与 pending 计数那两个仍在用 compat, 缺陷被它们兜住 ⇒ 门不红。
            # 原先挂的「拆 compat 歧义证明」是**错的层**: 那正是本门要测的防线。
            (
                SKILL,
                # ⚠️ round-12 重绑: `≤W` 扫描已改走 resolver, 原来那个 compat 调用点消失。
                # 同防线的仍存在站点是崩溃窗采用时刻证明里的这一处。
                "    if W_inst is None and not _fm_has_event_compat(fm, evid, _ALL_LEDGER_IDS):\n",
                "    if W_inst is None and not _fm_has_event(fm, evid):  # MUTANT: 第二站点同样退回裸查\n",
            ),
            (
                SKILL,
                '        and _fm_has_event_compat(fm, str(_o4.get("event_id") or ""), _ALL_LEDGER_IDS)\n',
                '        and _fm_has_event(fm, str(_o4.get("event_id") or ""))  # MUTANT: 第三站点\n',
            ),
        ),
        "complete",
    ),
    # ⛔ M55-fallback-without-uniqueness-proof 已**退役**（round-12, 如实记录）:
    # 变异体打的是 compat 侧的歧义证明 `if _sources and _sources != {ev_id}`。
    # round-12 把 `≤W` 全账扫描也改走统一 resolver + 完整事实之后, **那道扫描在
    # 所有可构造的场景里都先于 compat 拦住同一类歧义** —— 三态诊断实测: 变异体
    # 单独跑门全绿; 而挂上「拆掉 ≤W 扫描」这层之后, **只加层门就已经红**
    # (空变异对照判定为假杀) ⇒ 击杀完全由层贡献。
    # 与 M22 同类: **被取代的纵深**。守卫本身保留(便宜且无害), 但它不可能承重,
    # 保留变异只会逼出一个假杀。该性质现由 `≤W` 扫描侧的 M115 与门(67) 直接守着。
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
        # ⚠️ round-9 收窄: `manifest=_GOLDEN_MF)` 现在有两处（消费侧校验 + 产出侧
        # 自检）。锚点带上消费侧的上下文，避免命中 2 次而被静默跳过。
        "    _vio_, _warn_ = validate_record_full(_o, vault_id=_vid, manifest=_GOLDEN_MF)\n",
        "    _vio_, _warn_ = validate_record_full(_o, vault_id=_vid, manifest=None)  # MUTANT\n",
        "test_round5_routing_order_and_input_literal",
    ),
    (
        # 输入 ts 不做字面校验 ⇒ 写点自己产出不合规的账本行
        "M58-input-ts-not-literally-checked",
        SKILL,
        # ⚠️ round-9 挂第二层: 新加的**产出侧自检**（append 前跑 validate_record_full）
        # 会接管入口 ts 门的职责 —— 禁掉入口门后，带空白的 ts 被自检以
        # 「recorded_at 不符 §三 受理语法」拦下。要证入口门仍承重，须同时禁掉自检。
        "if not isinstance(_ts_in, str) or not _TS_RE.fullmatch(_ts_in):\n",
        "if False:  # MUTANT: 输入 ts 不校验\n",
        "test_round5_routing_order_and_input_literal",
        (
            (
                SKILL,
                "        _self_vio, _ = validate_record_full(rec, vault_id=_vid, manifest=_GOLDEN_MF)\n",
                "        _self_vio = []  # MUTANT: 同时禁掉产出侧自检\n",
            ),
        ),
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
        # ⚠️ round-10 挂第二层: **结构化写回**(PyYAML)已接管这条路径 —— 即使不
        # 规范化 inline 空列表, 结构化分支也能正确追加。要证这道规范化仍承重,
        # 必须同时强制走正则回落。(第五种成因: 缺陷面被修复消除)
        "M67-inline-calibration-not-normalized",
        SKILL,
        "    fm_text = _normalize_inline_calibration(fm_text)\n",
        "    pass  # MUTANT: 不规范化 inline 空列表\n",
        "test_round6_findings",
        (
            (
                SKILL,
                "        import yaml as _y\n",
                "        raise ImportError('MUTANT: 同时强制走正则写回')\n",
            ),
        ),
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
        # ⛔ 忠实复原 round-7 原缺陷: compat 侧 exact 命中**直接 return True**,
        # 绕过来源反查 ⇒ 历史裸形态与完整形态别名成一个, 另一次评分静默不入账。
        # ⚠️ 本条原先打的是 resolver 的 `if not _cands: return (None, None)` ——
        # 那是**死变异**: 该行唯一可达的调用点 (dup 路径 L1360) **丢弃返回值**,
        # 变异前后行为逐字相同, 门永远抓不到。死变异不是「门非承重」, 是变异选错行。
        "M72-exact-hit-bypasses-ambiguity",
        SKILL,
        "    _cands, _sources = _cands_and_sources(fm_text, ev_id, all_ledger_ids)\n    if not _cands:\n        return False\n",
        "    if _fm_has_event(fm_text, ev_id):  # MUTANT: exact 命中直接放行\n        return True\n    _cands, _sources = _cands_and_sources(fm_text, ev_id, all_ledger_ids)\n    if not _cands:\n        return False\n",
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
        # round-11b: 原绑**粗门** ⇒ 同层(禁全账迟到扫描)会在该门靠前的 B② 就把门
        # 弄红, M① 这段执行不到 ⇒ 假杀。改绑只跑 M① 的窄门; **层保留** ——
        # 迟到扫描是另一道会先拦住同一场景的独立防线, 属正当纵深(见上方注释)。
        "test_round11b_no_w_fallback_narrow",
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
        # round-11b: 改绑只看「FSRS 落在哪个时刻」的窄门（原粗门里同层拆的正是
        # 该门 B① 断言的 `scored_at`，那是假杀）。
        # ⚠️ 二次修订: 曾把落账侧 scored_at 作为 "complete" 第二站点挂上, 但对照
        # 实测**变异体单独即可杀**（在这道窄门上）⇒ 层是多余的, 撤掉。上面 docstring
        # 里「必须同时让 scored_at 退回」那句是**旧粗门下的推断**, 换窄门后不成立。
        # ⛔「变异体单独够不够」只能实测, 不能照抄旧结论。
        "test_round11b_fsrs_uses_stable_business_time",
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
        (
            (
                SKILL,
                "        import yaml as _y\n",
                "        raise ImportError('MUTANT: 同时禁掉写回侧 YAML')\n",
            ),
            (
                SKILL,
                "        import yaml  # F1 判定\n",
                "        raise ImportError('MUTANT: 同时强制走正则回落')\n",
            ),
        ),
    ),
    (
        # 空白 id 门退回全账 ⇒ 别节点的合法存量行阻塞整个 vault
        "M83-whitespace-id-gate-global",
        SKILL,
        '                  and _nkey(_r.get("node_id")) == _NODE_KEY\n',
        "                  and True  # MUTANT: 退回全账\n",
        "test_round8_high_findings",
    ),
]


# ── round-9 修复的承重变异
MUTATIONS += [
    (
        # 同 event_id 的别节点行不进冲突域 ⇒ 本次评分零次应用
        "M84-cross-node-id-collision-ignored",
        SKILL,
        '    if _nkey(dup.get("node_id")) != _NODE_KEY:\n',
        "    if False:  # MUTANT: 同键异主不拦\n",
        "test_round9_identity_and_self_check",
    ),
    (
        # append 前不做校验器自检 ⇒ 写点自产 validator 拒的行
        "M85-no-producer-self-check",
        SKILL,
        "        _self_vio, _ = validate_record_full(rec, vault_id=_vid, manifest=_GOLDEN_MF)\n",
        "        _self_vio = []  # MUTANT: 产出侧不自检\n",
        "test_round9_identity_and_self_check",
    ),
    (
        # F1 退回正则解析 ⇒ 合法 YAML 形态假阴性
        "M86-f1-regex-not-yaml",
        SKILL,
        "        import yaml  # F1 判定\n",
        "        raise ImportError('MUTANT: 强制走正则回落')\n",
        "test_round9_yaml_calibration_forms",
    ),
    (
        # null/~ 不规范化 ⇒ 首写产出非法 YAML
        "M87-null-calibration-not-normalized",
        SKILL,
        'r"^calibration_log:[ \\t]*(?:\\[[ \\t]*\\]|null|Null|NULL|~)?[ \\t]*(#[^\\n]*)?$"',
        'r"^calibration_log:[ \\t]*(?:\\[[ \\t]*\\])?[ \\t]*(#[^\\n]*)?$"  # MUTANT',
        "test_round9_yaml_calibration_forms",
    ),
    (
        # degraded 路径退回运行时刻 ⇒ 与正常路径产物不同
        # ⚠️ 这条变异**打不中**（第五种成因）: degraded 分支现在整体从 _SCORED_AT
        # 取值，只改 `_raw` 影响不到 last_examined/W。要复现原缺陷须让稳定时刻
        # 本身退回运行时刻 —— 那等价于 M79（缺稳定时刻回抄），已被它覆盖。
        # 保留本条并改绑到能真正观察到差异的门。
        "M88-degraded-uses-run-ts",
        SKILL,
        '_SCORED_AT = p.get("review_time")\n',
        '_SCORED_AT = p.get("ts")  # MUTANT: 稳定时刻退回运行时刻\n',
        "test_round8_stable_scored_at",
    ),
]


# ── round-9 B①B②B④（结构化 receipt）的承重变异
MUTATIONS += [
    (
        # receipt 不带 scored_at ⇒ F1-only 无法证明是同一次评分
        "M89-receipt-drops-scored-at",
        SKILL,
        "              f'    scored_at: {q_(_e_sa)}\\n'\n",
        "              f''\n",
        "test_round9_structured_receipt",
    ),
    (
        # receipt 不带 attempt_count
        "M90-receipt-drops-attempt",
        SKILL,
        "              f'    attempt_count: {_e_att}\\n'\n",
        "              f''\n",
        "test_round9_structured_receipt",
    ),
    (
        # F1-only 退回无条件 no-op ⇒ 同 ID 的另一次评分静默消失
        "M91-f1-only-unconditional-noop",
        SKILL,
        # ⚠️ round-11 重绑: F1-only 改走统一 resolver
        "        _rcpt, _ = _resolve_receipt(\n",
        "        _rcpt, _ = ({'scored_at': _SCORED_AT, 'grade_norm': GN2, 'ts': 'x'}, evid) and (lambda *a, **k: ({'scored_at': _SCORED_AT, 'grade_norm': GN2, 'ts': 'x', 'attempt_count': 1, 'event_id': evid, 'abandoned': bool(p.get('abandoned'))}, evid))(\n",
        "test_round9_structured_receipt",
    ),
    (
        # 存量行缺 scored_at 时静默吞掉告警 ⇒ 用户不知道自己在降级模式里
        "M92-legacy-row-warning-silenced",
        SKILL,
        '        print(f"[quiz-answer] ⚠️ {_ctx} 缺 payload.scored_at',
        '        _ = (f"[quiz-answer] ⚠️ {_ctx} 缺 payload.scored_at',
        "test_round9_structured_receipt",
    ),
]


# ── round-10 修复的承重变异
MUTATIONS += [
    (
        # 适用集路由退回 raw compare ⇒ NFD 行落不进适用集，永久漏算
        "M94-routing-raw-compare",
        SKILL,
        '    if _nkey(_o.get("node_id")) != _NODE_KEY:\n',
        '    if _o.get("node_id") != node_id:  # MUTANT\n',
        "test_round10_findings",
    ),
    (
        # receipt 不比 abandoned ⇒ 另一次评分被当作一致
        "M95-receipt-skips-abandoned",
        SKILL,
        # ⚠️ round-11 重绑: abandoned 现在是 facts 字典的一项
        # ⚠️ round-12 重绑: 事实清单已抽进构造器。
        '        "abandoned": (bool(_ab), _ok_bool),\n',
        "                # MUTANT: 不比 abandoned\n",
        # round-12 改绑窄门: 原门里 grade 的差异会替 abandoned 把门弄红,
        # 于是这条变异测不出 abandoned 是否承重。窄门把两者隔离(都是 0.0)。
        "test_round12_abandoned_isolated_from_grade",
    ),
    (
        # adopted time 不绑定 ⇒ 同一次评分可二次推进 FSRS
        "M96-adopted-time-unbound",
        SKILL,
        # ⚠️ round-11 重绑: adopted 绑定已并入统一 resolver 的 row= 分支
        "        if not (_a == _b == _c):\n",
        "        if False:  # MUTANT: 不绑定 adopted\n",
        "test_round10_findings",
    ),
    (
        # 写回退回正则插入 ⇒ inline 形态被写成非法 YAML
        "M97-writeback-regex-only",
        SKILL,
        "        import yaml as _y\n",
        "        raise ImportError('MUTANT: 强制走正则写回')\n",
        "test_round10_findings",
    ),
    (
        # 落账前不预演 ⇒ 先落账后损坏笔记
        "M98-no-pre-append-dry-run",
        SKILL,
        "        _append_calibration(fm, review_time)\n    except SystemExit:\n",
        "        pass  # MUTANT: 不预演\n    except SystemExit:\n",
        "test_round10_findings",
    ),
]


# ── round-11 修复的承重变异
MUTATIONS += [
    (
        # ⛔ 本条原先打的是 `_sources != {ev_id}` 那行（空集当唯一）——**空变异对照
        # 实测证明那是「制造性击杀」**: 只禁 facts 层、不打变异体, 门就已经红了。
        # 而且可达性探针实测: 跑完全 56 门 + 31 反例, `require_source=True 且
        # _sources 为空` **零命中** —— 那行守卫在当前调用点上不可达
        # (两个 require_source=True 的调用点都传入必含该 id 的账本集合)。
        # 真正拦住 round-11 B② 的是 **F1-only 分支的六项 facts 核对**, 本条改打它。
        "M99-f1only-skips-fact-check",
        SKILL,
        # ⚠️ round-12 重绑: F1-only 的 facts 改由构造器产出。
        "            ) if _att_cur is not None else None,\n",
        "            ) if False else None,  # MUTANT: 账本缺失时不核对事实就放行\n",
        "test_round11_unified_resolver",
    ),
    (
        # dup 路径不做三方同瞬间 ⇒ 改采用时刻可二次推进 FSRS
        "M100-no-tri-instant-binding",
        SKILL,
        # ⚠️ round-12 重绑: dup 调用点已带上完整事实。
        "    _resolve_receipt(fm, evid, _ALL_LEDGER_IDS, row=dup, facts=_facts_of_row(dup))\n",
        "    pass  # MUTANT: 不绑定采用时刻\n",
        "test_round11_unified_resolver",
        (
            # ⛔ 这不是「拆另一条防线」, 是**补齐同一条防线的第二站点**: 三方同瞬间
            # 绑定有**两个**调用点(dup 路径 + foreign replay)。只打前者时探针实测拒因
            # 仍是三方绑定那条消息, 只是来自后者 ⇒ 缺陷根本没放回来(成因⑤ 覆盖不完整)。
            # 原挂的「禁 facts」是**错的层**: 它拆的是另一道被测防线, 只加它门就红。
            (
                SKILL,
                "        fm, _rid_, _ALL_LEDGER_IDS, row=_o, facts=_facts_of_row(_o),\n",
                "        fm, _rid_, _ALL_LEDGER_IDS, row=None, facts=_facts_of_row(_o),  # MUTANT: 第二站点同样不绑定\n",
            ),
        ),
        "complete",
    ),
    # ⛔ M101-foreign-replay-bool-presence 已**退役**（round-11b, 如实记录）:
    # 它是**等价变异体** —— `_already_ = _rcpt_fg is not None` 与
    # `_fm_has_event_compat(fm, _rid_, _ALL_LEDGER_IDS)` 在**所有可达输入上取值相同**:
    # 两者都由同一组候选(`_cands_and_sources`)决定, 候选空则双双为假, 候选非空则
    # `_resolve_receipt` 必返回 dict(或抛), compat 也返回 True(或在同样的歧义上抛)。
    # 等价变异体不可能被任何门抓住 —— 保留它只会逼出一个「拆掉被测防线」的假层。
    # 它原本要守的性质(foreign replay 必须逐项核对事实)由门
    # `test_round11b_foreign_replay_checks_facts_narrow` 直接守着。
    (
        # receipt 的 attempt 只查类型不比值 ⇒ 999 也放行
        "M102-receipt-attempt-type-only",
        SKILL,
        # ⚠️ round-12 重绑: 事实清单已抽进构造器。
        '        "attempt_count": (_att, _ok_att),\n',
        "        # MUTANT: 不比 attempt 值\n",
        "test_round11_unified_resolver",
    ),
    (
        # receipt 的 ts 不做字面门 ⇒ 带空白的值被 strip 洗掉
        "M103-receipt-ts-no-literal-gate",
        SKILL,
        "        if not isinstance(_rc_ts, str) or not _rc_ts or _rc_ts != _rc_ts.strip():\n",
        "        if False:  # MUTANT: ts 不做字面门\n",
        "test_round11_unified_resolver",
    ),
    (
        # 写回退回「按文本外观猜结构」⇒ 一空格列表/quoted key 被写坏
        "M104-writeback-guess-by-text",
        SKILL,
        '            _cut = re.sub(r\'^(?:"calibration_log"|calibration_log):.*?(?=^\\S|\\Z)\', "",\n',
        "            _cut = re.sub(r'^calibration_log:.*?(?=^\\S|\\Z)', \"\",  # MUTANT: 只认裸键\n",
        "test_round11_writeback_by_parse_result",
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

# ── round-11b 修复的承重变异（判据逻辑只许一份）
MUTATIONS += [
    (
        # compat 侧重新内联一份副本 ⇒ 判据又变成两份, 下次改判据必漏一处
        "M110-reinline-duplicate-lookup",
        SKILL,
        "    _cands, _sources = _cands_and_sources(fm_text, ev_id, all_ledger_ids)\n    if not _cands:\n        return False\n",
        '    _cands = []  # MUTANT: 重新内联副本\n    if _fm_has_event(fm_text, ev_id):\n        _cands.append(ev_id)\n    _bare = ev_id[5:] if ev_id.startswith("quiz:") else None\n    if _bare is not None and _fm_has_event(fm_text, _bare):\n        _cands.append(_bare)\n    _sources = set()\n    for _tok in _cands:\n        for _lid in all_ledger_ids:\n            if _lid == _tok or (_lid.startswith("quiz:") and _lid[5:] == _tok):\n                _sources.add(_lid)\n    _sources.discard("")\n    if not _cands:\n        return False\n',
        "test_round11b_single_source_lookup",
    ),
    (
        # 唯一实现被改名 ⇒ 复用关系断掉（结构门的验伪锚: 只剩一份也可能是删没了）
        "M111-shared-impl-not-reused",
        SKILL,
        "def _cands_and_sources(fm_text, ev_id, all_ledger_ids=()):\n",
        "def _cands_and_sources_renamed(fm_text, ev_id, all_ledger_ids=()):  # MUTANT\n",
        "test_round11b_single_source_lookup",
    ),
    (
        # compat 侧把「空来源放行」改成「空来源也拒」⇒ 账本行丢失时无法恢复
        "M112-compat-empty-source-rejects",
        SKILL,
        "    if _sources and _sources != {ev_id}:\n",
        "    if _sources != {ev_id}:  # MUTANT: 空集也拒\n",
        "test_round11b_both_paths_still_behave",
    ),
]


# ── round-12 修复的承重变异（3 BLOCKER + 4 HIGH 的共同根因是事实清单分叉）
MUTATIONS += [
    (
        # 事实清单退回可缺项 ⇒ 四个站点又能各传各的
        "M113-facts-list-not-frozen",
        SKILL,
        "        if set(facts) != set(_FACT_KEYS):\n",
        "        if False:  # MUTANT: 允许缺项清单\n",
        "test_round12_facts_list_is_frozen",
    ),
    (
        # F1-only 漏 exam_board ⇒ 同 ID 换白板的另一次评分被吞
        "M114-f1only-drops-exam-board",
        SKILL,
        '        "exam_board": (str(_board or ""), _ok_board),\n',
        "        # MUTANT: F1-only 不比白板\n",
        "test_round12_b2_exam_board_in_facts",
    ),
    (
        # ≤W 扫描退回「只查 ID 在不在」⇒ validator-valid 的事实污染永久漏算
        "M115-late-scan-presence-only",
        SKILL,
        "    _rc2_, _ = _resolve_receipt(fm, _rid2_, _ALL_LEDGER_IDS, row=_o_, facts=_facts_of_row(_o_))\n    if _rc2_ is None:\n",
        "    if not _fm_has_event_compat(fm, _rid2_, _ALL_LEDGER_IDS):  # MUTANT: 只查 presence\n",
        "test_round12_b3_late_scan_checks_facts",
    ),
    (
        # 新 receipt 不带 provenance ⇒ 空来源时两个世界不可区分
        "M116-receipt-no-provenance",
        SKILL,
        "              f'    id_form: full\\n'\n",
        "              # MUTANT: 不写形态标记\n",
        "test_round12_b1_receipt_provenance",
    ),
    (
        # 空来源时不要求 provenance ⇒ 历史裸形态被当成完整形态
        "M117-empty-source-skips-provenance",
        SKILL,
        '        if not (isinstance(_probe, dict) and _probe.get("id_form") == "full"):\n',
        "        if False:  # MUTANT: 空来源不查形态标记\n",
        "test_round12_b1_receipt_provenance",
    ),
    (
        # 空 eid 不在入口拒 ⇒ 首跑写入、重跑永远认不出
        "M118-empty-eid-allowed",
        SKILL,
        "if not (isinstance(eid, str) and eid.strip()):\n",
        "if False:  # MUTANT: 空 eid 放行\n",
        "test_round12_empty_eid_rejected_at_entry",
    ),
    (
        # 崩溃窗不证明采用时刻 ⇒ W 被恢复成篡改值
        "M119-crash-window-adopted-time-unproven",
        SKILL,
        "    if W_inst is None and not _fm_has_event_compat(fm, evid, _ALL_LEDGER_IDS):\n",
        "    if False:  # MUTANT: 崩溃窗不证明采用时刻\n",
        "test_round12_high2_adopted_time_in_crash_window",
    ),
    (
        # 旧行缺 scored_at 时退回笼统拒因 ⇒ 用户无路可走
        "M120-legacy-row-generic-reason",
        SKILL,
        '        if "scored_at" not in _dpl:\n',
        "        if False:  # MUTANT: 不给可执行迁移指引\n",
        "test_round12_high3_legacy_row_missing_scored_at_is_actionable",
    ),
]


def first_fail(out):
    """门输出里的第一条失败**身份**（`文件:行号: 错误`），用于比较两次跑败在不败在同一处。

    ⛔ 兜底绝不能是**固定哨兵**: 首版返回 "(未定位失败点)" —— 当时 run_gate 带
    `--tb=no`, 输出里根本没有断言行, 于是两次都取到同一个哨兵、被判成「同一失败点」,
    **17 条变异被误报成假杀**。判据修好不等于缺陷消失: 提取器一断, 判据就退化成恒真。
    所以定位不到时返回**输出指纹**, 两个不同的输出永远不会相等。
    """
    for ln in out.split("\n"):
        t = ln.strip()
        # --tb=line 形态: /path/test_x.py:123: AssertionError: msg
        if re.match(r"^.*\.py:\d+: \w*(Error|Exception)", t):
            # ⚠️ 去掉绝对路径前缀: 它有 ~110 字符, 截断后两条不同的失败**看起来一样**,
            # 而真正的区分信息(行号 + 消息)恰好被截掉。身份要留信息密度高的那一半。
            return t.rsplit("/", 1)[-1][:220]
    for ln in out.split("\n"):
        t = ln.strip()
        if t.startswith("E ") or "AssertionError" in t:
            return t[:220]
    body = "\n".join(l for l in out.split("\n") if l.strip() and "warning" not in l.lower())
    return "digest:" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:24]


def main():
    failures = []
    kill_fail = {}
    # ⛔ 全文件基线核对（round-11b 新增，起因是一次真实污染）:
    # 更早一轮的探针往 `fsrs_bridge.py` 末尾追加了两段 `_s.exit(9)` 且**没有还原**。
    # 三裁判全绿、101 条变异全 KILLED、`grep -c MUTANT` 返回 0 —— 全都没抓到它,
    # 因为**那个变异体的文本里没有 "MUTANT" 字样**。锚点依赖变异体自己老实留标记,
    # 而变异体是「敌方」, 不能指望它配合。
    # 正确的外部锚点 = 对**每一个**会被变异的文件比对全文件 sha, 与标记无关。
    # ⛔ 编号唯一性静态门（round-11b 新增）: `M102-receipt-attempt-type-only` 与
    # `M102-reinline-duplicate-lookup` 曾并存 —— 全名不同, 所以「重名检查」不报,
    # 但**按前缀选择**的探针(`startswith("M102-")`)会静默选错另一条, 于是三态诊断
    # 诊断的是别的变异。判据要落在**实际被用来选择的那个键**上。
    _nums = collections.Counter(re.match(r"M(\d+[a-z]?)", m[0]).group(1) for m in MUTATIONS)
    _dup_nums = {k: v for k, v in _nums.items() if v > 1}
    if _dup_nums:
        print(f"✗✗ 变异编号碰撞 {_dup_nums} — 前缀选择会选错, 立即停")
        sys.exit(2)
    _testf_src = (ROOT / "backend" / TESTF).read_text(encoding="utf-8")
    _gates_missing = [m[0] for m in MUTATIONS if f"def {m[4]}(" not in _testf_src]
    if _gates_missing:
        print(f"✗✗ 绑定的门不存在: {_gates_missing} — rc=4 会被粗判据当成 KILLED, 立即停")
        sys.exit(2)
    _touched = sorted(
        {m[1] for m in MUTATIONS} | {x[0] for m in MUTATIONS if len(m) > 5 for x in m[5]}, key=lambda p: str(p)
    )
    _baseline = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in _touched}
    print("── 基线（跑前）──")
    for p, h in _baseline.items():
        print(f"   {h[:16]}  {p.name}")
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
        if killed:
            kill_fail[tag] = first_fail(r.stdout)
        status = f"KILLED ({why})" if killed else f"SURVIVED ⇒ 假门 ({why})"
        print(f"[{tag}] {gate} → {status}  [还原字节相同 {sha_after[:12]}]")
        if not killed:
            failures.append(f"{tag}: 门 {gate} 未抓住变异 (SURVIVED)")
            print("    ---- 门输出尾部 ----")
            print("    " + "\n    ".join(r.stdout.strip().split("\n")[-6:]))

    # ── 阶段 2: 空变异对照 (只施加同层, 不打变异体)
    # ⛔ 为什么必须有 (2026-09-02 实测): M99 挂了「禁 facts」层后报 KILLED,
    # 但只禁那一层、**不打变异体**, 门就已经红了 —— 击杀完全由层贡献, 变异体
    # 本身毫无鉴别力。这是「假绿」的镜像: **假杀**。带层的变异若不做这道对照,
    # 「KILLED」这个字样什么也不证明。
    # 判据: 只施加层时门必须**仍绿**; 变红 = 该条的击杀是制造出来的。
    # ⛔ 层有**两种**, 判据完全不同(round-11b 实测才分清):
    #   depth    —— 拆掉**别的**防线, 让被测那道成为唯一屏障。只加层必须**绿**,
    #               红了就说明拆错了(拆到被测防线本身)或粗门早退 ⇒ 假杀。
    #   complete —— 补齐**同一缺陷的其它站点**(如三方绑定有两个调用点)。
    #               只加层**本就可能红** —— 那是缺陷的一半, 不是假杀。
    #               它要证的是「变异体单独不够」: body-only 必须绿。
    # 这个区别是语义的, 机器判不出来, 只能由变异自己声明(第 7 元素, 默认 depth)。
    layered = [m for m in MUTATIONS if len(m) > 5 and m[5]]
    print(f"\n── 空变异对照 ({len(layered)} 条带同层) ──")
    for _m in layered:
        tag, gate, also = _m[0], _m[4], _m[5]
        kind = _m[6] if len(_m) > 6 else "depth"
        originals, texts = {}, {}
        for _p, _o, _n in also:
            if _p not in originals:
                originals[_p] = _p.read_bytes()
                texts[_p] = originals[_p].decode("utf-8")
        bad = False
        for _p, _o, _n in also:
            if texts[_p].count(_o) != 1:
                print(f"[{tag}] ✗ 对照锚点异常, 跳过")
                bad = True
                break
            texts[_p] = texts[_p].replace(_o, _n, 1)
        if bad:
            failures.append(f"{tag}: 空变异对照锚点异常")
            continue
        try:
            for _p, _t in texts.items():
                _p.write_bytes(_t.encode("utf-8"))
            r0 = run_gate(gate)
            red0 = r0.returncode == 1 and "1 failed" in r0.stdout
        finally:
            for _p, _b in originals.items():
                _p.write_bytes(_b)  # 无条件还原
        drift = [
            p.name
            for p in originals
            if hashlib.sha256(p.read_bytes()).hexdigest() != hashlib.sha256(originals[p]).hexdigest()
        ]
        if drift:
            print(f"[{tag}] ✗✗ 对照还原后字节不同: {drift} — 立即停")
            sys.exit(2)
        # ⛔ 判据不是「对照红就算假杀」—— 那条判据**太粗**, 而且是我 2026-09-02 在
        # 这道对照里亲手犯的同一个错(与 `rc != 0` 混进续跑信号同型)。粗门(如
        # test_internal_audit_findings)捆了多个子场景, 层可能弄红**另一个**子场景。
        # 实测 M23: 只加层败在「不得被当成一次复习重放」, 层+变异体败在「零写」——
        # **不同断言** ⇒ 变异体确实改变了行为, 不是假杀。
        # 正确判据: 只有两次败在**同一条**断言上, 才说明变异体毫无贡献。
        fa = first_fail(r0.stdout) if red0 else None
        fb = kill_fail.get(tag)
        if kind == "complete":
            # 这类层的合格判据不是「只加层要绿」, 而是「变异体单独不够」。
            _bp, _bo, _bn = _m[1], _m[2], _m[3]
            _bsnap = _bp.read_bytes()
            _btxt = _bsnap.decode("utf-8")
            if _btxt.count(_bo) != 1:
                failures.append(f"{tag}: complete 对照的变异体锚点异常")
                print(f"[{tag}] ✗ complete 对照锚点异常")
                continue
            try:
                _bp.write_bytes(_btxt.replace(_bo, _bn, 1).encode("utf-8"))
                rb = run_gate(gate)
                b_only = rb.returncode == 1 and "1 failed" in rb.stdout
            finally:
                _bp.write_bytes(_bsnap)  # 无条件还原 (EXIT trap 等价)
            if hashlib.sha256(_bp.read_bytes()).hexdigest() != hashlib.sha256(_bsnap).hexdigest():
                print(f"[{tag}] ✗✗ complete 对照还原后字节不同 — 立即停")
                sys.exit(2)
            if b_only:
                failures.append(f"{tag}: 声明为 complete 但变异体单独即可杀 ⇒ 层是多余的")
                print(f"[{tag}] ✗ complete 但变异体单独即可杀 ⇒ 撤层")
            else:
                print(f"[{tag}] ✓ complete: 变异体单独不够(门绿), 补齐站点后才红 ⇒ 层必要")
        elif not red0:
            print(f"[{tag}] ✓ 对照绿 (rc={r0.returncode}) ⇒ 击杀干净归因于变异体")
        elif fb is not None and fa == fb:
            failures.append(f"{tag}: 只加层与层+变异体败在同一条断言 ⇒ 击杀由层贡献 (假杀): {fa[:90]}")
            print(f"[{tag}] ✗ 假杀 — 两次同一失败点: {fa[:90]}")
        else:
            print(f"[{tag}] ✓ 对照红但失败点不同 ⇒ 变异体有可观测效果 (门较粗, 隔离不干净)")
            print(f"       只加层: {(fa or '')[:88]}")
            print(f"       +变异体: {(fb or '')[:88]}")

    # ── 收尾: 全文件基线复核（与「每条变异各自的快照」无关 —— 那是自证）
    print("── 基线复核（跑后）──")
    _drifted = []
    for p, h0 in _baseline.items():
        h1 = hashlib.sha256(p.read_bytes()).hexdigest()
        ok = h1 == h0
        print(f"   {'✓' if ok else '✗'} {h1[:16]}  {p.name}")
        if not ok:
            _drifted.append(f"{p.name}: {h0[:16]} → {h1[:16]}")
    if _drifted:
        failures.append("全文件基线漂移（有变异体没还原）: " + "; ".join(_drifted))
        print("   ⛔ 基线漂移 —— 生产文件里可能残留变异体, 立即人工核对")

    print()
    if failures:
        print("变异验证 FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(
        f"变异验证 PASS: {len(MUTATIONS)}/{len(MUTATIONS)} 全部被指定门杀死; "
        f"{len(layered)} 条带层变异全部通过空变异对照(击杀非层贡献); 全部逐字节还原。"
    )


if __name__ == "__main__":
    main()
