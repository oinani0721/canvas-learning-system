#!/usr/bin/env bash
# Codex round-1 LOW#5 的收口证据：死锁回退（repr 挪回锁内）发生时，
# 整条 pytest 进程是「一条目标失败 + 有界退出码」，不是「session 挂住」。
#
# 判据（三件都要）：
#   1. pytest 进程在 watchdog 时限内自己退出（HUNG = FAIL）；
#   2. 退出码非零且失败正文含死锁门的指定断言串；
#   3. 还原 sha 前后一致。
# 纪律同 m7-negctl.sh：字节副本 + EXIT trap 无条件还原 + sha 复核。
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EV="$ROOT/_bmad-output/审查/evidence-w44b"
GUARD="$ROOT/backend/tests/support/live_port_guard.py"
PY="$ROOT/backend/.venv/bin/python"
PYTEST="$ROOT/backend/.venv/bin/pytest"
NODE='tests/unit/test_live_port_guard_contract.py::TestSettlementAtomicity::test_record_does_not_deadlock_when_repr_reads_the_ledger'
EXPECT='record() 挂住了'
WATCHDOG=180
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

echo "=== 死锁回退 · 整进程有界退出验证（Codex round-1 LOW#5）==="
"$PY" "$EV/negctl_patch.py" apply r3 || exit $?
cd "$ROOT/backend" || exit 91
export PYTHONDONTWRITEBYTECODE=1
OUTF="$EV/deadlock-bounded-run.txt"
: > "$OUTF"
"$PYTEST" -q -p no:cacheprovider --tb=short "$NODE" > "$OUTF" 2>&1 &
PID=$!
SEEN_EXIT=0
for i in $(seq 1 "$WATCHDOG"); do
  if ! kill -0 "$PID" 2>/dev/null; then
    SEEN_EXIT=1
    break
  fi
  sleep 1
done
if [ "$SEEN_EXIT" != "1" ]; then
  echo "HUNG: pytest 进程 ${WATCHDOG}s 后仍活着 -- 死锁门的失败形态是挂 session"
  kill -TERM "$PID" 2>/dev/null
  wait "$PID" 2>/dev/null
  echo "DEADLOCK-BOUNDED-EXIT: FAIL（HUNG）"
  exit 1
fi
wait "$PID"
RC=$?
echo "pytest 退出码 = ${RC} (有界退出)"
grep -E '^(FAILED|ERROR)|passed|failed' "$OUTF" | head -3
HITS=$(grep -cF "$EXPECT" "$OUTF")
echo "目标断言串命中 = ${HITS}"
if [ "$RC" -ne 0 ] && [ "$HITS" -ge 1 ]; then
  echo "DEADLOCK-BOUNDED-EXIT: PASS (回退产生一条目标失败，进程有界退出 rc=${RC})"
else
  echo "DEADLOCK-BOUNDED-EXIT: FAIL (rc=${RC} hits=${HITS})"
  exit 1
fi
