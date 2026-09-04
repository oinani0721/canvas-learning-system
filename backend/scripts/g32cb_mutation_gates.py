#!/usr/bin/env python3
"""CARD-G3-2c-B 变异负控：证明四道防线**承重**，而不只是"门是绿的"。

X7-A 只证明了 round-17 的门在这套代码上全绿；绿门 ≠ 有效门。本脚本对每道防线
做一次「拆掉它」的变异，看**指定的那道门**是否变红。

⛔ 本脚本的防呆设计，逐条都是踩过的坑（见 memory）：

1. **串行**：原地变异并发跑会互踩。全程单进程顺序执行，不并行。
2. **无条件还原**：`finally` 里不带任何「别覆盖第三方改动」的 exit 防护——
   exit 时不还原，变异体就留在生产文件里（`if False:  # MUTANT` 在 SKILL.md
   里活过整整一轮，两天后才被下一张卡的测试红抓出来）。
3. **信号也要还原**：`SIGTERM` 默认处置**不做栈展开**，`finally` 不会执行。
   装 handler 转成异常，让 `finally` 有机会跑。
4. **全文件 sha 基线，不靠 grep 标记**：变异体的替换文本**不一定含 "MUTANT"
   字样**（历史上就有一次不含），所以锚点是跑前对**每个会被变异的文件**记全
   文件 sha、跑完逐个复核，与变异体是否配合无关。
5. **KILLED 判据是 `rc == 1`，不是 `rc != 0`**：pytest 的 `4`=用法错、
   `5`=零收集、`2`=中断、`3`=内部错。门名一打错，`rc != 0` 会让整份报告全绿
   而毫无意义。
6. **判据比对失败身份，防假杀**：只看「有测试失败」会把「变异让别的门红了」
   当成击杀。必须是**指定的那条测试**失败才算 KILLED。

⚠️ **拆防线，不要改参数**（M4/M5 踩了两次才对）：
   门是**从实现读上限**再按它构造输入的（`_validator_limits()`）。于是
   ① 把上限改成 `10**9` ⇒ 门去构造十亿层嵌套，卡死（实测 300s 超时）；
   ② 把上限改成 4096 ⇒ 门读到 4096、构造 4097 层，**仍然超限仍然被拒**，
      变异对门完全不可见（实测 SURVIVED）。
   同源保证了门不会与实现漂移，代价就是**改参数等于同时改了门的期望**。
   正确的变异是拆掉**判据本身**（`if depth > MAX:` → `if False:`）：
   上限常量不动，门的构造不变，而检查不再执行。

用法：`python3 backend/scripts/g32cb_mutation_gates.py [--list]`
"""

from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[2]
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
PYTEST = Path(
    "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pytest"
)
LEDGER_TEST = "tests/regression/test_g3_2_review_ledger.py"

#: (id, 说明, 目标文件, 原文本, 变异文本, 必须变红的测试)
#: ⚠️ 「必须变红的测试」是**身份判据**：变异后必须是这一条失败，别的门红不算数。
MUTATIONS = [
    (
        "M1",
        "truthiness 回退：严格 bool 判定退回「只拒 None」(round-17 B① 的原形态)",
        SKILL,
        "    if _rc_dup is not None and type(_rc_dup_applied) is not bool:",
        "    if _rc_dup is not None and _rc_dup_applied is None:  # MUTANT M1",
        "test_round17_fsrs_applied_must_be_strict_bool",
    ),
    (
        "M2",
        "去掉 foreign 凭据提升：`fsrs_applied: false` 补了调度却不升 true",
        SKILL,
        "        if _fa_fg is False:\n            fm, _ok_fg = _promote_applied(fm, _rid_)",
        "        if False:  # MUTANT M2 去掉 foreign 提升\n            fm, _ok_fg = _promote_applied(fm, _rid_)",
        "test_round17_foreign_degraded_recovery_converges",
    ),
    (
        "M3",
        "去掉写序锚方向校验：没有时刻/序数证据也认这个锚",
        SKILL,
        "                            if _ib_a is None and not _ord_ok:\n                                pass                      # 无证据 ⇒ 锚不可用, 走回落\n                            else:",
        "                            if False:  # MUTANT M3 去掉方向校验\n                                pass\n                            else:",
        # ⛔ 目标门换过一次，原因记在这里：原先绑
        # `test_round17_anchor_direction_is_verified`，实测 M3 `SURVIVED(rc=0)`。
        # 那道门的场景里后继 B 是**正常行**（review_time 与 attempt_count 都在），
        # `_ib_a` 不为 None ⇒ 原代码本来就走 else 分支，本变异拆掉的分支在该场景
        # **根本不执行**；它的拒绝来自另一处的「自相矛盾」检查。
        # 变异与门不匹配 ⇒ SURVIVED 不是「防线没用」，是「没有门守着这条防线」。
        # 补了 `test_g32cb_anchor_without_direction_evidence_falls_back`
        # （B 退化成无 review_time / 无 attempt_count 的 §6.3 行）才走得到该分支。
        "test_g32cb_anchor_without_direction_evidence_falls_back",
    ),
    (
        "M4",
        "去掉深度上限：§6.1 输入硬上限的深度维度失效（节点预算仍在）",
        VALIDATOR,
        "        if depth + 1 > MAX_VALUE_DEPTH:",
        "        if False:  # MUTANT M4 拆掉深度判据",
        "test_g32cb_depth_over_limit_rejected_before_first_append",
    ),
    (
        "M5",
        "去掉节点预算：只剩深度维度（证明两个维度各自承重，不是一个兜住另一个）",
        VALIDATOR,
        "        if seen > MAX_VALUE_NODES:",
        "        if False:  # MUTANT M5 拆掉节点判据",
        "test_g32cb_node_budget_over_limit_rejected_before_first_append",
    ),
]


class _Terminated(Exception):
    """把 SIGTERM/SIGINT 转成异常，好让 finally 里的还原跑得到。"""


def _install_signal_handlers() -> None:
    def _handler(signum, _frame):
        raise _Terminated(f"收到信号 {signum}")

    for _sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(_sig, _handler)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run_gate(test_name: str) -> tuple[int, str]:
    # ⚠️ 必须继承 os.environ 再覆盖：只给 PATH/HOME 的窄 env 会让写点子进程
    # 拿不到解释器环境而挂住（实测一次 10 分钟外部超时就是这么来的）。
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run(
        [str(PYTEST), "-q", "-p", "no:cacheprovider", f"{LEDGER_TEST}::{test_name}"],
        cwd=WT / "backend",
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _self_heal() -> list[str]:
    """启动即自愈：还原**上一次跑残留的**变异体。

    ⛔ 这一层不是冗余。实测教训：装了 SIGTERM handler 也**不够** —— 外部超时
    杀的是整个进程组，handler 还没来得及等 `subprocess.run` 返回就被终止，
    `finally` 的还原没跑完，`MAX_VALUE_DEPTH = 10**9` 就留在了生产文件里。
    无论 finally 和信号处理写得多小心，外部 kill 总可能发生；唯一可靠的兜底
    是**下一次启动时先检查并还原**。
    """
    healed = []
    for mid, _desc, target, old, new, _gate in MUTATIONS:
        src = target.read_text(encoding="utf-8")
        if new in src:
            target.write_text(src.replace(new, old, 1), encoding="utf-8")
            healed.append(f"{mid} @ {target.name}")
    return healed


def main() -> int:
    _install_signal_handlers()
    healed = _self_heal()
    if healed:
        print(f"⚠️ 自愈：还原了上一次残留的变异体 {healed}", flush=True)

    # ── 跑前：全文件 sha 基线（对**每个**会被变异的文件，不只是其中一个）──
    touched = sorted({m[2] for m in MUTATIONS}, key=str)
    baseline = {p: _sha(p) for p in touched}
    print("═══ 变异前 sha 基线 ═══", flush=True)
    for p, h in baseline.items():
        print(f"  {h}  {p.relative_to(WT)}", flush=True)

    # ── 绿态前提：变异前每道门必须是绿的，否则「变红」没有意义 ──
    print("\n═══ 绿态前提（变异前每道门必须绿）═══", flush=True)
    for mid, _desc, _f, _old, _new, gate in MUTATIONS:
        rc, _out = _run_gate(gate)
        print(f"  [{mid}] {gate} → rc={rc} {'✅' if rc == 0 else '❌ 前提不成立'}", flush=True)
        if rc != 0:
            print(f"⛔ {mid} 的门在变异前就不是绿的，变异结果无意义。中止。", flush=True)
            return 2

    results = []
    print("\n═══ 变异（串行）═══", flush=True)
    for mid, desc, target, old, new, gate in MUTATIONS:
        src = target.read_text(encoding="utf-8")
        if src.count(old) != 1:
            print(f"  [{mid}] ⛔ 锚文本在 {target.name} 中出现 {src.count(old)} 次（须恰好 1 次）— 跳过", flush=True)
            results.append((mid, gate, "ANCHOR-ERROR", desc))
            continue
        try:
            target.write_text(src.replace(old, new, 1), encoding="utf-8")
            rc, out = _run_gate(gate)
            # KILLED 判据：rc 恰为 1（测试失败），且失败的是**指定的那一条**
            killed = rc == 1 and (f"{gate}" in out) and ("1 failed" in out or "failed" in out)
            verdict = "KILLED" if killed else f"SURVIVED(rc={rc})"
            print(f"  [{mid}] {desc}\n        {gate} → rc={rc} ⇒ {verdict}", flush=True)
            if not killed:
                print(
                    f"        ⚠️ 输出尾部: {out.strip().splitlines()[-1][:160] if out.strip() else '(空)'}", flush=True
                )
            results.append((mid, gate, verdict, desc))
        finally:
            # ⛔ 无条件还原。不加任何「文件被第三方改过就别覆盖」的防护——
            # 那种防护会在 exit 时把变异体留在生产文件里。
            target.write_text(src, encoding="utf-8")

    # ── 跑后：逐个复核 sha（外部的、全量的判据，不依赖变异体配合）──
    print("\n═══ 变异后 sha 复核 ═══", flush=True)
    dirty = []
    for p, h0 in baseline.items():
        h1 = _sha(p)
        ok = h0 == h1
        print(f"  {'✅' if ok else '⛔'} {p.relative_to(WT)}  {h1}", flush=True)
        if not ok:
            dirty.append(p)

    print("\n═══ 汇总 ═══", flush=True)
    for mid, gate, verdict, desc in results:
        print(f"  {mid:4} {verdict:16} {gate}", flush=True)
    n_killed = sum(1 for _, _, v, _ in results if v == "KILLED")
    print(f"\n  {n_killed}/{len(MUTATIONS)} KILLED", flush=True)
    if dirty:
        print(f"⛔ 有文件未还原：{[str(p) for p in dirty]}", flush=True)
        return 3
    return 0 if n_killed == len(MUTATIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
