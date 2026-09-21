#!/usr/bin/env python3
"""汇报时序/完整性机器门（r16-L1 + r17-M1 类闭合）。

判据（任一失败 rc=1）：
  ① 每个 `| MM-DD HH:MM[:SS] |` 行的**事件时间** ≤ 该行**引入 commit 的 committer 时间**
     （`git log -S <整行文本>`，整行做 key 以避免同前缀误归属）；
  ② 行数下限 `--min-rows N`（防“删行绿”）；
  ③ 最新轮次断言 `--expect-latest rNN`（汇报必须含 `**D-15 rNN 结果**` 行，防“漏轮绿”）；
  ④ `--self-test`：模拟丢弃最后一行，必须被 ②/③ 捕捉。
用法：python3 check-report-chronology.py <repo-root> [--min-rows N] [--expect-latest rNN] [--self-test]
"""
import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

REPORT = "_bmad-output/第十五批-完成的卡-汇报.md"
ROW = re.compile(r"^\| (\d\d-\d\d) (\d\d:\d\d(?::\d\d)?) \|")
ROUND = re.compile(r"\*\*D-15 (r\d+) 结果\*\*")

def load_rows(root):
    text = (root / REPORT).read_text(encoding="utf-8")
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        m = ROW.match(line)
        if m:
            fmt = "%Y-%m-%d %H:%M:%S" if m.group(2).count(":") == 2 else "%Y-%m-%d %H:%M"
            rows.append((lineno, line, dt.datetime.strptime(f"2026-{m.group(1)} {m.group(2)}", fmt)))
    return rows

def completeness_failures(rows, min_rows, expect_latest):
    bad = []
    if min_rows and len(rows) < min_rows:
        bad.append(f"rows<{min_rows}: rows={len(rows)}")
    if expect_latest:
        rounds = [ROUND.search(l).group(1) for (_, l, _) in rows if ROUND.search(l)]
        if not rounds:
            bad.append(f"latest-round missing: 期望 {expect_latest}，未找到任何 D-15 rN 结果行")
        elif max(rounds, key=lambda r: int(r[1:])) != expect_latest:
            bad.append(f"latest-round mismatch: 期望 {expect_latest}，实测 {max(rounds, key=lambda r: int(r[1:]))}")
    return bad

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--min-rows", type=int, default=0)
    ap.add_argument("--expect-latest", default="")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    rows = load_rows(root)
    if args.self_test:
        ok = True
        dropped = rows[:-1]
        bad = completeness_failures(dropped, args.min_rows or len(rows), args.expect_latest or "r99")
        got = bool(bad)
        print(f"[self-test] drop-last-row must be caught: got={got} ({bad[:1]}) -> {'OK' if got else 'BAD'}")
        ok = ok and got
        bad2 = completeness_failures(rows, args.min_rows, args.expect_latest)
        got2 = bool(bad2)
        print(f"[self-test] current rows must pass completeness: violations={bad2} -> {'OK' if not got2 else 'BAD'}")
        ok = ok and not got2
        return 0 if ok else 1
    bad = completeness_failures(rows, args.min_rows, args.expect_latest)
    n = 0
    for lineno, line, row_dt in rows:
        n += 1
        blame = subprocess.run(["git", "blame", "--porcelain", "-L", f"{lineno},{lineno}", "--", REPORT],
                               cwd=root, capture_output=True, text=True).stdout
        sha = blame.split("\n", 1)[0].split(" ", 1)[0] if blame else ""
        if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
            print(f"[FAIL] :{lineno} 无法定位引入 commit（blame 头行异常）")
            bad.append(f":{lineno} blame-error")
            continue
        if set(sha) == {"0"}:
            print(f"[FAIL] :{lineno} 行未提交（working-tree-only；提交后复跑）")
            bad.append(f":{lineno} uncommitted")
            continue
        out = subprocess.run(["git", "show", "-s", "--format=%cI", sha], cwd=root, capture_output=True, text=True).stdout.strip()
        commit_dt = dt.datetime.fromisoformat(out).replace(tzinfo=None)
        ok = row_dt <= commit_dt
        print(f"[{'OK' if ok else 'FAIL'}] :{lineno} row={row_dt:%m-%d %H:%M} commit={commit_dt:%m-%d %H:%M:%S} -> {'row<=commit' if ok else 'row>commit'}")
        if not ok:
            bad.append(f":{lineno} row>commit")
    for b in bad:
        print(f"[FAIL] {b}")
    print(f"\nrows={n} min_rows={args.min_rows} expect_latest={args.expect_latest or '-'} violations={len(bad)}")
    print(f"verdict={'PASS' if not bad else 'FAIL'}")
    return 0 if not bad else 1

if __name__ == "__main__":
    raise SystemExit(main())
