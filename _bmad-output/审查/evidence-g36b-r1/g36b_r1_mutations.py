#!/usr/bin/env python3
"""CARD-G3-6b-R1 变异承重验证 — 8 条，严格串行。

MEMORY 铁律逐条落实：
- 串行：绝不并发（原地变异并发跑互踩，reference_mutation_script_serial_only）
- EXIT trap：finally 无条件还原，且还原后 **逐字节** 比对（sha256）
- **指定的那道门**必须变红，不是「某处有失败」（reference_gate_design_pitfalls）
- **只有 rc=1 算红**：pytest 的 rc=2(中断)/3(内部错)/4(用法错)/5(未收集到) 一律
  判 INVALID —— 它们都能让「测试没通过」看起来像「门抓住了变异」，而实际上门
  可能根本没跑。（Codex R1 轮 MEDIUM：原版把 rc!=0 一概算红，是同一类假绿。）
- **精确 nodeid**（`file::testname`）而非 `-k` 子串匹配：`-k` 会连带选中名字里
  含该子串的其它测试，红的来源就不唯一了。
- **保留 stderr**：判 INVALID 时要能看出是收集失败还是环境炸了。
- 锚点断言：old 必须在源码中恰好可命中，否则该条判 INVALID（防死变异）
- 还原用 `finally` + SIGINT/SIGTERM handler。**如实声明**：SIGKILL 或解释器硬崩
  仍会留下变异字节，所以还原后的**逐字节比对**才是真正的判据，前两者只是让
  常见路径不出错 —— 不要把它们当成 shell EXIT trap 的等价物来引用。

**运行环境依赖（R1 round-2 Codex LOW）**：本脚本跑的是 `backend/` 下的真实测试
套件，而 `backend/.env` **未被 git 跟踪**。在一个 clean clone 里直接跑，阶段 0 会
以 `rc=4` 失败（脚本会停在阶段 0 并打印诊断，不会把它误当成「门抓住了变异」）。
复现本脚本需要一个已配置 `backend/.env` 的工作树。
"""
from __future__ import annotations

import hashlib
import signal
import subprocess
import sys
from pathlib import Path

LANE = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard")
PICK = LANE / "scripts" / "daily_review_pick.py"
OVERVIEW = LANE / "backend" / "app" / "api" / "v1" / "endpoints" / "review_overview.py"
PICK_TESTS = "tests/regression/test_daily_review_pick.py"
OV_TESTS = "tests/unit/test_review_overview.py"

# (编号, 说明, 目标文件, old, new, 测试文件, 指定门)
MUTATIONS = [
    (
        "M1", "解耦 factors：why 不再由落盘 factors 复算",
        PICK,
        '"why_this_board": why_this_board(factors),',
        '"why_this_board": why_this_board({**factors, "due_total": factors["due_total"] + 1}),',
        PICK_TESTS, "test_g36b_why_this_board_recomputes_from_factors",
    ),
    (
        "M2", "sha 不随 decay 系数变（decay 常量退出摘要）",
        PICK,
        '"decay_beta_constants": {k: getattr(decay, k, None) for k in DECAY_CONSTANT_NAMES},',
        '"decay_beta_constants": {k: 0 for k in DECAY_CONSTANT_NAMES},',
        PICK_TESTS, "test_g36b_sha_changes_for_every_single_coefficient",
    ),
    (
        "M3", "渲染层自算分钟（UI 再算，违反单通路）",
        OVERVIEW,
        'text = html.escape(why) + f" · 预计 {int(mins)} 分钟"',
        'text = html.escape(why) + f" · 预计 {len(r.get(\'nodes\') or []) * 3} 分钟"',
        OV_TESTS, "test_g36b_page_renders_explain_row_and_escapes_hostile",
    ),
    (
        "M4", "排序倒序（改序，违反 A2 冻结）",
        PICK,
        'ranked.sort(key=lambda r: r["_tie"])',
        'ranked.sort(key=lambda r: r["_tie"], reverse=True)',
        PICK_TESTS, "test_g36b_top_boards_order_matches_head_baseline",
    ),
    (
        "M5", "截断放松 [:TOP_BOARDS_LIMIT] → [:99]",
        PICK,
        '"top_boards": ranked[:TOP_BOARDS_LIMIT],',
        '"top_boards": ranked[:99],',
        PICK_TESTS, "test_g36b_truncated_flags",
    ),
    (
        "M6", "消费端门禁失明（分钟不验形）",
        OVERVIEW,
        'if mins is not None and (type(mins) is not int or mins < 0):',
        'if mins is not None and False:',
        OV_TESTS, "test_g36b_garbage_explain_fields_degrade_corrupt_not_ok",
    ),
    (
        "M7", "_tie 派生回退成硬编码（round-1 HIGH 整改回退）",
        PICK,
        '"_tie": tuple(tie_parts[k] for k in TIE_FACTOR_KEYS),',
        '"_tie": (tie_parts["priority_pick"], tie_parts["board_last_recommended"], '
        'tie_parts["min_last_examined"], tie_parts["board"]),',
        PICK_TESTS, "test_g36b_tie_keys_are_single_source",
    ),
    (
        "M8", "渲染原子对回退（单边在场即渲染）",
        OVERVIEW,
        'if why and mins is not None:',
        'if why or mins is not None:',
        OV_TESTS, "test_g36b_one_sided_explain_fields_render_nothing",
    ),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate(testfile: str, gate: str) -> tuple[int, str]:
    """跑**精确 nodeid**（不是 -k 子串），返回 (rc, stdout+stderr 尾部)。"""
    nodeid = f"{testfile}::{gate}"
    r = subprocess.run(
        [".venv/bin/pytest", nodeid, "-q", "-p", "no:cacheprovider", "--no-header"],
        cwd=LANE / "backend", capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "PYTHONDONTWRITEBYTECODE": "1",
             "HOME": str(Path.home()), "LANG": "en_US.UTF-8"},
    )
    tail = ((r.stdout or "")[-400:] + " ||STDERR|| " + (r.stderr or "")[-300:])
    return r.returncode, tail.strip().replace("\n", " | ")


def _install_restore_handlers(originals: dict) -> None:
    """SIGINT/SIGTERM 时也还原（finally 覆盖不到信号中断）。

    如实声明：SIGKILL / 解释器硬崩仍会留下变异字节 —— 这不是 EXIT trap 的
    等价物，最终判据始终是脚本末尾的逐字节比对。
    """
    def _restore(signum, _frame):
        for path, raw in originals.items():
            try:
                path.write_bytes(raw)
            except OSError:
                pass
        print(f"\n⚠ 收到信号 {signum}，已尝试还原全部目标文件", file=sys.stderr)
        sys.exit(130)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _restore)


def main() -> int:
    _install_restore_handlers({PICK: PICK.read_bytes(), OVERVIEW: OVERVIEW.read_bytes()})
    baseline = {PICK: sha(PICK), OVERVIEW: sha(OVERVIEW)}
    print("变异前基线 sha256:")
    for p, s in baseline.items():
        print(f"  {p.name}: {s}")

    # 先确认每道指定门在未变异状态下是绿的（否则"红"证明不了是变异造成的）
    print("\n── 阶段 0：确认 8 道指定门在原样代码下全绿（红的来源必须可归因）──")
    for tag, _desc, _f, _o, _n, tf, gate in MUTATIONS:
        rc, tail = run_gate(tf, gate)
        status = "绿" if rc == 0 else f"⛔ rc={rc}"
        print(f"  {tag} {gate}: {status}")
        if rc != 0:
            print(f"      {tail}")
            print("  ⛔ 前置不成立，中止（无法归因）")
            return 2

    results = []
    print("\n── 阶段 1：8 条变异，严格串行 ──")
    for tag, desc, target, old, new, tf, gate in MUTATIONS:
        raw = target.read_bytes()
        src = raw.decode("utf-8")
        hits = src.count(old)
        if hits != 1:
            results.append((tag, "INVALID", f"锚点命中 {hits} 次（应为 1）— 死变异", ""))
            print(f"[{tag}] INVALID 锚点命中 {hits} 次")
            continue
        try:
            target.write_text(src.replace(old, new, 1), encoding="utf-8")
            assert sha(target) != baseline[target], "变异未真正落盘"
            rc, tail = run_gate(tf, gate)
        finally:
            target.write_bytes(raw)  # EXIT trap 等价物：无条件还原
            restored = sha(target)
            assert restored == baseline[target], f"{tag} 还原后字节不一致！{restored}"

        if rc == 1:
            # R1 round-2 收窄: rc=1 只证明「这个 nodeid 失败了」，**不能**单凭
            # 退出码证明是哪条断言失败 —— 所以红时也把 failure tail 归档下来。
            verdict, note = "✅ 红", "rc=1（该 nodeid 失败；具体断言见下方 tail）"
        elif rc == 0:
            verdict, note = "空转", "rc=0 指定门未变红 —— 门不承重"
        else:
            verdict, note = "INVALID", (
                f"rc={rc} —— pytest 2=中断/3=内部错/4=用法错/5=未收集到，"
                "都不是「门抓住了变异」")
        results.append((tag, verdict, note, desc))
        print(f"[{tag}] {verdict:6s} {gate}  ({note})")
        print(f"        变异: {desc}")
        # 红/非红都归档 pytest 尾部：红时用来确认失败的是**预期的那条断言**
        print(f"        pytest: {tail[:360]}")

    print("\n── 阶段 2：还原后逐字节校验 ──")
    ok_bytes = True
    for p, s in baseline.items():
        now = sha(p)
        same = now == s
        ok_bytes &= same
        print(f"  {p.name}: {'逐字节一致 ✅' if same else f'⛔ 漂移 {now}'}")

    killed = sum(1 for _t, v, _n, _d in results if v == "✅ 红")
    print(f"\n{'=' * 60}\n变异结果: {killed}/{len(MUTATIONS)} 条各杀其指定门；还原完整性: "
          f"{'PASS' if ok_bytes else 'FAIL'}")
    for tag, v, note, _d in results:
        if v != "✅ 红":
            print(f"  ⛔ {tag}: {v} — {note}")
    return 0 if (killed == len(MUTATIONS) and ok_bytes) else 1


if __name__ == "__main__":
    sys.exit(main())
