#!/usr/bin/env zsh
# (f) 计数自检一致性：EXPECTED_FIXED_COUNT / EXPECTED_GLOB_COUNT 必须随数组同步。
#   用法: zsh count_selfcheck.zsh <门路径>
# 判据：fake-backend 里跑一次正常命令，stdout/stderr **不得**出现两条计数 GATE-BROKEN 文案，
#       且必须出现 `RUNTIME-FILES: unchanged`。
# ⛔ 验伪锚（承重）：把 EXPECTED_FIXED_COUNT / EXPECTED_GLOB_COUNT 各改错一次，
#    同一判据**必须**当场变红 —— 否则「没出现 GATE-BROKEN」证明不了计数自检还活着
#    （它可能是被别的原因绕过了）。
set -u
GATE_SRC="$1"
typeset -i bad=0

run_once() {  # $1=门文本文件 $2=场景名 $3=期望(ok|broken-fixed|broken-glob)
  local src="$1" name="$2" want="$3" T out rc
  T=$(mktemp -d); trap "rm -rf $T" EXIT
  mkdir -p "$T/backend/app/data" "$T/backend/data" "$T/backend/tests" "$T/backend/scripts"
  print -r -- '# fake' > "$T/backend/app/main.py"
  cp "$src" "$T/backend/scripts/lifespan_isolation_runtime_sha.sh"
  out=$(bash "$T/backend/scripts/lifespan_isolation_runtime_sha.sh" -- /usr/bin/true 2>&1); rc=$?
  local has_fixed has_glob has_unchanged
  has_fixed=$(print -r -- "$out" | grep -c '固定监视项有')
  has_glob=$(print -r -- "$out"  | grep -c 'glob 监视模式有')
  has_unchanged=$(print -r -- "$out" | grep -cE '^RUNTIME-FILES: unchanged$')
  print -r -- "[$name] rc=$rc 固定计数GATE-BROKEN=$has_fixed glob计数GATE-BROKEN=$has_glob unchanged=$has_unchanged"
  case "$want" in
    ok)           [[ $has_fixed == 0 && $has_glob == 0 && $has_unchanged == 1 && $rc == 0 ]] || bad=1 ;;
    broken-fixed) [[ $has_fixed == 1 && $has_unchanged == 0 && $rc == 1 ]] || bad=1 ;;
    broken-glob)  [[ $has_glob  == 1 && $has_unchanged == 0 && $rc == 1 ]] || bad=1 ;;
  esac
  trap - EXIT; rm -rf "$T"
}

run_once "$GATE_SRC" "正常门" ok

# 验伪锚①：把 EXPECTED_FIXED_COUNT 改错
W=$(mktemp -d); trap "rm -rf $W" EXIT
sed -E 's/^EXPECTED_FIXED_COUNT=[0-9]+$/EXPECTED_FIXED_COUNT=99/' "$GATE_SRC" > "$W/fixed.sh"
grep -qE '^EXPECTED_FIXED_COUNT=99$' "$W/fixed.sh" || { print -r -- "!! 验伪锚① 变异没落上"; bad=1; }
run_once "$W/fixed.sh" "验伪锚①·固定计数改错" broken-fixed

# 验伪锚②：把 EXPECTED_GLOB_COUNT 改错
sed -E 's/^EXPECTED_GLOB_COUNT=[0-9]+$/EXPECTED_GLOB_COUNT=99/' "$GATE_SRC" > "$W/glob.sh"
grep -qE '^EXPECTED_GLOB_COUNT=99$' "$W/glob.sh" || { print -r -- "!! 验伪锚② 变异没落上"; bad=1; }
run_once "$W/glob.sh" "验伪锚②·glob计数改错" broken-glob
rm -rf "$W"; trap - EXIT

print -r -- "COUNT-SELFCHECK bad=$bad"
exit $bad
