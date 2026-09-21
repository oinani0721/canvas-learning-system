#!/usr/bin/env python3
"""汇报时序/完整性机器门 v3（r16-L1 + r17-M1 + r18-M1/L1 类闭合）。

判据（任一失败 rc=1）：
  ① 每 `| MM-DD HH:MM[:SS] |` 行的**事件时间** ≤ 该行**引入 commit 的 committer 时间**
     （归属 = `git blame --porcelain -L <行号>,<行号>` 逐行定位；行未提交 ⇒ 红）；
  ② `--min-rows N`：行数下限（防删行）；
  ③ `--expect-latest rNN`：现存 `**D-15 rNN 结果**` 轮次的**最大值**必须 = rNN（防漏最新轮）；
  ④ `--min-round rM`：最早标记轮次必须 = rM；且轮次序号**连续无缺、无重复**（防“删中间轮+复制另轮”置换）；
  ⑤ `--expect-rows-sha256 <hex>`：全部行文本 `"\n".join(rows)` 的 sha256 必须 = 给定值（行集合/内容冻结）；
  ⑥ `--expect-next rNN`：报告须含 `rNN 绑整改档待跑` 指针（报告↔待跑状态对账）；
  ⑦ `--self-test`：内存模拟 (a) 丢最后一行 (b) 删中间轮+复制另一轮 (c) 行集合哈希篡改，
     三类都必须被 ②③④⑤ 的相应守卫捕捉。
用法：python3 check-report-chronology.py <repo-root> [--min-rows N] [--min-round rM] [--expect-latest rNN]
      [--expect-rows-sha256 HEX] [--expect-next rNN] [--self-test]
"""
import argparse
import datetime as dt
import hashlib
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
    return text, rows

def rows_sha256(rows):
    return hashlib.sha256("\n".join(l for (_, l, _) in rows).encode("utf-8")).hexdigest()

def round_nums(rows):
    return [int(ROUND.search(l).group(1)[1:]) for (_, l, _) in rows if ROUND.search(l)]

def completeness_failures(rows, text, min_rows, min_round, expect_latest, expect_rows_sha256, expect_next):
    bad = []
    if min_rows and len(rows) < min_rows:
        bad.append(f"rows<{min_rows}: rows={len(rows)}")
    nums = round_nums(rows)
    if min_round:
        want_min = int(min_round[1:])
        if not nums or min(nums) != want_min:
            bad.append(f"min-round mismatch: 期望 {min_round}，实测 {('r' + str(min(nums))) if nums else '无'}")
    if expect_latest:
        want = int(expect_latest[1:])
        if not nums or max(nums) != want:
            bad.append(f"latest-round mismatch: 期望 {expect_latest}，实测 {('r' + str(max(nums))) if nums else '无'}")
    dups = sorted({n for n in nums if nums.count(n) > 1})
    if dups:
        bad.append(f"round-duplicate: {['r' + str(n) for n in dups]}")
    if nums:
        gaps = [n for n in range(min(nums), max(nums) + 1) if n not in nums]
        if gaps:
            bad.append(f"round-gap: {['r' + str(n) for n in gaps]}")
    if expect_rows_sha256:
        got = rows_sha256(rows)
        if got != expect_rows_sha256:
            bad.append(f"rows-sha256 mismatch: expect={expect_rows_sha256} actual={got}")
    if expect_next and f"{expect_next} 绑整改档待跑" not in text:
        bad.append(f"next-pointer missing: 期望含 '{expect_next} 绑整改档待跑'")
    return bad

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--min-rows", type=int, default=0)
    ap.add_argument("--min-round", default="")
    ap.add_argument("--expect-latest", default="")
    ap.add_argument("--expect-rows-sha256", default="")
    ap.add_argument("--expect-next", default="")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    text, rows = load_rows(root)
    if args.self_test:
        ok = True
        cur_sha = rows_sha256(rows)
        # (a) 丢最后一行
        d1 = completeness_failures(rows[:-1], text, args.min_rows or len(rows), args.min_round, args.expect_latest, args.expect_rows_sha256 or cur_sha, args.expect_next)
        got1 = any("rows<" in b for b in d1)
        print(f"[self-test] drop-last-row caught: {got1} ({d1[:1]}) -> {'OK' if got1 else 'BAD'}")
        ok = ok and got1
        # (b) 删中间轮 + 复制另一轮（行数不变、最大轮不变）
        nums = round_nums(rows)
        if len(nums) >= 3:
            target = nums[0]
            donor = nums[-2] if nums[-2] != target else nums[-1]
            idx_target = next(i for i, (_, l, _) in enumerate(rows) if ROUND.search(l) and int(ROUND.search(l).group(1)[1:]) == target)
            idx_donor = next(i for i, (_, l, _) in enumerate(rows) if ROUND.search(l) and int(ROUND.search(l).group(1)[1:]) == donor)
            mutated = list(rows)
            mutated[idx_target] = (rows[idx_target][0], rows[idx_donor][1], rows[idx_target][2])
            d2 = completeness_failures(mutated, text, args.min_rows or len(rows), args.min_round, args.expect_latest, args.expect_rows_sha256 or cur_sha, args.expect_next)
            got2 = any(("round-gap" in b or "round-duplicate" in b or "rows-sha256" in b) for b in d2)
            print(f"[self-test] delete+duplicate bypass caught: {got2} ({d2[:2]}) -> {'OK' if got2 else 'BAD'}")
            ok = ok and got2
        # (c) 行集合哈希篡改
        d3 = completeness_failures(rows, text, args.min_rows, args.min_round, args.expect_latest, "0" * 64, args.expect_next)
        got3 = any("rows-sha256" in b for b in d3)
        print(f"[self-test] rows-sha256 tamper caught: {got3} -> {'OK' if got3 else 'BAD'}")
        ok = ok and got3
        return 0 if ok else 1
    bad = completeness_failures(rows, text, args.min_rows, args.min_round, args.expect_latest, args.expect_rows_sha256, args.expect_next)
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
        ok_row = row_dt <= commit_dt
        print(f"[{'OK' if ok_row else 'FAIL'}] :{lineno} row={row_dt:%m-%d %H:%M} commit={commit_dt:%m-%d %H:%M:%S} -> {'row<=commit' if ok_row else 'row>commit'}")
        if not ok_row:
            bad.append(f":{lineno} row>commit")
    for b in bad:
        print(f"[FAIL] {b}")
    print(f"\nrows={n} rows_sha256={rows_sha256(rows)} min_rows={args.min_rows} min_round={args.min_round or '-'} expect_latest={args.expect_latest or '-'} expect_next={args.expect_next or '-'} violations={len(bad)}")
    print(f"verdict={'PASS' if not bad else 'FAIL'}")
    return 0 if not bad else 1

if __name__ == "__main__":
    raise SystemExit(main())
