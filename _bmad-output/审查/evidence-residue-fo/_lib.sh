#!/bin/bash
# CARD-TOOL-residue-fail-open — 对照共用件
# [BATCH-2026-09-11-第十四批 / CARD-TOOL-residue-fail-open]
#
# 口径(协议 §1 / 卡文 裁判 3):
#   一份对照 = 同一个输入, 在**旧版块**(git show 08100483:lefthook.yml 抽出)上必须打
#   `[Mutant-Scan] OK` 且 rc=0, 在**新版块**(当前工作树抽出)上必须不打 OK 且 rc=1。
#   只证明「新版会红」不算封住 —— 那不排除它红的是别的原因。
#
# ⚠️ round-2 起每条都跑**两种解释器**: `bash`(普通模式)与 `sh`(本机解析到 bash 的 POSIX
#   模式, 也就是 lefthook 2.1.6 `sh -c` 真正会用的那个)。两者结论可能不同 —— 例如 `:` 是
#   POSIX 特殊内建, 在 sh 下重定向失败会直接退出 shell, 于是旧版在 sh 下本来就不是 OK。
#   这种差异**如实分开记**, 不取对自己有利的那一种。
#
# 本文件不含变异标记字面量: 一律 MARK=$(printf 'MUT%s' 'ANT') 现拼。
set -u

CARD_ROOT=${CARD_ROOT:?CARD_ROOT 必须指向车道树绝对路径}
BASE_SHA=${BASE_SHA:-08100483}
MARK=$(printf 'MUT%s' 'ANT')
INTERPS=${T8A_INTERPS:-"bash sh"}

REAL_GIT=$(command -v git)
export GIT_AUTHOR_NAME=t8a GIT_AUTHOR_EMAIL=t8a@example.invalid
export GIT_COMMITTER_NAME=t8a GIT_COMMITTER_EMAIL=t8a@example.invalid
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t8a-case.XXXXXX") || exit 1
trap 'rm -rf "$WORK"' EXIT

# --- 抽块: 锚点现求, 不写死行号 -------------------------------------------
extract_block() {   # $1 = lefthook.yml 路径, $2 = 输出 .sh
  local s e
  s=$(/usr/bin/grep -cF 'mutant-residue-scan:' "$1")
  [ "$s" = 1 ] || { echo "extract_block: 块名锚点命中 $s 次(应为 1)"; return 1; }
  s=$(/usr/bin/grep -cF 'Mutant-Scan] OK' "$1")
  [ "$s" = 1 ] || { echo "extract_block: 块末锚点命中 $s 次(应为 1)"; return 1; }
  s=$(/usr/bin/grep -nF 'mutant-residue-scan:' "$1" | cut -d: -f1)
  e=$(/usr/bin/grep -nF 'Mutant-Scan] OK' "$1" | cut -d: -f1)
  awk -v s="$s" -v e="$e" 'NR>s+1 && NR<=e' "$1" | sed 's/^        //' > "$2"
  [ -s "$2" ] || { echo "extract_block: 抽出物为空"; return 1; }
}

prepare_blocks() {
  "$REAL_GIT" -C "$CARD_ROOT" show "$BASE_SHA":lefthook.yml > "$WORK/old.yml" || return 1
  extract_block "$WORK/old.yml" "$WORK/old.sh" || return 1
  extract_block "$CARD_ROOT/lefthook.yml" "$WORK/new.sh" || return 1
  echo "旧版块 = git show $BASE_SHA:lefthook.yml 抽出, $(wc -l < "$WORK/old.sh" | tr -d ' ') 行"
  echo "新版块 = 当前工作树 lefthook.yml 抽出, $(wc -l < "$WORK/new.sh" | tr -d ' ') 行"
  echo "解释器: $INTERPS  (sh -> $(/bin/sh -c 'echo bash ${BASH_VERSION:-非bash}'))"
}

mkrepo() {          # $1 = 仓目录
  mkdir -p "$1" || return 1
  ( cd "$1" && "$REAL_GIT" init -q . && "$REAL_GIT" commit -q --allow-empty -m base ) >/dev/null 2>&1
}

# --- 跑一版块 -------------------------------------------------------------
# run_block <old|new> <interp> <仓目录> [PATH 前缀]
run_block() {
  local which=$1 interp=$2 repo=$3 shim=${4:-} rc
  if [ -n "$shim" ]; then
    ( cd "$repo" && PATH="$shim:$PATH" "$interp" "$WORK/$which.sh" ) > "$WORK/$which.out" 2>&1
  else
    ( cd "$repo" && "$interp" "$WORK/$which.sh" ) > "$WORK/$which.out" 2>&1
  fi
  rc=$?
  echo "  ----- [$which / $interp] rc=$rc -----"
  sed -n '1,25p' "$WORK/$which.out" | sed 's/^/  /'
  echo "  ----- [$which / $interp] end rc=$rc -----"
  return $rc
}

# judge <标签> <old_rc> <new_rc> -> 打印判定, SEALED 返回 0
judge() {
  local id=$1 orc=$2 nrc=$3 okold=NO oknew=NO verdict
  if /usr/bin/grep -qF '[Mutant-Scan] OK (staged additions' "$WORK/old.out" && [ "$orc" = 0 ]; then
    okold=YES
  fi
  if ! /usr/bin/grep -qF '[Mutant-Scan] OK (staged additions' "$WORK/new.out" && [ "$nrc" = 1 ]; then
    oknew=YES
  fi
  if [ "$okold" = YES ] && [ "$oknew" = YES ]; then verdict=SEALED; else verdict=NOT-SEALED; fi
  echo "  旧版打 OK 且 rc=0 : $okold  (rc=$orc)"
  echo "  新版不打 OK 且 rc=1: $oknew  (rc=$nrc)"
  echo "  == $id: $verdict"
  [ "$verdict" = SEALED ]
}

# run_both <case-id> <仓目录> [PATH 前缀] —— 两种解释器各跑一遍, 结论分开记
run_both() {
  local id=$1 repo=$2 shim=${3:-} interp orc nrc summary=""
  for interp in $INTERPS; do
    echo "######## 解释器 = $interp ########"
    run_block old "$interp" "$repo" "$shim"; orc=$?
    run_block new "$interp" "$repo" "$shim"; nrc=$?
    if judge "$id / $interp" "$orc" "$nrc"; then
      summary="$summary $interp=SEALED"
    else
      summary="$summary $interp=NOT-SEALED"
    fi
  done
  echo "CASE $id:$summary"
}

# 在主循环之前注入一段故障语句(旧/新两版注入完全相同的文本; 锚点唯一性由脚本断言)
inject_before_loop() {   # $1 = 注入文本
  local inj=$1 w
  for w in old new; do
    INJ="$inj" python3 - "$WORK/$w.sh" "$WORK/$w.inj.sh" <<'PY'
import os, sys
src, dst = sys.argv[1], sys.argv[2]
inj = os.environ["INJ"].rstrip("\n") + "\n"
out, hit = [], 0
for line in open(src):
    if line.startswith("while IFS= read -r -d ") and line.rstrip().endswith("f; do"):
        out.append(inj); hit += 1
    out.append(line)
assert hit == 1, "注入锚点命中 %d 次(应为 1)" % hit
open(dst, "w").writelines(out)
PY
    mv "$WORK/$w.inj.sh" "$WORK/$w.sh"
  done
  echo "注入(旧/新两版同一位置、同一文本, 主循环之前):"
  printf '  %s\n' "$inj"
}
