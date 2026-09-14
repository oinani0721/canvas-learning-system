#!/usr/bin/env python3
"""CARD-G3-9 负控的负控 —— 逐条抽掉对账脚本里的判据, 证明"声称的那条测试"确实变红。

不是"跑一遍有失败就算数": 每个变异体点名**它必须打红的那个 nodeid**, 并要求该 nodeid
FAILED。变异串必须在文件中**唯一**命中, 否则该变异作废 (改到了别处 = 结论不可归因)。

v2 (2026-09-14): 原 6 条按 ruff format 后的形态更新; 另为 Codex r1 的九条修复各加一个
变异体 (M7-M12) —— 修复本身也必须有牙齿, 否则"修了"只是把代码改了一下。

纪律 (本仓既有教训):
  - 还原基准 = **变异前的 sha**, 不是 HEAD。
  - 跑前 / 跑后各落一次全文件 shasum, 逐字节比对。
"""

import hashlib
import subprocess
import sys
from pathlib import Path

WT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3")
SCRIPT = WT / "backend" / "scripts" / "g39_three_view_reconcile.py"
TESTFILE = "tests/regression/test_g39_three_view_reconcile.py"

# (变异名, 原串, 替换串, 必须变红的 nodeid)
MUTANTS = [
    # ---- 基础判据 ----
    ("M1_去掉_overview板级due对账",
     '            diffs.append(_diff("overview ↔ picker.due_nodes", f"boards[{b}].due", a, c, "reimplementation"))',
     "            pass  # MUTANT", "test_negctl_overview_board_due_plus_one"),
    ("M2_去掉_板序对账", "    if ov_order != exp_order:", "    if False:  # MUTANT",
     "test_negctl_picker_top_boards_order_swapped"),
    ("M3_去掉_stats与明细长度对账",
     '        diffs.append(_diff("picker.stats ↔ picker.due_nodes", "due_count", p_stats_due, p_len_due, "cross-source"))',
     "        pass  # MUTANT", "test_negctl_stats_due_nodes_mismatch"),
    ("M4_把corrupt降级成not-fetched豁免", "    if status not in OVERVIEW_COMPARABLE_STATUS:",
     "    if False:  # MUTANT", "test_falsify_anchor_overview_corrupt_counts_as_semantic_diff"),
    ("M5_把行序对账退化成集合比较", "        if ov_seq != expected:",
     "        if sorted(ov_seq) != sorted(expected):  # MUTANT", "test_node_order_mirrors_urgency_not_scan_order"),
    ("M6_用isinstance判number（bool陷阱）", "    return type(v) is int or type(v) is float",
     "    return isinstance(v, (int, float))  # MUTANT", "test_dashboard_bool_is_not_a_js_number"),
    # ---- Codex r1 九条修复的缺陷形态 ----
    ("M8_板集退回只比到期板（r1 HIGH-1）", "    expected_boards = set(group_due) | zero_source",
     "    expected_boards = set(group_due)  # MUTANT", "test_r1_high1_zero_due_board_missing_from_overview_is_a_diff"),
    ("M9_picker解析退回宽松（r1 HIGH-3）",
     '            payload = json.loads(p.read_text(encoding="utf-8"), parse_constant=_reject_js_nonstandard)',
     '            payload = json.loads(p.read_text(encoding="utf-8"))  # MUTANT',
     "test_r1_high3_nan_is_rejected_like_js_json_parse"),
    ("M10_已连接后的读取失败退回豁免（r1 HIGH-4）",
     '        return {"__read_error__": f"{type(e).__name__}: {str(e)[:160]}"}, None',
     '        return None, f"{type(e).__name__}: {str(e)[:160]}"  # MUTANT',
     "test_r1_high4_read_failure_after_connect_is_not_exempted"),
    ("M11_boards损坏退回当成旧投影（r1 MEDIUM-5）",
     '        return None, f"boards 顶层键在, 但不是数组 (实为 {type(rollup).__name__})"',
     "        return None, None  # MUTANT", "test_r1_medium5_corrupt_boards_key_is_a_diff_not_scope_note"),
    ("M12_重复vault_id退回取首条（r1 LOW-9）", "    if len(hits) > 1:", "    if False:  # MUTANT",
     "test_r1_low9_duplicate_vault_entries_is_a_diff"),
    ("M13_去掉代理旁路（本卡自查）",
     "    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)",
     "    return urllib.request.build_opener(_NoRedirect)  # MUTANT",
     "test_fetch_overview_opener_bypasses_system_proxy"),
    # ---- Codex r2 十一条修复的缺陷形态 ----
    ("M14_响应头阶段失败退回豁免（r2 HIGH-1）", "        if _is_connection_failure(e):", "        if True:  # MUTANT",
     "test_r2_high1_headerless_hang_is_not_exempted"),
    ("M15_连接判定收得过紧（r2 HIGH-1 反面）", "        if _is_connection_failure(e):", "        if False:  # MUTANT",
     "test_r2_high1_connection_refused_still_exempted"),
    ("M16_板序退回只比前缀（r2 HIGH-2）", "    if ov_order != exp_order:",
     "    if ov_order[: len(top_names)] != exp_order[: len(top_names)]:  # MUTANT",
     "test_r2_high2_order_after_prefix_is_checked"),
    ("M17_去掉板行唯一性检查（r2 HIGH-3）", "            if b in seen_boards:", "            if False:  # MUTANT",
     "test_r2_high3_duplicate_overview_board_row_is_a_diff"),
    ("M18_buckets无boards退回当旧投影（r2 MEDIUM-4）", '    elif rollup_due is None and "buckets" in pk:',
     "    elif False:  # MUTANT", "test_r2_medium4_buckets_without_boards_is_not_legacy"),
    ("M19_板集漏掉upcoming（r2 MEDIUM-5）",
     "    zero_source = set(rollup_rows) if rollup_rows is not None else set(upcoming)",
     "    zero_source = set(rollup_rows) if rollup_rows is not None else set()  # MUTANT",
     "test_r2_medium5_legacy_upcoming_zero_board_is_not_a_false_diff"),
    ("M20_计数类型门禁放宽（r2 MEDIUM-6）", "    return v if type(v) is int else None",
     "    return v if isinstance(v, (int, float)) else None  # MUTANT", "test_r2_medium6_rollup_due_type_is_strict"),
    ("M21_去掉模板插值异常镜像（r2 MEDIUM-7）",
     '    if isinstance(v, dict):\n        return "toString" in v',
     "    if isinstance(v, dict):\n        return False  # MUTANT",
     "test_r2_medium7_generated_at_throwing_value_degrades_dashboard"),
    ("M22_不可哈希节点不再拦（r2 MEDIUM-9 / r3 MEDIUM-7 上移后）", "        if bad_nodes:",
     "        if False:  # MUTANT", "test_r2_medium9_unhashable_node_does_not_abort_reconcile"),
    # ---- Codex r3 十一条修复的缺陷形态 ----
    ("M23_跟随重定向（r3 HIGH-1）",
     "    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)",
     "    return urllib.request.build_opener(urllib.request.ProxyHandler({}))  # MUTANT",
     "test_r3_high1_redirect_is_not_followed"),
    ("M24_errno混平台数字（r3 MEDIUM-2）",
     '    for _n in ("ECONNREFUSED", "EHOSTUNREACH", "ENETUNREACH", "EHOSTDOWN", "ENETDOWN", "EADDRNOTAVAIL")',
     '    for _n in ("ECONNREFUSED", "EHOSTUNREACH", "ETIME")  # MUTANT',
     "test_r3_medium2_errno_set_comes_from_current_platform"),
    ("M25_数组不递归传播（r3 MEDIUM-4）",
     "    if isinstance(v, list):\n        return any(_js_interp_throws(x) for x in v)",
     "    if isinstance(v, list):\n        return False  # MUTANT",
     "test_r3_medium4_array_propagates_element_throw"),
    ("M26_去掉backlog插值检查（r3 MEDIUM-5）",
     "    if _js_interp_throws(backlog_cnt):",
     "    if False:  # MUTANT",
     "test_r3_medium5_backlog_interp_throw_degrades_dashboard"),
    ("M27_backlog比较退回宽松相等（r3 MEDIUM-6）",
     '    if not _same_count(dash["backlog_count"], ov_backlog):',
     '    if dash["backlog_count"] != ov_backlog:  # MUTANT',
     "test_r3_medium6_false_backlog_is_not_equal_to_zero"),
    ("M28_零到期板节点不查（r3 MEDIUM-9）",
     "        if ov_nodes_by_board[b]:",
     "        if False:  # MUTANT",
     "test_r3_medium9_zero_due_board_nodes_must_be_empty"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_pytest(nodeid: str) -> tuple[int, str]:
    r = subprocess.run(
        [str(WT / "backend" / ".venv" / "bin" / "pytest"), "-q", "-p", "no:cacheprovider", f"{TESTFILE}::{nodeid}"],
        cwd=str(WT / "backend"),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(Path.home())},
    )
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    baseline_sha = sha(SCRIPT)
    baseline_text = SCRIPT.read_text(encoding="utf-8")
    print(f"跑前 shasum: {baseline_sha}")
    print("还原基准 = 变异前 sha (脚本是新文件, HEAD 无此文件)\n")

    ok = True
    killed = 0
    for name, old, new, nodeid in MUTANTS:
        hits = baseline_text.count(old)
        if hits != 1:
            print(f"[{name}] ⛔ 变异串命中 {hits} 次 (须恰好 1) — 该变异作废\n")
            ok = False
            continue
        SCRIPT.write_text(baseline_text.replace(old, new), encoding="utf-8")
        rc, out = run_pytest(nodeid)
        SCRIPT.write_text(baseline_text, encoding="utf-8")
        after = sha(SCRIPT)
        restored = "OK" if after == baseline_sha else f"⛔ 未还原 {after}"
        is_killed = rc != 0 and "failed" in out
        killed += 1 if is_killed else 0
        tail = [ln for ln in out.splitlines() if "passed" in ln or "failed" in ln]
        print(f"[{name}]")
        print(f"  点名 nodeid : {nodeid}")
        print(f"  变异后 rc   : {rc}  ⇒ {'KILLED (判据有牙齿)' if is_killed else '⛔ SURVIVED (判据空转!)'}")
        print(f"  还原        : {restored}")
        print(f"  pytest 摘要 : {tail[-1] if tail else '(无)'}\n")
        if not is_killed or after != baseline_sha:
            ok = False

    print(f"跑后 shasum: {sha(SCRIPT)}  (与跑前{'相同' if sha(SCRIPT) == baseline_sha else '不同 ⛔'})")
    print(f"\n结论: KILLED {killed}/{len(MUTANTS)} — {'全部被点名的断言打红 ⇒ 负控有牙齿' if ok else '⛔ 存在空转判据或未还原'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
