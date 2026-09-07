#!/usr/bin/env python3
"""CARD-RV-W4-4 (d)③ —— HIGH-1 整改的独立复现（新旧两树对照）。

[BATCH-2026-09-07-第十三批 / CARD-RV-W4-4]

复现 Y7-A 的 Codex round-1 HIGH-1 所述三步，并在**当前 HEAD** 与**审查当时的形态**
上各跑一次，看结论是否翻转：

    Codex 原话（存档 :14-22）：
    「安装成功→替换 seam 为抛异常函数→发送受拦审计事件→捕获异常，
      得到 blocked=0, unaccounted=0，子进程退出 0。」

⛔ **本脚本只放 `_bmad-output`，不进代码树；不建立任何真实连接**——受拦事件由
   ``sys.audit("socket.connect", None, ("127.0.0.1", 7691))`` 合成，与契约
   ``test_live_port_guard_contract.py:902`` 的手法相同。禁连 7691/7687。

## 为什么对照树不是 `93d47028`

卡文 (d)③ 写「旧行为需在 ``93d47028`` 树上用同一脚本对照复现一次」。**该口径在本树
不可执行**，本脚本用 mode=parent 把它实测出来：

    git show 93d47028:backend/tests/support/live_port_guard.py | grep -c '_finalize_race_seam'
    → 0        （RECORD_LATE 同样 0，finalize_and_snapshot 同样 0）

注入点 seam 是 **Y7-A 本卡引入的**，父提交里根本没有它。在 `93d47028` 上跑同一脚本
只会得到 ``AttributeError: module has no attribute '_finalize_race_seam_hook'``——
那与 Codex 描述的失败模式（记账被跳过）毫无关系，把它当成「旧行为复现」就是拿
一个无关的失败冒充对照。

Codex 审的是**工作区**（`03ac8bf8` + 本卡 round-1 diff），那个形态**没有任何 commit
承载**。所以真正同构的对照 = 取 HEAD 源码、把 round-1 之后加上的
``try/except BaseException`` 拆掉、恢复裸调用——即「被否掉的那版写法」本身，不是
机械变异。三跑：

    head    当前 HEAD 原文                      期望：记账发生，rc=3
    mutant  HEAD 原文 − try/except（= round-1） 期望：复现 Codex 的 0/0/rc=0
    parent  93d47028 原文                       期望：脚本报「无此注入点，口径不可执行」

## 变异生效自证（防假 SURVIVED / 假 KILLED）

* 替换前断言锚点在源码中**恰好 1 次**（行级，不是子串——12 空格的裸调用行是
  16 空格 try 体内那行的子串，用 ``count()`` 会双向说谎）；
* 替换后 ``ast.parse`` 必须通过（语法不合法的变异体会死在编译期，让门因**别的**
  原因红，冒充击杀）；
* 替换后断言 ``try:`` 块已消失且裸调用**行级**恰好 1 行；
* 变异体写在独立临时目录，**代码树一个字节都不碰**（跑完对 HEAD 文件复核 sha）。
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BACKEND = REPO / "backend"
GUARD_REL = "tests/support/live_port_guard.py"

# round-1 之后加上的保护（HEAD :654-657）。拆掉它 = 回到 Codex 审的那个形态。
TRY_BLOCK = (
    "            try:\n"
    "                _finalize_race_seam_hook()\n"
    "            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流\n"
    "                pass\n"
)
BARE_CALL = "            _finalize_race_seam_hook()\n"

# 子进程：装门 → 替换 seam 为抛异常函数 → 合成受拦审计事件 → 读账本 → 正常返回。
# 进程 rc 由 atexit 里的 _final_accounting 决定，这正是 Codex 判据的那一位。
CHILD = r'''
import json, os, sys, traceback

guard_root = sys.argv[1]
ledger_path = sys.argv[2]
os.environ["W4_GUARD_LEDGER"] = ledger_path
sys.path.insert(0, guard_root)

out = {"stage": "import"}
try:
    from tests.support import live_port_guard as guard
except BaseException as exc:
    out["error"] = f"{type(exc).__name__}: {exc}"
    print("REPRO-JSON: " + json.dumps(out, ensure_ascii=False), flush=True)
    sys.exit(90)

out["stage"] = "install"
try:
    guard.install()
except BaseException as exc:
    out["error"] = f"{type(exc).__name__}: {exc}"
    print("REPRO-JSON: " + json.dumps(out, ensure_ascii=False), flush=True)
    sys.exit(91)

# 步骤 2：把注入点替换成抛异常的函数（Codex 原话的第二步）。
out["stage"] = "replace-seam"
if not hasattr(guard, "_finalize_race_seam_hook"):
    out["error"] = "NO_SEAM: 本树没有 _finalize_race_seam_hook —— 卡文的对照口径在此树不可执行"
    print("REPRO-JSON: " + json.dumps(out, ensure_ascii=False), flush=True)
    sys.exit(92)

exc_kind = sys.argv[3] if len(sys.argv) > 3 else "RuntimeError"
_EXC = {"RuntimeError": RuntimeError, "KeyboardInterrupt": KeyboardInterrupt, "SystemExit": SystemExit}[exc_kind]

def boom():
    raise _EXC("seam 故意抛出（CARD-RV-W4-4 (d)③/④ 注入 " + exc_kind + "）")

guard._finalize_race_seam_hook = boom
out["seam_raises"] = exc_kind

# 步骤 3：合成一次到受拦端口的审计事件。不建立任何真实连接。
out["stage"] = "audit-event"
caught = None
try:
    sys.audit("socket.connect", None, ("127.0.0.1", 7691))
except BaseException as exc:
    caught = f"{type(exc).__name__}: {str(exc)[:120]}"
out["caught"] = caught

# 步骤 4：读账本（进程内快照，不依赖落盘）。
snap = guard.STATE.late_snapshot()
out["stage"] = "done"
out["blocked"] = snap["blocked"]
out["unaccounted"] = snap["unaccounted"]
out["total"] = snap["total"]
print("REPRO-JSON: " + json.dumps(out, ensure_ascii=False), flush=True)
# 正常返回 —— rc 交给 atexit 的 _final_accounting 决定。
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_mutant(dest: Path) -> dict:
    """把 HEAD 的 guard 拷进 dest，并拆掉 seam 调用的 try/except。返回自证信息。"""
    src_root = BACKEND
    (dest / "tests" / "support").mkdir(parents=True, exist_ok=True)
    for rel in ("tests/__init__.py", "tests/support/__init__.py"):
        shutil.copy2(src_root / rel, dest / rel)

    original = (src_root / GUARD_REL).read_text(encoding="utf-8")

    # ── 变异生效自证 ①：锚点唯一（行级，不靠 count 子串）────────────────────
    lines = original.splitlines(keepends=True)
    try_starts = [i for i in range(len(lines) - 3) if "".join(lines[i:i + 4]) == TRY_BLOCK]
    assert len(try_starts) == 1, f"try 块锚点不唯一：{len(try_starts)} 处"
    bare_before = [n for n, ln in enumerate(lines, 1) if ln == BARE_CALL]
    assert not bare_before, f"HEAD 里已存在裸调用行 {bare_before} —— 锚点前提不成立"

    mutated = original.replace(TRY_BLOCK, BARE_CALL)
    assert mutated != original, "替换没有发生"

    # ── 变异生效自证 ②：语法合法（不合法的变异体会死在编译期冒充击杀）───────
    ast.parse(mutated)

    # ── 变异生效自证 ③：try 块消失、裸调用行级恰好 1 行 ────────────────────
    mlines = mutated.splitlines(keepends=True)
    assert not [i for i in range(len(mlines) - 3) if "".join(mlines[i:i + 4]) == TRY_BLOCK], "try 块仍在"
    bare_after = [n for n, ln in enumerate(mlines, 1) if ln == BARE_CALL]
    assert len(bare_after) == 1, f"裸调用行数 = {len(bare_after)}，期望 1"

    (dest / GUARD_REL).write_text(mutated, encoding="utf-8")
    return {
        "try_block_line": try_starts[0] + 1,
        "bare_call_line_after": bare_after[0],
        "head_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest()[:16],
        "mutant_sha256": hashlib.sha256(mutated.encode("utf-8")).hexdigest()[:16],
    }


def build_parent(dest: Path, rev: str) -> dict:
    """把 `rev` 的 guard 取出来放 dest（只读取 git 对象，不切树、不 checkout）。"""
    (dest / "tests" / "support").mkdir(parents=True, exist_ok=True)
    for rel in ("tests/__init__.py", "tests/support/__init__.py", GUARD_REL):
        blob = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{rev}:backend/{rel}"],
            capture_output=True, check=True,
        ).stdout
        (dest / rel).write_bytes(blob)
    text = (dest / GUARD_REL).read_text(encoding="utf-8")
    return {
        "rev": rev,
        "seam_occurrences": text.count("_finalize_race_seam"),
        "record_late_occurrences": text.count("RECORD_LATE"),
        "lines": len(text.splitlines()),
    }


def run(mode: str, guard_root: Path, seam_raises: str = "RuntimeError") -> dict:
    with tempfile.TemporaryDirectory(prefix=f"w4-repro-{mode}-") as td:
        ledger = Path(td) / "ledger.json"
        child = Path(td) / "child.py"
        child.write_text(CHILD, encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            [sys.executable, str(child), str(guard_root), str(ledger), seam_raises],
            capture_output=True, text=True, env=env, timeout=120,
        )
        payload = {}
        for line in proc.stdout.splitlines():
            if line.startswith("REPRO-JSON: "):
                payload = json.loads(line[len("REPRO-JSON: "):])
        ledger_file = None
        if ledger.exists():
            ledger_file = json.loads(ledger.read_text(encoding="utf-8"))
        return {
            "mode": mode,
            "seam_raises": seam_raises,
            "rc": proc.returncode,
            "payload": payload,
            "ledger_file": {
                k: ledger_file[k] for k in ("total", "blocked", "unaccounted") if k in (ledger_file or {})
            } if ledger_file else None,
            "stderr_tail": proc.stderr.strip()[-400:],
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent-rev", default="93d47028")
    ap.add_argument("--workdir", default=None, help="临时目录父路径（默认系统 temp）")
    args = ap.parse_args()

    guard_file = BACKEND / GUARD_REL
    sha_before = sha(guard_file)

    root = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="w4-repro-roots-"))
    root.mkdir(parents=True, exist_ok=True)

    print("=== CARD-RV-W4-4 (d)③ HIGH-1 整改复现（三跑对照）===")
    print(f"    repo      : {REPO}")
    print(f"    guard     : {guard_file}")
    print(f"    sha(before): {sha_before[:16]}")
    print()

    results = []

    # ── 跑 1：HEAD 原文 ─────────────────────────────────────────────────────
    results.append(run("head", BACKEND))

    # ── 跑 2：HEAD − try/except（= Codex 审的 round-1 形态）─────────────────
    mut_root = root / "mutant"
    selfcheck = build_mutant(mut_root)
    print(f"[变异自证] try 块起于 HEAD :{selfcheck['try_block_line']}；"
          f"变异体裸调用在 :{selfcheck['bare_call_line_after']}；"
          f"sha {selfcheck['head_sha256']} → {selfcheck['mutant_sha256']}")
    results.append(run("mutant", mut_root))

    # ── 跑 3：父提交原文（卡文口径的可执行性实测）───────────────────────────
    par_root = root / "parent"
    parent_info = build_parent(par_root, args.parent_rev)
    print(f"[父树事实] {parent_info['rev']}: _finalize_race_seam 出现 "
          f"{parent_info['seam_occurrences']} 次 / RECORD_LATE {parent_info['record_late_occurrences']} 次 "
          f"/ {parent_info['lines']} 行")
    results.append(run("parent", par_root))

    # ── 跑 4/5：(d)④ —— `except BaseException` 吞掉的是不是只有「注入点的异常」──
    #    推理说它会吞 KeyboardInterrupt / SystemExit；推理不算证据，实际打一发看
    #    记账与 rc 有没有被这两种 BaseException 改掉（「代码机制 ≠ 观测到的失败」）。
    results.append(run("head-kbint", BACKEND, seam_raises="KeyboardInterrupt"))
    results.append(run("head-sysexit", BACKEND, seam_raises="SystemExit"))
    print()

    for r in results:
        p = r["payload"]
        print(f"--- mode={r['mode']} ---")
        print(f"    rc            = {r['rc']}")
        print(f"    stage         = {p.get('stage')}")
        if p.get("error"):
            print(f"    error         = {p['error']}")
        else:
            print(f"    caught        = {p.get('caught')}")
            print(f"    blocked       = {p.get('blocked')}  unaccounted = {p.get('unaccounted')}  total = {p.get('total')}")
        print(f"    ledger_file   = {r['ledger_file']}")
        if r["stderr_tail"]:
            print(f"    stderr_tail   = {r['stderr_tail'][:200]}")
    print()

    by = {r["mode"]: r for r in results}
    head, mut, par = by["head"], by["mutant"], by["parent"]
    kbi, sxe = by["head-kbint"], by["head-sysexit"]

    # ── 判据（每条都要能翻转，不是「没报错就算过」）──────────────────────────
    checks = []
    checks.append((
        "head 记账未被跳过（blocked≥1 且 unaccounted≥1）",
        head["payload"].get("blocked", 0) >= 1 and head["payload"].get("unaccounted", 0) >= 1,
        f"blocked={head['payload'].get('blocked')} unaccounted={head['payload'].get('unaccounted')}",
    ))
    checks.append((
        "head 不再是 Codex 原话的 (0, 0, rc=0)",
        not (head["payload"].get("blocked") == 0 and head["payload"].get("unaccounted") == 0 and head["rc"] == 0),
        f"(blocked={head['payload'].get('blocked')}, unaccounted={head['payload'].get('unaccounted')}, rc={head['rc']})",
    ))
    checks.append((
        "head 仍对调用方抛出（拦截语义未被 try 吞掉）",
        (head["payload"].get("caught") or "").startswith("RuntimeError"),
        f"caught={head['payload'].get('caught')}",
    ))
    checks.append((
        "mutant 复现 Codex 原话 blocked=0, unaccounted=0, rc=0",
        mut["payload"].get("blocked") == 0 and mut["payload"].get("unaccounted") == 0 and mut["rc"] == 0,
        f"(blocked={mut['payload'].get('blocked')}, unaccounted={mut['payload'].get('unaccounted')}, rc={mut['rc']})",
    ))
    checks.append((
        "两跑结论确实翻转（对照有效，不是两边都绿）",
        head["payload"].get("blocked") != mut["payload"].get("blocked"),
        f"head.blocked={head['payload'].get('blocked')} vs mutant.blocked={mut['payload'].get('blocked')}",
    ))
    checks.append((
        f"parent {args.parent_rev} 无此注入点 ⇒ 卡文对照口径不可执行",
        (par["payload"].get("error") or "").startswith("NO_SEAM"),
        f"error={par['payload'].get('error')}",
    ))
    # (d)④：BaseException 的两个子类同样只被吞在 seam 内，不改记账、不改 rc。
    for label, res in (("KeyboardInterrupt", kbi), ("SystemExit", sxe)):
        checks.append((
            f"seam 抛 {label} 仍照常记账且 rc=3（吞的只是注入点，不是承重路径）",
            res["payload"].get("blocked") == 1 and res["payload"].get("unaccounted") == 1 and res["rc"] == 3,
            f"(blocked={res['payload'].get('blocked')}, unaccounted={res['payload'].get('unaccounted')}, rc={res['rc']})",
        ))
        checks.append((
            f"seam 抛 {label} 时调用方收到的仍是**拦截**异常，不是注入的那个",
            (res["payload"].get("caught") or "").startswith("RuntimeError")
            and "受拦端口" in (res["payload"].get("caught") or ""),
            f"caught={(res['payload'].get('caught') or '')[:60]}",
        ))

    checks.append((
        "代码树未被本脚本改动（sha 逐字节一致）",
        sha(guard_file) == sha_before,
        f"{sha(guard_file)[:16]} vs {sha_before[:16]}",
    ))

    ok = True
    for name, passed, detail in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}  ({detail})")
        ok &= passed

    print()
    if not args.workdir:
        shutil.rmtree(root, ignore_errors=True)
    print(f"HIGH1-REPRO: {'PASS' if ok else 'FAIL'} — {sum(1 for _, p, _ in checks if p)}/{len(checks)} 条判据成立")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
