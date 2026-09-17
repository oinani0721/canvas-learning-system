#!/bin/bash
# CASE m3 — d / dn 被换成非普通文件, 整份 diff 被丢掉(Codex round-2 MEDIUM)
# 自述: 与 case-9 同型故障, 只是把目标从 hits 换成 d / dn。mktemp 垫片把它们预置成指向
#       /dev/null 的符号链接: `>` 不会替掉已有的符号链接, 于是 git 与 tr 都"写成功"了而
#       内容全丢, awk 从设备读到 EOF 也成功退出, hits 保持正常空文件 —— 计数、哨兵、
#       hits 类型检查**全部通过**, round-2 版块照样打 OK 退 0。
#       round-3 在写之后核「d / dn 是可读的普通文件」⇒ 退 1。
# ⚠️ 这一条的「旧版」= round-2 的 commit f9e31034, 不是 B14_BASE —— 要证的是
#    「hits 那条守住了、d/dn 没守住」, 拿更早的版本当旧版会把几件事混在一起。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE m3: d / dn 不是普通文件 ==="
BASE_SHA=f9e31034
prepare_blocks || exit 1
echo "⚠️ 本条的旧版 = round-2 commit f9e31034(hits 已有类型检查, d/dn 还没有)"

for TARGET in d dn; do
  echo "######## 被换掉的临时文件 = $TARGET ########"
  SHIM="$WORK/bin-$TARGET"; mkdir -p "$SHIM"
  cat > "$SHIM/mktemp" <<SHIMEOF
#!/bin/sh
p=\$(/usr/bin/mktemp "\$@") || exit 1
ln -s /dev/null "\$p/$TARGET"
printf '%s\n' "\$p"
SHIMEOF
  chmod +x "$SHIM/mktemp"
  REPO="$WORK/repo-$TARGET"; mkrepo "$REPO" || exit 1
  printf 'x = 1  # %s\n' "$MARK" > "$REPO/p.py"
  ( cd "$REPO" && "$REAL_GIT" add p.py )
  echo "输入: 暂存 p.py(带标记, 不在允许名单内) —— 真实命中"
  echo "注入: mktemp 垫片把 $TARGET 预置成 -> /dev/null"
  run_both "m3-$TARGET" "$REPO" "$SHIM"
done
