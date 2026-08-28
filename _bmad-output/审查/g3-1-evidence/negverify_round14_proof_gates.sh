#!/usr/bin/env bash
# round-14 负验证: 证明 proof 参考 verifier 的三道门是**承重的**, 不是真空通过。
#
# 背景 (Codex round-13 HIGH): "现有校验器和测试也没有 proof 行为实现, 十二轮
# 存证仅做文本计数, 无法消除该歧义"。本脚本把三条冻结逐一拆掉, 断言对应测试
# 必须变红 —— 若拆掉后仍全绿, 说明那条门是装饰品。
#
# 用法: bash negverify_round14_proof_gates.sh
# 期望: 三个变体各红 1 条, 且恰好是对应的那一条; 还原后全绿。

set -uo pipefail
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VALIDATOR="$WT/backend/scripts/validate_learning_events.py"
TESTS="$WT/backend/tests/regression/test_learning_events_schema_contract.py"
PY="/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python"
BAK="$(mktemp)"
cp "$VALIDATOR" "$BAK"
trap 'cp "$BAK" "$VALIDATOR"; rm -f "$BAK"' EXIT

run() {  # run <-k 表达式>
  (cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q -k "$1" 2>&1 | grep -E "(^FAILED|[0-9]+ (passed|failed))" )
}

echo "=== 基线 (未改动) ==="
run "two_layer or bypass or tail"

echo
echo "=== 变体A: 尾部约束**递归**施于 ancestor (round-13 指出的另一种解释) ==="
echo "    期望: test_normal_two_layer_chain_is_provable 变红"
echo "    —— 正常链 L1=t1、L2=t2 的 ancestor(cursor=1) 会因 L2 存在而失效"
perl -0pi -e 's/verify_degraded_proof\(ancestor, applicable, is_top_level=False, _depth=_depth \+ 1\)/verify_degraded_proof(ancestor, applicable, is_top_level=True, _depth=_depth + 1)/' "$VALIDATOR"
run "two_layer or bypass"
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体B: 拆掉跨层单调门 (round-12 反例的封堵) ==="
echo "    期望: test_layered_split_cannot_bypass_monotonicity 变红"
perl -0pi -e 's/if ancestor_end is not None and ancestor_end >= instants\[0\]:/if False:/' "$VALIDATOR"
run "two_layer or bypass"
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体C: 拆掉最外层尾部门 (round-11 尾部逃逸的封堵) ==="
echo "    期望: test_top_level_must_cover_ledger_tail 变红"
perl -0pi -e 's/    if is_top_level:\n        tail = sorted/    if False:\n        tail = sorted/' "$VALIDATOR"
run "tail"
cp "$BAK" "$VALIDATOR"

echo
echo "=== 还原后全量 ==="
(cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q 2>&1 | grep -E "passed|failed" | tail -1)
