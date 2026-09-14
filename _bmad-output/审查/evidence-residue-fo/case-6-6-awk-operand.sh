#!/bin/bash
# CASE 6-6 — awk 的文件参数形如 `name=value` 时被当成变量赋值
# 自述: 把 TMPDIR 设成一个**相对路径**且首段含 `=`(t=x)。于是 "$TMPD/d" 长成
#       `t=x/lefthook-mutant-residue.XXXX/d` —— awk 把这种操作数当**赋值**而不是文件名,
#       转而去读 stdin, 而循环的 stdin 正是记录流本身 ⇒ awk 一次吞完, 主循环在第一条
#       之后就结束, 第二个(带标记的)文件根本没被扫 ⇒ 旧版块打 OK 退 0。
#       新版块改成 `< "$TMPD/d"`, 彻底不给操作数 ⇒ 两条都扫到 ⇒ BLOCKED 退 1。
# ⚠️ 本机 awk(version 20200816)**不认 `--`**: 实测 `awk '…' -- 'a=b/d'` 报
#    can't open file `--` 且 `a=b/d` 仍被当赋值, 所以不能用 `--` 封这条。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 6-6: awk 文件参数被当作 name=value 赋值 ==="
prepare_blocks || exit 1

echo "旁证(本机 awk 语义):"
mkdir -p "$WORK/a=b"; printf 'hello\n' > "$WORK/a=b/d"
( cd "$WORK" && echo -n "  裸操作数 'a=b/d' -> "; awk '{print "GOT:"$0}' 'a=b/d' < /dev/null; echo "[空=被当赋值]" )
( cd "$WORK" && echo -n "  加 -- 之后    -> "; awk '{print "GOT:"$0}' -- 'a=b/d' < /dev/null 2>&1 | tr '\n' ' '; echo )
( cd "$WORK" && echo -n "  < 重定向      -> "; awk '{print "GOT:"$0}' < 'a=b/d' )
echo -n "  awk 版本: "; awk --version 2>&1 | head -1

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
mkdir -p "$REPO/t=x"
printf 'y = 2  # nothing here\n' > "$REPO/a_clean.py"
printf 'x = 1  # %s\n' "$MARK" > "$REPO/b_dirty.py"
( cd "$REPO" && "$REAL_GIT" add a_clean.py b_dirty.py )

export TMPDIR='t=x'
echo "输入: 暂存 a_clean.py(无标记, 排序在前) + b_dirty.py(带标记); TMPDIR='t=x'(相对路径, 首段含 =)"

run_both 6-6 "$REPO"
