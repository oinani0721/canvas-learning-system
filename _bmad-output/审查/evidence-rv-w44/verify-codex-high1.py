#!/usr/bin/env python3
"""CARD-RV-W4-4 —— 独立验证本卡外审 Codex 的 HIGH-1（不采信片段实验，跑完整 guard）。

[BATCH-2026-09-07-第十三批 / CARD-RV-W4-4]

Codex 的主张（`codex-review-CARD-RV-W4-4.md` :5-20）：

    `_final_accounting` 里 `write_ledger()` 抛异常后走到
        1280: except Exception as exc:
        1281:     print(f"*** W4 guard: 账本落盘失败 ...", file=sys.stderr)
    这条 print **在 :1291-1303 的保护块之外**。stderr 若也坏了，它抛出的异常会越过
    :1288 的退出判定与 :1304 的 os._exit ⇒ 有未结账拦截却 rc=0。

    Codex 自述：「独立片段实验……得到 rc=0。没有实际写盘。**完整 guard 与真实文件系统
    故障组合未验证**。」

本脚本补上它没做的那一半：**用完整 guard + 真实文件系统故障**跑一次。

## 故障怎么来（不 monkeypatch，用真实 I/O 错误）

`W4_GUARD_LEDGER` 指向一个**目录**。`write_ledger` 的 `open(path, "w")` 会抛
`IsADirectoryError`（`OSError` 子类，被 `:1280 except Exception` 接住）——这是真实的
文件系统故障，不是替换出来的假异常。

## stderr 怎么坏（时序）

`atexit` 是 LIFO。`install()` 里 `register_final_accounting()` 先注册；本脚本随后再注册
一个「弄坏 stderr」的回调 ⇒ 它**先**跑，`_final_accounting` 跑时 stderr 已经坏了。

## 三跑对照（判据要能翻转，不是「没报错就算过」）

    A  ledger 指向目录 + stderr 坏   期望（若 Codex 成立）rc=0 —— 缺陷复现
    B  ledger 指向目录 + stderr 正常 期望 rc=3 —— 证明「落盘失败」本身不阻断退出
    C  ledger 正常     + stderr 坏   期望 rc=3 —— 证明「stderr 坏」本身已被 :1291 保护住

只有 A 红而 B、C 绿，才说明缺陷**恰好**在「两个条件同时成立」那一格，
而不是「随便坏一个就退不出去」（那会是另一个更大的问题，也会让 A 的结论失去指向性）。

⛔ 本脚本只放 `_bmad-output`，不进代码树；不建立任何真实连接（受拦事件由 `sys.audit` 合成）。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BACKEND = REPO / "backend"
GUARD = BACKEND / "tests/support/live_port_guard.py"

CHILD = r'''
import atexit, io, json, os, sys

backend = sys.argv[1]
ledger_path = sys.argv[2]
break_stderr = sys.argv[3] == "1"

os.environ["W4_GUARD_LEDGER"] = ledger_path
sys.path.insert(0, backend)

from tests.support import live_port_guard as guard

guard.install()          # 内部 register_final_accounting()：先注册 ⇒ 后跑

if break_stderr:
    # atexit LIFO：本回调后注册 ⇒ 先跑 ⇒ _final_accounting 执行时 stderr 已坏。
    def _break():
        broken = io.StringIO()
        broken.close()
        sys.stderr = broken
    atexit.register(_break)

# 合成一条到受拦端口的审计事件，让账本里有一条未结账拦截（不建立真实连接）。
try:
    sys.audit("socket.connect", None, ("127.0.0.1", 7691))
except BaseException as exc:
    pass

snap = guard.STATE.late_snapshot()
print("CHILD-JSON: " + json.dumps(
    {"blocked": snap["blocked"], "unaccounted": snap["unaccounted"], "total": snap["total"]},
    ensure_ascii=False), flush=True)
# 正常返回 —— rc 完全交给 atexit 的 _final_accounting 决定。
'''


def run(label: str, ledger_is_dir: bool, break_stderr: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix="w4-verify-high1-") as td:
        td_path = Path(td)
        child = td_path / "child.py"
        child.write_text(CHILD, encoding="utf-8")
        if ledger_is_dir:
            ledger = td_path / "ledger_as_dir"
            ledger.mkdir()                      # open(path,"w") → IsADirectoryError
        else:
            ledger = td_path / "ledger.json"
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            [sys.executable, str(child), str(BACKEND), str(ledger), "1" if break_stderr else "0"],
            capture_output=True, text=True, env=env, timeout=120,
        )
        payload = {}
        for line in proc.stdout.splitlines():
            if line.startswith("CHILD-JSON: "):
                payload = json.loads(line[len("CHILD-JSON: "):])
        return {
            "label": label,
            "rc": proc.returncode,
            "in_process": payload,
            "stderr_tail": proc.stderr.strip()[-300:],
        }


def main() -> int:
    sha_before = hashlib.sha256(GUARD.read_bytes()).hexdigest()
    print("=== 独立验证 Codex 本卡 HIGH-1（完整 guard + 真实文件系统故障）===")
    print(f"    guard      : {GUARD}")
    print(f"    sha(before): {sha_before[:16]}")
    print()

    a = run("A  ledger=目录 + stderr 坏", ledger_is_dir=True, break_stderr=True)
    b = run("B  ledger=目录 + stderr 正常", ledger_is_dir=True, break_stderr=False)
    c = run("C  ledger=正常 + stderr 坏", ledger_is_dir=False, break_stderr=True)

    for r in (a, b, c):
        print(f"--- {r['label']} ---")
        print(f"    rc          = {r['rc']}")
        print(f"    进程内账本   = {r['in_process']}")
        if r["stderr_tail"]:
            print(f"    stderr_tail = {r['stderr_tail'][:200]}")
    print()

    checks = [
        ("三跑的进程内账本都记到了那条拦截（前提成立，否则后面全无意义）",
         all(r["in_process"].get("blocked") == 1 and r["in_process"].get("unaccounted") == 1
             for r in (a, b, c)),
         f"A={a['in_process']} B={b['in_process']} C={c['in_process']}"),
        ("B：只有落盘失败时仍 rc=3（落盘失败本身不阻断强制退出）",
         b["rc"] == 3, f"rc={b['rc']}"),
        ("C：只有 stderr 坏时仍 rc=3（:1291-1303 的保护块在位）",
         c["rc"] == 3, f"rc={c['rc']}"),
        ("A：两者同时成立时 rc=0 —— Codex 的 HIGH-1 复现",
         a["rc"] == 0, f"rc={a['rc']}"),
        ("A 与 B/C 结论确实不同（缺陷落在那一格，不是随便坏一个就退不出去）",
         a["rc"] != b["rc"] and a["rc"] != c["rc"],
         f"A={a['rc']} B={b['rc']} C={c['rc']}"),
        ("代码树未被本脚本改动",
         hashlib.sha256(GUARD.read_bytes()).hexdigest() == sha_before, "sha 一致"),
    ]

    ok = True
    for name, passed, detail in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}  ({detail})")
        ok &= passed

    print()
    verdict = "CONFIRMED" if a["rc"] == 0 else "NOT-REPRODUCED"
    print(f"VERIFY-CODEX-HIGH1: {verdict} — {sum(1 for _, p, _ in checks if p)}/{len(checks)} 条判据成立")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
