#!/usr/bin/env bash
# CARD-W4-7 (d) M-1 负控：分类器末行改成只判 `type(host) is str`
# （Codex 原话：这样改，该类六个测试仍能满足）。
#
# 判据：旧 6 条逐条 PASSED 原文 / 新增 3 条逐条 FAILED；还原 sha 前后同。
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EV="$ROOT/_bmad-output/审查/evidence-w47"
GUARD="$ROOT/backend/tests/support/live_port_guard.py"
PY="$ROOT/backend/.venv/bin/python"
PYTEST="$ROOT/backend/.venv/bin/pytest"
CLS='tests/unit/test_live_port_guard_contract.py::TestSelftestAddressClassification'
OLD6=(
  test_genuine_selftest_address_is_classified
  test_tuple_subclass_disguise_is_not_selftest
  test_str_subclass_eq_disguise_is_not_selftest
  test_non_tuple_is_not_selftest
  test_audit_hook_does_not_block_plain_safe_address
  test_genuine_selftest_address_reaches_blocking_path
)
NEW3=(
  test_plain_ipv4_on_blocked_port_is_not_selftest
  test_plain_hostname_on_blocked_port_is_not_selftest
  test_plain_ipv6_four_tuple_on_blocked_port_is_not_selftest
)
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

echo "=== M-1 NEGCTL: _is_selftest_address 末行 -> 只判 type(host) is str ==="
echo "sha-before = $SHA_BEFORE"
"$PY" "$EV/negctl_patch_w47.py" apply m1 || exit $?
cd "$ROOT/backend" || exit 91
export PYTHONDONTWRITEBYTECODE=1

echo
echo "--- 旧 6 条在变异体上（逐条原文）---"
OLD_PASS=0
for t in "${OLD6[@]}"; do
  LINE="$($PYTEST -q -p no:cacheprovider -v "$CLS::$t" 2>&1 | grep -E "::$t " | head -1)"
  echo "  $LINE"
  echo "$LINE" | grep -q PASSED && OLD_PASS=$((OLD_PASS + 1))
done
echo "旧 6 条 PASSED 计数 = $OLD_PASS / 6"

echo
echo "--- 新 3 条在同一个变异体上（逐条原文）---"
NEW_FAIL=0
for t in "${NEW3[@]}"; do
  LINE="$($PYTEST -q -p no:cacheprovider -v "$CLS::$t" 2>&1 | grep -E "::$t " | head -1)"
  echo "  $LINE"
  echo "$LINE" | grep -q FAILED && NEW_FAIL=$((NEW_FAIL + 1))
done
echo "新 3 条 FAILED 计数 = $NEW_FAIL / 3"

echo
if [ "$OLD_PASS" -eq 6 ] && [ "$NEW_FAIL" -eq 3 ]; then
  echo "M1-NEGCTL: PASS（旧 6 条全绿 / 新 3 条全红）"
  exit 0
else
  echo "M1-NEGCTL: FAIL（old_pass=$OLD_PASS new_fail=$NEW_FAIL）"
  exit 1
fi
