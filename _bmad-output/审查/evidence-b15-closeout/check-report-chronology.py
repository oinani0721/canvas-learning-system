"""汇报时序/完整性机器门 v5（v4 + r20-M2/L1/L3：sha 必填 + 权威序列连续/已提交 + 描述清理）。

判据（任一失败 rc=1）：
  ① 每 `| MM-DD HH:MM[:SS] |` 行事件时间 ≤ 其引入 commit committer 时间（`git blame --porcelain -L` 逐行）；
  ② 权威推导：从 STATUS 与台账推导 completed/next；两侧 completed 序列 r1..rN 必须连续无缺无重、
     pending == N+1、台账最新轮行含同一 next；且 STATUS/台账 工作区必须干净（已提交）；
  ③ 报告轮次集合必须 == r4..rN（r1–r3 为叙事行）；行数 ≥ 标注轮次+6；须含 `r{next} 绑整改档待跑`；
  ④ `--expect-rows-sha256 HEX` 必填（缺省即红）：全部行文本 join 的 sha256 必须相符；
  ⑤ `--self-test`：丢行 / 删中间+复制置换 / 哈希篡改 三类必须被捕捉。
用法：python3 check-report-chronology.py <repo-root> --expect-rows-sha256 HEX [--min-round rM] [--self-test]
"""
import argparse
import datetime as dt
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPORT = "_bmad-output/第十五批-完成的卡-汇报.md"
STATUS = "_bmad-output/审查/evidence-b15-closeout/STATUS.md"
LEDGER = "_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md"
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

def authoritative_state(root):
    """v4：从 STATUS/台账 推导 {completed,next}；不自洽 ⇒ 返回 (None,None,failures)。"""
    bad = []
    st = (root / STATUS).read_text(encoding="utf-8").splitlines()
    completed = sorted(int(m.group(1)) for m in (re.match(r"^- r(\d+)（绑 ", l) for l in st) if m)
    pend = sorted(int(m.group(1)) for m in (re.match(r"^- r(\d+)：绑定本整改档", l) for l in st) if m)
    lg = (root / LEDGER).read_text(encoding="utf-8").splitlines()
    l_rounds = sorted(int(m.group(1)) for m in (re.match(r"^\| \*\*B15 D-15 终审（r(\d+)）\*\*", l) for l in lg) if m)
    l_next = sorted(int(m.group(1)) for m in (re.search(r"r(\d+) 绑整改档（待跑）", l) for l in lg) if m)
    if not completed:
        bad.append("status-completed missing")
    if not pend or len(pend) != 1:
        bad.append(f"status-pending 非唯一: {pend}")
    last = max(completed) if completed else 0
    nxt = last + 1 if completed else None
    if not l_rounds or max(l_rounds) != last:
        bad.append(f"ledger-rounds 与 STATUS 不一致: ledger-max={max(l_rounds) if l_rounds else '-'} status-max=r{last}")
    # 台账最新轮行必须指向 r(last+1) 待跑
    if l_rounds and nxt:
        last_lg_row = [l for l in lg if re.match(rf"^\| \*\*B15 D-15 终审（r{last}）\*\*", l)]
        if not last_lg_row or f"r{nxt} 绑整改档（待跑）" not in last_lg_row[0]:
            bad.append(f"ledger-next 与 STATUS 不一致: 期望最新轮行含 'r{nxt} 绑整改档（待跑）'")
    if completed and completed != list(range(1, max(completed) + 1)):
        bad.append(f"status-completed 非连续: {['r' + str(n) for n in completed]}")
    if l_rounds and l_rounds != list(range(min(l_rounds), max(l_rounds) + 1)):  # 台账 D-15 行自 r4 起
        bad.append(f"ledger-rounds 非连续: {['r' + str(n) for n in l_rounds]}")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", STATUS, LEDGER], cwd=root, capture_output=True, text=True).stdout.strip()
    if dirty:
        bad.append(f"authority-dirty: STATUS/台账 工作区未提交变更: {dirty.splitlines()[:2]}")
    if pend and nxt and pend[-1] != nxt:
        bad.append(f"round-not-contiguous: completed-max=r{last} 但 STATUS 待跑=r{pend[-1]}（期望 r{nxt}）")
    return completed, nxt, bad

def round_nums(rows):
    return [int(ROUND.search(l).group(1)[1:]) for (_, l, _) in rows if ROUND.search(l)]

def completeness_failures(rows, text, completed, nxt, min_round, expect_rows_sha256, auth_bad):
    bad = list(auth_bad)
    expected_rounds = list(range(4, max(completed) + 1)) if completed else []  # r1–r3 为叙事行（r3 为“更正/续报”）
    min_rows = len(expected_rounds) + 6
    if len(rows) < min_rows:
        bad.append(f"rows<{min_rows}（=标注轮次+6）: rows={len(rows)}")
    nums = round_nums(rows)
    if min_round:
        want_min = int(min_round[1:])
        if not nums or min(nums) != want_min:
            bad.append(f"min-round mismatch: 期望 {min_round}，实测 {('r' + str(min(nums))) if nums else '无'}")
    if nums != expected_rounds:
        bad.append(f"round-set mismatch: 报告={['r' + str(n) for n in nums]} != 期望标注轮次={['r' + str(n) for n in expected_rounds]}（r1–r3 为叙事行）")
    if nxt and f"r{nxt} 绑整改档待跑" not in text:
        bad.append(f"next-pointer missing: 期望含 'r{nxt} 绑整改档待跑'")
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
    return bad

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--min-round", default="")
    ap.add_argument("--expect-rows-sha256", default="")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    text, rows = load_rows(root)
    completed, nxt, auth_bad = authoritative_state(root)
    if args.self_test:
        ok = True
        cur_sha = rows_sha256(rows)
        # (a) 丢最后一行（权威期望不变 ⇒ 应红）
        d1 = completeness_failures(rows[:-1], text, completed, nxt, args.min_round, args.expect_rows_sha256 or cur_sha, [])
        d1 = d1 + [b for b in auth_bad]
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
            d2 = completeness_failures(mutated, text, completed, nxt, args.min_round, args.expect_rows_sha256 or cur_sha, [])
            got2 = any(("round-gap" in b or "round-duplicate" in b or "rows-sha256" in b or "round-set" in b) for b in d2)
            print(f"[self-test] delete+duplicate bypass caught: {got2} ({d2[:2]}) -> {'OK' if got2 else 'BAD'}")
            ok = ok and got2
        # (c) 行集合哈希篡改
        d3 = completeness_failures(rows, text, completed, nxt, args.min_round, "0" * 64, [])
        got3 = any("rows-sha256" in b for b in d3)
        print(f"[self-test] rows-sha256 tamper caught: {got3} -> {'OK' if got3 else 'BAD'}")
        ok = ok and got3
        return 0 if ok else 1
    if not args.expect_rows_sha256:
        auth_bad = auth_bad + ["rows-sha256-required: 必须显式提供 --expect-rows-sha256（fail-closed）"]
    bad = completeness_failures(rows, text, completed, nxt, args.min_round, args.expect_rows_sha256, auth_bad)
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
    print(f"\nrows={n} rows_sha256={rows_sha256(rows)} min_round={args.min_round or '-'} completed={'r' + str(max(completed)) if completed else '-'} next={'r' + str(nxt) if nxt else '-'} violations={len(bad)}")
    print(f"verdict={'PASS' if not bad else 'FAIL'}")
    return 0 if not bad else 1

if __name__ == "__main__":
    raise SystemExit(main())
