#!/usr/bin/env python3
"""SHELLOPTS=noexec 假绿的「先红 / 调用方自证后绿」实测（卡文 (g)(h)）。

为什么用 Python 跑：`SHELLOPTS=noexec` 让 bash 只解析不执行，**任何 bash 调用方
自己也会被噎死**，所以断言必须落在免疫 noexec 的进程里（Python / make / pytest）。
本文件既是判据，也是验收单里「调用方自证断言」Python 版的原文。

用法: python3 noexec_contract.py <门绝对路径>
退出码: 0 = 契约成立
"""

import os
import re
import subprocess
import sys
import tempfile

VERDICT_PREFIX = "RUNTIME-FILES:"
#: ⛔ **整行**精确匹配。只判 `RUNTIME-FILES:` 子串会把 `RUNTIME-FILES: GATE-BROKEN …`
#: 当成结论——那是门损坏，不是门给了结论（Codex round-1 MEDIUM-1）。
VERDICT_RE = re.compile(r"^RUNTIME-FILES: (unchanged|CHANGED)$", re.M)


def caller_assert(stdout_stderr: str) -> int:
    """调用方自证断言：门必须自报**合法结论行**；没有 ⇒ 门没跑或已损坏 ⇒ 判红。

    ⛔ 只看 rc 的调用方在 SHELLOPTS=noexec 下会把「门压根没跑」读成「通过」。
    ⛔ 本断言**不替代** rc：有结论行只说明门跑到了终点，过没过仍要传播 rc。
    """
    return 0 if VERDICT_RE.search(stdout_stderr) else 1


def caller_exit_code(proc: subprocess.CompletedProcess) -> int:
    """完整调用方语义：先要求结论行，再原样传播门的 rc。"""
    if caller_assert(proc.stdout + proc.stderr):
        return 1
    return proc.returncode


def make_fake_backend(gate: str, tmp: str) -> str:
    """搭一个最小 fake backend，让对照跑的结论确定是 unchanged（不受真实树并发影响）。"""
    for sub in ("backend/app/data", "backend/data", "backend/tests", "backend/scripts"):
        os.makedirs(os.path.join(tmp, sub), exist_ok=True)
    with open(os.path.join(tmp, "backend/app/main.py"), "w", encoding="utf-8") as fh:
        fh.write("# fake\n")
    dst = os.path.join(tmp, "backend/scripts/lifespan_isolation_runtime_sha.sh")
    with open(gate, "rb") as src, open(dst, "wb") as out:
        out.write(src.read())
    return dst


def main() -> int:
    gate = sys.argv[1]
    failures = []

    # ── 断言自身的验伪锚：不是恒红也不是恒绿 ──────────────────────────────
    cases = [
        ("空输出", "", 1),
        ("unchanged", "RUNTIME-FILES: unchanged\n", 0),
        ("CHANGED", "RUNTIME-FILES: CHANGED\n", 0),
        # Codex round-1 MEDIUM-1 的三个负例：宽判据会把它们全判成「门给了结论」
        ("GATE-BROKEN", "RUNTIME-FILES: GATE-BROKEN — 固定监视项有 3 个, 期望 5 个\n", 1),
        ("前缀碎片", "RUNTIME-FILES: unchanged-ish\n", 1),
        ("行内非行首", "foo RUNTIME-FILES: unchanged\n", 1),
        ("快照表头（含 RUNTIME-FILES 但无冒号结论）", "=== RUNTIME-FILES before (x) ===\n", 1),
    ]
    got = {n: caller_assert(s) for n, s, _ in cases}
    print("[断言验伪锚] " + "  ".join(
        f"{n}={got[n]}(期望{w})" for n, _, w in cases))
    for n, _, want in cases:
        if got[n] != want:
            failures.append(f"caller_assert 对「{n}」判 {got[n]}，期望 {want}")

    # rc 传播（一）：函数级——手工构造的结果对象，只证 caller_exit_code 的算术
    # ⚠️ 这一组**不是**端到端证据（Codex round-2 LOW-2），端到端那组在下面 main() 里。
    fake_changed = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="RUNTIME-FILES: CHANGED\n", stderr="")
    fake_ok = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="RUNTIME-FILES: unchanged\n", stderr="")
    fake_cmdrc = subprocess.CompletedProcess(
        args=[], returncode=7, stdout="RUNTIME-FILES: unchanged\n", stderr="")
    rc_got = (caller_exit_code(fake_changed), caller_exit_code(fake_ok),
              caller_exit_code(fake_cmdrc))
    print(f"[rc 传播·函数级(人工结果对象)] CHANGED→{rc_got[0]}(期望1) "
          f"unchanged→{rc_got[1]}(期望0) 被包裹命令 rc=7→{rc_got[2]}(期望7)")
    if rc_got != (1, 0, 7):
        failures.append("caller_exit_code 没有原样传播门的 rc")

    # ── (g) 先红：SHELLOPTS=noexec ⇒ 门没跑、rc=0、零结论行 ────────────────
    env = dict(os.environ, SHELLOPTS="noexec")
    p = subprocess.run(["bash", gate, "--", "/usr/bin/true"],
                       capture_output=True, text=True, env=env)
    both = p.stdout + p.stderr
    no_verdict = VERDICT_PREFIX not in both
    print(f"[g 先红·真门] rc={p.returncode} no_verdict={no_verdict} out_len={len(both)}")
    if not (p.returncode == 0 and no_verdict):
        failures.append("noexec 先红前提不成立（门在 noexec 下不该产出结论行）")

    # ── (h) 后绿：断言对 noexec 输出判红 ────────────────────────────────
    a_noexec = caller_assert(both)
    print(f"[h 后绿·断言(noexec输出)] = {a_noexec} (期望 1)")
    if a_noexec != 1:
        failures.append("断言未能把 noexec 的空输出判红")

    # ── (h) 对照：正常 run（fake-backend，结论确定 unchanged）⇒ 断言放行 ───
    #    ⛔ 对照跑**必须**落在 fake-backend：真实树上有并发 pytest 长跑时，真门可能
    #       如实判 CHANGED，对照就不再是「确定 unchanged」的干净参照。
    sh_caller = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "noexec_caller_assert.sh")
    with tempfile.TemporaryDirectory() as tmp:
        dst = make_fake_backend(gate, tmp)
        q = subprocess.run(["bash", dst, "--", "/usr/bin/true"],
                           capture_output=True, text=True)
        okboth = q.stdout + q.stderr
        a_ok = caller_assert(okboth)
        has_unchanged = "RUNTIME-FILES: unchanged" in okboth
        print(f"[h 对照·正常run] rc={q.returncode} has_unchanged={has_unchanged} "
              f"断言={a_ok} (期望 rc=0 / True / 0)")
        if not (q.returncode == 0 and has_unchanged and a_ok == 0):
            failures.append("正常 run 下断言不放行（断言恒红 = 没用的门）")

        # ── rc 传播（二）：**端到端**——真跑门包一条 `exit 7`，看外层进程退出码 ──
        #    Codex round-2 LOW-2：上面那组是函数级人工结果对象，证不了端到端。
        #    这里起一个真的子 Python，让它按配方判据跑真门，再看它自己的退出码。
        runner = os.path.join(tmp, "e2e_caller.py")
        with open(runner, "w", encoding="utf-8") as fh:
            fh.write(
                "import re, subprocess, sys\n"
                "VERDICT = re.compile(r'^RUNTIME-FILES: (unchanged|CHANGED)$', re.M)\n"
                "p = subprocess.run(['bash', sys.argv[1], '--', '/bin/sh', '-c',\n"
                "                    'exit 7'], capture_output=True, text=True)\n"
                "sys.stderr.write(f'gate_rc={p.returncode}\\n')\n"
                "if not VERDICT.search(p.stdout + p.stderr):\n"
                "    raise SystemExit(1)\n"
                "raise SystemExit(p.returncode)\n")
        e2e = subprocess.run([sys.executable, runner, dst],
                             capture_output=True, text=True)
        print(f"[rc 传播·端到端] 门包 `exit 7` ⇒ 外层调用方进程退出码="
              f"{e2e.returncode}（期望 7）  门自身 rc: {e2e.stderr.strip()}")
        if e2e.returncode != 7:
            failures.append(
                f"端到端 rc 传播失败：外层退出码 {e2e.returncode}，期望 7")
        # 端到端验伪锚：换成哑门（rc=0 零输出）⇒ 外层必须退 1，而不是 0
        dud_e2e = os.path.join(tmp, "dud_gate_e2e.sh")
        with open(dud_e2e, "w", encoding="utf-8") as fh:
            fh.write("#!/usr/bin/env bash\nexit 0\n")
        e2e_dud = subprocess.run([sys.executable, runner, dud_e2e],
                                 capture_output=True, text=True)
        print(f"[rc 传播·端到端验伪锚] 哑门(rc=0 零输出) ⇒ 外层退出码="
              f"{e2e_dud.returncode}（期望 1，不是 0）")
        if e2e_dud.returncode != 1:
            failures.append(
                f"端到端验伪锚失败：哑门下外层退出码 {e2e_dud.returncode}，期望 1")

        # ── 如实登记：bash 版调用方在同一 noexec 环境下自己也不执行 ─────────
        if os.path.exists(sh_caller):
            r_noexec = subprocess.run(["bash", sh_caller, dst],
                                      capture_output=True, text=True, env=env)
            r_plain = subprocess.run(["bash", sh_caller, dst],
                                     capture_output=True, text=True)
            print(f"[shell 版·同一 noexec 环境] rc={r_noexec.returncode} "
                  f"out_len={len(r_noexec.stdout + r_noexec.stderr)} "
                  f"← 如实登记：bash 调用方自己也被 noexec 噎死，"
                  f"故常驻断言必须落在非 bash 进程")
            print(f"[shell 版·正常环境] rc={r_plain.returncode} "
                  f"stdout={r_plain.stdout.strip()!r} (期望 rc=0 且放行)")
            if r_plain.returncode != 0:
                failures.append("shell 版断言在正常环境下不放行")
            # shell 版的验伪锚：门被换成一个「什么都不打印」的壳 ⇒ 必须判红
            dud = os.path.join(tmp, "dud_gate.sh")
            with open(dud, "w", encoding="utf-8") as fh:
                fh.write("#!/usr/bin/env bash\nexit 0\n")
            r_dud = subprocess.run(["bash", sh_caller, dud],
                                   capture_output=True, text=True)
            print(f"[shell 版·验伪锚(哑门 rc=0 零输出)] rc={r_dud.returncode} "
                  f"(期望 != 0)")
            if r_dud.returncode == 0:
                failures.append("shell 版断言放行了「rc=0 但零结论行」的哑门")
        else:
            failures.append(f"缺 shell 版断言文件 {sh_caller}")

    if failures:
        for f in failures:
            print(f"!! {f}")
        print("NOEXEC-CONTRACT: FAIL")
        return 1
    print("NOEXEC-CONTRACT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
