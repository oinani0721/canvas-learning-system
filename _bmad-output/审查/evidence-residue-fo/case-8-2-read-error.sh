#!/bin/bash
# CASE 8-2 — 主循环的 read 报错(非 EOF 的非零退出), 却与「正常读完」无法区分
# 自述: 在**旧/新两版块的同一位置**(主循环之前)注入同一条故障语句, 把记录流换成一个
#       目录。open 成功, 但 read 报 `Is a directory` —— 本机实测该错误被完全吞掉:
#       循环跑 0 次而 loop_rc 仍是 0 ⇒ 旧版块打 OK 退 0。
#       新版块用「主循环消费的记录数 SEEN 必须等于清单里的 NUL 个数 EXPECTED」判出来 ⇒ 退 1。
# ⚠️ 如实声明: 这一条用的是**注入**而不是天然触发 —— 枚举那一步的 `> names` 会先于
#    主循环执行, 所以 names 不可能一开始就是目录。注入文本与注入点在两版完全相同,
#    两次运行之间唯一的差别就是块的版本; 注入锚点的唯一性由 _lib.sh 断言(命中必须 = 1)。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 8-2: 主循环 read 报错被吞 ==="
prepare_blocks || exit 1

echo "旁证(本机 read 语义): 从目录 fd 读 ="
/bin/sh -c 'n=0; while IFS= read -r -d "" v; do n=$((n+1)); done < /tmp; echo "  records=$n loop_rc=$?"' 2>&1 | sed 's/^/  /'

inject_before_loop 'mv "$TMPD/names" "$TMPD/names.orig" && mkdir "$TMPD/names"   # 注入: 记录流换成目录'

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf 'x = 1  # %s\n' "$MARK" > "$REPO/p.py"
( cd "$REPO" && "$REAL_GIT" add p.py )
echo "输入: 暂存 p.py(带标记, 不在允许名单内)"

run_both 8-2 "$REPO"
