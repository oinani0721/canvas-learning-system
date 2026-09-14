#!/bin/bash
# CASE 9 — `[ -s hits ]` 为假被当成「没有命中」, 而它也可能是「结论取不到」
# 自述: 用 mktemp 垫片把 hits 预置成一个指向 /dev/null 的符号链接。
#       `: > hits` 成功(truncate /dev/null), awk 的命中也"写进去"了 —— 但写丢了;
#       `[ -s hits ]` 于是恒假 ⇒ 旧版块打 OK 退 0, **一个真实的残留标记就这样过去了**。
#       这是十条里唯一一条旧版「打 OK 的同时确有真命中」的对照。
#       新版块在 `[ -s ]` 为假之后追核 hits 仍是可读普通文件 ⇒ 退 1。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 9: -s hits 取不到有效状态 ==="
prepare_blocks || exit 1

SHIM="$WORK/bin"; mkdir -p "$SHIM"
cat > "$SHIM/mktemp" <<SHIMEOF
#!/bin/sh
d=\$(/usr/bin/mktemp "\$@") || exit 1
ln -s /dev/null "\$d/hits"
printf '%s\n' "\$d"
SHIMEOF
chmod +x "$SHIM/mktemp"

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
printf 'x = 1  # %s\n' "$MARK" > "$REPO/p.py"
( cd "$REPO" && "$REAL_GIT" add p.py )

echo "输入: 暂存 p.py(带标记, 不在允许名单内) —— 这是一条**真实命中**"
echo "注入: mktemp 垫片把 hits 预置成 -> /dev/null(可写但写进去就丢, size 恒 0)"
echo "      (垫片只改环境, 旧/新两版块本体一字未动)"

run_block old "$REPO" "$SHIM"; OLD_RC=$?
run_block new "$REPO" "$SHIM"; NEW_RC=$?
judge 9 "$OLD_RC" "$NEW_RC"
