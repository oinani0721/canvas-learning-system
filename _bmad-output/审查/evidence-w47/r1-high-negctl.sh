#!/usr/bin/env bash
# CARD-W4-7 · Codex 逐轮意见的整改负控：把**修前形态**写回生产代码，
# 证明新增的门确实拦得住它们（而不是只在当前实现上恒绿）。
#
# r1-high1: extract_port 退回 `except Exception`（漏 BaseException）
# r1-high2: _is_uvloop_module 退回 `type(name) is not str -> False`（str 子类一律放行）
# r2-med1 : 退回 round-2 Codex 给的静态反例（放行 uvloop.loop）
#
# 判据（round-3 Codex LOW 处方：**逐参数**绑定预期结果，不用总数）：
#   * pytest rc 必须恰好是 1（failed）—— 拒绝 2（INTERRUPTED）/ 3（INTERNALERROR）等；
#   * EXPECT_FAIL 里的每个参数 id 都必须出现在 FAILED 行里；
#   * EXPECT_PASS 里的每个参数 id 都**不得**出现在 FAILED 行里；
#   * 失败正文（`^E ` 行）命中期望串的次数 >= 应失败参数数。
# 还原：EXIT 负责还原；INT/TERM 显式退出 130/143（不沿用进入时的 $?，免得被信号
# 打断的跑因为「上一条命令成功」而以 0 收场，伪装成通过）。
set -uo pipefail
CASE="${1:?r1-high1|r1-high2|r2-med1|r3-med1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EV="$ROOT/_bmad-output/审查/evidence-w47"
GUARD="$ROOT/backend/tests/support/live_port_guard.py"
PY="$ROOT/backend/.venv/bin/python"
PYTEST="$ROOT/backend/.venv/bin/pytest"
T='tests/unit/test_live_port_guard_contract.py'

# 每个 case：被测节点 / 应失败的参数 id / 应通过的参数 id / 失败正文期望串
case "$CASE" in
  r1-high1)
    NODE="$T::TestExtractPort::test_index_raising_baseexception_is_also_fail_closed"
    EXPECT_FAIL=(SystemExit KeyboardInterrupt _CustomBaseException)
    EXPECT_PASS=()
    EXPECT_BODY='放了出来 —— 它会越过 STATE.record()'
    ;;
  r1-high2)
    NODE="$T::TestGuardLiveness::test_str_subclass_module_name_is_still_blocked"
    EXPECT_FAIL=(uvloop uvloop.loop)
    EXPECT_PASS=()
    EXPECT_BODY='DID NOT RAISE'
    ;;
  r2-med1)
    # round-2 反例：`str.startswith(...) and name.startswith(...)` —— 第二项走**重载**，
    # 实测放行 uvloop.loop-denier（重载 startswith 恒 False）。另三格仍被拦。
    NODE="$T::TestGuardLiveness::test_lying_str_subclass_on_uvloop_value_is_still_blocked"
    EXPECT_FAIL=('uvloop.loop-denier')
    EXPECT_PASS=('uvloop.loop-affirmer' 'uvloop-affirmer' 'uvloop-denier')
    EXPECT_BODY='DID NOT RAISE'
    ;;
  r3-med1)
    # round-3 反例：`str.startswith(...) and not (name == "uvloop")` —— 第二项走**重载相等**，
    # 实测放行 uvloop.loop-affirmer（重载相等恒真 ⇒ not(...) 为假）。另三格仍被拦。
    # 两个反例各放行**不同**的一格 —— 这正是交叉参数化（子类行为 × 真实值）的理由。
    NODE="$T::TestGuardLiveness::test_lying_str_subclass_on_uvloop_value_is_still_blocked"
    EXPECT_FAIL=('uvloop.loop-affirmer')
    EXPECT_PASS=('uvloop.loop-denier' 'uvloop-affirmer' 'uvloop-denier')
    EXPECT_BODY='DID NOT RAISE'
    ;;
  *) echo "未知 case: $CASE"; exit 64 ;;
esac

BACKUP="$(mktemp -d)"
cp -p "$GUARD" "$BACKUP/guard.py"
SHA_BEFORE="$(shasum -a 256 "$GUARD" | awk '{print $1}')"
_restore_files() {
  cp -p "$BACKUP/guard.py" "$GUARD"
  local sha_after
  sha_after="$(shasum -a 256 "$GUARD" | awk '{print $1}')"
  echo "--- 还原 ---"
  echo "sha-before = $SHA_BEFORE"
  echo "sha-after  = $sha_after"
  rm -rf "$BACKUP"
  if [ "$SHA_BEFORE" != "$sha_after" ]; then
    echo "RESTORE-MISMATCH"
    return 90
  fi
  echo "RESTORE-OK: sha-before == sha-after"
  return 0
}
on_exit() { local rc=$?; _restore_files || rc=90; exit $rc; }
on_int() { _restore_files; echo "INTERRUPTED (SIGINT)"; exit 130; }
on_term() { _restore_files; echo "TERMINATED (SIGTERM)"; exit 143; }
trap on_exit EXIT
trap on_int INT
trap on_term TERM

echo "=== NEGCTL case=$CASE ==="
echo "被测门: $NODE"
echo "应失败参数: ${EXPECT_FAIL[*]:-<无>}"
echo "应通过参数: ${EXPECT_PASS[*]:-<无>}"
echo "失败正文期望串: $EXPECT_BODY"
"$PY" "$EV/negctl_patch_w47.py" apply "$CASE" || exit $?
cd "$ROOT/backend" || exit 91
export PYTHONDONTWRITEBYTECODE=1
OUT="$($PYTEST -q -p no:cacheprovider --tb=long "$NODE" 2>&1)"
RC=$?
echo "pytest 退出码 = ${RC}（要求恰好 1 = failed；2=INTERRUPTED / 3=INTERNALERROR 一律不算）"
echo "$OUT" | grep -E '^(FAILED|ERROR)|passed|failed' | head -10
echo "--- 失败正文（^E 限定行）---"
echo "$OUT" | grep -E '^E ' | head -8

PROBLEMS=()
[ "$RC" -eq 1 ] || PROBLEMS+=("pytest rc=$RC 不是 1")
FAILED_LINES="$(echo "$OUT" | grep -E '^FAILED ' || true)"
for p in ${EXPECT_FAIL[@]+"${EXPECT_FAIL[@]}"}; do
  echo "$FAILED_LINES" | grep -qF "[$p]" || PROBLEMS+=("应失败参数 [$p] 没出现在 FAILED 行里")
done
for p in ${EXPECT_PASS[@]+"${EXPECT_PASS[@]}"}; do
  if echo "$FAILED_LINES" | grep -qF "[$p]"; then
    PROBLEMS+=("应通过参数 [$p] 却失败了")
  fi
done
BODY_HITS=$(echo "$OUT" | grep -E '^E ' | grep -cF "$EXPECT_BODY")
WANT_BODY=${#EXPECT_FAIL[@]}
echo "失败正文命中期望串 = $BODY_HITS ; 应失败参数数 = $WANT_BODY"
if [ "$BODY_HITS" -lt "$WANT_BODY" ]; then
  PROBLEMS+=("失败正文命中 $BODY_HITS < 应失败参数数 $WANT_BODY —— 有参数不是因指定理由红的")
fi

if [ ${#PROBLEMS[@]} -eq 0 ]; then
  echo "NEGCTL-$CASE: PASS（逐参数预期全部对上；rc=${RC}）"
  exit 0
else
  printf 'NEGCTL-%s: FAIL —— %s\n' "$CASE" "$(IFS='; '; echo "${PROBLEMS[*]}")"
  exit 1
fi
