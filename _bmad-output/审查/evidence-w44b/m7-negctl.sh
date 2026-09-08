#!/usr/bin/env bash
# CARD-W4-4b 负控跑器：把 Codex 点名的宽松写法临时写进生产代码，
# 让**旧门**与**新门**在同一个变异体上各跑一次 —— 旧门绿 / 新门红才算收紧成立。
#
# 用法: bash _bmad-output/审查/evidence-w44b/m7-negctl.sh <1|2|3|4|5a|5b|m4>
#
# 安全（手册 §四.1.7）：
#   * 变异前把被改文件按字节存副本，EXIT trap **无条件**从副本还原（含 SIGTERM/SIGINT）；
#   * 还原后 shasum -a 256 前后逐字节比对，不同即 RESTORE-MISMATCH 报错；
#   * 禁 git stash / git checkout HEAD -- <path>（前者跨 worktree 共享，后者清暂存区）。
#
# 判据（不只看红绿）：
#   * 旧门必须 passed；新门必须 failed **且失败正文含指定串** —— 只断 rc!=0 会被
#     「模块导不进来」这类更早的失败喂饱（假杀）。
set -uo pipefail

CASE="${1:?用法: m7-negctl.sh <1|2|3|4|5a|5b|m4>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EV="$ROOT/_bmad-output/审查/evidence-w44b"
GUARD="$ROOT/backend/tests/support/live_port_guard.py"
CONTRACT="$ROOT/backend/tests/unit/test_live_port_guard_contract.py"
OLD_CONTRACT="$ROOT/backend/tests/unit/test_negctl_old_live_port_guard_contract.py"
PY="$ROOT/backend/.venv/bin/python"
PYTEST="$ROOT/backend/.venv/bin/pytest"
BACKUP="$(mktemp -d)"

case "$CASE" in
  1)  NODE='TestSettlementAtomicity::test_finalize_and_snapshot_sets_the_flag_and_snapshots_under_one_lock'
      EXPECT='结算的临界区锁的不是 self._lock' ;;
  2)  NODE='TestSettlementAtomicity::test_settlement_path_never_nests_the_lock'
      EXPECT='不在已持锁 helper' ;;
  3)  NODE='TestSettlementAtomicity::test_audit_hook_reads_the_settlement_state_through_record'
      EXPECT='.finalizing 属性访问' ;;
  4)  NODE='TestInstallOrder::test_audit_hook_is_installed_before_the_target_precheck'
      EXPECT='承重 hook 装在预检之后' ;;
  5a) NODE='TestFinalizeRaceSeam::test_seam_is_called_unconditionally_not_inside_a_condition'
      EXPECT='注入点落在恒假分支里' ;;
  5b) NODE='TestFinalizeRaceSeam::test_seam_is_called_unconditionally_not_inside_a_condition'
      EXPECT='注入点不在受拦分支内' ;;
  m4) NODE='' ; EXPECT='' ;;
  *)  echo "未知 case: $CASE"; exit 64 ;;
esac

cp -p "$GUARD" "$BACKUP/guard.py"
SHA_BEFORE="$(shasum -a 256 "$GUARD" | awk '{print $1}')"

restore() {
  local rc=$?
  cp -p "$BACKUP/guard.py" "$GUARD"
  rm -f "$OLD_CONTRACT"
  local sha_after
  sha_after="$(shasum -a 256 "$GUARD" | awk '{print $1}')"
  echo "--- 还原 ---"
  echo "sha-before = $SHA_BEFORE"
  echo "sha-after  = $sha_after"
  if [ "$SHA_BEFORE" != "$sha_after" ]; then
    echo "RESTORE-MISMATCH: 生产文件没还原干净 ⛔"
    rm -rf "$BACKUP"
    exit 90
  fi
  echo "RESTORE-OK: sha-before == sha-after"
  rm -rf "$BACKUP"
  exit $rc
}
trap restore EXIT INT TERM

echo "=== NEGCTL case=$CASE ==="
echo "被测门: ${NODE:-<M4 探针>}"
echo "期望新门失败正文含: ${EXPECT:-<见探针 reason>}"
echo

# 旧门取自本卡开工前那一 commit（钉死，不用动态 HEAD —— 本卡合入后 HEAD 已是新门，
# 再跑会把新门当旧门，对照变成自证；Codex round-1 LOW）。
BASE_SHA="10c80be7"
git -C "$ROOT" show "${BASE_SHA}:backend/tests/unit/test_live_port_guard_contract.py" > "$OLD_CONTRACT"

cd "$ROOT/backend" || exit 91
export PYTHONDONTWRITEBYTECODE=1

echo "--- 打变异 ---"
"$PY" "$EV/negctl_patch.py" apply "$CASE" || exit $?
echo

if [ "$CASE" = "m4" ]; then
  echo "--- M4 修前对照：结算路径退回直接 write_ledger ---"
  "$PY" scripts/lifespan_isolation_guard_probes.py 2>&1 \
    | grep -E 'late-ledger-survives-stale-final-write|原因:|GUARD-PROBES'
  exit 0
fi

echo "--- 旧门（HEAD 那一版）在同一个变异体上 ---"
OLD_OUT="$("$PYTEST" -q -p no:cacheprovider --tb=line \
  "tests/unit/test_negctl_old_live_port_guard_contract.py::$NODE" 2>&1)"
echo "$OLD_OUT" | grep -E '^(FAILED|ERROR)|passed|failed|no tests ran' | head -3
OLD_VERDICT=fail
echo "$OLD_OUT" | grep -qE '^1 passed|， *1 passed|1 passed' && OLD_VERDICT=pass
echo "OLD-GATE: $OLD_VERDICT"
echo

echo "--- 新门（本卡收紧后）在同一个变异体上 ---"
NEW_OUT="$("$PYTEST" -q -p no:cacheprovider --tb=long \
  "tests/unit/test_live_port_guard_contract.py::$NODE" 2>&1)"
echo "$NEW_OUT" | grep -E '^(FAILED|ERROR)|passed|failed' | head -3
NEW_VERDICT=pass
echo "$NEW_OUT" | grep -qE '1 failed' && NEW_VERDICT=fail
echo "NEW-GATE: $NEW_VERDICT"
echo "新门失败正文命中期望串: $(echo "$NEW_OUT" | grep -cF "$EXPECT") 处"
echo "$NEW_OUT" | grep -F "$EXPECT" | head -2
echo

if [ "$OLD_VERDICT" = "pass" ] && [ "$NEW_VERDICT" = "fail" ] && echo "$NEW_OUT" | grep -qF "$EXPECT"; then
  echo "NEGCTL-$CASE: PASS（旧门放行 / 新门以指定理由拦下）"
  exit 0
else
  echo "NEGCTL-$CASE: FAIL（old=$OLD_VERDICT new=$NEW_VERDICT 期望串命中=$(echo "$NEW_OUT" | grep -cF "$EXPECT")）"
  exit 1
fi
