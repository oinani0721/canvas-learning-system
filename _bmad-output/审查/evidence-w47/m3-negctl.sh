#!/usr/bin/env bash
# CARD-W4-7 (e) M-3 翻转对照：把预检从 guard_plugin 的 pytest_configure 里**摘走**，
# 同一个最小 pytest 会话必须**不再** fail-closed。
#
# 这才是「入口保留了预检」的翻转用例：正探针只证明「现在拦住了」，
# 摘掉之后仍然拦住，说明拦它的是别的层（判据没绑定到 pytest_configure 这一层）。
#
# 纪律：字节副本 + EXIT trap 无条件还原 + shasum 前后逐字节同。
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PLUGIN="$ROOT/backend/tests/support/guard_plugin.py"
PY="$ROOT/backend/.venv/bin/python"
MARK='不在允许的测试端口白名单'
BACKUP="$(mktemp -d)"
SESSION="$(mktemp -d)"
printf 'def test_smoke():\n    assert True\n' > "$SESSION/test_smoke.py"
cp -p "$PLUGIN" "$BACKUP/guard_plugin.py"
SHA_BEFORE="$(shasum -a 256 "$PLUGIN" | awk '{print $1}')"
restore() {
  local rc=$?
  cp -p "$BACKUP/guard_plugin.py" "$PLUGIN"
  local sha_after
  sha_after="$(shasum -a 256 "$PLUGIN" | awk '{print $1}')"
  echo "--- 还原 ---"
  echo "sha-before = $SHA_BEFORE"
  echo "sha-after  = $sha_after"
  rm -rf "$BACKUP" "$SESSION"
  if [ "$SHA_BEFORE" != "$sha_after" ]; then
    echo "RESTORE-MISMATCH"
    exit 90
  fi
  echo "RESTORE-OK: sha-before == sha-after"
  exit $rc
}
trap restore EXIT INT TERM

run_session() {   # $1 = NEO4J_TEST_URI
  cd "$ROOT/backend" || exit 91
  env -u NEO4J_URI -u NEO4J_TEST_URI -u NEO4J_PASSWORD \
      PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/backend" NEO4J_TEST_URI="$1" \
      "$PY" -m pytest -q -p no:cacheprovider -p tests.support.guard_plugin "$SESSION" 2>&1
}

echo "=== M-3 翻转对照：预检在 / 不在 pytest_configure ==="
echo "sha-before = $SHA_BEFORE"

echo
echo "--- 跑法 A（现状：预检在 pytest_configure 里）URI -> 受拦端口 7691 ---"
OUT_A="$(run_session bolt://127.0.0.1:7691)"; RC_A=$?
echo "rc=$RC_A ; 拒因串命中=$(echo "$OUT_A" | grep -cF "$MARK")"
echo "$OUT_A" | grep -F "$MARK" | head -1

echo
echo "--- 摘掉预检（只删 guard_plugin 里那一行调用）---"
"$PY" - "$PLUGIN" <<'PYEOF'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
old = "    live_port_guard.assert_test_uri_not_blocked()\n"
assert s.count(old) == 1, f"锚点出现 {s.count(old)} 次（期望 1）"
p.write_text(s.replace(old, "    pass  # 负控：预检被摘走\n", 1), encoding="utf-8")
print("MUTANT-APPLIED: 预检已从 pytest_configure 摘走")
PYEOF

echo
echo "--- 跑法 B（对照：预检不在入口里）同一个 URI -> 受拦端口 7691 ---"
OUT_B="$(run_session bolt://127.0.0.1:7691)"; RC_B=$?
echo "rc=$RC_B ; 拒因串命中=$(echo "$OUT_B" | grep -cF "$MARK")"

echo
if [ "$RC_A" -ne 0 ] && echo "$OUT_A" | grep -qF "$MARK" && [ "$RC_B" -eq 0 ] && ! echo "$OUT_B" | grep -qF "$MARK"; then
  echo "M3-NEGCTL: PASS（A 因预检 fail-closed / B 摘掉后不再 fail-closed ⇒ 拦它的确实是入口里那一行）"
  exit 0
else
  echo "M3-NEGCTL: FAIL（rc_A=$RC_A rc_B=$RC_B）"
  exit 1
fi
