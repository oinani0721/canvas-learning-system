#!/bin/bash
# CASE m4 — d 与 dn 是同一个 inode, 整份 diff 在读之前被截空(Codex round-3 MEDIUM)
# 自述: mktemp 垫片把 dn 预置成指向 d 的链接(符号链接 / 硬链接各一个变体)。于是:
#         1) git 正常写出含标记的 d —— 第一处类型检查通过(d 是普通文件);
#         2) shell 先开 `< d` 再 `> dn` —— 同一个 inode 被截断成空;
#         3) tr 读到 EOF、rc=0; dn 的类型检查也通过(-f 跟随符号链接, 硬链接更是普通文件);
#         4) awk 空输入、rc=0; hits 正常为空; 计数与哨兵不变 ⇒ round-3 版块照样打 OK 退 0。
#       round-4 加了一条 `d -ef dn`(比 inode, 两种链接都认得出) ⇒ 退 1。
# ⚠️ 这一条的「旧版」= round-3 的 commit 9020a1a5(d/dn 已有类型检查, 还没有 -ef), 不是 B14_BASE。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE m4: d 与 dn 同 inode ==="
BASE_SHA=9020a1a5
prepare_blocks || exit 1
echo "⚠️ 本条的旧版 = round-3 commit 9020a1a5(有类型检查, 无 -ef)"

for KIND in symlink hardlink; do
  echo "######## 链接形态 = $KIND ########"
  SHIM="$WORK/bin-$KIND"; mkdir -p "$SHIM"
  if [ "$KIND" = symlink ]; then MKLINK='ln -s "$p/d" "$p/dn"'; else MKLINK='ln "$p/d" "$p/dn"'; fi
  cat > "$SHIM/mktemp" <<SHIMEOF
#!/bin/sh
p=\$(/usr/bin/mktemp "\$@") || exit 1
: > "\$p/d"
$MKLINK
printf '%s\n' "\$p"
SHIMEOF
  chmod +x "$SHIM/mktemp"
  REPO="$WORK/repo-$KIND"; mkrepo "$REPO" || exit 1
  printf 'x = 1  # %s\n' "$MARK" > "$REPO/p.py"
  ( cd "$REPO" && "$REAL_GIT" add p.py )
  echo "输入: 暂存 p.py(带标记, 不在允许名单内) —— 真实命中"
  echo "注入: mktemp 垫片预置 d, 并把 dn 做成指向 d 的 $KIND"
  run_both "m4-$KIND" "$REPO" "$SHIM"
done
