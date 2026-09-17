#!/bin/bash
# CASE h1 — 同一条新增行里 NUL 出现在标记**之前**(Codex round-1 HIGH)
# 自述: awk 的字符串是 NUL 终止的。git 加了 --text 之后**确实**把完整字节交了出来, 但 awk 的
#       index($0, M) 只看得到 NUL 之前那一截 —— 实测 `+x<NUL> # <标记>` 判 MISS 且 rc=0。
#       所以 round-1 的「补 --text 就抓得到」是不完整的: 6-3 把标记放第一行、NUL 放第二行,
#       恰好避开了这个缺口。本条把标记放在同一行的 NUL **之后**, 直击该缺口。
#       round-2 在喂 awk 之前补了 `LC_ALL=C tr '\000' '?'` 等长归一化 ⇒ 新版 BLOCKED 退 1。
# ⚠️ 这一条的「旧版」= round-1 的 commit cd31cffd(已经带 --text), 不是 B14_BASE ——
#    因为要证的是「--text 之后仍然漏」, 拿没有 --text 的 B14_BASE 当旧版会把两件事混在一起。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE h1: 同行内 NUL 在标记之前 ==="
BASE_SHA=cd31cffd
prepare_blocks || exit 1
echo "⚠️ 本条的旧版 = round-1 commit cd31cffd(已含 --text), 不是 B14_BASE"

echo "旁证(本机 awk 语义, 直接喂两种排列):"
printf '+x\000 # %s\n' "$MARK" > "$WORK/nul_first.txt"
printf '+x # %s\000\n' "$MARK" > "$WORK/nul_after.txt"
for f in nul_first nul_after; do
  printf '  %-10s -> ' "$f"
  awk -v M="$MARK" '/^\+/{ if (index($0,M)) print "HIT"; else print "MISS" }' "$WORK/$f.txt"
done
printf '  %-10s -> ' "归一化后"
LC_ALL=C tr '\000' '?' < "$WORK/nul_first.txt" | awk -v M="$MARK" '/^\+/{ if (index($0,M)) print "HIT"; else print "MISS" }'

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf 'x = 1 \000 # %s\n' "$MARK" > "$REPO/p.py"
( cd "$REPO" && "$REAL_GIT" add p.py )
echo "输入: 暂存 p.py —— 同一行内先 NUL 后标记(不在允许名单内)"
echo "旁证: git --text 确实把标记交了出来(下面这行里能看到它) ="
( cd "$REPO" && "$REAL_GIT" --no-pager --literal-pathspecs diff --cached --no-color \
    --no-ext-diff --no-textconv --text --no-renames -U0 --diff-filter=AMT -- p.py \
    | LC_ALL=C tr '\000' '?' | /usr/bin/grep '^+x' )

run_both h1 "$REPO"
