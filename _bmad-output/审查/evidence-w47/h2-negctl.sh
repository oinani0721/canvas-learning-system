#!/usr/bin/env bash
# CARD-W4-7 (c) H-2 负控：把哨兵常量临时改成 "localhost"。
#
# 判据（卡文 (c) 明写「禁只贴汇总」）：
#   * 旧的 6 条 TestSelftestAddressClassification 用例**逐条**贴出 PASSED 原文；
#   * 新增的 test_selftest_host_is_an_unconnectable_sentinel 必须 FAILED
#     且失败正文含指定串（绑定「被哪一条断言拒的」，防更早的失败喂饱判据）；
#   * 还原 sha 前后逐字节相同。
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EV="$ROOT/_bmad-output/审查/evidence-w47"
GUARD="$ROOT/backend/tests/support/live_port_guard.py"
PY="$ROOT/backend/.venv/bin/python"
PYTEST="$ROOT/backend/.venv/bin/pytest"
CLS='tests/unit/test_live_port_guard_contract.py::TestSelftestAddressClassification'
NEW_NODE="$CLS::test_selftest_host_is_an_unconnectable_sentinel"
EXPECT='哨兵首字符必须是 NUL'
# 卡文 §〇 点名的、改常量后**仍应全绿**的 6 条旧用例
OLD6=(
  test_genuine_selftest_address_is_classified
  test_tuple_subclass_disguise_is_not_selftest
  test_str_subclass_eq_disguise_is_not_selftest
  test_non_tuple_is_not_selftest
  test_audit_hook_does_not_block_plain_safe_address
  test_genuine_selftest_address_reaches_blocking_path
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

echo "=== H-2 NEGCTL: _SELFTEST_HOST -> \"localhost\" ==="
echo "sha-before = $SHA_BEFORE"
"$PY" "$EV/negctl_patch_w47.py" apply h2 || exit $?
cd "$ROOT/backend" || exit 91
export PYTHONDONTWRITEBYTECODE=1

echo
echo "--- 旧 6 条在变异体上（逐条 PASSED 原文，禁只贴汇总）---"
OLD_PASS=0
for t in "${OLD6[@]}"; do
  LINE="$($PYTEST -q -p no:cacheprovider -v "$CLS::$t" 2>&1 | grep -E "::$t " | head -1)"
  echo "  $LINE"
  echo "$LINE" | grep -q PASSED && OLD_PASS=$((OLD_PASS + 1))
done
echo "旧 6 条 PASSED 计数 = $OLD_PASS / 6"

echo
echo "--- 新哨兵断言在同一个变异体上 ---"
NEW_OUT="$($PYTEST -q -p no:cacheprovider --tb=long "$NEW_NODE" 2>&1)"
echo "$NEW_OUT" | grep -E '^(FAILED|ERROR)|passed|failed' | head -3
echo "失败正文命中期望串 = $(echo "$NEW_OUT" | grep -cF "$EXPECT")"
echo "$NEW_OUT" | grep -E '^E ' | head -3

echo
if [ "$OLD_PASS" -eq 6 ] && echo "$NEW_OUT" | grep -qE '[0-9]+ failed' && echo "$NEW_OUT" | grep -qF "$EXPECT"; then
  echo "H2-NEGCTL: PASS（旧 6 条全绿 / 新断言以指定理由拦下）"
  exit 0
else
  echo "H2-NEGCTL: FAIL（old_pass=$OLD_PASS 期望串命中=$(echo "$NEW_OUT" | grep -cF "$EXPECT")）"
  exit 1
fi
