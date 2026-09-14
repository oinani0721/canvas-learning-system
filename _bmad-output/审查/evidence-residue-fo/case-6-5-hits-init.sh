#!/bin/bash
# CASE 6-5 — `: > "$TMPD/hits"` 是全块唯一无显式守卫的一步
# 自述: 用一个 mktemp 垫片让块拿到的临时目录里**预先**放一个只读(444)的 hits。
#       旧版块的 `: > hits` 因此失败, 但没有守卫 ⇒ 继续往下跑, 最后照样打 OK 退 0。
#       新版块给这一步补了 `|| { …FAILED…; exit 1; }` ⇒ 退 1。
# ⚠️ 本条对照证明的是「初始化失败被吞掉」, **不是**「漏掉了一个真实残留」: 暂存面里
#    只放一个允许名单内的文件, 否则后面的 `>> hits` 会失败而那一步本来就有守卫,
#    旧版块会因此退 1, 对照就不成立了(那样只证明得了别的东西)。
set -u
. "$(dirname "$0")/_lib.sh"

echo "=== CASE 6-5: hits 初始化失败无守卫 ==="
prepare_blocks || exit 1

SHIM="$WORK/bin"; mkdir -p "$SHIM"
cat > "$SHIM/mktemp" <<SHIMEOF
#!/bin/sh
d=\$(/usr/bin/mktemp "\$@") || exit 1
: > "\$d/hits" && chmod 444 "\$d/hits"
printf '%s\n' "\$d"
SHIMEOF
chmod +x "$SHIM/mktemp"

REPO="$WORK/repo"; mkrepo "$REPO" || exit 1
mkdir -p "$REPO/_bmad-output"
printf 'allowlisted note, no marker here\n' > "$REPO/_bmad-output/x.md"
( cd "$REPO" && "$REAL_GIT" add _bmad-output/x.md )

echo "输入: 暂存 _bmad-output/x.md(允许名单内, 主循环会 continue, 不会写 hits)"
echo "注入: mktemp 垫片在临时目录里预置 444 的 hits, 使 \`: > hits\` 失败"
echo "      (垫片只改环境, 旧/新两版块本体一字未动)"

run_block old "$REPO" "$SHIM"; OLD_RC=$?
run_block new "$REPO" "$SHIM"; NEW_RC=$?
judge 6-5 "$OLD_RC" "$NEW_RC"
