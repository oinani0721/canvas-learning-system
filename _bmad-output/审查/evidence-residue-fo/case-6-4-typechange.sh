#!/bin/bash
# CASE 6-4 — 枚举 --diff-filter 不含 T
# 自述: 仓里先提交一个 symlink tc.py, 再把它换成同名的**普通文件**(内容带标记)并暂存。
#       git 把这次改动判为 T(typechange): 它既不算 A 也不算 M ⇒ 旧版块的 AM 枚举拿到
#       空清单、主循环一次都不跑、打 OK 退 0。新版块枚举与单文件 diff 都改成 AMT ⇒
#       该文件进扫描面, 其新内容那一段 diff 确实带 + 行 ⇒ BLOCKED 退 1。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 6-4: 枚举 --diff-filter 不含 T(typechange) ==="
prepare_blocks || exit 1

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf 'seed\n' > "$REPO/seed.txt"
( cd "$REPO" && "$REAL_GIT" add seed.txt && "$REAL_GIT" commit -q -m seed ) >/dev/null 2>&1
( cd "$REPO" && ln -s seed.txt tc.py && "$REAL_GIT" add tc.py && "$REAL_GIT" commit -q -m tc-symlink ) >/dev/null 2>&1
/bin/rm -f "$REPO/tc.py"
printf 'x = 1  # %s\n' "$MARK" > "$REPO/tc.py"
( cd "$REPO" && "$REAL_GIT" add tc.py )

echo "输入: tc.py 由 symlink 变成带标记的普通文件并暂存"
echo -n "旁证 AM  枚举 : "; ( cd "$REPO" && "$REAL_GIT" --no-pager diff --cached --no-color --no-renames --name-only --diff-filter=AM  -z | tr '\000' '|' ); echo "  <-- 空"
echo -n "旁证 AMT 枚举 : "; ( cd "$REPO" && "$REAL_GIT" --no-pager diff --cached --no-color --no-renames --name-only --diff-filter=AMT -z | tr '\000' '|' ); echo

run_both 6-4 "$REPO"
