#!/usr/bin/env bash
# 复核负控（r1/r2）：证明自查复核新增的两道门在**修前形态**上必红。
# 纪律同 m7-negctl.sh：字节副本 + EXIT trap 无条件还原 + sha 前后比对。
set -uo pipefail
CASE="${1:?r1|r2}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EV="$ROOT/_bmad-output/审查/evidence-w44b"
GUARD="$ROOT/backend/tests/support/live_port_guard.py"
PY="$ROOT/backend/.venv/bin/python"
PYTEST="$ROOT/backend/.venv/bin/pytest"
case "$CASE" in
  r1) NODE='TestSettlementAtomicity::test_block_message_binds_the_reason_despite_a_hostile_repr'
      EXPECT='Regex pattern' ;;
  r2) NODE='TestSingleLedgerSnapshot::test_publish_ledger_refuses_stale_even_after_a_failed_write'
      EXPECT='陈旧快照反而写成功' ;;
esac
BACKUP="$(mktemp -d)"
cp -p "$GUARD" "$BACKUP/guard.py"
SHA_BEFORE="$(shasum -a 256 "$GUARD" | awk '{print $1}')"
restore() {
  local rc=$?
  cp -p "$BACKUP/guard.py" "$GUARD"
  local sha_after
  sha_after="$(shasum -a 256 "$GUARD" | awk '{print $1}')"
  echo "--- 还原 ---"
  echo "sha-before = $SHA_BEFORE"
  echo "sha-after  = $sha_after"
  if [ "$SHA_BEFORE" != "$sha_after" ]; then
    echo "RESTORE-MISMATCH"
    rm -rf "$BACKUP"
    exit 90
  fi
  echo "RESTORE-OK: sha-before == sha-after"
  rm -rf "$BACKUP"
  exit $rc
}
trap restore EXIT INT TERM
echo "=== REVIEW-NEGCTL case=$CASE 被测门: $NODE ==="
"$PY" "$EV/negctl_patch.py" apply "$CASE" || exit $?
cd "$ROOT/backend" || exit 91
export PYTHONDONTWRITEBYTECODE=1
OUT="$($PYTEST -q -p no:cacheprovider --tb=long "tests/unit/test_live_port_guard_contract.py::$NODE" 2>&1)"
echo "$OUT" | grep -E '^(FAILED|ERROR)|passed|failed' | head -3
echo "--- 失败正文（_ 限定行）---"
echo "$OUT" | grep -E '^E ' | head -6
if echo "$OUT" | grep -qE '[0-9]+ failed' && echo "$OUT" | grep -qF "$EXPECT"; then
  echo "REVIEW-NEGCTL-$CASE: PASS（门在修前形态上以指定理由拦下）"
else
  echo "REVIEW-NEGCTL-$CASE: FAIL（期望串命中=$(echo "$OUT" | grep -cF "$EXPECT")）"
fi
