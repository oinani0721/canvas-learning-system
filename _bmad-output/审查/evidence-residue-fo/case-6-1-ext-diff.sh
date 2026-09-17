#!/bin/bash
# CASE 6-1 — 单文件 diff 缺 --no-ext-diff
# 自述: 暂存一个带标记的新文件, 并通过 GIT_CONFIG_* 注入 diff.external(一个只 exit 0
#       的程序)。外部 diff 接管输出后 git 仍 rc=0 而正文为 0 字节, awk 无输入 ⇒ 零命中,
#       旧版块照样打 OK 退 0。新版块加了 --no-ext-diff, 拿回真 diff ⇒ BLOCKED 退 1。
# 注: git 配置一律用 GIT_CONFIG_COUNT/KEY/VALUE 环境注入, 不写任何仓库配置(卡文 (i))。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 6-1: 单文件 diff 缺 --no-ext-diff ==="
prepare_blocks || exit 1

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf '#!/bin/sh\nexit 0\n' > "$WORK/ext.sh"; chmod +x "$WORK/ext.sh"
printf 'x = 1  # %s\n' "$MARK" > "$REPO/p.py"
( cd "$REPO" && "$REAL_GIT" add p.py )

export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=diff.external GIT_CONFIG_VALUE_0="$WORK/ext.sh"
echo "输入: 暂存 p.py(带标记, 路径不在允许名单内); diff.external=$WORK/ext.sh (只 exit 0)"
echo "旁证: 旧标志集下 git 的输出字节数 ="
( cd "$REPO" && "$REAL_GIT" --no-pager --literal-pathspecs diff --cached --no-color \
    --no-renames -U0 --diff-filter=AM -- p.py | wc -c )

run_both 6-1 "$REPO"
