#!/bin/bash
# CASE 6-3 — 单文件 diff 缺 --text
# 自述: 暂存一个前 8000 字节里带 NUL 的文件(标记在第一行)。git 判它是二进制, 只输出
#       `Binary files … differ`, 既无 @@ 也无 + 行 ⇒ 旧版块零命中、打 OK 退 0。
#       新版块加了 --text, 拿回逐行 diff ⇒ BLOCKED 退 1。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 6-3: 单文件 diff 缺 --text ==="
prepare_blocks || exit 1

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf 'x = 1  # %s\n\000binary-tail\n' "$MARK" > "$REPO/p.py"
( cd "$REPO" && "$REAL_GIT" add p.py )

echo "输入: 暂存 p.py — 第 1 行带标记, 第 2 行以 NUL 开头(落在前 8000 字节内)"
echo "旁证: 旧标志集下 git 的输出 ="
( cd "$REPO" && "$REAL_GIT" --no-pager --literal-pathspecs diff --cached --no-color \
    --no-renames -U0 --diff-filter=AM -- p.py | sed -n '1,5p' )

run_block old "$REPO"; OLD_RC=$?
run_block new "$REPO"; NEW_RC=$?
judge 6-3 "$OLD_RC" "$NEW_RC"
