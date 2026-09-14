#!/bin/bash
# CARD-TOOL-residue-fail-open — 九条(+`-s hits`)对照的共用件
# [BATCH-2026-09-11-第十四批 / CARD-TOOL-residue-fail-open]
#
# 口径(协议 §1 / 卡文 裁判 3):
#   一份对照 = 同一个输入, 在**旧版块**(git show 08100483:lefthook.yml 抽出)上打
#   `[Mutant-Scan] OK` 且 rc=0, 在**新版块**(当前工作树抽出)上不打 OK 且 rc=1。
#   只证明「新版会红」不算封住 —— 那不排除它红的是别的原因。
#
# 本文件不含变异标记字面量: 一律 MARK=$(printf 'MUT%s' 'ANT') 现拼。
set -u

CARD_ROOT=${CARD_ROOT:?CARD_ROOT 必须指向车道树绝对路径}
BASE_SHA=${BASE_SHA:-08100483}
MARK=$(printf 'MUT%s' 'ANT')

REAL_GIT=$(command -v git)
export GIT_AUTHOR_NAME=t8a GIT_AUTHOR_EMAIL=t8a@example.invalid
export GIT_COMMITTER_NAME=t8a GIT_COMMITTER_EMAIL=t8a@example.invalid
# 临时仓一律与本机 git 配置隔离, 免得 ~/.gitconfig 把对照结论带偏
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
}

mkrepo() {          # $1 = 仓目录
  mkdir -p "$1" || return 1
  ( cd "$1" && "$REAL_GIT" init -q . && "$REAL_GIT" commit -q --allow-empty -m base ) >/dev/null 2>&1
}

# --- 跑一版块 -------------------------------------------------------------
# run_block <old|new> <仓目录> [额外 PATH 前缀]  ; 额外环境由调用方 export
run_block() {
  local which=$1 repo=$2 shim=${3:-}
  local rc
  if [ -n "$shim" ]; then
    ( cd "$repo" && PATH="$shim:$PATH" bash "$WORK/$which.sh" ) > "$WORK/$which.out" 2>&1
  else
    ( cd "$repo" && bash "$WORK/$which.sh" ) > "$WORK/$which.out" 2>&1
  fi
  rc=$?
  echo "----- [$which 版块] rc=$rc -----"
  sed -n '1,25p' "$WORK/$which.out"
  echo "----- [$which 版块] end rc=$rc -----"
  return $rc
}

# --- 判定 -----------------------------------------------------------------
# judge <case-id> <old_rc> <new_rc>
judge() {
  local id=$1 orc=$2 nrc=$3 okold=NO oknew=NO verdict
  if /usr/bin/grep -qF '[Mutant-Scan] OK (staged additions' "$WORK/old.out" && [ "$orc" = 0 ]; then
    okold=YES
  fi
  if ! /usr/bin/grep -qF '[Mutant-Scan] OK (staged additions' "$WORK/new.out" && [ "$nrc" = 1 ]; then
    oknew=YES
  fi
  if [ "$okold" = YES ] && [ "$oknew" = YES ]; then verdict=SEALED; else verdict=NOT-SEALED; fi
  echo "旧版打 OK 且 rc=0 : $okold  (rc=$orc)"
  echo "新版不打 OK 且 rc=1: $oknew  (rc=$nrc)"
  echo "CASE $id: $verdict"
  [ "$verdict" = SEALED ]
}

# 在主循环之前注入一段故障语句(旧/新两版注入完全相同的文本, 锚点唯一性由脚本断言)
inject_before_loop() {   # $1 = 注入文本(单行或多行)
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
