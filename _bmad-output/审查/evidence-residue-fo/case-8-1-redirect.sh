#!/bin/bash
# CASE 8-1 — 主循环的输入重定向打不开, 却不置 FAILED
# 自述: 用 mktemp 垫片让临时目录里**预置**一个只写(200)的 names。
#       枚举那一步 `> "$TMPD/names"` 写得进去(只写权限足够), 但主循环的
#       `done < "$TMPD/names"` 打不开(Permission denied) ⇒ 循环一次都不跑,
#       而这个失败没有任何人去看 ⇒ 旧版块打 OK 退 0, 带标记的文件白白放过去。
#       新版块在枚举之后加了「必须是可读的普通文件」前置校验 ⇒ 退 1。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 8-1: 主循环输入重定向打不开 ==="
prepare_blocks || exit 1

SHIM="$WORK/bin"; mkdir -p "$SHIM"
cat > "$SHIM/mktemp" <<SHIMEOF
#!/bin/sh
d=\$(/usr/bin/mktemp "\$@") || exit 1
: > "\$d/names" && chmod 200 "\$d/names"
printf '%s\n' "\$d"
SHIMEOF
chmod +x "$SHIM/mktemp"

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf 'x = 1  # %s\n' "$MARK" > "$REPO/p.py"
( cd "$REPO" && "$REAL_GIT" add p.py )

echo "输入: 暂存 p.py(带标记, 不在允许名单内)"
echo "注入: mktemp 垫片预置 200(只写)的 names —— 写得进、读不出"
echo "      (垫片只改环境, 旧/新两版块本体一字未动)"

run_block old "$REPO" "$SHIM"; OLD_RC=$?
run_block new "$REPO" "$SHIM"; NEW_RC=$?
judge 8-1 "$OLD_RC" "$NEW_RC"
