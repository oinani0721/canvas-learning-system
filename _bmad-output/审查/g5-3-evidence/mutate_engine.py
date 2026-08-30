#!/usr/bin/env python3
"""G5-3 回归门变异反证器。

对每条对抗审查修复做一次「撤销」变异（只作用于 /private/tmp 下的引擎副本），
把对应的裁判指向变异体跑一遍，断言它**变红**。全绿 = 那道门空转。

⛔ 不修改仓库任何文件。每个变异体是独立文件，串行执行互不覆盖
（历史教训: 并发变异会让 B 的还原把 A 的 mutation 写回而测试照样全绿）。

用法: python3 mutate_engine.py <engine.py> <judge.py> <workdir>
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

#: (变异名, 撤销哪条修复, [(原文, 替换)...], 该变异必须弄红的测试)
MUTATIONS: list[tuple[str, str, list[tuple[str, str]], str]] = [
    (
        "no-seed-dedup",
        "撤销 Concepts 种子 NFC 去重",
        [("        key = nfc(seed)\n        if key in seen_members:", "        key = nfc(seed)\n        if False:")],
        "TestReviewRegressions::test_duplicate_seed_in_concepts_no_longer_kills_the_board",
    ),
    (
        "fallback-anchor-with-line",
        "把行号塞回 fallback 命名锚点",
        [
            (
                'anchor = f"{file_rel}\\x00{\'/\'.join(sec[\'_norm_path\'])}\\x00{b}\\x00{sec[\'_occurrence\']}"',
                'anchor = f"{file_rel}:{sec[\'line\']}"',
            )
        ],
        "TestReviewRegressions::test_fallback_name_has_no_line_number",
    ),
    (
        "fingerprint-includes-machine",
        "指纹不再排除机器生成段",
        [
            (
                'lines, sec["line"], sec["end"], machine\n            ),',
                'lines, sec["line"], sec["end"], None\n            ),',
            )
        ],
        "TestReviewRegressions::test_machine_generated_tail_does_not_pollute_fingerprint",
    ),
    (
        "basis-out-of-key",
        "把 basis 从身份键载荷里拿掉",
        [("        str(occurrence),\n        basis,\n    ]", "        str(occurrence),\n    ]")],
        "TestReviewRegressions::test_seed_whole_to_section_changes_id_via_basis",
    ),
    (
        "no-ambiguous-flag",
        "不再标记身份歧义",
        [('"identity_ambiguous": sec["_ambiguous_group"] > 1,', '"identity_ambiguous": False,')],
        "TestReviewRegressions::test_duplicate_paths_are_flagged_as_identity_ambiguous",
    ),
    (
        "no-truncation-suspect",
        "撤销截断嫌疑标记与 over_threshold 告警",
        [
            (
                'truncated_either = bool(og.get("over_threshold") or ng.get("over_threshold"))',
                "truncated_either = False",
            ),
            ('for side, g in (("旧", og), ("新", ng)):\n        if g.get("over_threshold"):', 'for side, g in ():\n        if g.get("over_threshold"):'),
        ],
        "TestReviewRegressions::test_truncation_suspect_flagged_when_board_grows_past_same_threshold",
    ),
    (
        "no-vault-warning",
        "撤销跨 vault 告警",
        [('if old.get("vault_fingerprint") != new.get("vault_fingerprint"):', "if False:")],
        "TestReviewRegressions::test_cross_vault_compare_warns",
    ),
    (
        "no-basis-integrity",
        "撤销同 ID 两侧 basis 相等校验",
        [("        if ob != nb:", "        if False:"), ('            compute_stable_id(b["file"], hp, occ, b["basis"]) == sid,', '            True,')],
        "TestReviewRegressions::test_same_id_different_basis_is_refused",
    ),
    (
        "no-overlap-reason",
        "撤销 overlap 变更项",
        [
            (
                'if (o.get("derived_overlap") or {}) != (c.get("derived_overlap") or {}):\n            reasons.append("overlap")',
                'if False:\n            reasons.append("overlap")',
            )
        ],
        "TestReviewRegressions::test_derived_overlap_transition_gets_its_own_reason",
    ),
    (
        "no-md-escape",
        "撤销 MD 表格单元格转义",
        [('return str(s).replace("\\\\", "\\\\\\\\").replace("|", "\\\\|")', "return str(s)")],
        "TestReviewRegressions::test_pipe_in_heading_does_not_break_md_table",
    ),
    (
        "no-filename-length-check",
        "撤销产物文件名长度预检",
        [("        if n > MAX_FILENAME_BYTES:", "        if False:")],
        "TestReviewRegressions::test_overlong_board_name_rejected_with_zero_products",
    ),
    (
        "no-candidate-schema-check",
        "撤销候选 source_anchor 整段入口校验（连同复算兜底一并撤，以隔离该门）",
        [('        a = c.get("source_anchor")\n        _need(isinstance(a, dict), f"{role} preview 候选的 source_anchor 不是对象{tag}")\n        _need(\n            _nonempty_str(a.get("file")),\n            f"{role} preview 候选 source_anchor.file 非法{tag}",\n        )\n        for k in ("line_start", "line_end"):\n            _need(\n                _is_int(a.get(k)) and a[k] >= 1,\n                f"{role} preview 候选 source_anchor.{k} 不是正整数{tag}",\n            )\n        _need(\n            a["line_end"] >= a["line_start"],\n            f"{role} preview 候选 source_anchor 行区间倒置{tag}",\n        )\n        _need(\n            isinstance(a.get("heading_path"), list)\n            and a["heading_path"]\n            and all(_nonempty_str(x) for x in a["heading_path"]),\n            f"{role} preview 候选 source_anchor.heading_path 非法或为空{tag}",\n        )\n        # 原文标题路径必须与归一化路径**正向对得上**。\n        # ⛔ 我在 round-4 写过「归一化有损、只能绑层数」——那是错的（Codex round-5 指出）：\n        # 不需要从归一化反推原文, 把原文**再正向归一化一遍**比对即可。只绑层数时,\n        # 同层数的伪造标题（["完全伪造的父标题","完全伪造的子标题"]）能静默通过并把\n        # 伪造锚点送进 diff。这是**无需读 vault 就能对账的内部不一致**, 不属「无签名」边界。\n        _need(\n            normalize_heading_path(a["heading_path"]) == hp,\n            f"{role} preview 候选的 heading_path 正向归一化后与 heading_path_normalized 不符{tag}",\n        )\n\n', '        a = c.get("source_anchor")\n\n'), ('            compute_stable_id(b["file"], hp, occ, b["basis"]) == sid,', '            True,')],
        "TestReviewRegressions::test_broken_source_anchor_rejected_before_any_write",
    ),
    (
        "occurrence-counts-candidates-only",
        "occurrence 改为只数达标候选（撤销「按全部小节计数」）",
        [
            (
                "    for sec in secs:\n        norm = tuple(normalize_heading_path(sec[\"path\"] + [sec[\"text\"]]))\n        seen_paths[norm] = seen_paths.get(norm, 0) + 1",
                "    for sec in secs:\n        norm = tuple(normalize_heading_path(sec[\"path\"] + [sec[\"text\"]]))\n        if not passes_content_gate(sec, lines, stripped, comments):\n            sec[\"_norm_path\"] = list(norm)\n            sec[\"_occurrence\"] = 0\n            continue\n        seen_paths[norm] = seen_paths.get(norm, 0) + 1",
            )
        ],
        "TestReviewRegressions::test_occurrence_counts_all_sections_not_just_candidates",
    ),
    # ── Codex round-2（复核轮）修复的变异 ────────────────────────────────
    (
        "ra-ignores-comment-mask",
        "Recent Activity 扫描不再避开普通 HTML 注释",
        [("        if not kind[i] and not pre_comment[i]:", "        if not kind[i]:")],
        "TestRound2Regressions::test_commented_out_recent_activity_does_not_swallow_user_text",
    ),
    (
        "schema-check-existence-only",
        "撤销 vault_fingerprint 的存在+格式校验（安全字段可缺失 → fail-open）",
        [('    _need(\n        _nonempty_str(data.get("vault_fingerprint"))\n        and bool(_VF_RE.match(data["vault_fingerprint"])),\n        f"{role} preview 的 vault_fingerprint 缺失或格式非法（缺了会让跨 vault 比对静默通过）: {p}",\n    )\n', '')],
        "TestRound2Regressions::test_missing_or_mistyped_safety_fields_are_refused[<lambda>-vault_fingerprint]",
    ),
    (
        "no-created-file-rollback",
        "成对发布失败时不撤销本次新建的空文件",
        [("            if was_new:", "            if False:")],
        "TestRound2Regressions::test_second_product_rejection_leaves_no_first_product",
    ),
    (
        "basis-compare-raw",
        "basis 比较退回 raw dict（NFC/NFD 等价改名被假拒绝）",
        [
            (
                '        ob = _basis_key(old_by[sid]["stable_id_basis"])\n        nb = _basis_key(new_by[sid]["stable_id_basis"])',
                '        ob = old_by[sid]["stable_id_basis"]\n        nb = new_by[sid]["stable_id_basis"]',
            )
        ],
        "TestRound2Regressions::test_nfc_nfd_equivalent_source_name_is_not_falsely_refused",
    ),
    (
        "max-units-unchecked",
        "撤销 --max-units 正整数校验",
        [("    if args.max_units < 1:", "    if False:")],
        "TestRound2Regressions::test_max_units_must_be_positive",
    ),
    (
        "payload-no-length-prefix",
        "载荷退回裸 U+0000 拼接（分段歧义可碰撞）",
        [('    payload = "\\x00".join(f"{len(seg)}:{seg}" for seg in segs)', '    payload = "\\x00".join(segs)')],
        "TestRound2Regressions::test_payload_encoding_is_injective_under_nul_bytes",
    ),
    # ── Codex round-3（二次复核）修复的变异 ──────────────────────────────
    (
        "bool-counts-as-int",
        "整数校验退回 isinstance(v, int)（Python 把 bool 当 int → JSON true/false 放行）",
        [
            (
                "def _is_int(v: object) -> bool:",
                "def _is_int(v: object) -> bool:\n    return isinstance(v, int)  # mutated\n\n\ndef _is_int_unused(v: object) -> bool:",
            )
        ],
        "TestRound3Regressions::test_bool_is_not_accepted_as_int_on_candidate[True-index]",
    ),
    (
        "rollback-uses-exists",
        "回滚判「本次新建」退回 Path.exists()（dangling symlink 被误删）",
        [
            (
                "    created = [not os.path.lexists(str(path)) for path, _ in items]",
                "    created = [not path.exists() for path, _ in items]",
            )
        ],
        "TestRound3Regressions::test_dangling_symlink_target_is_not_deleted_on_rejection",
    ),
    (
        "no-stable-id-recompute",
        "撤销 stable_id 复算对账（「类型对但语义坏」整类放行）",
        [
            (
                '            compute_stable_id(b["file"], hp, occ, b["basis"]) == sid,',
                "            True,",
            )
        ],
        "TestRound3Regressions::test_semantically_broken_but_well_typed_input_is_refused[<lambda>-\u590d\u7b97]",
    ),
    (
        "no-cross-field-binding",
        "撤销 basis↔候选/anchor 的交叉绑定校验",
        [
            (
                '            b["basis"] == c["basis"],',
                "            True,",
            )
        , ('            compute_stable_id(b["file"], hp, occ, b["basis"]) == sid,', '            True,')],
        "TestRound3Regressions::test_semantically_broken_but_well_typed_input_is_refused[<lambda>-basis]",
    ),
    (
        "no-id-format-check",
        "撤销 stable_id / content_fingerprint 格式校验",
        [
            (
                '        _need(bool(_ID_RE.match(sid)), f"{role} preview 候选的 stable_id 格式非法{tag}")',
                "        _need(True, \"\")",
            )
        , ('            compute_stable_id(b["file"], hp, occ, b["basis"]) == sid,', '            True,')],
        "TestRound3Regressions::test_semantically_broken_but_well_typed_input_is_refused[<lambda>-stable_id]",
    ),
    # ── Codex round-4（终裁轮）修复的变异 ──────────────────────────────
    (
        "no-scale-gate-consistency",
        "撤销 scale_gate 四方对账（改 total_candidates 即可静默压掉截断告警）",
        [
            (
                '        sg["over_threshold"] == (sg["total_candidates"] > sg["threshold"]),',
                "        True,",
            ),
            (
                '        sg["threshold"] >= 1\n        and sg["kept"] == len(data["candidates"])\n        and sg["total_candidates"] >= sg["kept"],',
                "        True,",
            ),
        ],
        "TestRound4Regressions::test_semantic_layer_fail_open_is_closed[<lambda>-scale_gate]",
    ),
    (
        "accepts-foreign-namespace",
        "撤销「只认本引擎这一代」（两侧协同重标 namespace 即可全过）",
        [
            (
                '        data["stable_id_namespace"] == STABLE_ID_NAMESPACE,',
                "        True,",
            )
        ],
        "TestRound4Regressions::test_relabelled_namespace_on_both_sides_is_refused",
    ),
    (
        "no-vault-fingerprint-format",
        "撤销 vault_fingerprint 格式校验（空白串可通过）",
        [
            (
                '        _nonempty_str(data.get("vault_fingerprint"))\n        and bool(_VF_RE.match(data["vault_fingerprint"])),',
                '        _nonempty_str(data.get("vault_fingerprint")),',
            )
        ],
        "TestRound4Regressions::test_semantic_layer_fail_open_is_closed[<lambda>-vault_fingerprint]",
    ),
    # ── Codex round-5 修复的变异 ────────────────────────────────────────
    (
        "heading-path-depth-only",
        "标题路径绑定退回「只比层数」（同层数伪造标题可静默通过）",
        [
            (
                '            normalize_heading_path(a["heading_path"]) == hp,',
                '            len(a["heading_path"]) == len(hp),',
            )
        ],
        "TestRound5Regressions::test_same_depth_forged_heading_path_is_refused",
    ),
    (
        "no-board-file-binding",
        "撤销 board ↔ board_file 对账",
        [
            (
                '        data["board_file"] == f"原白板/{data[\'board\']}.md",',
                "        True,",
            )
        ],
        "TestRound5Regressions::test_board_relabel_without_board_file_is_refused",
    ),
    # ── Codex round-6 修复的变异 ────────────────────────────────────────
    (
        "no-basis-dir-binding",
        "撤销 basis ↔ 来源目录前缀的自洽校验",
        [
            (
                '            a["file"].startswith(expect_dir),',
                "            True,",
            )
        ],
        "TestRound6Regressions::test_internally_checkable_forgery_is_refused[\u6765\u6e90\u76ee\u5f55]",
    ),
    (
        "no-suggested-name-recompute",
        "撤销 suggested_name 由原文标题复算的对账",
        [
            (
                "            == c[\"suggested_name\"],",
                "            or True,",
            )
        ],
        "TestRound6Regressions::test_internally_checkable_forgery_is_refused[\u590d\u7b97\u4e0d\u7b26]",
    ),
    (
        "no-sources-membership",
        "撤销「候选来源文件必须在 sources 清单里」",
        [
            (
                '            a["file"] in source_files,',
                "            True,",
            )
        ],
        "TestRound6Regressions::test_internally_checkable_forgery_is_refused[sources]",
    ),
    (
        "no-id-stability-binding",
        "撤销 id_stability 常量比对",
        [
            (
                '        data.get("id_stability") == ID_STABILITY,',
                "        True,",
            )
        ],
        "TestRound6Regressions::test_internally_checkable_forgery_is_refused[id_stability]",
    ),
]

#: ⛔ 覆盖声明（Codex round-3 LOW 要求收紧措辞）：本矩阵证明的是「每个变异体都能让
#: **它点名的那一道门**变红」，不是「每道门覆盖了该修复的全部字段/全部分支」。
#: 例如 `schema-check-existence-only` 只关掉 vault_fingerprint 单点守卫，
#: 不能代表 HIGH-2 的全部类型门；后者由 10 组参数化用例 + round-3 的 bool/语义组另行覆盖。
#:
#: 另有一层**有意的冗余**需要说明：round-3 加的「stable_id 复算对账」在语义上兜住了
#: basis 交叉绑定、ID 格式、source_anchor 完整性这几道门 —— 单独撤掉其中任一道，
#: 测试仍会被复算拦红。所以那几条变异是**连同复算一起撤**的（否则测不出该门的作用）。
#: 它们保留的价值是**诊断精度**：复算只会说「对不上」，这几道门能直接点出是哪个字段坏了。
#:
#: ⛔ 如实声明：还有一条修复**没有**行为门，因此不在上表里 ——
#: 「身份自检从规模门截断之后移到之前」。原因：该自检唯一已知的可达触发路径是
#: 「同一来源文件被扫两次」，而那条路径已在**源头**（Concepts 种子 NFC 去重）消除。
#: 去重之后，同一份 preview 内 (file, path, occurrence, basis) 四元组按构造互异，
#: 除非发生 64-bit 哈希真碰撞，否则自检根本触发不了 —— 也就无法用黑盒测试证明
#: 「它跑在截断之前」这件事。它保留为纵深防御（万一将来新增了别的扫描入口），
#: 但覆盖状态是「无测试」，不假装有。


def main() -> int:
    engine_src = Path(sys.argv[1]).read_text(encoding="utf-8")
    judge_src = Path(sys.argv[2]).read_text(encoding="utf-8")
    work = Path(sys.argv[3])
    work.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for name, what, pairs, test_id in MUTATIONS:
        mutated = engine_src
        applied = 0
        for old, new in pairs:
            if old not in mutated:
                print(f"[{name}] ⛔ 变异锚点未命中（引擎已改动？）: {old[:60]!r}")
                failures.append(f"{name}: 锚点未命中")
                break
            mutated = mutated.replace(old, new, 1)
            applied += 1
        if applied != len(pairs):
            continue
        if mutated == engine_src:
            failures.append(f"{name}: 变异未生效")
            continue

        eng_path = work / f"engine-{name}.py"
        eng_path.write_text(mutated, encoding="utf-8")
        judge_path = work / f"judge-{name}.py"
        judge_path.write_text(
            re.sub(
                r"^SCRIPT = .*$",
                f'SCRIPT = Path({str(eng_path)!r})',
                judge_src,
                count=1,
                flags=re.M,
            ),
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, "-m", "pytest", f"{judge_path}::{test_id}", "-q", "--no-header", "-p", "no:randomly"],
            capture_output=True,
            text=True,
        )
        red = r.returncode != 0
        mark = "✅ 变红" if red else "❌ 仍全绿（门空转）"
        print(f"[{name}] {what}\n    → {test_id.split('::')[-1]}: {mark}")
        if not red:
            failures.append(f"{name}: 注入缺陷后测试仍绿 —— {test_id}")

    print()
    if failures:
        print("⛔ 未通过的变异:")
        for f in failures:
            print("   -", f)
        return 1
    print(f"✅ {len(MUTATIONS)} 个变异体全部让对应的门变红 —— 无空转门")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
