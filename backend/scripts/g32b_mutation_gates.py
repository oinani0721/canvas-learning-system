#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CARD-G3-2b 变异验证 (串行, 逐字节还原)。

判据 (MEMORY reference_gate_design_pitfalls / reference_mutation_script_serial_only):
  - 每个变异把生产代码**精确退回旧实现形态** (同构复现审查者的绕过, 非弱变异);
  - **指定的那道门**必须变红 (不是「某处有失败」);
  - 变异体必须**先编译得过** —— 编译期就死的变异体制造的是假杀, 判 SYNTAX-INVALID;
  - 击杀必须落在**声称的那一条断言**上 —— round-19 起判据是**断言源位置**
    (`EXPECT_LOC`) **与** 消息片段 (`EXPECT_MSG`) 的 AND, 不是「这个门里随便哪条红了」,
    也不是「消息或位置二选一」;
  - 还原后必须与变异前**逐字节相同**, 否则立即停。

后两条由 CARD-DEBT-mutation-kill-identity 抽进共用模块 `mutation_kill_identity`,
四套 harness (g32b / g32cb / g32ccr1 / g33) 同一份实现。

⛔ round-19 (CARD-DEBT-mutkill-R2) 改了什么:
  · 判据从「消息子串出现过就算」改成「pytest 报的失败**位置**就是它指名的那条语句」
    —— Y1-B 外审 HIGH-1 实测: 前提断言把子进程 stderr 插进消息首行时, 目标断言
    根本没执行而消息判据照样成立。位置是唯一能分开这两者的面;
  · 解析面限定在 `=== short test summary info ===` 区内 (Y1-B HIGH-2);
  · 39 条 `KILLED-UNBOUND` 全部改绑 `EXPECT_LOC` (消息绑不出来的那些, 位置绑得出来);
  · 裁决统一成共用模块的六档 `VERDICTS`, `ANCHOR-ERROR` / `SYNTAX-INVALID` 一并进
    `_verdicts` 参与计数 (原先走旁路, 六档之和对不上 `len(MUTATIONS)`);
  · 信号处置统一成 `RestoreGuard`: 四个信号 (补齐 SIGQUIT) + **还原期不可打断**。

用法:
  `python3 backend/scripts/g32b_mutation_gates.py`          跑全部 (约 36 min)
  `python3 backend/scripts/g32b_mutation_gates.py --list`   只列变异与锚点命中数(不改任何文件)
  `python3 backend/scripts/g32b_mutation_gates.py --probe`  只观察每条实际红在哪条断言上
                                                            (并打印可直接回填的 `EXPECT_LOC`)
"""

import collections
import hashlib
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mutation_kill_identity import (  # noqa: E402  (必须在 sys.path 兜底之后)
    VERDICTS,
    RestoreGuard,
    check_expect_loc_unique,
    check_expect_msg_unique,
    failed_locations,
    failed_reasons,
    gate_hit,
    judge_env,
    judge_flags,
    kill_identity,
    loc_token_for,
    matched_loc_tokens,
    parse_failed_nodeids,
    syntax_check,
    unparsed_failure_lines,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = ROOT / "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
BRIDGE = ROOT / "canvas-vault/.claude/scripts/fsrs_bridge.py"
SCHEMA = ROOT / "docs/learning-events-schema-v1.md"
TESTF = "tests/regression/test_g3_2_review_ledger.py"
#: 门文件的绝对路径 —— `expect_loc` 的语句指纹从这份源码算，位置行也要与它比对。
GATE_FILE = ROOT / "backend" / TESTF

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
        # ⚠️ round-15 重绑: 条件已加上 `or "scored_at" in _pl`。
        '        if "schema_ext" in _pl or _looks_like_review_ext(_pl) or "scored_at" in _pl:\n',
        '        if "schema_ext" in _pl:  # MUTANT: 只看 marker\n',
        "test_round3_findings",
        # ⚠️ round-15: 变异体现在**同时**拆掉 `_looks_like_review_ext` 与 `scored_at`
        # 两支（后者是本轮新增的纵深, 留着它变异杀不动）。层仍是校验器那道。
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


def _self_heal_leftovers() -> list[str]:
    """启动即自愈：还原**上一次被外部杀死时残留的**变异体。

    ⛔ 本脚本已有 `finally` 无条件还原，但那挡不住"整个进程组被杀"——
    2026-09-04 实测：跑到一半 python 进程消失，`for _inst_, _ln_, _o_ in []:  # MUTANT`
    留在了 `SKILL.md` 里（输出文件 0 字节，连缓冲都没 flush）。
    `finally` 和信号处理写得再小心，外部 kill 总可能发生；唯一可靠的兜底是
    **下一次启动时先检查**。

    ⚠️ 覆盖面补齐（CARD-DEBT-mutation-kill-identity）：原先只扫**主锚**的变异体，
    **同层**（第 6 元素）的变异体留在文件里时自愈看不见 —— 而 M157 的层锚正好
    就是那种「落盘前失败、整条跳过」的条目，它的层变异体一旦残留，下一次跑
    连锚点自检都会读到被改过的源。
    """
    healed = []
    for _mut in MUTATIONS:
        _edits = [(_mut[1], _mut[2], _mut[3])] + [tuple(x) for x in (_mut[5] if len(_mut) > 5 else ())]
        for _target, _old, _new in _edits:
            try:
                src = _target.read_text(encoding="utf-8")
            except OSError:
                continue
            if _new in src and _old not in src:
                _target.write_text(src.replace(_new, _old, 1), encoding="utf-8")
                healed.append(f"{_mut[0]} @ {_target.name}")
    return healed


def _PYTEST_BIN() -> str:
    """pytest 可执行文件路径。

    ⚠️ 原为硬编码 `ROOT/backend/.venv/bin/pytest` —— 在**没有自己 venv 的车道**
    （从主干新切的工作树就是这样）直接 `FileNotFoundError`，脚本跑不起来。
    优先取环境变量 `G32B_PYTEST`，其次才是车道内的 venv；两者都不可用时**报清楚**，
    不要留一个 FileNotFoundError 让人去猜。
    """
    import os as _os

    env = _os.environ.get("G32B_PYTEST")
    if env and pathlib.Path(env).exists():
        return env
    local = ROOT / "backend/.venv/bin/pytest"
    if local.exists():
        return str(local)
    raise SystemExit(
        f"✗✗ 找不到 pytest：环境变量 G32B_PYTEST 未设或指向不存在的路径，"
        f"且本车道无 {local} —— 请设 G32B_PYTEST 指向可用的 pytest 后重跑"
    )


def nodeid_of(gate):
    """门函数名 → pytest nodeid。判据比的是 nodeid，不是「门名字样在输出里」。"""
    return f"{TESTF}::{gate}"


def run_gate(name):
    return subprocess.run(
        # ⛔ 命令行开关统一从 `judge_flags()` 取, 四套一份 —— 各写各的时, 有人漏了
        # `--tb=line` 就会让 `expect_loc` 恒不命中, 报告长得跟「门都不承重」一样。
        # 少哪一条会怎么坏, 见该函数的 docstring 与 `judge_surface_missing()`。
        [_PYTEST_BIN(), nodeid_of(name), *judge_flags()],
        cwd=str(ROOT / "backend"),
        capture_output=True,
        text=True,
        timeout=900,
        env={**os.environ, **judge_env()},
    )


def is_killed(proc, gate, expect_msg, expect_loc=None, *, require_gate_file=True):
    """KILLED = **指定的那道门**红了 **且** 红在**声称的那一条断言**上。

    pytest 的退出码里只有 1 表示「测试失败」：4 = 用法错误（门名打错、nodeid
    不存在），5 = 一个都没收集到，2 = 中断，3 = 内部错误。这些非 1 的码在
    `rc != 0` 判据下会被当成 KILLED —— 门名一打错，整份变异报告就全绿而毫无
    意义。这正是 MEMORY 里「rc=5 不算红」那条教训的同族。

    ⛔ round-18 (CARD-DEBT-mutation-kill-identity) 收紧的一半: 原判据到
    「摘要是 1 failed」为止 —— 这个门里**别的**断言红了同样满足。M15 假杀
    (Z2) 正是这个形态: 变异体编译期就死, 目标断言反而通过, 红落在另一条上。
    现在必须 `EXPECT_MSG[tag]` 出现在**该 nodeid 自己的**短摘要 reason 里。

    ⛔ round-19 收紧的另一半（CARD-DEBT-mutkill-R2 / Y1-B HIGH-1）：消息判据**分不开**
    「前提断言红了」与「目标断言红了」—— 前提断言的消息里内嵌了被测子进程的输出，
    子进程只要在运行期把期望片段拼出来，短摘要的 reason 就含它。现在再加一维
    `EXPECT_LOC[tag]`：pytest 自己算出来的失败**语句位置**必须就是它指名的那条。
    两维是 **AND**，⛔ 不是二选一。

    ⚠️ 返回 `(verdict, why)`，`verdict` ∈ 共用模块的 `VERDICTS` 前四档：
      · `KILLED`          —— 红在声称的那一条断言上（位置 [+ 消息] 都对上）；
      · `KILLED-UNBOUND`  —— 位置与消息**都**没绑。⚠️ 本树实测**为 1**（`M97`：该变异
        让门死在 yaml 库里，不落在门文件的任何一条断言上，位置与消息都绑不出来），
        ⛔ 不是 0 —— 别把「目标 0」写成「已经是 0」。档位保留是因为「绑不出来」这件事
        将来还可能发生，静默并进 KILLED 就是把结论说宽；
      · `SURVIVED`        —— 门没红，或红在别的断言 / 别的位置上；
      · `HARNESS-ERROR`   —— rc 不是 1（2 中断 / 3 内部错 / 4 用法错 / 5 零收集）、
        判据面缺失、或 `expect_loc` 的锚在门文件里已找不到（门被别的卡改写）。
        ⛔ 最后一种尤其不能记成 SURVIVED —— 那会把「门被改了」说成「防线失效」。
    """
    return kill_identity(
        proc.returncode,
        proc.stdout + proc.stderr,
        nodeid_of(gate),
        expect_msg,
        gate_file=GATE_FILE,
        expect_loc=expect_loc,
        require_gate_file=require_gate_file,
    )


def observed_reason(out, gate):
    """指定门自己的短摘要 reason（没红则 None）—— 诊断与 `--probe` 用。"""
    nodeid = nodeid_of(gate)
    hits = [r for nid, r in failed_reasons(out) if gate_hit(nodeid, {nid})]
    return hits[0] if hits else None


def observed_loc(out):
    """本次失败的**位置** token（`--probe` 回填 `EXPECT_LOC` 用；没有则 None）。

    ⛔ 回填这件事如实说：它是「跑一次看它红在哪」再写回表里，**判据与被测量同源** ——
    今天证不出「这条变异确实打红了它声称的那条断言」。它的价值在**从今往后**：门或
    生产代码一漂移、击杀落到别的语句上，就会当场报 SURVIVED / HARNESS-ERROR，
    而不是像过去那样静默记成 KILLED。这一条写进了验收单「本卡未证明什么」。
    """
    locs = failed_locations(out)
    if not locs:
        return None, None
    path, lineno, _ = locs[0]
    # ⛔ 原始 `<路径>:<行号>` 也一并返回并落进 probe 存档：`expect_loc` 的取值方式
    # 将来若再变（本卡就把它从「全局语句指纹」改成「作用域内语句指纹」改过一次），
    # 有了原始位置就能**离线重算**，不必再跑一趟两小时的 probe。
    return loc_token_for(GATE_FILE, path, lineno), f"{path}:{lineno}"


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
                # ⚠️ round-13 重绑: 崩溃窗条件行已改（去掉 W_inst is None 限制）。
                "    if (not _fm_has_event_compat(fm, evid, _ALL_LEDGER_IDS)\n",
                "    if (not _fm_has_event(fm, evid)  # MUTANT: 第二站点同样退回裸查\n",
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
        # ⚠️ 不能加 `# MUTANT` 注释: 这是**行内子串**替换, 注释会把它右边的
        # 闭合括号一起吃掉 ⇒ 语法错误假杀（round-17 MEDIUM 实测）。
        # 缺陷由参数本身表达即可, 标记靠全文件 sha 基线而不是 grep。
        "json.dumps(rec, ensure_ascii=False, allow_nan=True)",
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
    # ⛔ M72-exact-hit-bypasses-ambiguity 已**退役**（round-15, 如实记录）:
    # 变异体打的是 `_fm_has_event_compat` 里「exact 命中绕过歧义检查」那一段。
    # round-15 之后, 该门 B① 场景里的歧义由**更早的 provenance 判据**拦下
    # （「这条 receipt 存的是完整 id 还是历史裸形态，两种情形字节完全相同」），
    # 可达性探针实测: 跑该门时 compat 的歧义分支**命中 0 次**;
    # 三态诊断也全绿（层+变异体一起施加门仍不红 —— 排除纵深兜住与覆盖不完整,
    # 只剩「门的场景不经过被变异的那段」）。
    # 与 M22/M55 同类: **被取代的纵深**。守卫本身保留(便宜且对别的路径仍有效),
    # 但它在现有门集上不可能承重, 保留变异只会逼出一个假杀。
    # 该性质现由 provenance 判据 + 门(84)-(88) 与 M117/M125/M139 直接守着。
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
    # ── M87-null-calibration-not-normalized：退役（**被取代的死纵深**）
    # 变异体删掉 `_normalize_inline_calibration` 正则里的 `null|Null|NULL|~` 分支。
    # round-17 实测（修好它原先的语法错误之后）SURVIVED —— 真因不是门不承重，而是
    # 该性质已由**结构化重建路径**接管: `_cur = _doc.get("calibration_log")` 对
    # null/~ 形态得到 None，`_cur or []` 直接当空列表重建，正则归一化对它无话可说。
    # ⚠️ 如实声明未证明面: PyYAML 不可用时的回落路径仍走正则（代码自述「非等价:
    # 只认 block list 形态」）。那条路径本卡没有门覆盖，退役不代表它被证明过。
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
    # ⛔ M92-legacy-row-warning-silenced 已**退役**（round-14, 如实记录）:
    # 它打的是「缺 scored_at 的告警被静默」。round-14 BLOCKER② 把那条**告警升成了
    # fail-closed**（告警后回落 review_time 会把两个不同原始时刻的评分别名成同一次,
    # 实测新评分静默不入账）—— 于是「告警在不在」不再是要守的性质,
    # 「缺 scored_at 停不停」才是, 由 M129 与门(80) 直接守着。
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
        # ⛔ round-17 改绑: 原门的场景**篡改的是账本时刻**, 而 round-16 把
        # `_adopted_ok` 收紧成「只认 A3 复算值」之后, 那个场景在更早处就被拒了 ——
        # 三方绑定对它退化成冗余纵深, 变异随之存活（原本是 KILLED）。
        # ⚠️ 承重面被更早的防线取代**不等于**该退役: 该性质仍只有它守着, 只是需要
        # 一个走得到它的场景 —— 账本自洽、只有 receipt 的第三个瞬间对不上。
        "test_round17_tri_instant_binding_narrow",
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
        # ⚠️ round-13 重绑: 已改走共用的 `_norm_board`。
        '        "exam_board": (_norm_board(_board), _ok_board),\n',
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
        # ⚠️ round-14 重绑: 字面已统一为带引号（与结构化写回同源）。
        "              f'    id_form: {q_(\"full\")}\\n'\n",
        "              # MUTANT: 不写形态标记\n",
        "test_round12_b1_receipt_provenance",
    ),
    (
        # 空来源时不要求 provenance ⇒ 历史裸形态被当成完整形态
        "M117-empty-source-skips-provenance",
        SKILL,
        # ⚠️ round-13 重绑: 判据已拆成 `_exact_hit and _marked`。
        "        if not (_exact_hit and _marked):\n",
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
        # ⚠️ round-13 重绑: 条件行已改。
        '        _dup_sa = _dpl.get("scored_at")\n',
        "        _dup_sa = None  # MUTANT: 崩溃窗不证明采用时刻\n",
        "test_round12_high2_adopted_time_in_crash_window",
        (
            # ⚠️ round-14 depth 层: pending 复放循环里新增的采用时刻证明会先于本站点
            # 拦住同类缺陷 ⇒ 变异体单独杀不动。拆掉**那一道**（不是被测的这一道）。
            (
                SKILL,
                '    if not _fm_has_event_compat(fm, str(_o.get("event_id") or ""), _ALL_LEDGER_IDS):\n        _p_sa = _pl.get("scored_at")\n',
                '    if False:  # MUTANT: 拆掉 pending 侧的采用时刻证明\n        _p_sa = _pl.get("scored_at")\n',
            ),
        ),
    ),
    (
        # 旧行缺 scored_at 时退回笼统拒因 ⇒ 用户无路可走
        "M120-legacy-row-generic-reason",
        SKILL,
        '        if "scored_at" not in _dpl:\n',
        "        if False:  # MUTANT: 不给可执行迁移指引\n",
        "test_round12_high3_legacy_row_missing_scored_at_is_actionable",
        (
            # ⚠️ round-14 depth 层: 「缺 scored_at 一律 fail-closed」会先拦住 ⇒
            # 拆掉它, 让被测的那道成为唯一屏障。
            (
                SKILL,
                '    if not isinstance(_pl.get("scored_at"), str) or not _pl["scored_at"]:\n        raise SystemExit(\n',
                "    if False:  # MUTANT: 拆掉「缺 scored_at 即停」这道纵深\n        raise SystemExit(\n",
            ),
        ),
    ),
]


# ── round-13 修复的承重变异（四条误拒 + 两条漏网）
MUTATIONS += [
    (
        # 消费侧又开始舍入 ⇒ 合法三位小数分数被拒
        "M121-consumer-rounds-grade",
        SKILL,
        "_norm_gn = lambda v: v                                    # 不舍入: receipt 存的是原值\n",
        "_norm_gn = lambda v: round(float(v or 0.0), 2)  # MUTANT: 消费侧舍入\n",
        "test_round13_consumer_must_not_reshape_values",
    ),
    (
        # 消费侧又开始强转 ⇒ writer 自己产出的整数板名被判类型非法
        "M122-consumer-coerces-board",
        SKILL,
        # ⚠️ round-15 重绑: 已改为保留显式 null。
        "_norm_board = lambda v: v\n",
        '_norm_board = lambda v: str(v or "")  # MUTANT: 消费侧强转\n',
        "test_round13_consumer_must_not_reshape_values",
    ),
    (
        # 采用时刻退回字面比较 ⇒ 合法小数秒输入被永久拒
        "M123-adopted-time-literal-compare",
        SKILL,
        "    _i = _i.astimezone(timezone.utc).replace(microsecond=0)\n",
        "    pass  # MUTANT: 不截整秒, 退回字面语义\n",
        "test_round13_adopted_time_recomputed_not_compared_literally",
    ),
    (
        # 崩溃窗证明只在 W 为空时做 ⇒ W 非空的篡改照常放行
        "M124-crash-window-only-when-w-empty",
        SKILL,
        "            and _dup_rt_inst is not None and (W_inst is None or _dup_rt_inst > W_inst)):\n",
        "            and _dup_rt_inst is not None and W_inst is None):  # MUTANT: 只管 W 空\n",
        "test_round13_adopted_time_recomputed_not_compared_literally",
        (
            # ⚠️ round-14 depth 层: pending 复放循环里新增的采用时刻证明会先于本站点
            # 拦住同类缺陷 ⇒ 变异体单独杀不动。拆掉**那一道**（不是被测的这一道）。
            (
                SKILL,
                '    if not _fm_has_event_compat(fm, str(_o.get("event_id") or ""), _ALL_LEDGER_IDS):\n        _p_sa = _pl.get("scored_at")\n',
                '    if False:  # MUTANT: 拆掉 pending 侧的采用时刻证明\n        _p_sa = _pl.get("scored_at")\n',
            ),
        ),
    ),
    (
        # id_form 标记对裸形态回落也放行 ⇒ 两个完整 id 别名
        "M125-id-form-authorizes-bare-fallback",
        SKILL,
        "        if not (_exact_hit and _marked):\n",
        "        if not _marked:  # MUTANT: 裸形态回落也认标记\n",
        "test_round13_id_form_only_proves_exact_hit",
        (
            # ⚠️ round-14 depth 层: 候选阶段的形态判定会先拦住 ⇒ 拆掉它。
            (
                SKILL,
                '        if not (isinstance(_bare_e, dict) and _bare_e.get("id_form") == "full"):\n            _cands.append(_bare)\n',
                "        _cands.append(_bare)  # MUTANT: 拆掉候选阶段的形态判定\n",
            ),
        ),
    ),
    (
        # F1-only 不折算后继 ⇒ 合法非-tip 续跑被误拒
        "M126-f1only-no-successor-discount",
        SKILL,
        "        _att_cur = (_att_now_f1 - _succ_f1) if _att_now_f1 is not None else None\n",
        "        _att_cur = _att_now_f1  # MUTANT: 直接拿当前 tip 比\n",
        "test_round13_f1only_ordinal_discounts_successors",
    ),
]


# ── round-14 修复的承重变异（3 漏网 + 3 误拒）
MUTATIONS += [
    (
        # 事实比较退回 Python == ⇒ 1 与 true 被判相等
        "M127-facts-python-equality",
        SKILL,
        "            elif _canon_fact(_got) != _canon_fact(_want):\n",
        "            elif _got != _want:  # MUTANT: 退回 Python ==\n",
        "test_round14_facts_compare_is_type_sensitive",
    ),
    (
        # 形态标记不在候选阶段生效 ⇒ 来源非空时仍被当作别人的裸形态
        "M128-id-form-not-at-candidate-stage",
        SKILL,
        '        if not (isinstance(_bare_e, dict) and _bare_e.get("id_form") == "full"):\n            _cands.append(_bare)\n',
        "        _cands.append(_bare)  # MUTANT: 候选阶段不查形态标记\n",
        "test_round14_id_form_checked_at_candidate_stage",
    ),
    (
        # 缺 scored_at 退回「告警后回落」⇒ 两个原始时刻被别名
        "M129-missing-scored-at-warn-only",
        SKILL,
        '    if not isinstance(_pl.get("scored_at"), str) or not _pl["scored_at"]:\n        raise SystemExit(\n',
        "    if False:  # MUTANT: 缺 scored_at 只告警不停\n        raise SystemExit(\n",
        "test_round14_missing_scored_at_is_fail_closed",
    ),
    (
        # pending 复放不证明采用时刻 ⇒ foreign pending 可携带任意时刻
        "M130-pending-adopted-time-unproven",
        SKILL,
        '    if not _fm_has_event_compat(fm, str(_o.get("event_id") or ""), _ALL_LEDGER_IDS):\n        _p_sa = _pl.get("scored_at")\n',
        '    if False:  # MUTANT: pending 不证明采用时刻\n        _p_sa = _pl.get("scored_at")\n',
        "test_round14_every_pending_proves_adopted_time",
    ),
    # ⛔ M131 已**退役**（round-16）: 它的变异体「只认 pushed」现在**恰是生产实现**
    # —— round-16 按规格 A3 收紧回去了。同一条性质的反向变异由 M149 覆盖。
    # ⚠️ 变异表不只会因锚点漂移失效, 也会因**口径反转**失效: 被测性质本身翻转时,
    # 正反两面只需保留一条。
    (
        # candidate 恒用 GN2 ⇒ 多位小数 durable 行永远无法由原白板落定
        "M132-candidate-always-rounded",
        SKILL,
        '                    "grade_norm": (GN if (_dgn := (_dpl.get("grade_norm")))\n                                   is not None and _dgn != GN2 and _dgn == GN else GN2),\n',
        '                    "grade_norm": GN2,  # MUTANT: 恒用两位小数\n',
        "test_round14_legacy_precision_identity",
    ),
]


# ── round-15 自查修复的承重变异
MUTATIONS += [
    # ⛔ M133 已**退役**（round-16）: envelope 已改用类型保真的规范树 `_canon_tree`,
    # 不再走 `json.dumps + _num_norm`。该性质由 M146/M147 与门(91) 直接守着。
    # ⛔ M134 已**退役**（round-16）: `_num_norm` 已被 `_canon_tree` 取代,
    # 「bool 与数值必须分型」由 M147 与门(91) 的等价面断言守着。
]


# ── round-15 修复的承重变异
MUTATIONS += [
    (
        # scored_at 不进扩展行识别 ⇒ 损坏行伪装成 §6.3 历史行
        "M135-scored-at-not-in-ext-detection",
        SKILL,
        '        if "schema_ext" in _pl or _looks_like_review_ext(_pl) or "scored_at" in _pl:\n',
        '        if "schema_ext" in _pl or _looks_like_review_ext(_pl):  # MUTANT\n',
        "test_round15_scored_at_in_ext_detection",
    ),
    (
        # 退回用 W 覆盖当凭据 ⇒ 后继事件制造假覆盖
        "M136-w-coverage-as-applied-proof",
        SKILL,
        '        _rc_applied = _rcpt.get("fsrs_applied")\n        if _rc_applied is not True:\n',
        "        _rc_applied = True  # MUTANT: 退回 W 覆盖\n        if False:\n",
        "test_round15_event_level_fsrs_applied",
    ),
    (
        # receipt 不记 fsrs_applied ⇒ 事件级凭据消失
        "M137-receipt-no-applied-flag",
        SKILL,
        '              f\'    fsrs_applied: {"true" if _e_applied else "false"}\\n\'\n',
        "              # MUTANT: 不记事件级调度凭据\n",
        "test_round15_event_level_fsrs_applied",
    ),
    (
        # board 校验退回 string-only ⇒ 自产自拒
        "M138-board-string-only",
        SKILL,
        "_ok_board = lambda v: True",
        "_ok_board = lambda v: isinstance(v, str)  # MUTANT",
        "test_round15_board_no_self_produced_rejection",
    ),
    (
        # 来源反查两头试 ⇒ exact full receipt 被当成别人的 bare 来源
        "M139-source-lookup-both-ways",
        SKILL,
        # ⚠️ round-16 重绑: 条件已加上「exact 且带 full 标记才豁免」。
        '            elif _lid.startswith("quiz:") and _lid[5:] == _tok and not (_is_exact and _tok_marked):\n',
        '            elif _lid.startswith("quiz:") and _lid[5:] == _tok:  # MUTANT: 不分解释类型\n',
        "test_round15_source_lookup_respects_candidate_kind",
    ),
    (
        # 裸形态碰撞的独立判据被去掉 ⇒ 回到「顺带实现」的脆弱状态
        "M140-bare-collision-no-own-judge",
        SKILL,
        '    if _cands:\n        _bare_of = lambda x: x[5:] if x.startswith("quiz:") else x\n',
        '    if False:  # MUTANT: 去掉裸形态碰撞的独立判据\n        _bare_of = lambda x: x[5:] if x.startswith("quiz:") else x\n',
        "test_round15_bare_collision_has_own_judge",
    ),
    # ── M141-rolling-baseline-from-durable：退役（**schema-valid producer-domain equivalent**，不是无条件等价）
    # ⛔ round-17 MEDIUM 收窄: 逐路径复核的结论是「**合法自产状态**上两支等价」，
    # 而**被写坏的、带 receipt 的 pending 行**上并不等价（那条路径既跳过
    # `_adopted_ok` 也不执行 `_append_calibration`）。本卡的题面明确把「日志被别的
    # 程序写坏」算在输入域内，所以不能写成无条件等价。
    # 该损坏态由「损坏账本 fail-closed」那一族门守着；等严格 receipt 状态门补齐后，
    # 才谈得上证明它也不可达或不可观察。**移交**。
    #
    # ⛔⛔ round-16 我给的退役推证是**错的**，round-17 独立审查证伪。原话是：
    #   「`_w_roll` 赋值之后紧接着 `_append_calibration(..., actual_ts=_w_after)`，
    #     其 `_aa_diff` 哨兵一旦发现两值不同瞬间就 raise，于是差异必然在被观测前
    #     把进程打死」。
    # 两处都不成立：
    #   ① 那次调用在 `if _o.get("event_id") != evid and not _already_:` **之内** ——
    #      pending 行是本次事件(dup) 或已带可解析 receipt 时整个被跳过，哨兵看不到分叉；
    #   ② 变异体里 `_w_after = None` ⇒ `if actual_ts is not None` 恒假 ⇒ `_aa_diff`
    #      恒 False，哨兵**结构性失效**，更不可能「把进程打死」。
    # ⚠️ 错误的形状值得记住：「赋值之后**紧接着**」是**文本相邻**，不是**控制流必达**。
    #    中间隔着一个 `if`，我读代码时把它读成了直线。
    #
    # ✅ 真正的退役理由（round-17 独立复核实测，与结论无关地更强）：
    #    差异**可观测**（一支零写、一支把违反 A3/A6 的状态原子发布），但制造差异所需的
    #    输入在 schema 不变量下**不可达**，需要两处生产产不出的手术：
    #      · 把一条无 receipt 的行**插到已有行之前**（违反 schema §一 append-only）；
    #      · 节点保留 `calibration_log` 却同时删掉 `fsrs_*` 与 `attempt_count`
    #        （节点是 tmp+fsync+os.replace 原子发布，崩溃只给整份旧或整份新；
    #         唯一可达的「有 receipt 无 W」是 degraded 遗留，而它**保留** attempt_count）。
    #    在**可达**形态上实测两支逐字相同（崩溃窗预置、append-only 真实产生顺序两组，
    #    ORIG 与 MUT 均 rc=1 zero-write=True，输出逐字一致）。
    #    ⇒ 保留它只会逼出一道预置违反 schema 不变量的门（本卡明令禁止的「fixture 形态
    #      ≠ 生产形态」），故退役。
    #
    # ⚠️ 连带如实记：`_aa_diff` 哨兵在全部门下**从未被触发**（拆成 `if False:` 全绿）。
    #    所以它是一道**当前不可达的纵深**，不能作为 round-16 H④「分叉升为硬错误」的
    #    执行归因 —— 真正拦住 H④ 那个形态的是 `_adopted_ok` 的收紧。归因已就地更正。
]


# ── round-16 修复的承重变异
MUTATIONS += [
    (
        # dup 分支退回全局 W 判「已应用」⇒ 后继事件制造假覆盖
        # ⚠️ 锚点更新（CARD-DEBT-mutation-kill-identity，Z6-C 移交项 1/4）：
        # round-17 B① 把 `bool(_rc_dup_applied)` 收紧成 `(_rc_dup_applied is True)`，
        # 旧锚从此**命中 0 次** ⇒ 这一条整整一轮什么都没测（Z6-C 全量 138 里的
        # 4 条 ANCHOR-ERROR 之一）。现址 `SKILL.md:2213-2216`，车道树 count=1 实测。
        # ⚠️ 更锚后**性质不变**：变异打的仍是「dup 分支不看事件级凭据、改用全局 W 猜」，
        # 与 round-17 收紧的是同一个赋值式；收紧改的是「怎么判 true」，本变异拆的是
        # 「判不判事件级凭据」，两者不是同一件事（所以不能拿 g32cb M1 替代）。
        "M142-dup-uses-global-w",
        SKILL,
        "    _fsrs_applied = (\n"
        "        (_rc_dup_applied is True) if _rc_dup is not None\n"
        "        else (W_inst is not None and W_inst >= _dup_inst)\n"
        "    )\n",
        "    _fsrs_applied = W_inst is not None and W_inst >= _dup_inst  # MUTANT\n",
        "test_round16_fsrs_applied_across_all_branches",
    ),
    (
        # 旧条目缺凭据时不拒 ⇒ 回落 W 猜
        # ⚠️ 锚点更新（Z6-C 移交项 2/4）：round-17 B① 把「只拒 None」改成
        # 「不是 bool 就拒」，旧锚 `_rc_dup_applied is None` 命中 0 次。
        # 现址 `SKILL.md:2183`，车道树 count=1 实测。
        # ⚠️ 与 `g32cb` 的 M1 **锚在同一行但不是同一个变异**（Codex 已逐行反证过
        # 「M1 承重」这个说法不成立）：M1 把判据退回 `is None`（缺键仍被拒，只放过
        # 非布尔值），本条 `if False:` 把整道拒绝拆掉（缺键也放过）。绑的门也不同。
        "M143-missing-applied-flag-tolerated",
        SKILL,
        "    if _rc_dup is not None and type(_rc_dup_applied) is not bool:\n",
        "    if False:  # MUTANT: 缺凭据不拒\n",
        "test_round16_fsrs_applied_across_all_branches",
    ),
    (
        # false + W 覆盖不判状态矛盾 ⇒ 宣称「已完整应用」
        "M144-false-plus-w-not-contradiction",
        SKILL,
        "    if _rc_dup is not None and _rc_dup_applied is False and W_inst is not None and W_inst >= _dup_inst:\n",
        "    if False:  # MUTANT: 不判状态矛盾\n",
        "test_round16_fsrs_applied_across_all_branches",
    ),
    (
        # 恢复成功后不升 true ⇒ 凭据生命周期断裂
        # ⚠️ 锚点更新（Z6-C 移交项 3/4，**纯重构漂移**）：那段 `_fa_pat.sub(...)`
        # 已抽成 `_promote_applied()`（`SKILL.md:579` 定义），旧锚命中 0 次。
        # 防线本身没动，只是搬了家 ⇒ 更锚到**dup 恢复**的调用点 `SKILL.md:2726`
        # （车道树 count=1 实测）。
        # ⚠️ 不能换成 `:2602` 那个调用点：那是 **foreign** 恢复，已由 `g32cb` 的 M2
        # 覆盖；两个调用点触发事件不同（重跑同一事件 vs 由另一事件触发），
        # Codex 已反证「M2 能替代本条」不成立。
        "M145-recovery-does-not-promote-flag",
        SKILL,
        "        fm, _ = _promote_applied(fm, evid)\n",
        "        pass  # MUTANT: 恢复后不升 true\n",
        "test_round16_fsrs_applied_across_all_branches",
    ),
    (
        # ⛔ 直接复原审查抓到的**压平缺陷**：`Decimal.normalize()` 受默认 context
        # 精度 28 位限制，`10**30` 与 `10**30+1` 都变成 `1E+30`。
        # ⚠️ 我先前两版变异都无效，各错在一处：
        #   ① 在**新实现**上改单个类型标签 —— 规范树的**结构**（元组长度+内容）
        #      已提供类型区分，改标签打不出行为差异;
        #   ② 把「退回旧数值编码」的代码插进**字符串分支** —— 而数值分支在它**之前**
        #      就 return 了，插入位置在控制流上**不可达**。
        # ⛔ 变异和门一样要问：**这段代码会被执行到吗**。
        "M146-canon-num-precision-loss",
        SKILL,
        "        _sign, _digits, _exp = _d.as_tuple()\n",
        "        _sign, _digits, _exp = _d.normalize().as_tuple()  # MUTANT: 受 context 精度限制\n",
        "test_round16_canonical_tree_type_faithful",
    ),
    # ⛔ M147 已并入 M146（同一缺陷载体：整套旧编码），单改标签打不出行为差异。
    (
        # 无标记 exact 不枚举历史裸来源 ⇒ 借用他人 receipt
        "M148-unmarked-exact-single-source",
        SKILL,
        '            elif _lid.startswith("quiz:") and _lid[5:] == _tok and not (_is_exact and _tok_marked):\n',
        '            elif _lid.startswith("quiz:") and _lid[5:] == _tok and not _is_exact:  # MUTANT\n',
        # round-16 改绑: 原门测的是**反向**性质（exact full 不被当别人的 bare 来源），
        # 本变异打的是正向（无标记 exact 不枚举历史裸来源）—— 两个不同的场景。
        "test_round16_unmarked_exact_enumerates_both_sources",
    ),
    (
        # A3 判据退回「两个可解释值」⇒ 同瞬间两行被放行
        "M149-adopted-two-values",
        SKILL,
        "    return _got == _adopted_from(_sa, _w_inst)\n",
        "    return _got == _adopted_from(_sa, _w_inst) or _got == _adopted_from(_sa, None)  # MUTANT\n",
        "test_round16_same_instant_rows_rejected_per_a3",
        (
            # ⚠️ depth 层: round-16 加的「不该到达的状态」哨兵会独立拦住同一个坏状态
            # （它不是被测对象，是另一道防线）。拆掉它，让 A3 判据成为唯一屏障。
            (
                SKILL,
                "    if _aa_diff:\n",
                "    if False:  # MUTANT: 拆掉兜底哨兵\n",
            ),
        ),
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


# ── round-16 三条 HIGH 的承重变异
MUTATIONS += [
    (
        # 别节点非法整数 id 阻塞本节点（登记面退回 str() 强转）
        "M150-all-ledger-ids-coerce-str",
        SKILL,
        "_ALL_LEDGER_IDS = tuple(\n",
        '_ALL_LEDGER_IDS = tuple(  # MUTANT: 登记面退回 str() 强转\n    str(_r.get("event_id") or "") for _, _r in _rows if isinstance(_r, dict)\n) if True else tuple(\n',
        "test_round16_foreign_nonstr_event_id_does_not_block",
    ),
    (
        # receipt 的 exam_board 退回「JSON 字面裸嵌 YAML」⇒ 自产自拒
        "M151-exam-board-bare-json-in-yaml",
        SKILL,
        "              f'    board_form: {q_(\"json\")}\\n'\n",
        "",  # MUTANT: 连标记一起去掉（旧版本从来没有这一行）
        "test_round16_exam_board_roundtrips_through_yaml",
        (
            # ⚠️ 忠实性: 只把标记改成 legacy 而保留新式双编码, 会产出**任何正式
            # 版本都没写过的混合 receipt**（round-17 MEDIUM 指出）。真实的旧形态是
            # 「没有 board_form 行 + exam_board 存裸值」——两处必须一起退回。
            (
                SKILL,
                '              f\'    exam_board: {q_(json.dumps(_e_pl.get("exam_board", ""), ensure_ascii=False, sort_keys=True))}\\n\'\n',
                '              f\'    exam_board: {q_(_e_pl.get("exam_board", ""))}\\n\'\n',
            ),
        ),
        "complete",
    ),
    (
        # F1-only 无视持久写序锚, 退回按时刻猜 cursor
        "M152-f1-ignores-write-order-anchor",
        SKILL,
        '                if isinstance(_rc_probe_f1, dict) and "pred_id" in _rc_probe_f1:\n',
        "                if False:  # MUTANT: 无视写序锚\n",
        "test_round16_f1_only_uses_persisted_write_order_anchor",
    ),
    (
        # 无锚旧 receipt 不做歧义证明 ⇒ 硬算一个错的期望序数
        "M153-legacy-cursor-skips-ambiguity-proof",
        SKILL,
        "                    if _amb_f1:\n",
        "                    if False:  # MUTANT: 不证明就硬算\n",
        "test_round16_legacy_receipt_without_anchor_says_unprovable",
    ),
]


# ── round-17（对抗预审确认项）的承重变异
MUTATIONS += [
    # ── M154-q-bare-ensure-ascii-false：退役（**承重面上移，不是死纵深**）
    # 原变异拆掉 `q_()` 的往返自证，绑 `test_round17_receipt_survives_yaml_hostile_chars`。
    # CARD-G3-2c-C 把字符轴反转成**一律拒绝**（§6.1 字符轴规范输入集，码点区间闭合），
    # 判据上移到校验器 `value_charset_problems()`，那道门也随之反转为
    # `test_round17_hostile_chars_now_rejected_not_survived`。
    # ⇒ 非规范码点在**进入 q_() 之前**就被拒，本变异再拆 `q_()` 也观察不到差异（会 SURVIVED）。
    # 承重面移交：`g32cb_mutation_gates.py` 的 M6（拆字符轴判据）与 M7（区间退化成枚举），
    # 二者实测均 KILLED。
    # ⚠️ 如实声明未证明面：`q_()` 的往返自证如今是**纵深**（校验器被绕过时仍起作用），
    # 退役**不等于**它被证明过。要为纵深挂变异，必须同时禁掉校验器那一层（depth 类变异），
    # 那是另一套设计，本脚本不做。
    (
        # 无视 board_form 标记恒 json.loads ⇒ 旧条目读不出来（向后兼容契约无承重面）
        "M155-board-form-ignored",
        SKILL,
        '                    if _e.get("board_form") == "json":\n',
        "                    if True:  # MUTANT: 无视标记恒解码\n",
        "test_round17_legacy_receipt_without_board_form_still_read",
    ),
    (
        # 锚点命中 0 条即判死 ⇒ 把 F1-only 自己的前提（账本行丢失）变成死路
        "M156-anchor-miss-is-hard-error",
        SKILL,
        "                        if len(_hit_f1) > 1:\n",
        "                        if len(_hit_f1) != 1:  # MUTANT: 锚点成唯一证据\n",
        "test_round17_anchor_is_preferred_not_sole_evidence",
    ),
    (
        # 不校验锚点方向 ⇒ 指向后继即可让被篡改的 attempt_count 通过序数复算
        "M157-anchor-direction-unchecked",
        SKILL,
        "                            if _ib_a is not None and _ib_a > _rc_inst_f1:\n",
        "                            if False:  # MUTANT: 不校验方向\n",
        "test_round17_anchor_direction_is_verified",
        (
            # ⚠️ 「方向校验」在生产里有**两个站点**（时刻 / 序数）—— 它们是同一道
            # 防御的两半, 不是纵深。只拆一半时另一半照样抓住篡改 ⇒ 缺陷根本没被
            # 放回来（实测 SURVIVED）。属「变异覆盖不完整」, 处置是补齐同缺陷的其它站点。
            # ⚠️ 锚点更新（Z6-C 移交项 4/4）：序数那一半原是多行布尔表达式里的
            # `and _na_a >= _nr_a` 续行，现已合成一行 `if _ord_ok and _na_a >= _nr_a:`
            # （`SKILL.md:1997`，车道树 count=1 实测），旧层锚命中 0 次。
            # ⛔ 层锚失败发生在**落盘之前** ⇒ 整条跳过 —— 主锚命中 1 次**不算测过**，
            # 这一条与另外三条一样，Z6-C 那轮什么都没测到。
            (
                SKILL,
                "                            if _ord_ok and _na_a >= _nr_a:\n",
                "                            if _ord_ok and False:  # MUTANT: 不校验方向(序数)\n",
            ),
        ),
        "complete",
    ),
]


# ── round-17 终审（3 BLOCKER + 1 HIGH）的承重变异
MUTATIONS += [
    (
        # 凭据判据退回「只拒 None」⇒ 字符串 "false" 被 truthiness 当成已应用, 静默漏一次 FSRS
        "M158-fsrs-applied-truthiness",
        SKILL,
        "    if _rc_dup is not None and type(_rc_dup_applied) is not bool:\n",
        "    if _rc_dup is not None and _rc_dup_applied is None:  # MUTANT: 只拒 None\n",
        "test_round17_fsrs_applied_must_be_strict_bool",
    ),
    # ── M159-rebuild-bare-json-dumps：退役（同 M154，承重面上移 + 载体不可达）
    # 原变异让重建路径退回裸 `json.dumps`，绑
    # `test_round17_rebuild_preserves_existing_receipt_bytes`（该门用 U+0085 作载体）。
    # 字符轴反转后那个载体**不可达**（首写即拒），门已改为
    # `test_round17_rebuild_hostile_carrier_is_unreachable_now` 只锁"老路确实被封"。
    # ⚠️ 它原先守的性质 —— **追加新条目时不得改动已有条目** —— 与字符轴无关，仍然要守；
    # 已移交给 `test_g32cc_emitter_rebuild_never_mutates_existing_entries`：用**合法中文值**
    # 走同一条重建路径，逐项类型敏感比对**整个条目**（不只 exam_board 那一行），
    # 并断言删账本行后重跑不二次计分。
    # ⚠️ 如实声明未证明面：该新门当前**没有对应的变异**为它承重打分 —— 要打，
    # 变异对象应是重建路径的**类型保真比较**（`_canon_tree(_kept) != _canon_tree(_cur)`）
    # 而不是字符编码。登记为 backlog。
    # ── M160-canon-tree-recursive：退役（**被更强的防线取代，且已被独立复核证伪**）
    # 原变异把 `_canon_tree` 退回递归实现，绑 `test_round17_deep_json_recovers_after_crash_window`。
    # CARD-G3-2c-B 给账本加了输入硬上限（深度 ≤64）后，>64 层不再是合法输入，
    # 那道门的用例从 512/900 降到上限内 ⇒ **递归版在上限内也绰绰有余**。
    # Codex 独立复核实测：把 `_canon_tree` 换回等价递归实现，该门仍 PASS。
    # ⇒ 本变异已无鉴别力（必然 SURVIVED），且它想守的性质（深层值不造成不可恢复窗）
    # 现在由**上限本身**承担：`g32cb_mutation_gates.py` 的 M4（拆深度判据）/
    # M5（拆节点判据）实测 KILLED。
    # ⚠️ 如实声明：显式栈实现仍然保留（纵深），但在新契约下它与递归版**无可观测差异**，
    # 因此没有任何门能区分两者 —— 这是取代，不是"证明了显式栈没必要"。
    (
        # foreign 恢复**静默**不提升事件级凭据 ⇒ 两阶段永不收敛, 原白板卡死
        "M161-foreign-no-credential-promotion",
        SKILL,
        "            fm, _ok_fg = _promote_applied(fm, _rid_)\n",
        "            _ok_fg = True  # MUTANT: foreign 静默不提升凭据\n",
        "test_round17_foreign_degraded_recovery_converges",
    ),
]


#: 每条变异**声称**会打红的那一条断言的消息片段（首行字面，门文件里恰好 1 次）。
#: 见 `mutation_kill_identity` 的模块 docstring —— 判据面是 `-rf` 短摘要的 reason，
#: 它只取断言消息的**第一行**，所以绑到第一个 `{}` 插值之后的内容会恒不命中。
#: ⛔ 缺项不得静默放过：`_check_expect_msg()` 要求每个 tag 要么在这里，要么在
#: `EXPECT_MSG_EXEMPT` 里带理由。
#:
#: ⚠️ **这张表是怎么来的，如实说**（CARD-DEBT-mutation-kill-identity）：
#:   · `M142` / `M143` / `M145` / `M157` 这 4 条（本卡刚更锚的）是**先读门源码**
#:     推出「这条变异会先撞上哪一格/哪一条断言」再写的。例如
#:     `test_round16_fsrs_applied_across_all_branches` 的四格状态机：缺键→①、
#:     false+未覆盖→②、false+W 覆盖→③、true+W 未覆盖→④，四条变异各打一格。
#:   · 其余 91 条是**先跑一次 `--probe`**（不做判定、裁决一律 OBSERVED、rc 恒 4）
#:     拿到该门实际的短摘要拒因，再逐条对着变异意图确认「这条断言就是它声称要打红
#:     的那条」后回填的。
#:   ⛔ 后一种绑定方式**今天证不出多少东西**（判据与被测量同源）；它的价值在
#:   **从今往后**：门或生产代码一漂移、击杀落到别的断言上，就会立刻报 SURVIVED，
#:   而不是像过去那样静默记成 KILLED。这一条已写进验收单「本卡未证明什么」。
EXPECT_MSG: dict[str, str] = {
    "M1-R1-candidate-spread": "合法乱序形态的 out_of_order 键仍须 envelope 冲突",
    "M3-R3-attempt-uses-tip": "历史事件原样重跑必须 no-op, 不得报冲突: ",
    "M4-R4-normal-path-uses-payload-ts": "含 idle 状态 + A3 bump 时, 恢复产物必须与直接应用逐字节相同",
    "M6b-R7-tail-ignores-lf-state": "带终止 LF 的坏末行必须 fail-closed (旧实现 rc=0 当截断容忍)",
    "M7-R6-schema-drops-owner-clause": "§6.2 duplicate 门段落缺「",
    "M8-6cell-cell4-allow-recovery": "格4: 顺序错乱无机械判据, 必须 fail-closed",
    "M11-N1-drop-out-of-order-semantic-gate": "标 out_of_order 但晚于水位线的行必须 fail-closed（否则静默丢一次评分）",
    "M17-N1-schema-drops-writer-side-clause": "」— 写点侧口径未回写契约",
    "M18b-R7blank-judge-file-end-not-last-line": "] 应 fail-closed（该行是完整落盘后损坏）",
    "M19-B1-drop-rating-completeness": "] 评分事实不完整的行不得被重放",
    "M21-B2-drop-attempt-sync-on-replay": "A2 重放必须把 attempt 推到 durable 值，否则下一个事件会复用同一序数",
    "M28-C4-mastery-uses-unrounded-gn": "同一 durable 事件（GN2 相同）在两次不同的未舍入输入下必须产出相同的 mastery",
    "M33-R3-merge-recovery-and-append": "两条 pending 时不得在同一次运行里既恢复又追加",
    "M34-R3-drop-routing-envelope-gate": "] 不可路由的行必须 fail-closed（§一 路由信封读方义务）",
    "M35-R3-effective-at-over-strict": " 写点结论应为 ",
    "M36b-replay-drops-mastery": " 写点结论应为 ",
    "M37c-replay-includes-dup-double-eats-ema": " 不得二次吸收成绩 (EMA 双吃)",
    "M39-attempt-regex-rejects-single-quote": " 应承接为 ",
    "M42-late-unmarked-row-silently-skipped": "] 未标 out_of_order 的迟到行不得被静默放过",
    "M43-f1-evaluated-after-calibration-replay": " 写点结论应为 ",
    "M44-drop-looks-like-review-ext": "抹掉 marker 但留扩展键 = 把完整评分伪装成历史行，必须拒",
    "M46-yaml-single-quote-escape": "YAML 单引号 '' 转义形态下 F1 必须命中，否则副作用被算第二遍: ",
    "M48-attribution-check-after-payload-skip": "别节点的坏行不得越权阻塞本节点写入: ",
    "M52-calibration-strips-quiz-prefix": "正常场景回归: ",
    "M53-f1-query-strips-prefix-only": "正常场景回归: ",
    "M54-f1-uses-bare-eid": "裸形态相同的两个 event_id 并存时必须 fail-closed: ",
    "M56-full-validation-after-branching": "标了 out_of_order 但时刻带空白的行必须在分流前被校验拦下",
    "M57-validate-without-golden-manifest": "伪造的 fsrs 身份键必须被 manifest 绑定门拦下",
    "M59-ordinal-ignores-legacy-scored-rows": "拒因必须点名真因，而不是 envelope 冲突: ",
    "M60-normal-path-stores-bare-eid": "正常路径必须存完整账本 id: ",
    "M62-node-id-type-only": " 无法路由，静默跳过等于漏算",
    "M63-ts-match-not-fullmatch": "拒因须来自 ts 的字面门: ",
    "M64-dumps-allows-nan": "NaN 会被 json.dumps 原样写成字面量，而校验器拒收",
    "M66-legacy-same-id-rejected": "同 ID 的合法历史行必须幂等 no-op（A4.5）: ",
    "M67-inline-calibration-not-normalized": "产出了非法 YAML: ",
    "M68-blank-lines-tolerated": "] 校验器拒，写点也必须拒",
    "M69-bom-tolerated": "] 校验器拒，写点也必须拒",
    "M70-ordinal-w-only-not-calibration": "E2 已贡献 attempt（校准里有它），重跑 E1 必须幂等: ",
    "M71-ignore-provable-legacy-ordinal": "历史行带合法 attempt_count ⇒ 账本可证，必须放行: ",
    "M73-late-scan-after-early-exit": "幂等早退不得绕过全账迟到扫描（那次复习会永久漏算）",
    "M74-candidate-copies-durable-rt": "同 ID 承载另一业务时刻必须被 envelope 识别",
    "M78-first-write-uses-run-ts": " 推进, 而不是本次运行时刻 2026-08-01T10:05:00Z: ",
    "M80-envelope-compares-adopted-rt": "A3 采用值不进等价面，续跑必须可恢复: ",
    "M82-calibration-header-no-comment": "] 同 ID 重跑必须收敛（此前永久停住）: ",
    "M83-whitespace-id-gate-global": "别节点的合法存量行不得阻塞整个 vault: ",
    "M84-cross-node-id-collision-ignored": "别节点占用本次幂等键会让本次评分**零次应用**，必须拒",
    "M85-no-producer-self-check": "2026-02-30 形状合法但日期不存在 —— 词法门放行，自检必须拦",
    "M86-f1-regex-not-yaml": "键顺序不是事实差异，F1 必须仍命中: ",
    "M88-degraded-uses-run-ts": "scored_at = 原始稳定业务时刻: ",
    "M94-routing-raw-compare": "E1 必须落进适用集（否则 attempts 会是 [1,1]，E1 永久漏算）: ",
    "M95-receipt-skips-abandoned": "同为弃答的续跑必须恢复: ",
    "M96-adopted-time-unbound": "篡改采用时刻会让同一次评分二次推进 FSRS",
    "M98-no-pre-append-dry-run": "⛔ 必须**零写**拒绝 —— 先落账后损坏笔记是最糟的中间态",
    "M99-f1only-skips-fact-check": "账本缺失时裸形态来源无从证明，不得静默吞掉这次评分",
    "M100-no-tri-instant-binding": "⛔ receipt 的第三个瞬间对不上 ⇒ 必须停",
    "M103-receipt-ts-no-literal-gate": "] 必须拒 —— 只查类型/非空是「声明比实现宽」",
    "M104-writeback-guess-by-text": "不得同时出现 quoted 与 bare 两个语义相同的键: ",
    "M110-reinline-duplicate-lookup": "来源反查逻辑出现多份 —— 判据一旦分叉, 修一处就会漏另一处",
    "M111-shared-impl-not-reused": "唯一实现必须以具名函数存在(否则无从复用)",
    "M112-compat-empty-source-rejects": "来源为空但事实自洽必须仍能恢复: ",
    "M113-facts-list-not-frozen": "缺项检查的守卫必须真的在",
    "M114-f1only-drops-exam-board": "同板续跑必须恢复: ",
    "M115-late-scan-presence-only": "账本行与 receipt 的事实不一致时不得放行",
    "M116-receipt-no-provenance": "新写入必须带形态标记",
    "M118-empty-eid-allowed": "空/纯空白 event_id 必须拒: ",
    "M119-crash-window-adopted-time-unproven": "水位线为空时采用时刻≠原始时刻的行必须拒",
    "M120-legacy-row-generic-reason": "拒因必须点名旧行缺字段: ",
    "M121-consumer-rounds-grade": "⛔ 消费侧舍入会把合法的三位小数行永久拒掉: ",
    "M122-consumer-coerces-board": "⛔ 消费侧强转会拒掉 writer 自己产出的状态: ",
    "M123-adopted-time-literal-compare": "⛔ 字面比较会把合法的小数秒输入永久拒掉: ",
    "M124-crash-window-only-when-w-empty": "W 非空的崩溃窗同样不得放行篡改",
    "M125-id-form-authorizes-bare-fallback": "另一个完整 id 的评分应当入账: ",
    "M126-f1only-no-successor-discount": "⛔ 非-tip 的合法续跑不得被误拒: ",
    "M127-facts-python-equality": "1 与 true 是不同的 JSON 事实，不得判成同一次评分",
    "M128-id-form-not-at-candidate-stage": "⛔ 不得静默跳过（原缺陷：rc=0 而账本与 attempt 全不动）: rc=",
    "M130-pending-adopted-time-unproven": "foreign pending 的采用时刻同样要证",
    "M132-candidate-always-rounded": "⛔ 给出原值时必须能落定: ",
    "M135-scored-at-not-in-ext-detection": "带 scored_at 的行不得被当历史行跳过",
    "M136-w-coverage-as-applied-proof": "后继事件推过的 W 不算这次的调度凭据",
    "M137-receipt-no-applied-flag": "降级路径必须记 false",
    "M138-board-string-only": "] 自产自拒: ",
    "M139-source-lookup-both-ways": "⛔ 来源反查错位导致误拒: ",
    "M142-dup-uses-global-w": "不得再推进水位线",
    "M143-missing-applied-flag-tolerated": "旧条目缺事件级凭据 ⇒ 不可证，必须停",
    "M144-false-plus-w-not-contradiction": "⛔ 不得宣称「已完整应用」—— 那次的调度贡献其实永久错位了",
    "M145-recovery-does-not-promote-flag": "⛔ 恢复成功后必须把该条目升为 true",
    "M146-canon-num-precision-loss": "] 两份不同事实不得判等",
    "M148-unmarked-exact-single-source": "拒因须点名「来源可能是多个 event_id」（不退化成「随便什么理由拒了都算数」）: ",
    "M149-adopted-two-values": "同瞬间两行违反 A3，必须 fail-closed",
    "M150-all-ledger-ids-coerce-str": "⛔ 别节点坏行不得阻塞本节点的幂等重跑: ",
    "M151-exam-board-bare-json-in-yaml": "首写应放行 board=",
    "M152-f1-ignores-write-order-anchor": "⛔ 有写序锚就该认得出这是同一次评分: ",
    "M153-legacy-cursor-skips-ambiguity-proof": "拒因须点名「顺序不可证明」, 不能报一个算错的期望序数: ",
    "M155-board-form-ignored": "⛔ 旧条目必须按原语义读得出来: ",
    "M156-anchor-miss-is-hard-error": "⛔ 前驱行也丢了时必须回落到可证的路径, 而不是判死: ",
    "M157-anchor-direction-unchecked": "⛔ 锚点指向后继 ⇒ 与账本自相矛盾, 必须停",
    "M158-fsrs-applied-truthiness": "] 非布尔凭据不得被当成「已应用」",
    "M161-foreign-no-credential-promotion": "⛔ 恢复后 E1 仍不可重跑 ⇒ 两阶段不收敛，那张白板卡死: ",
    # ⚠️ Codex round-1 MEDIUM-5 整改：这一条原被判「片段不唯一」进了豁免表，**是错的**——
    # 该断言的消息是 `"裸 \\r 结尾在字节上无 LF ⇒ 应按截断隔离: " + r2.stdout + r2.stderr`
    # （字符串拼接），去掉含转义的开头后剩下的这段在门文件里恰好 1 次，可直接绑，不必改门。
    "M13b-N2-text-mode-read": "结尾在字节上无 LF ⇒ 应按截断隔离: ",
}

#: 显式豁免表 `{tag: 具体理由}` —— **不是「先欠着」**，每条都写清楚为什么绑不出来。
#: 四种形态（都由 `--probe` 的实际拒因分类，不是猜的）：
#:   ① 断言消息**整体就是被测子进程的 stderr**（`assert X, r.stderr[:N]` 形态）——
#:      门文件侧一个字面片段都没有；绑生产文本会让判据被生产输出喂饱（正是要防的）；
#:   ② 断言消息**求值为空串**，短摘要里只有 `AssertionError:`；
#:   ③ **无消息断言**，短摘要给的是 pytest 改写出来的**值**（`assert 1 == 0`）——
#:      那是值不是身份，换个 fixture 数据就变；
#:   ④ 该变异让门以**未捕获异常**失败（如 `yaml.parser.ParserError`），
#:      根本没落在门里任何一条断言上。
#:   ⑤ 断言消息**逐字抄自生产的报错文案** —— 片段在生产文件里也命中，绑上去判据就能被
#:      生产输出喂饱（`M76` 就是这一类，由自检当场拦下）；
#:   ⑥ 该门实际打红的那条断言，其消息首行的字面片段在门文件里**不唯一**（>1 次）——
#:      绑上去就不能证明红在哪一条。
#: ⚠️ 这四种的根都在**门文件本体**（消息写法），而门本体不在本卡范围
#: （`backend/tests/**` 的 `git diff` 为空）。补消息后这些条目就能从表里去掉 ——
#: 已在验收单「台账待登记条目」里移交。
EXPECT_MSG_EXEMPT: dict[str, str] = {
    "M76-self-node-id-gate-dropped": "⑤ 该门此处断言的消息**逐字抄自生产的报错文案**"
    "(`SKILL.md:331` 的 `写出去的事件将永远路由不到任何节点`) —— 绑上去等于让判据可被生产输出"
    "喂饱; 这一条是被 `check_expect_msg_unique()` 的「生产侧命中 0 次」当场拦下的, 不是事后补的",
    "M2b-R2-drop-utc-offset-check": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M5-R5-drop-rating-consistency": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M9-6cell-cell2-drop-orphan-noop": "② 该门此处断言的消息**求值为空串**, 短摘要里只有 'AssertionError:' —— 没有任何可绑的身份",
    "M10-R2-value-not-literal": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M12-N1-drop-out-of-order-shape-gate": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M14-N3-drop-duplicate-key-hook": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M15b-N4-decode-with-replace": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M16-N5-hard-compute-attempt-across-pending": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M20-B1-drop-gradenorm-completeness": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M23-C1-drop-event-type-gate": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M24-C1-drop-concept-id-gate": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M25-C1-drop-vault-id-gate": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M26-C2-drop-eid-whitespace-gate": "② 该门此处断言的消息**求值为空串**, 短摘要里只有 'AssertionError:' —— 没有任何可绑的身份",
    "M29-R3-drop-event-version-gate": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M30-R3-drop-two-instant-consistency": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M31-R3-drop-attempt-required": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M32-R3-drop-payload-object-gate": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M38b-attempt-expectation-masked-by-max": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M45-allow-dup-and-foreign-same-round": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M47-skip-validator-record-check": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M49-event-version-accepts-bool": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M50-non-object-line-silently-skipped": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M51-line-strip-washes-nonjson-whitespace": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M58-input-ts-not-literally-checked": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M61-durable-eid-whitespace-not-scanned": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M65-loads-allows-nan": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M75-w-fallback-restored": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M77-ordinal-fixed-minus-one": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M79-missing-scored-at-falls-back": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M81-legacy-out-of-order-honored": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
    "M89-receipt-drops-scored-at": "③ 该门此处是**无消息断言**, 短摘要给的是 pytest 改写出来的值(如 'assert 1 == 0'), 那是值不是身份, 换个 fixture 数据就变",
    "M90-receipt-drops-attempt": "③ 该门此处是**无消息断言**, 短摘要给的是 pytest 改写出来的值(如 'assert 1 == 0'), 那是值不是身份, 换个 fixture 数据就变",
    "M91-f1-only-unconditional-noop": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M97-writeback-regex-only": "④ 该变异让门以**未捕获异常**失败(yaml.parser.ParserError), 而不是落在门里任何一条断言上; 可绑的身份是异常类名, 但它不在门文件里(唯一性判据要求片段在门文件里恰好 1 次)",
    "M102-receipt-attempt-type-only": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M117-empty-source-skips-provenance": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M129-missing-scored-at-warn-only": "① 该门此处断言的消息**整体就是被测子进程的 stderr**(`assert X, r.stderr[:N]` 形态), 没有任何来自门文件的字面片段可绑; 绑生产文本会让判据被生产输出喂饱",
    "M140-bare-collision-no-own-judge": "⑥ 该门实际打红的那条断言, 其消息首行的字面片段在门文件里不唯一(出现 >1 次), 绑上去就不能证明红在哪一条; 门本体不在本卡范围, 无法给它加更具身份的消息",
}

#: 每条变异**声称**会打红的那一条断言的**源位置**（`stmt:<12 位十六进制>` =
#: 门文件里那条语句的 AST 规范化指纹，见 `mutation_kill_identity.stmt_fingerprints`）。
#:
#: ⛔ 它解决 `EXPECT_MSG` 解决不了的那一半（Y1-B Codex HIGH-1）：消息判据分不开
#: 「前提断言红了」与「目标断言红了」—— 前提断言 `assert X, r.stderr[:250]` 的消息
#: **就是被测子进程的输出**，子进程运行期拼出期望片段即可喂饱它，而目标断言根本没
#: 执行。位置是唯一能把两者分开的面（本树实测：前提在第 12 行、目标在第 14 行）。
#:
#: ⚠️ **这张表是怎么来的，如实说**：全部 138 条由 `--probe` 跑一遍观察实际失败位置
#: 后回填 —— **判据与被测量同源**，所以它今天证不出「每条变异确实红在它声称的那条
#: 断言上」。价值在**从今往后**：门文件或生产代码一漂移、击杀落到别的语句上，就会
#: 当场报 SURVIVED；语句本身被改写则报 HARNESS-ERROR（锚失效），而不是静默记 KILLED。
#: 这一条写进了验收单「本卡未证明什么」。
#:
#: ⚠️ 与 `EXPECT_MSG` 的关系是 **AND**：两张表都填的条目要**同时**满足。
#: `EXPECT_MSG_EXEMPT` 里那 39 条消息绑不出来的，**位置照样绑得出来** —— 这正是
#: 本卡收掉 `KILLED-UNBOUND` 的路径（消息层面「门文件里没有可绑的字面片段」这个
#: 障碍，在位置层面根本不存在）。
EXPECT_LOC: dict[str, str] = {
    "M1-R1-candidate-spread": "stmt:4c1212185e58",
    "M10-R2-value-not-literal": "stmt:c8e430b5ce69",
    "M100-no-tri-instant-binding": "stmt:39865442dbff",
    "M102-receipt-attempt-type-only": "stmt:4a06447ea2ed",
    "M103-receipt-ts-no-literal-gate": "stmt:21b2c1271f1e",
    "M104-writeback-guess-by-text": "stmt:f1292729490d",
    "M11-N1-drop-out-of-order-semantic-gate": "stmt:ca81a81d7804",
    "M110-reinline-duplicate-lookup": "stmt:dde87dd27a48",
    "M111-shared-impl-not-reused": "stmt:2f4d388556cd",
    "M112-compat-empty-source-rejects": "stmt:94abf1ed0d40",
    "M113-facts-list-not-frozen": "stmt:c35112d8953f",
    "M114-f1only-drops-exam-board": "stmt:b0c9ce36d2d6",
    "M115-late-scan-presence-only": "stmt:3e5396d26747",
    "M116-receipt-no-provenance": "stmt:e30d9b3ac723",
    "M117-empty-source-skips-provenance": "stmt:9ca250d2cb86",
    "M118-empty-eid-allowed": "stmt:317e2c449747",
    "M119-crash-window-adopted-time-unproven": "stmt:145eea442feb",
    "M12-N1-drop-out-of-order-shape-gate": "stmt:35b14b243932",
    "M120-legacy-row-generic-reason": "stmt:c02294a5bd2d",
    "M121-consumer-rounds-grade": "stmt:9d5fb257e061",
    "M122-consumer-coerces-board": "stmt:ab54b8dff138",
    "M123-adopted-time-literal-compare": "stmt:d88acbf51056",
    "M124-crash-window-only-when-w-empty": "stmt:77ae00af992d",
    "M125-id-form-authorizes-bare-fallback": "stmt:572a3ee726bc",
    "M126-f1only-no-successor-discount": "stmt:18e32036cadb",
    "M127-facts-python-equality": "stmt:523fa0f8056b",
    "M128-id-form-not-at-candidate-stage": "stmt:9f9a85d5fc7b",
    "M129-missing-scored-at-warn-only": "stmt:6493eeda8b37",
    "M130-pending-adopted-time-unproven": "stmt:6db14305c84b",
    "M132-candidate-always-rounded": "stmt:365965dc1868",
    "M135-scored-at-not-in-ext-detection": "stmt:d2ef99c632e0",
    "M136-w-coverage-as-applied-proof": "stmt:7c583471ae35",
    "M137-receipt-no-applied-flag": "stmt:d9799c0407f2",
    "M138-board-string-only": "stmt:ddb1ac7b825b",
    "M139-source-lookup-both-ways": "stmt:2a658b5996f6",
    "M13b-N2-text-mode-read": "stmt:ccadd817ee44",
    "M14-N3-drop-duplicate-key-hook": "stmt:c36b63813880",
    "M140-bare-collision-no-own-judge": "stmt:a6f9e6ddb8bb",
    "M142-dup-uses-global-w": "stmt:0684e01177a1",
    "M143-missing-applied-flag-tolerated": "stmt:29b292760220",
    "M144-false-plus-w-not-contradiction": "stmt:cee527a2355b",
    "M145-recovery-does-not-promote-flag": "stmt:d991bfed7c72",
    "M146-canon-num-precision-loss": "stmt:2c929478afb9",
    "M148-unmarked-exact-single-source": "stmt:af1aac28fd2b",
    "M149-adopted-two-values": "stmt:00aa4d0e6852",
    "M150-all-ledger-ids-coerce-str": "stmt:7d86ad8ec66d",
    "M151-exam-board-bare-json-in-yaml": "stmt:02bd83e0408f",
    "M152-f1-ignores-write-order-anchor": "stmt:2fb6988c11c0",
    "M153-legacy-cursor-skips-ambiguity-proof": "stmt:bae0b20e342c",
    "M155-board-form-ignored": "stmt:198937f8b0e9",
    "M156-anchor-miss-is-hard-error": "stmt:fc5865fc8e8f",
    "M157-anchor-direction-unchecked": "stmt:e9e9942976c8",
    "M158-fsrs-applied-truthiness": "stmt:03581c229ae0",
    "M15b-N4-decode-with-replace": "stmt:839c95da5e9d",
    "M16-N5-hard-compute-attempt-across-pending": "stmt:6105a6838306",
    "M161-foreign-no-credential-promotion": "stmt:b4eeeb249561",
    "M17-N1-schema-drops-writer-side-clause": "stmt:25f0c301c8ba",
    "M18b-R7blank-judge-file-end-not-last-line": "stmt:4f4c009720a9",
    "M19-B1-drop-rating-completeness": "stmt:eb278d473046",
    "M20-B1-drop-gradenorm-completeness": "stmt:029dbd458414",
    "M21-B2-drop-attempt-sync-on-replay": "stmt:0a23ffe8bc92",
    "M23-C1-drop-event-type-gate": "stmt:8b4fc14dc10c",
    "M24-C1-drop-concept-id-gate": "stmt:8b4fc14dc10c",
    "M25-C1-drop-vault-id-gate": "stmt:8b4fc14dc10c",
    "M26-C2-drop-eid-whitespace-gate": "stmt:fbbc07945c4f",
    "M28-C4-mastery-uses-unrounded-gn": "stmt:387b0acac7b8",
    "M29-R3-drop-event-version-gate": "stmt:060ef934e40c",
    "M2b-R2-drop-utc-offset-check": "stmt:c8e430b5ce69",
    "M3-R3-attempt-uses-tip": "stmt:5f57d5a17a10",
    "M30-R3-drop-two-instant-consistency": "stmt:29076bdbfb99",
    "M31-R3-drop-attempt-required": "stmt:3a5f92ec3335",
    "M32-R3-drop-payload-object-gate": "stmt:018880e4697d",
    "M33-R3-merge-recovery-and-append": "stmt:70a1d6f0227f",
    "M34-R3-drop-routing-envelope-gate": "stmt:a97f7048ae36",
    "M35-R3-effective-at-over-strict": "stmt:d86d7cf272eb",
    "M36b-replay-drops-mastery": "stmt:d86d7cf272eb",
    "M37c-replay-includes-dup-double-eats-ema": "stmt:d044551b54ae",
    "M38b-attempt-expectation-masked-by-max": "stmt:cca8c7fef0f3",
    "M39-attempt-regex-rejects-single-quote": "stmt:2798bffda0b5",
    "M4-R4-normal-path-uses-payload-ts": "stmt:57424559200c",
    "M42-late-unmarked-row-silently-skipped": "stmt:b15598c59d0d",
    "M43-f1-evaluated-after-calibration-replay": "stmt:d86d7cf272eb",
    "M44-drop-looks-like-review-ext": "stmt:408708753b17",
    "M45-allow-dup-and-foreign-same-round": "stmt:fbde4102f5f1",
    "M46-yaml-single-quote-escape": "stmt:69c6585e235e",
    "M47-skip-validator-record-check": "stmt:4833e323c049",
    "M48-attribution-check-after-payload-skip": "stmt:f570beec970a",
    "M49-event-version-accepts-bool": "stmt:54141b83b77e",
    "M5-R5-drop-rating-consistency": "stmt:5a01df2235e9",
    "M50-non-object-line-silently-skipped": "stmt:54141b83b77e",
    "M51-line-strip-washes-nonjson-whitespace": "stmt:4833e323c049",
    "M52-calibration-strips-quiz-prefix": "stmt:66f84ab960c6",
    "M53-f1-query-strips-prefix-only": "stmt:66f84ab960c6",
    "M54-f1-uses-bare-eid": "stmt:f37fd0cfdafe",
    "M56-full-validation-after-branching": "stmt:698d987de6fb",
    "M57-validate-without-golden-manifest": "stmt:fce7260b7bf2",
    "M58-input-ts-not-literally-checked": "stmt:6be363a3f232",
    "M59-ordinal-ignores-legacy-scored-rows": "stmt:60314e1a7217",
    "M60-normal-path-stores-bare-eid": "stmt:1422b2c7228a",
    "M61-durable-eid-whitespace-not-scanned": "stmt:6cee3c61a23a",
    "M62-node-id-type-only": "stmt:b6c5326fc2b1",
    "M63-ts-match-not-fullmatch": "stmt:07cb0040ddda",
    "M64-dumps-allows-nan": "stmt:ddb8eacf26a8",
    "M65-loads-allows-nan": "stmt:4d0254dfdb35",
    "M66-legacy-same-id-rejected": "stmt:95e147e1f7fe",
    "M67-inline-calibration-not-normalized": "stmt:e8fa7624b738",
    "M68-blank-lines-tolerated": "stmt:f2650d485101",
    "M69-bom-tolerated": "stmt:f2650d485101",
    "M6b-R7-tail-ignores-lf-state": "stmt:9c28ca435681",
    "M7-R6-schema-drops-owner-clause": "stmt:067444db3590",
    "M70-ordinal-w-only-not-calibration": "stmt:1bd6f16f888f",
    "M71-ignore-provable-legacy-ordinal": "stmt:5fa1e33caf3b",
    "M73-late-scan-after-early-exit": "stmt:a5a836844898",
    "M74-candidate-copies-durable-rt": "stmt:ba1b0beed806",
    "M75-w-fallback-restored": "stmt:66f7e7eef6ad",
    "M76-self-node-id-gate-dropped": "stmt:cca6ed1276e8",
    "M77-ordinal-fixed-minus-one": "stmt:df0f8fdcce4a",
    "M78-first-write-uses-run-ts": "stmt:587ae367008e",
    "M79-missing-scored-at-falls-back": "stmt:4b52b515653f",
    "M8-6cell-cell4-allow-recovery": "stmt:4b7707fc8e3d",
    "M80-envelope-compares-adopted-rt": "stmt:0c25208a7faa",
    "M81-legacy-out-of-order-honored": "stmt:7841011453a9",
    "M82-calibration-header-no-comment": "stmt:ec8befbec429",
    "M83-whitespace-id-gate-global": "stmt:2d0cbb42e886",
    "M84-cross-node-id-collision-ignored": "stmt:1408ac1b01d8",
    "M85-no-producer-self-check": "stmt:d795daad875c",
    "M86-f1-regex-not-yaml": "stmt:fff10e01e48e",
    "M88-degraded-uses-run-ts": "stmt:174ad960ddfc",
    "M9-6cell-cell2-drop-orphan-noop": "stmt:5ad5a11505d6",
    "M91-f1-only-unconditional-noop": "stmt:1f2e99d5342c",
    "M94-routing-raw-compare": "stmt:5febef1f1d44",
    "M95-receipt-skips-abandoned": "stmt:ce507603ae0e",
    "M96-adopted-time-unbound": "stmt:bf9ba7e022de",
    "M98-no-pre-append-dry-run": "stmt:c817310a444c",
    "M99-f1only-skips-fact-check": "stmt:bc76ff9bc959",
}

#: `EXPECT_LOC` 的显式豁免表 `{tag: 理由}` —— 与 `EXPECT_MSG_EXEMPT` 同一纪律：
#: 不是「先欠着」，每条都要写清楚为什么连位置都绑不出来。已知的两种形态：
#:   ⓐ 失败落在**门文件之外**（变异让门以未捕获异常死在第三方库里）⇒ 只能绑到
#:      文件级 `file:<名>`，身份比 `stmt:` 弱，必须登记；
#:   ⓑ pytest 报的行不属于任何语句（极少见，如落在装饰器/续行上）。
#: `expect_loc` 的指纹落在**共享 helper**（不是 nodeid 指名的测试函数）里的已登记条目。
#: ⛔ 为什么必须显式登记：helper 被多道门共用时，指纹本身证不了「红在**哪道门**的调用上」
#: —— 判据仍成立（每条变异只跑自己那道门，(nodeid, loc) 组合唯一），但身份比「测试函数内
#: 的断言」弱一档。不登记的话，新增一条时没人知道它落进了 helper（独立复核 2026-09-08）。
#: 实测共 5 条：`_c1_reject_once` ← M23/M24/M25（三道 narrow 门共用）；`_parity_once` ← M49/M50。
EXPECT_LOC_HELPER: dict[str, str] = {
    "M23-C1-drop-event-type-gate": "位置落在共享 helper `_c1_reject_once` 的断言上 —— 该 helper 被 test_round11b_c1_event_type_narrow 等 3 道门共用, 指纹证不了红在哪道门的调用; (nodeid, loc) 组合在本表登记的门内仍唯一",
    "M24-C1-drop-concept-id-gate": "位置落在共享 helper `_c1_reject_once` 的断言上 —— 同上, (nodeid, loc) 在本门内唯一",
    "M25-C1-drop-vault-id-gate": "位置落在共享 helper `_c1_reject_once` 的断言上 —— 同上, (nodeid, loc) 在本门内唯一",
    "M49-event-version-accepts-bool": "位置落在共享 helper `_parity_once` 的断言上 —— 该 helper 被 2 道门共用, 指纹证不了红在哪道门的调用; (nodeid, loc) 在本门内唯一",
    "M50-non-object-line-silently-skipped": "位置落在共享 helper `_parity_once` 的断言上 —— 同上, (nodeid, loc) 在本门内唯一",
}

EXPECT_LOC_EXEMPT: dict[str, str] = {
    "M89-receipt-drops-scored-at": "ⓒ 实测位置落在门 `test_round9_structured_receipt` 的**第 1/14 条 assert**(`assert _run_writer_settled(...).returncode == 0`)——那是**构造前提**(先写进一条正常 receipt), 不是「receipt 缺字段」这条被测性质; 该断言无消息、且期望子进程**成功**, 变异一让写点失败它必然先红而目标断言从不执行 = Z2-M15 假杀同型。⛔ 绑上去会把假杀记成 KILLED, 故收回 KILLED-UNBOUND。筛出它的可复跑判据见 evidence-mutkill-r2/premise_anchor_screen.py",
    "M90-receipt-drops-attempt": "ⓒ 实测位置落在门 `test_round9_structured_receipt` 的**第 1/14 条 assert**(`assert _run_writer_settled(...).returncode == 0`)——那是**构造前提**(先写进一条正常 receipt), 不是「receipt 缺字段」这条被测性质; 该断言无消息、且期望子进程**成功**, 变异一让写点失败它必然先红而目标断言从不执行 = Z2-M15 假杀同型。⛔ 绑上去会把假杀记成 KILLED, 故收回 KILLED-UNBOUND。筛出它的可复跑判据见 evidence-mutkill-r2/premise_anchor_screen.py",
    "M97-writeback-regex-only": "ⓐ 该变异让门在**门文件之外**失败(实见 file:parser.py), 只能绑到文件级弱身份; 按 check_expect_loc_unique 的纪律必须登记而不是当成与 stmt: 同等强度",
}

#: 本卡（CARD-DEBT-mutation-kill-identity）退役的变异，逐条写「为什么」。
#: 早于本卡的退役写在各自 `MUTATIONS +=` 块的行内注释里（M154 / M159 / M160）。
RETIRED_MUTATIONS: dict[str, str] = {}


def _anchor_audit():
    """只读锚点自检：每条变异的**主锚**与**同层锚**都必须恰好命中 1 次。

    返回 `(ok, rows)`；`rows` 的每项是 `(tag, kind, hits, 文件名, gate)`，
    `kind` ∈ {"主锚", "同层锚"}。

    ⚠️ 这道自检**不是**防假绿的那一层：变异循环里本来就有 `count(old) != 1 →
    failures + 跳过`，锚漂时脚本照样 `sys.exit(1)`，不会伪装成「138/138 KILLED」。
    它加的是两件事：① 把判断提到 36 分钟的慢步骤**之前**；② 给 `--list` 一个
    不改任何文件的只读入口（g32cb / g32ccr1 早就有，g32b 一直没有 —— 于是
    Z6-C 那 4 条锚漂要等一整轮跑完才逐条冒出来）。

    ⚠️ 已知盲区（与 g32cb 同款，本卡未修）：判据是「原文本在**整个文件**里出现
    1 次」，不是「命中了那条**执行语句**」。锚落在注释里、或前导空格多一个但仍是
    子串，count 都可能仍为 1。要真堵得绑执行块内的语句身份（AST），属另立卡。
    """
    rows, ok = [], True
    cache = {}

    def _text(p):
        if p not in cache:
            cache[p] = p.read_text(encoding="utf-8")
        return cache[p]

    for _m in MUTATIONS:
        tag, path, old, gate = _m[0], _m[1], _m[2], _m[4]
        n = _text(path).count(old)
        rows.append((tag, "主锚", n, path.name, gate))
        if n != 1:
            ok = False
        for _p, _o, _n in _m[5] if len(_m) > 5 else ():
            n2 = _text(_p).count(_o)
            rows.append((tag, "同层锚", n2, _p.name, gate))
            if n2 != 1:
                ok = False
    return ok, rows


def _print_anchor_rows(rows):
    for tag, kind, n, fname, gate in rows:
        flag = "" if n == 1 else "   ⛔ 须恰好 1 次 —— 锚文本漂了，变异会静默失配"
        print(f"  [{tag}] {kind}命中 {n} 次 @ {fname} → {gate}{flag}", flush=True)


def _check_expect_msg():
    """`EXPECT_MSG` 完整性 + 唯一性自检。返回违规说明列表（空 = 通过）。"""
    gate_file = str(ROOT / "backend" / TESTF)
    items = [(m[0], gate_file, EXPECT_MSG.get(m[0])) for m in MUTATIONS]
    problems = check_expect_msg_unique(
        items,
        exempt=EXPECT_MSG_EXEMPT,
        # ⛔ 片段还必须在**生产侧命中 0 次**：门里不少断言消息的**第一行**内嵌了
        # `{r.stderr}`，那条断言一旦红，被测子进程的整份输出就进了判据面。
        # ⚠️ 不收 `backend/scripts/` 整目录 —— 本文件自己在那儿、`EXPECT_MSG` 表里
        # 逐字写着这些片段，整目录扫会把「表里写了」误报成「生产里也有」(判据自指)。
        # 被变异的 `validate_learning_events.py` / schema 按**单文件**收进来。
        prod_roots=(
            ROOT / "canvas-vault",
            ROOT / "backend" / "app",
            ROOT / "backend" / "scripts" / "validate_learning_events.py",
            SCHEMA,
        ),
    )
    stale = sorted((set(EXPECT_MSG) | set(EXPECT_MSG_EXEMPT)) - {m[0] for m in MUTATIONS})
    if stale:
        # ⛔ 反向也要看：表里留着一个已经不存在的 tag，说明这张表与变异表已经脱节，
        # 「每条都绑好了」这句话不再可信（与 g33 的 baseline_missing 同型）。
        problems.append(f"EXPECT_MSG/EXEMPT 里有已不存在的 tag: {stale}")
    return problems


def _check_expect_loc():
    """`EXPECT_LOC` 完整性 + 唯一性自检（round-19 新增）。返回违规说明列表。"""
    gate_file = str(GATE_FILE)
    problems = check_expect_loc_unique(
        [(m[0], gate_file, EXPECT_LOC.get(m[0])) for m in MUTATIONS],
        exempt=EXPECT_LOC_EXEMPT,
    )
    stale = sorted((set(EXPECT_LOC) | set(EXPECT_LOC_EXEMPT)) - {m[0] for m in MUTATIONS})
    if stale:
        problems.append(f"EXPECT_LOC/EXEMPT 里有已不存在的 tag: {stale}")
    stale_h = sorted(set(EXPECT_LOC_HELPER) - {m[0] for m in MUTATIONS})
    if stale_h:
        problems.append(f"EXPECT_LOC_HELPER 里有已不存在的 tag: {stale_h}")
    # ⛔ 指纹所在作用域必须就是 nodeid 指名的测试函数; 落在共享 helper 里的必须显式
    # 登记 EXPECT_LOC_HELPER(理由: 指纹证不了红在哪道门的调用, 身份弱一档)。
    from mutation_kill_identity import _stmts_with_scope, _fp  # 局部导入: 避免顶部再挂一层

    _scopes = {}
    for _node, _sc in _stmts_with_scope(GATE_FILE):
        _scopes.setdefault(_fp(_node, _sc), _sc)
    for _m in MUTATIONS:
        _loc = EXPECT_LOC.get(_m[0])
        if not _loc or not _loc.startswith("stmt:"):
            continue
        _sc = _scopes.get(_loc[5:])
        if _sc is None:
            continue  # 「指纹已找不到」由共用自检报, 这里不重复
        if _sc != _m[4] and _m[0] not in EXPECT_LOC_HELPER:
            problems.append(
                f"{_m[0]}: expect_loc 的指纹落在作用域 `{_sc}`（≠ 门 {_m[4]}）—— 共享 helper "
                f"身份弱一档, 须登记 EXPECT_LOC_HELPER 并写理由"
            )
    # ⛔ 收口后的不变量：既没有 `expect_msg` 又没有 `expect_loc` = `KILLED-UNBOUND`，
    # 本卡目标 0 条。留一条**必须在两张豁免表里都写了理由** —— 那是「显式登记的残留」，
    # 放行；两张表里没写全的才是「静默欠着」，当场报出来（而不是等跑完两小时在汇总里
    # 看见一个数）。
    # ⚠️ 判据这样分是有来由的：把「已登记的残留」也判成失败会让全跑在自检阶段
    # sys.exit(2)，于是「其余 137 条还好着」这个信息一起丢掉。
    silently_unbound = sorted(
        m[0]
        for m in MUTATIONS
        if EXPECT_MSG.get(m[0]) is None
        and EXPECT_LOC.get(m[0]) is None
        and not (m[0] in EXPECT_MSG_EXEMPT and m[0] in EXPECT_LOC_EXEMPT)
    )
    if silently_unbound:
        problems.append(
            "这些条目消息与位置都没绑，且没有在**两张**豁免表里都写理由"
            f"（= 静默欠着，不是显式登记的残留）: {silently_unbound}"
        )
    return problems


#: 当前**已落盘**的变异 `{路径: (原始字节, 我们写进去的字节)}`，外加当前变异 tag。
#: 信号到达时按它无条件还原 —— ⛔ 为什么不能只靠 `finally`（round-19 收紧，见
#: `RestoreGuard` 的 docstring）：旧写法把信号转成异常让 `finally` 跑，可信号若正好落在
#: **还原循环内部**，异常从 finally 里逃出去 ⇒ 剩下的文件还留着变异体（负控
#: `negctl_signal.py` 实测：5 个目标里 3 个没还原）。
#:
#: ⛔⛔ 为什么要记「写进去的字节」而不只是原文（round-19 的**回归修复**，独立复核抓到）：
#: 第一版把「第三方改动存证」留在 `finally` 里的 `_restore_one()`，而信号路径上
#: `RestoreGuard` **先**还原了文件 —— 等 `finally` 跑到时读到的 `now` 已经是原文，
#: 与「我们写进去的变异体」必然不等 ⇒ 那道判据在信号路径上**恒真**。两个后果都很坏：
#:   ① 没有第三方改动时，每次 Ctrl-C 都为每个目标文件打一条「被第三方改动」并写一份
#:      **其实是脚本自己快照**的 `.bak`（本卡自己的 probe 存档里已复现两次：
#:      `probe-g32b-20260908T080307.txt:36` 与 `…081108.txt:63`，两份新 `.bak` 里
#:      `grep -c` 变异标记 = 0，而 09-04 那批真·跨车道污染的 `.bak` 计数 = 2）；
#:   ② **有**第三方改动 T 时，guard 先用原文覆盖了 T ⇒ T 既没被存证也没被保留，
#:      而打印文案还宣称「其内容已存证…请人工核对是否需要合并回去」—— 恰好是这段
#:      注释本来要防的那件事，且属「声明比证据宽」。
#: 修法：把比对**前移进第一个碰文件的人**（`_restore_active`），两条路径共用同一份
#: 「读时快照 vs 现盘内容」比对；还原后清表，于是 `finally` 再调一次是干净的 no-op。
_ACTIVE_SNAPSHOT: dict[pathlib.Path, tuple[bytes, bytes]] = {}
_ACTIVE_TAG = [""]


def _arm_mutation(tag, edits):
    """把变异写盘并登记快照。`edits` = `{path: (原始字节, 变异后字节)}`。

    ⛔ 顺序不能反：先登记再落盘。信号可能落在两次 `write_bytes` 之间，那时 `finally`
    还没进，只有 `_ACTIVE_SNAPSHOT` 能告诉 handler 该还原哪些文件。
    """
    _ACTIVE_TAG[0] = tag
    _ACTIVE_SNAPSHOT.update(edits)
    for _p, (_orig, _new) in edits.items():
        _p.write_bytes(_new)


def _restore_active():
    """把登记过的文件逐字节写回，并在写回**之前**做第三方改动存证。幂等。

    并发编辑防护: 还原写的是**读时快照**, 若变异窗口内有人改了这个文件, 无条件写回
    会**静默丢掉他的改动**, 而「还原后字节相同」自检比的是自己的快照, 恒相同、看不见
    这件事。窗口最长 900s × 多条变异, 不是理论风险。
    ⚠️ 并行下这道自检**是自证** —— 2026-09-02 三个变异进程交错跑, 每条各自都显示
    「还原成功」, 却在生产文件里留下了别人的变异体。外部锚点 (grep 标记 + 与已知良好
    sha 比对) 才是证据。见 MEMORY: reference_mutation_script_module_level_side_effects。

    ⚠️ **幂等的含义要写清**: 表被清空后再调一次是 no-op —— 它**不会**再打一条
    「被第三方改动」。这正是上面 ①② 两个后果的封堵点: 信号路径先跑到这里、做完比对
    与还原、清表; `finally` 里那一次于是什么也不做, 不再伪造告警、也不再覆盖任何东西。
    """
    for _p, (_orig, _written) in list(_ACTIVE_SNAPSHOT.items()):
        now = _p.read_bytes()
        if now == _orig:
            # 两种窗口都长这样: ①登记了快照但变异体**还没写**(_arm_mutation 的写盘循环
            # 被信号打断, 该文件仍是原文); ②已经被还原过(guard 先跑、finally 再跑)。
            # 两种都不是第三方改动 —— 不跳过的话 ① 会被误报成「被第三方改动」并存证
            # 一份**其实是原文**的伪 .bak(独立复核 2026-09-08 LOW; 与 N3 那个 HIGH 同族)。
            continue
        if now != _written:
            # ⛔ 首版这里 sys.exit(3) 且**不还原** —— 那是致命的方向错误: 变异体会被
            # 留在生产文件里。实测代价: 一次触发后 `if False:` 那个变异体在 SKILL.md
            # 里活了整整一轮, 差点被 commit。正确顺序是「先把第三方内容存证, 再无条件
            # 还原」—— 变异体绝不能留, 而第三方改动也不能无声蒸发。
            stash = pathlib.Path(f"/private/tmp/g32b-mutation-thirdparty-{_ACTIVE_TAG[0]}-{_p.name}.bak")
            stash.write_bytes(now)
            # ⛔ 日志**不得挡住还原**（round-2 HIGH）：顺序是 存证 → print → 写回原文，
            # print 一抛异常，当前文件与后续文件都还原不了；`RestoreGuard._safe_log`
            # 包不到这个回调（它在 g32b 里）。诊断失败绝不能升级成数据完整性事故。
            try:
                print(
                    f"[{_ACTIVE_TAG[0]}] ⚠️ 变异窗口内 {_p.name} 被第三方改动 — 其内容已存证到 {stash}; "
                    f"仍按快照还原(变异体不得留在生产文件里), 请人工核对是否需要合并回去",
                    flush=True,
                )
            except BaseException:  # noqa: BLE001  日志失败不改变控制流
                pass
        _p.write_bytes(_orig)  # 逐字节还原 (无条件 = EXIT trap 等价)
    _ACTIVE_SNAPSHOT.clear()


#: ⛔ 四个信号（含 SIGQUIT —— 收口前 g32b/g32cb/g32ccr1 三套都漏了它，而它的默认
#: 处置同样不做栈展开）+ 还原期不可打断。SIGKILL 挡不住，如实声明：被 `-9` 打断时
#: 靠下一次启动的 `_self_heal_leftovers()` 与跑前跑后全文件 sha 对账兜底。
_GUARD = RestoreGuard(_restore_active)


def _syntax_errors(texts):
    """变异后的文本是否仍是合法 Python。返回问题描述（空 = 没问题）。

    `.py` 直接 parse；SKILL.md 取其中的 PYEOF 块（写点本体就在里面）。
    Markdown 规格文件不含可执行代码，跳过。
    """
    _bad = [f"{_p.name}: {_err}" for _p, _t in texts.items() if (_err := syntax_check(_p, _t))]
    return "; ".join(_bad)


def main():
    _argv = sys.argv[1:]
    if "--list" in _argv:
        # 只读入口：不施加任何变异、不写盘。
        _ok, _rows = _anchor_audit()
        print("═══ 变异清单与锚点自检（只读）═══")
        _print_anchor_rows(_rows)
        _bad_anchor = [r for r in _rows if r[2] != 1]
        print(f"\n  共 {len(MUTATIONS)} 条变异 / {len(_rows)} 个锚点；异常锚点 {len(_bad_anchor)} 个")
        # ⛔ Codex round-1 MEDIUM-7 整改：原先退出码**只看锚点**——门消息漂了、
        # EXPECT_MSG 自检已经打印出错，`--list` 却照样返回 0。退出码必须同时取决于
        # 两项自检，否则「只读自检通过」这句话是假的。
        _bad_msg = _check_expect_msg()
        for _p in _bad_msg:
            print(f"  ⛔ EXPECT_MSG 自检: {_p}")
        # ⛔ round-19：位置判据同样要进只读入口的退出码 —— 否则「`--list` 通过」
        # 只覆盖了两维里的一维，说得比证据宽。
        _bad_loc = _check_expect_loc()
        for _p in _bad_loc:
            print(f"  ⛔ EXPECT_LOC 自检: {_p}")
        print(
            f"  绑定覆盖：EXPECT_MSG {len(EXPECT_MSG)} 条 / EXPECT_LOC {len(EXPECT_LOC)} 条 "
            f"/ 消息豁免 {len(EXPECT_MSG_EXEMPT)} / 位置豁免 {len(EXPECT_LOC_EXEMPT)} "
            f"（共 {len(MUTATIONS)} 条变异）"
        )
        return 0 if (_ok and not _bad_msg and not _bad_loc) else 4

    _probe = "--probe" in _argv
    # `--only <前缀>[,<前缀>…]`：按 tag 前缀挑变异。⛔ 判据落在**实际用来选择的那个键**
    # 上（round-11b 的编号碰撞教训）；选空了要报失败，不能空跑当成通过。
    # ⛔ Codex round-1 LOW-8 整改：裸 `--only`（缺值）原先被**静默忽略**、退化成全量跑
    # ——「我只想定点复核 4 条」变成「跑了 45 分钟全量并落进 PASS 判定」。缺值 / 空前缀
    # 一律当场报错退出，不猜用户意图。
    _only = None
    for _i, _a in enumerate(_argv):
        if _a == "--only":
            if _i + 1 >= len(_argv) or _argv[_i + 1].startswith("--"):
                print("✗✗ `--only` 缺少取值（用法：`--only M142,M143` 或 `--only=M142`）")
                return 4
            _only = set(_argv[_i + 1].split(","))
        elif _a.startswith("--only="):
            _only = set(_a.split("=", 1)[1].split(","))
    if _only is not None and not all(p.strip() for p in _only):
        print(f"✗✗ `--only` 含空前缀 {sorted(_only)} —— 空前缀会命中全部 tag, 拒绝执行")
        return 4
    failures = []
    kill_fail = {}
    _syntax_invalid = []
    _observed = {}
    _verdicts = {}
    _GUARD.install()
    # ⛔ 自愈也在写盘，而且发生在 `install()` **之后** —— 它是唯一「已落盘但快照未登记」
    # 的窗口（独立复核 2026-09-08）。放进 `critical()`：这段期间收到的信号只记待办、
    # 不打断，免得自愈自己被截断成「还原了一半」。
    with _GUARD.critical():
        _healed = _self_heal_leftovers()
    if _healed:
        print(f"⚠️ 自愈：还原了上一次残留的变异体 {_healed}", flush=True)
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
    # ⚠️ 不写 `re.match(...).group(1)`：tag 若不以 `M<数字>` 开头，`match` 是 None，
    # 那里会抛 AttributeError —— 编号唯一性这道门自己先崩，比它要防的问题更难查。
    _unnamed = [m[0] for m in MUTATIONS if not re.match(r"M(\d+[a-z]?)", m[0])]
    if _unnamed:
        print(f"✗✗ 变异 tag 不符合 `M<编号>` 命名: {_unnamed} — 前缀选择/碰撞检查都会失灵, 立即停")
        sys.exit(2)
    _nums = collections.Counter(re.findall(r"^M(\d+[a-z]?)", m[0])[0] for m in MUTATIONS)
    _dup_nums = {k: v for k, v in _nums.items() if v > 1}
    if _dup_nums:
        print(f"✗✗ 变异编号碰撞 {_dup_nums} — 前缀选择会选错, 立即停")
        sys.exit(2)
    _testf_src = (ROOT / "backend" / TESTF).read_text(encoding="utf-8")
    _gates_missing = [m[0] for m in MUTATIONS if f"def {m[4]}(" not in _testf_src]
    if _gates_missing:
        print(f"✗✗ 绑定的门不存在: {_gates_missing} — rc=4 会被粗判据当成 KILLED, 立即停")
        sys.exit(2)
    # ⛔ EXPECT_MSG 自检先于慢步骤：绑不唯一 ⇒ 「红在哪一条断言上」不再可证。
    # `--probe` 是**发现**步骤（首次绑定 EXPECT_MSG 时用），它不做击杀判定，
    # 所以跳过这道自检；作为交换，它的裁决一律记 OBSERVED、rc 恒 4，
    # 任何人都不可能把 probe 的输出当成「通过」。
    if not _probe:
        if _bad := _check_expect_msg():
            for _b in _bad:
                print(f"✗✗ EXPECT_MSG 自检失败 — {_b}")
            sys.exit(2)
        if _bad := _check_expect_loc():
            for _b in _bad:
                print(f"✗✗ EXPECT_LOC 自检失败 — {_b}")
            sys.exit(2)
    # ⛔ 锚点自检提到慢步骤之前（本卡新增；原先要等 36 分钟逐条冒出来）。
    # 这里**不中止**：锚漂的条目在下面的循环里照样记 failures 并跳过，
    # 中止会让「其余 134 条还好着」这个信息也丢掉。
    _ok_anchor, _rows_anchor = _anchor_audit()
    if not _ok_anchor:
        print("── 锚点自检（跑前）：有异常 ──")
        _print_anchor_rows([r for r in _rows_anchor if r[2] != 1])
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
        if _only is not None and not any(tag.startswith(p) for p in _only):
            continue
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
                print(f"[{tag}] ✗ ANCHOR-ERROR {which}锚点在 {_p.name} 命中 {c} 次, 跳过")
                _anchor_bad = True
                break
            texts[_p] = texts[_p].replace(_o, _n, 1)
        if _anchor_bad:
            # ⛔ round-19：进 `_verdicts` 参与六档计数。原先它只进 failures、
            # 汇总里由 `_rows_anchor` 另算一个旁路数 ⇒ 六档之和对不上
            # `len(MUTATIONS)`，「哪一条去哪儿了」不可核。
            _verdicts[tag] = "ANCHOR-ERROR"
            continue
        mutated = {p: t.encode("utf-8") for p, t in texts.items()}
        # ⛔ round-17 MEDIUM: 变异体必须先**语法有效**。实测 138 条里有 2 条是
        # 语法错误假杀（M64 的 `# MUTANT` 注释吞掉了闭合括号、M87 吞掉了逗号）——
        # 程序根本跑不起来, 门当然红, 而那红色**与被测性质无关**。
        # 语法坏掉 ⇒ 判 harness failure, 不计 KILLED。
        _syn = _syntax_errors(texts)
        if _syn:
            failures.append(f"{tag}: SYNTAX-INVALID 变异体编译不过（假杀面）—— {_syn}")
            print(f"[{tag}] ⛔ SYNTAX-INVALID 变异体编译不过, 不计 KILLED: {_syn}")
            _syntax_invalid.append(tag)
            _verdicts[tag] = "SYNTAX-INVALID"  # round-19: 进六档计数, 不走旁路
            continue
        try:
            _arm_mutation(tag, {_p: (originals[_p], _b) for _p, _b in mutated.items()})
            r = run_gate(gate)
            if _probe:
                _out = r.stdout + r.stderr
                verdict, why = "OBSERVED", (f"reason={observed_reason(_out, gate)!r} loc={observed_loc(_out)!r}")
            else:
                # ⛔ `require_gate_file` 对**位置豁免**条目关掉：它们登记的理由之一
                # (ⓐ) 就是「失败落在门文件之外」。不关的话那条弱位置判据会把一条已
                # 登记的合法条目永远判成 SURVIVED —— 收紧收掉一整个轴的形态。
                verdict, why = is_killed(
                    r,
                    gate,
                    EXPECT_MSG.get(tag),
                    EXPECT_LOC.get(tag),
                    require_gate_file=tag not in EXPECT_LOC_EXEMPT,
                )
            killed = verdict.startswith("KILLED")
        finally:
            # 并发编辑防护: 还原写的是**读时快照**, 若变异窗口内有人改了这个文件,
            # 无条件写回会**静默丢掉他的改动**, 而「还原后字节相同」自检比的是自己
            # 的快照, 恒相同、看不见这件事。窗口最长 900s × 多条变异, 不是理论风险。
            # ⚠️ 并行下这道自检**是自证** —— 2026-09-02 三个变异进程交错跑, 每条各自
            # 都显示「还原成功」, 却在生产文件里留下了别人的变异体。外部锚点
            # (grep MUTANT + 与已知良好 sha 比对) 才是证据。见 MEMORY:
            # reference_mutation_script_module_level_side_effects。
            # ⛔ round-19: 整个还原循环放进 `critical()` —— 循环中途收到信号时只记
            # 待办、不打断, 跑完再兑现。旧写法(信号转异常)会让异常从这个 finally
            # 里逃出去, 剩下的文件留着变异体(负控实测 5 个目标里 3 个没还原)。
            # ⚠️ 与信号路径**同一个函数**: 信号先跑过它的话这里就是 no-op(表已清空),
            # 不会再伪造一条「被第三方改动」告警(见 `_ACTIVE_SNAPSHOT` 的注释 ①②)。
            with _GUARD.critical():
                _restore_active()
        _drift = [
            _p.name
            for _p in originals
            if hashlib.sha256(_p.read_bytes()).hexdigest() != hashlib.sha256(originals[_p]).hexdigest()
        ]
        if _drift:
            print(f"[{tag}] ✗✗ 还原后字节不同: {', '.join(_drift)} — 立即停 (rc=3 数据完整性)")
            sys.exit(3)
        sha_after = sha(path)
        if killed:
            # ⛔ round-19: 记**位置身份**而不是 `first_fail` 的文本。空变异对照要回答的是
            # 「只加层与层+变异体是不是败在**同一条断言**上」——`first_fail` 取的是
            # `<file>:<line>: <Exc>: <msg>` 截断到 220 字符的**文本**，其中 `<msg>` 可能
            # 内嵌被测子进程的输出（正是 Y1-B HIGH-1 的喂饱面）。两次跑只要子进程输出
            # 有一点不同，同一条断言也会被判成「不同失败点」⇒ 层贡献的假杀被放行
            # （独立复核 2026-09-08 实测已放行两条）。位置 token 不含任何子进程可控字节。
            # ⛔ 记**全部**位置 token 而不是 locs[0]（Codex round-1 HIGH）：判据侧
            # 用「任一命中」，对照侧却固定取第一条 ⇒ 「别的位置, 目标位置」这种序列
            # 会让两边比的不是同一次失败，假杀被放行。
            kill_fail[tag] = (
                [t for t in matched_loc_tokens(r.stdout + r.stderr, GATE_FILE) if t],
                first_fail(r.stdout),
            )
        if _probe:
            _out = r.stdout + r.stderr
            # ⛔ round-19: 位置**也要**记下来 —— `EXPECT_LOC` 就是从这里回填的。
            # 首版只记了 reason, 于是跑完 36 分钟拿不到位置, 整趟白跑（实测踩过）。
            _tok, _raw = observed_loc(_out)
            _observed[tag] = (observed_reason(_out, gate), _tok, r.returncode, _raw)
            print(
                f"[{tag}] {gate} → OBSERVED rc={r.returncode} loc={_tok!r} at={_raw!r} reason={_observed[tag][0]!r}",
                flush=True,
            )
            continue
        _verdicts[tag] = verdict
        # ⛔ 三种非 KILLED 各说各的话（Codex round-1 MEDIUM-4）：
        # `HARNESS-ERROR` 是**负控自己坏了**，把它印成「SURVIVED ⇒ 假门」等于把
        # 「pytest 没跑成」说成「门不承重」——诊断指错方向，是本族反复栽的坑。
        _label = {
            "KILLED": f"KILLED ({why})",
            "KILLED-UNBOUND": f"KILLED-UNBOUND 未绑断言身份, 判据退化成旧口径 ({why})",
            "SURVIVED": f"SURVIVED ⇒ 假门 ({why})",
            "HARNESS-ERROR": f"HARNESS-ERROR 负控自己坏了, 不是关于被测物的结论 ({why})",
        }[verdict]
        print(f"[{tag}] {gate} → {_label}  [还原字节相同 {sha_after[:12]}]")
        if verdict == "SURVIVED":
            failures.append(f"{tag}: 门 {gate} 未抓住变异 (SURVIVED — {why})")
            print("    ---- 门输出尾部 ----")
            print("    " + "\n    ".join(r.stdout.strip().split("\n")[-6:]))
        elif verdict == "HARNESS-ERROR":
            failures.append(f"{tag}: HARNESS-ERROR — {why}")
            print("    ---- 门输出尾部 ----")
            print("    " + "\n    ".join(r.stdout.strip().split("\n")[-6:]))

    # ⛔ `--only` 的提示放在 probe 之前打印, 但**不在这里返回** —— 否则
    # `--probe --only X` 会走进这一支、把 OBSERVED 表吞掉。两条支路的 rc 都是 4。
    if _only is not None:
        # ⛔ 部分跑一律 rc=4，绝不落到「PASS」那条路上：`--only` 是诊断辅助
        # （给刚更锚的条目做定点复核），不是全量结论。选空了同样是失败 ——
        # 空跑被当成通过是本仓踩过的形态。
        _sel = [m[0] for m in MUTATIONS if any(m[0].startswith(p) for p in _only)]
        print(f"\n⚠️ --only {sorted(_only)} 选中 {len(_sel)} 条: {_sel}")
        if not _sel:
            print("⛔ --only 没选中任何变异 — 判失败，免得空跑被当成通过")
        print("⚠️ 部分跑不构成全量结论，rc 恒为 4。")
        if failures:
            for _f in failures:
                print("  -", _f)
        if not _probe:
            # ⛔ 部分跑的 rc=4 **让位**于更硬的结论(独立复核: 四套原先在「部分跑 +
            # HARNESS-ERROR」上各给各的码)。优先级与全量一致: 还原(3) > 负控坏(2) > 部分跑(4)。
            if any(v == "HARNESS-ERROR" for v in _verdicts.values()):
                print("⛔ 其中有 HARNESS-ERROR —— 负控自己坏了, rc=2 盖过「部分跑 rc=4」")
                return 2
            return 4

    if _probe:
        # ⛔ probe 只**观察**，从不判定。裁决一律 OBSERVED、rc 恒 4 —— 它的输出
        # 不可能被误读成「通过」。作用: 首次为 EXPECT_MSG 找候选串时，知道每条
        # 实际红在哪条断言上；候选是否**就是这条变异声称的那条**，要人去对
        # 变异意图与门源码，不是拿这份输出直接回填(那就成了「期望值与被测量同源」)。
        print("\n── PROBE 观察表（不是裁决）──")
        for _t, (_reason, _loc, _rc, _raw) in _observed.items():
            print(f"  {_t}\trc={_rc}\tloc={_loc!r}\tat={_raw!r}\treason={_reason!r}")
        # ⛔ 可直接回填 `EXPECT_LOC` 的形态：单独打一段, 免得人从上面那张混排表里手抄。
        # ⚠️ 它是**观察结果**, 不是「已验证的期望值」—— 判据与被测量同源, 见
        # `EXPECT_LOC` 的表头注释与验收单「本卡未证明什么」。
        print("\n── 可回填的 EXPECT_LOC（观察值, 不是已验证的期望值）──")
        for _t, (_reason, _loc, _rc, _raw) in sorted(_observed.items()):
            print(f"EXPECT_LOC_CANDIDATE\t{_t}\t{_loc or ''}\t{_rc}\t{_raw or ''}")
        _no_loc = sorted(t for t, (_, l, _rc, _raw) in _observed.items() if not l)
        print(f"\n⚠️ 观察不到位置的条目 {len(_no_loc)} 条: {_no_loc}")
        print(f"⚠️ --probe 不做击杀判定，rc 恒为 4。观察 {len(_observed)} 条。")
        return 4

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
            _arm_mutation(f"{tag}-layeronly", {_p: (originals[_p], _t.encode("utf-8")) for _p, _t in texts.items()})
            r0 = run_gate(gate)
            # ⛔ 「对照绿」只认 rc=0（Codex round-1 HIGH）：旧写法 `rc==1 and "1 failed"`
            # 把 rc=4/5（用法错、零收集）与 rc=1 但「2 failed」全都落进 else 的
            # 「✓ 对照绿 ⇒ 击杀干净归因于变异体」—— 负控没跑成被读成结论。
            _r0_green = r0.returncode == 0
            # ⛔ 「恰一条失败」不能用全文子串（round-2 MEDIUM）：`11 failed`、
            # `1 failed, 1 error` 都含 "1 failed"。改结构化：摘要区里目标门恰 1 条
            # FAILED 且无 ERROR，且没有解析不掉的失败行。
            _r0_out = r0.stdout + r0.stderr
            _r0_fails = parse_failed_nodeids(_r0_out)
            _r0_single_red = (
                r0.returncode == 1
                and len(_r0_fails) == 1
                and gate_hit(nodeid_of(gate), _r0_fails)
                and not unparsed_failure_lines(_r0_out)
            )
            red0 = _r0_single_red
        finally:
            with _GUARD.critical():  # round-19: 还原期不可被第二个信号打断
                _restore_active()
        drift = [
            p.name
            for p in originals
            if hashlib.sha256(p.read_bytes()).hexdigest() != hashlib.sha256(originals[p]).hexdigest()
        ]
        if drift:
            print(f"[{tag}] ✗✗ 对照还原后字节不同: {drift} — 立即停 (rc=3 数据完整性)")
            sys.exit(3)
        # ⛔ 判据不是「对照红就算假杀」—— 那条判据**太粗**, 而且是我 2026-09-02 在
        # 这道对照里亲手犯的同一个错(与 `rc != 0` 混进续跑信号同型)。粗门(如
        # test_internal_audit_findings)捆了多个子场景, 层可能弄红**另一个**子场景。
        # 实测 M23: 只加层败在「不得被当成一次复习重放」, 层+变异体败在「零写」——
        # **不同断言** ⇒ 变异体确实改变了行为, 不是假杀。
        # 正确判据: 只有两次败在**同一条**断言上, 才说明变异体毫无贡献。
        # `(位置 token, 文本)` 两元组：位置是承重判据，文本只用于打印诊断。
        fa = (
            ([t for t in matched_loc_tokens(r0.stdout + r0.stderr, GATE_FILE) if t], first_fail(r0.stdout))
            if red0
            else None
        )
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
                _arm_mutation(f"{tag}-bodyonly", {_bp: (_bsnap, _btxt.replace(_bo, _bn, 1).encode("utf-8"))})
                rb = run_gate(gate)
                # 同上：complete 对照的「变异体单独不够」只认 rc=0 为绿。
                _rb_green = rb.returncode == 0
                _rb_out = rb.stdout + rb.stderr
                _rb_fails = parse_failed_nodeids(_rb_out)
                b_only = (
                    rb.returncode == 1
                    and len(_rb_fails) == 1
                    and gate_hit(nodeid_of(gate), _rb_fails)
                    and not unparsed_failure_lines(_rb_out)
                )
            finally:
                with _GUARD.critical():  # round-19: 还原期不可被第二个信号打断
                    _restore_active()
            if hashlib.sha256(_bp.read_bytes()).hexdigest() != hashlib.sha256(_bsnap).hexdigest():
                print(f"[{tag}] ✗✗ complete 对照还原后字节不同 — 立即停 (rc=3 数据完整性)")
                sys.exit(3)
            if b_only:
                failures.append(f"{tag}: 声明为 complete 但变异体单独即可杀 ⇒ 层是多余的")
                print(f"[{tag}] ✗ complete 但变异体单独即可杀 ⇒ 撤层")
            elif _rb_green:
                print(f"[{tag}] ✓ complete: 变异体单独不够(门绿 rc=0), 补齐站点后才红 ⇒ 层必要")
            else:
                failures.append(f"{tag}: complete 对照 rc={rb.returncode} 既非绿也非单条红 — 判据面不成立")
                print(f"[{tag}] ⛔ complete 对照 rc={rb.returncode}（非 0/1 或多例失败）—— 不构成结论")
                if _verdicts.get(tag) == "KILLED":
                    _verdicts[tag] = "HARNESS-ERROR"
        elif _r0_green:
            print(f"[{tag}] ✓ 对照绿 (rc=0) ⇒ 击杀干净归因于变异体")
        elif not red0:
            # rc 既不是 0 也不是「恰一条红」⇒ 对照本身没跑成，不能当成「绿」。
            failures.append(f"{tag}: 空变异对照 rc={r0.returncode} 既非绿也非单条红 — 判据面不成立")
            print(f"[{tag}] ⛔ 空变异对照 rc={r0.returncode}（非 0/1 或多例失败）—— 不构成结论")
            if _verdicts.get(tag) == "KILLED":
                _verdicts[tag] = "HARNESS-ERROR"
        elif (
            fb is not None
            and fa is not None
            and fa[0]
            and fb[0]
            and (
                # ⛔ 有目标位置绑定时，只有**目标位置**同时出现在两趟里才算假杀
                # （round-2 MEDIUM）：泛交集会因「别的失败位置恰好重合」把有效击杀
                # 误降档 —— 主变异 {目标 T, 其它 U}、空对照 {U} 时 T 只在变异后才红。
                EXPECT_LOC.get(tag) in set(fa[0]) & set(fb[0]) if EXPECT_LOC.get(tag) else set(fa[0]) & set(fb[0])
            )
        ):
            _tgt = EXPECT_LOC.get(tag)
            _same = [_tgt] if _tgt else sorted(set(fa[0]) & set(fb[0]))
            failures.append(f"{tag}: 只加层与层+变异体败在同一条断言 ⇒ 击杀由层贡献 (假杀): {_same} {fa[1][:70]}")
            print(f"[{tag}] ✗ 假杀 — 两次同一失败点 {_same}: {fa[1][:80]}")
            # ⛔ 还要**降档**：独立复核指出, 首版只 append failures 不回写 _verdicts,
            # 于是主循环记下的 KILLED 原样进汇总 —— 「137/138 KILLED」里混着已判假杀
            # 的条目, 出口文案说得比证据宽。假杀 = 负控自己的变异没有鉴别力 ⇒ HARNESS-ERROR。
            if _verdicts.get(tag) == "KILLED":
                _verdicts[tag] = "HARNESS-ERROR"
        elif fb is not None and fa is not None and (not fa[0] or not fb[0]):
            # 位置取不到就**不敢下结论**：报 harness 面的问题，而不是替它猜一个。
            failures.append(f"{tag}: 空变异对照拿不到位置 token (只加层={fa[0]} 层+变异体={fb[0]}) — 判据面不成立")
            print(f"[{tag}] ⛔ 空变异对照的位置判据面不成立: 只加层={fa[0]!r} 层+变异体={fb[0]!r}")
            if _verdicts.get(tag) == "KILLED":
                _verdicts[tag] = "HARNESS-ERROR"
        else:
            print(f"[{tag}] ✓ 对照红但失败**位置**不同 ⇒ 变异体有可观测效果 (门较粗, 隔离不干净)")
            print(f"       只加层  : {fa[0] if fa else None} {(fa[1] if fa else '')[:70]}")
            print(f"       +变异体: {fb[0] if fb else None} {(fb[1] if fb else '')[:70]}")

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
        # ⛔ 还原失败是**数据完整性**问题，优先级高于一切结论（Codex round-1 MEDIUM：
        # 验收单声明了 rc=3 契约而代码没实现）。这里直接 rc=3 退出，不与 SURVIVED/
        # HARNESS-ERROR 混在同一个码上。
        print("   ⛔ 基线漂移 —— 生产文件里可能残留变异体, 立即人工核对 (rc=3)")
        for _d in _drifted:
            print("   -", _d)
        return 3

    # ── 汇总: 六档计数（四套统一口径, 见 mutation_kill_identity.VERDICTS）
    # ⛔ ANCHOR-ERROR 与 SYNTAX-INVALID 都**不是**关于被测物的结论 —— 前者是变异
    # 没打进去, 后者是负控自己坏了。单列出来, 不许并进 KILLED / SURVIVED 任何一边。
    # ⛔ round-19: 这两档改为一并进 `_verdicts`, 于是「六档之和 = len(MUTATIONS)」
    # 成为可核的不变量（原先它们走旁路计数, 加起来对不上, 「哪一条去哪儿了」无从查）。
    _n = {v: sum(1 for x in _verdicts.values() if x == v) for v in VERDICTS}
    _n_anchor_pre = len({r[0] for r in _rows_anchor if r[2] != 1})
    print()
    print("── 汇总 ──")
    # ⛔ Codex round-1 HIGH-3 整改: 「绑了断言身份的击杀」与「只证明了指定门红了」
    # **分开报**。合起来说成「N 条全部被指定断言杀死」是把结论说得比证据宽 ——
    # 豁免条目的判据仍是旧口径, 它们不在「红在声称的那条断言上」这个结论里。
    print(f"KILLED (绑定断言身份: 位置 [+ 消息]): {_n['KILLED']}/{len(MUTATIONS)}")
    print(f"KILLED-UNBOUND (仅证明指定门红了, 位置与消息都没绑): {_n['KILLED-UNBOUND']}")
    print(
        f"KILLED 合计 (两者之和, **不等于**「全部被指定断言杀死」): "
        f"{_n['KILLED'] + _n['KILLED-UNBOUND']}/{len(MUTATIONS)}"
    )
    print(f"SURVIVED: {_n['SURVIVED']}")
    print(f"HARNESS-ERROR: {_n['HARNESS-ERROR']} (负控自己坏了, 不是关于被测物的结论)")
    print(f"ANCHOR-ERROR: {_n['ANCHOR-ERROR']} (变异未施加, 不是结论)")
    print(f"SYNTAX-INVALID: {_n['SYNTAX-INVALID']} (>0 说明负控自己坏了) {_syntax_invalid or ''}")
    _total = sum(_n.values())
    # ⛔ 这里**一定**是全量：`--only` 与 `--probe` 都在到达汇总段之前 `return 4`
    # （两个出口分别在「部分跑提示」与「PROBE 观察表」两段里, 具体行不写死 —— 行号
    # 必须实测不能推算, 上一版把行号写进注释, 后续编辑一漂移就指错地方）。
    # 首版写成 `len(MUTATIONS) if _only is None else …`, 那个 else 分支**永不求值** ——
    # 死分支会让下一个人以为 `--only` 走过汇总, 从而按错误前提改出口逻辑（独立复核指出）。
    # ⚠️ **不**把汇总段前移来「让它活起来」: 阶段 2 的 `layered` 不受 `_only` 过滤,
    # 前移会让定点复核把全部带层变异写进生产文件; 且汇总段末尾的 `return 1` 会打破
    # 「部分跑 rc 恒为 4、绝不落到 PASS 那条路」这条纪律。⇒ 如实声明:
    # **`--only` 不产出六档聚合表**（逐条标签仍打, 缺的是计数与「六档之和」不变量）。
    _expect_total = len(MUTATIONS)
    _sum_ok = _total == _expect_total
    print(f"六档之和: {_total} (应 = {_expect_total}) {'✓' if _sum_ok else '⛔ 对不上, 有条目没落进任何一档'}")
    # ⛔ 「应一致」这句原先从没被比较过 —— 声明比证据宽。做成真判据：跑前的只读锚点
    # 自检与主循环里实际记下的 ANCHOR-ERROR 条数必须相等；不等说明两者看到的树不同
    # （例如变异窗口内锚文本被改了），那本身就是要报出来的事。
    _anchor_agree = _n_anchor_pre == _n["ANCHOR-ERROR"]
    print(
        f"（跑前只读锚点自检: 异常锚点 {_n_anchor_pre} 条; 主循环记下 ANCHOR-ERROR "
        f"{_n['ANCHOR-ERROR']} 条 ⇒ {'一致 ✓' if _anchor_agree else '⛔ 不一致'}）"
    )
    if not _anchor_agree:
        failures.append(
            f"跑前锚点自检 {_n_anchor_pre} 条 != 主循环 ANCHOR-ERROR {_n['ANCHOR-ERROR']} 条"
            " —— 两者看到的树不同（变异窗口内锚文本被改？）"
        )
    if not _sum_ok:
        # ⛔ 计数口径坏了 = 负控自己坏了 ⇒ rc=2（与另三套同契约）。
        print(f"⛔ 六档之和 {_total} != {_expect_total} —— 有条目没落进任何一档, 计数口径坏了 (rc=2)")
        return 2
    print()
    # ⛔ 退出码语义四套统一（独立复核 2026-09-08：原先 HARNESS-ERROR 与 SURVIVED 压成
    # 同一个 rc=1 —— 「pytest 没跑成」与「门不承重」两个方向完全相反的结论共用一个码）：
    #   rc=2  有 HARNESS-ERROR（负控自己坏了，先去修 harness，别去改门）
    #   rc=1  有 SURVIVED 或别的 failures（关于被测物的结论）
    #   rc=4  部分跑（--only / --probe / --list 自检不过）—— 不构成全量结论
    #   rc=0  全部 KILLED；⚠️ **已登记**的 KILLED-UNBOUND 残留只报不判失败 ——
    #         未登记的那种在跑之前就被 `_check_expect_loc()` / `_check_expect_msg()`
    #         挡在 rc=2 上了，走不到这里。
    if _n["HARNESS-ERROR"]:
        print(f"⛔ HARNESS-ERROR {_n['HARNESS-ERROR']} 条 —— 负控自己坏了, 不是关于被测物的结论 (rc=2)")
        for f in failures:
            print("  -", f)
        return 2
    if failures:
        print("变异验证 FAIL:")
        for f in failures:
            print("  -", f)
        return 1
    # ⛔ 收尾文案必须与**新的**分档口径一致（跨车道交叉通报 2026-09-08 的同型教训：
    # 扩展了裁决集合却沿用旧出口文案 ⇒ 结论比证据宽）。旧文案写死「138/138 全部被
    # 指定门的指定断言杀死」—— 而 `KILLED-UNBOUND` 只证明了「指定门红了」，把它算进
    # 那句话就是把两种强度不同的结论并成一句。
    if _n["KILLED-UNBOUND"]:
        print(
            f"⚠️ 其中 {_n['KILLED-UNBOUND']} 条只证明了「指定门红了」(KILLED-UNBOUND)，"
            f"**不在**「红在声称的那条断言上」这个结论里；逐条理由见 EXPECT_MSG_EXEMPT "
            f"与 EXPECT_LOC_EXEMPT。"
        )
    print(
        f"变异验证 PASS: {_n['KILLED']}/{len(MUTATIONS)} 红在**声称的那一条断言**上"
        f"（绑定维度: 断言源位置 [+ 消息]）; 另有 {_n['KILLED-UNBOUND']} 条 KILLED-UNBOUND; "
        f"{len(layered)} 条带层变异全部通过空变异对照(击杀非层贡献); 全部逐字节还原。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
