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
# ⚠️ 恢复保证的边界 (Codex 十五轮 LOW, 如实声明): 正常退出与常规信号由 EXIT trap
# 用备份恢复, 并在末尾逐字节比对; 但 SIGKILL/掉电/宿主崩溃时无法恢复 ——
# 该情况下用 `git checkout backend/scripts/validate_learning_events.py` 还原。
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

# run_pytest <-k 表达式> — 跑一次并回填 OUT / RC / COLLECTED
# round-16 (Codex 十五轮 MEDIUM): 原实现只 grep `^FAILED` —— collection error、
# internal error、0 collected 都会被当成"全绿"。现改为同时看 exit code 与收集数。
run_pytest() {
  OUT="$(cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q -k "$1" 2>&1)"
  RC=$?
  COLLECTED="$(grep -oE "[0-9]+ (passed|failed|deselected)" <<<"$OUT" | awk '{s+=$1} END {print s+0}')"
}

# expect_red <预期失败的测试名> <-k 表达式>
expect_red() {
  local expected="$1"
  run_pytest "$2"
  # pytest exit code: 0=全通过 1=有测试失败 2=中断 3=内部错 4=用法错 5=无测试
  if [ "$RC" -ne 1 ]; then
    fail "预期 exit code 1 (有测试失败), 实际 $RC — 可能是 collection/internal error 而非真的门变红"
    grep -E "ERROR|error" <<<"$OUT" | head -2 | sed 's/^/     /'
    return 1
  fi
  if [ "$COLLECTED" -eq 0 ]; then
    fail "0 个测试被收集 — 过滤表达式与实现漂移"
    return 1
  fi
  if ! grep -q "^FAILED .*::${expected}\b" <<<"$OUT"; then
    fail "预期 ${expected} 变红, 实际失败的是别的测试"
    grep "^FAILED" <<<"$OUT" | head -3 | sed 's/^/     /'
    return 1
  fi
  pass "${expected} 如期变红"
  grep -E "passed|failed" <<<"$OUT" | tail -1 | sed 's/^/     /'
  return 0
}

echo "=== 基线 (未改动): 五门应全绿 ==="
run_pytest "two_layer or bypass or tail or independent_oracle or genesis_anchor"
if [ "$RC" -ne 0 ]; then
  fail "基线 exit code $RC (期望 0) — 后续变体结论不可信"
elif [ "$COLLECTED" -eq 0 ]; then
  fail "基线 0 个测试被收集 — 后续变体结论不可信"
else
  pass "基线全绿 (exit 0, 收集 $COLLECTED 项)"
fi
grep -E "passed|failed" <<<"$OUT" | tail -1 | sed 's/^/     /'

echo
echo "=== 变体A: 尾部约束**递归**施于 ancestor (round-13 指出的另一种解释) ==="
echo "    正常链 L1=t1、L2=t2 的 ancestor(cursor=1) 会因 L2 存在而失效"
if mutate 's/            is_top_level=False,\n            _depth=depth \+ 1,/            is_top_level=True,\n            _depth=depth + 1,/'; then
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
if mutate 's/        if offenders:/        if False:/'; then
  expect_red test_genesis_anchor_is_really_anchored "genesis_anchor"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体F: genesis first_event_line 不校验 (round-15 Codex HIGH) ==="
if mutate 's/    if earliest is not None and first_line != earliest:/    if False:/'; then
  expect_red test_first_event_line_must_equal_earliest_node_event "first_event_line"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体G: 算法身份不绑 manifest (round-15 Codex HIGH) ==="
if mutate 's/        elif manifest is not None and version != manifest\["library_version"\]:/        elif False:/'; then
  expect_red "test_algorithm_identity_binds_to_golden_manifest\[fsrs_library_version-garbage" "algorithm_identity"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 还原后全量 ==="
FINAL="$(cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q 2>&1)"
FINAL_RC=$?
if [ "$FINAL_RC" -ne 0 ]; then
  fail "还原后 exit code $FINAL_RC — 脚本未正确恢复文件, 或存在真实失败"
  grep "^FAILED" <<<"$FINAL" | head -3 | sed 's/^/     /'
elif ! shasum -a 256 "$VALIDATOR" | grep -q "$(shasum -a 256 "$BAK" | cut -d' ' -f1)"; then
  fail "还原后校验器字节与备份不一致 — 恢复不完整"
else
  pass "还原后全绿且字节与备份逐字相同"
fi
grep -E "passed|failed" <<<"$FINAL" | tail -1 | sed 's/^/     /'

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: PASS — 全部门均为承重门"
  exit 0
fi
echo "RESULT: FAIL — $FAILURES 项不符预期"
exit 1
