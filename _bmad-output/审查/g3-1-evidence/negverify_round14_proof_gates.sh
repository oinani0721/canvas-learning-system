#!/usr/bin/env bash
# 负验证: 证明 proof 参考 verifier 的门是**承重的**, 不是真空通过。
#
# 背景 (Codex round-13 HIGH): "现有校验器和测试也没有 proof 行为实现, 十二轮
# 存证仅做文本计数, 无法消除该歧义"。本脚本把冻结条款逐一拆掉, 断言对应测试
# 必须变红 —— 若拆掉后仍全绿, 说明那条门是装饰品。
#
# round-15 机械化 (Codex round-14 MEDIUM: 原脚本只 grep 输出、不校验 perl 是否
# 命中、最终恒 exit 0 —— 三个替换模式全失配时 A/B/C 会"全绿"而脚本仍成功):
#   - 每个 mutation 断言 perl **恰好命中 1 处**, 未命中即 FAIL 退出;
#   - 每个变体断言 pytest **确实失败**, 且失败的正是**预期那条测试名**;
#   - 任一环节不符 ⇒ 脚本非零退出。
#
# 用法: bash negverify_round14_proof_gates.sh ; echo $?
# 期望: 全部 PASS, exit 0。

set -uo pipefail
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VALIDATOR="$WT/backend/scripts/validate_learning_events.py"
TESTS="$WT/backend/tests/regression/test_learning_events_schema_contract.py"
PY="/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python"
BAK="$(mktemp)"
cp "$VALIDATOR" "$BAK"
FAILURES=0
trap 'cp "$BAK" "$VALIDATOR"; rm -f "$BAK"' EXIT

fail() { echo "  ❌ $*"; FAILURES=$((FAILURES + 1)); }
pass() { echo "  ✅ $*"; }

# mutate <perl表达式> — 断言恰好命中 1 处
mutate() {
  local expr="$1"
  local before after
  before="$(shasum -a 256 "$VALIDATOR" | cut -d' ' -f1)"
  perl -0pi -e "$expr" "$VALIDATOR"
  after="$(shasum -a 256 "$VALIDATOR" | cut -d' ' -f1)"
  if [ "$before" = "$after" ]; then
    fail "mutation 未命中 (文件未变) — 模式已与实现漂移, 本变体结论无效"
    return 1
  fi
  return 0
}

# expect_red <预期失败的测试名> <-k 表达式>
expect_red() {
  local expected="$1" filter="$2" out
  out="$(cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q -k "$filter" 2>&1)"
  if ! grep -q "^FAILED .*::${expected}\b" <<<"$out"; then
    fail "预期 ${expected} 变红, 实际未失败"
    grep -E "passed|failed" <<<"$out" | tail -1
    return 1
  fi
  if ! grep -qE "^[0-9]+ failed|[0-9]+ failed," <<<"$(grep -E "failed" <<<"$out" | tail -1)"; then
    : # 汇总行形态因 pytest 版本而异, 上面的 FAILED 行已是充分判据
  fi
  pass "${expected} 如期变红"
  grep -E "passed|failed" <<<"$out" | tail -1 | sed 's/^/     /'
  return 0
}

echo "=== 基线 (未改动): 三门应全绿 ==="
BASE="$(cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q -k "two_layer or bypass or tail" 2>&1)"
if grep -q "^FAILED" <<<"$BASE"; then
  fail "基线就有失败 — 后续变体结论不可信"
else
  pass "基线全绿"
fi
grep -E "passed|failed" <<<"$BASE" | tail -1 | sed 's/^/     /'

echo
echo "=== 变体A: 尾部约束**递归**施于 ancestor (round-13 指出的另一种解释) ==="
echo "    正常链 L1=t1、L2=t2 的 ancestor(cursor=1) 会因 L2 存在而失效"
if mutate 's/_verify_proof_level\(\s*ancestor, applicable, ledger_path=ledger_path, is_top_level=False, _depth=_depth \+ 1\s*\)/_verify_proof_level(ancestor, applicable, ledger_path=ledger_path, is_top_level=True, _depth=_depth + 1)/s'; then
  expect_red test_normal_two_layer_chain_is_provable "two_layer or bypass"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体B: 拆掉跨层单调门 (round-12 反例的封堵) ==="
if mutate 's/if ancestor_end is not None and ancestor_end >= instants\[0\]:/if False:/'; then
  expect_red test_layered_split_cannot_bypass_monotonicity "two_layer or bypass"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体C: 拆掉最外层尾部门 (round-11 尾部逃逸的封堵) ==="
if mutate 's/    if is_top_level:\n        tail = sorted/    if False:\n        tail = sorted/'; then
  expect_red test_top_level_must_cover_ledger_tail "tail"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体D: state_hash 恒返回常量 (round-14 Codex: 同源循环下 14/14 仍全绿) ==="
if mutate 's/    return hashlib\.sha256\(blob\)\.hexdigest\(\), \[\]/    return "0" * 64, []/'; then
  expect_red test_canonical_state_hash_matches_independent_oracle "independent_oracle"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体E: genesis 原文 FSRS 字段检查失效 (round-14 Codex HIGH) ==="
if mutate 's/            if offenders:/            if False:/'; then
  expect_red test_genesis_anchor_is_really_anchored "genesis_anchor"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 还原后全量 ==="
FINAL="$(cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q 2>&1)"
if grep -q "^FAILED" <<<"$FINAL"; then
  fail "还原后仍有失败 — 脚本未正确恢复文件"
else
  pass "还原后全绿"
fi
grep -E "passed|failed" <<<"$FINAL" | tail -1 | sed 's/^/     /'

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: PASS — 全部门均为承重门"
  exit 0
fi
echo "RESULT: FAIL — $FAILURES 项不符预期"
exit 1
