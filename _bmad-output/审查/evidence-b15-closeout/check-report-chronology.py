#!/usr/bin/env python3
"""汇报时序机器门（r16-L1 类闭合）。

判据：`第十五批-完成的卡-汇报.md` 每个 `| MM-DD HH:MM[:SS] |` 行的**事件时间**
必须 ≤ 该行的**引入 commit committer 时间**（`git log -S <行首 60 字符>`）。
退出码：0 = 全过；1 = 存在负时序（逐条打印）。用法：python3 check-report-chronology.py <repo-root>
"""
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
REPORT = "_bmad-output/第十五批-完成的卡-汇报.md"
ROW = re.compile(r"^\| (\d\d-\d\d) (\d\d:\d\d(?::\d\d)?) \|")

def main() -> int:
    text = (ROOT / REPORT).read_text(encoding="utf-8")
    bad = 0
    n = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        m = ROW.match(line)
        if not m:
            continue
        n += 1
        fmt = "%Y-%m-%d %H:%M:%S" if m.group(2).count(":") == 2 else "%Y-%m-%d %H:%M"
        row_dt = dt.datetime.strptime(f"2026-{m.group(1)} {m.group(2)}", fmt)
        key = line[:60]
        out = subprocess.run(["git", "log", "--format=%cI", "-1", "-S", key, "--", REPORT],
                             cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if not out:
            print(f"[FAIL] :{lineno} 无法定位引入 commit（key={key!r}）")
            bad += 1
            continue
        commit_dt = dt.datetime.fromisoformat(out).replace(tzinfo=None)  # %cI 带本地偏移；两侧均按本地墙钟比
        ok = row_dt <= commit_dt
        print(f"[{'OK' if ok else 'FAIL'}] :{lineno} row={row_dt:%m-%d %H:%M} commit={commit_dt:%m-%d %H:%M:%S} -> {'row<=commit' if ok else 'row>commit'}")
        if not ok:
            bad += 1
    print(f"\nrows={n} violations={bad}\nverdict={'PASS' if bad == 0 else 'FAIL'}")
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
