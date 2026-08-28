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
BAK="$(mktemp)" || { echo "❌ mktemp 失败"; exit 1; }
cp "$VALIDATOR" "$BAK" || { echo "❌ 初始备份失败, 拒绝继续 (否则无法还原)"; exit 1; }
FAILURES=0
trap 'cp "$BAK" "$VALIDATOR"; rm -f "$BAK"' EXIT

fail() { echo "  ❌ $*"; FAILURES=$((FAILURES + 1)); }
pass() { echo "  ✅ $*"; }

# mutate <perl表达式> — 断言恰好命中 1 处
mutate() {
  local expr="$1" hits
  local before after
  before="$(shasum -a 256 "$VALIDATOR" | cut -d' ' -f1)"
  # round-16 Codex MEDIUM: 只比前后 SHA 不能排除"命中两处"。先用 /g 变体数命中数。
  hits="$(perl -0ne "\$n = () = (\$_ =~ s${expr#s}g); print \$n" "$VALIDATOR" 2>/dev/null || echo "?")"
  perl -0pi -e "$expr" "$VALIDATOR"
  after="$(shasum -a 256 "$VALIDATOR" | cut -d' ' -f1)"
  if [ "$before" = "$after" ]; then
    fail "mutation 未命中 (文件未变) — 模式已与实现漂移, 本变体结论无效"
    return 1
  fi
  if [ "$hits" != "1" ] && [ "$hits" != "?" ]; then
    fail "mutation 命中 $hits 处 (要求恰 1 处) — 变体语义不唯一"
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

# expect_red <预期失败的测试名 | 竖线分隔的多个> <-k 表达式>
# 一道门可以被多条测试覆盖 (如尾部门同时被 tail 与 out_of_order 两条依赖),
# 故判据是"失败集合 **子集于** 预期集合", 而不是"只有一条失败"。
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
  local first="${expected%%|*}"
  if ! grep -qE "^FAILED .*::(${expected})" <<<"$OUT"; then
    fail "预期 ${first} 变红, 实际失败的是别的测试"
    grep "^FAILED" <<<"$OUT" | head -3 | sed 's/^/     /'
    return 1
  fi
  # round-16 Codex MEDIUM: 只查"预期那条在失败列表里"不够 —— 无关的连带失败会让
  # "该门承重"的结论不成立。判据 = 失败集合 ⊆ 预期集合。
  local others
  others="$(grep "^FAILED" <<<"$OUT" | grep -cvE "::(${expected})" || true)"
  if [ "${others:-0}" -ne 0 ]; then
    fail "除预期的 ${expected} 外还有 ${others} 条失败 — 无法归因于该门"
    grep "^FAILED" <<<"$OUT" | grep -vE "::(${expected})" | head -3 | sed 's/^/     /'
    return 1
  fi
  if grep -qE "^ERROR|errors? during collection" <<<"$OUT"; then
    fail "输出含 ERROR/collection error"
    return 1
  fi
  pass "${first} 如期变红"
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
  expect_red "test_top_level_must_cover_ledger_tail|test_out_of_order_false_cannot_hide_tail_event" "tail"
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
echo "=== 变体H: earliest 退回最早**适用**行 (round-16 survivor) ==="
if mutate 's/    earliest = min\(scan\["node_event_lines"\]\) if \(scan and scan\["node_event_lines"\]\) else \(min\(lines\) if lines else None\)/    earliest = min(lines) if lines else None/'; then
  expect_red test_survivor_earliest_uses_all_node_events "survivor_earliest"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体I: stability 上界删除 (round-16 survivor) ==="
if mutate 's/    if isinstance\(stability, float\) and not \(0 < stability <= STABILITY_MAX\):/    if isinstance(stability, float) and not (0 < stability):/'; then
  expect_red test_survivor_stability_upper_bound_is_enforced "survivor_stability"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体J: 区间只查 library_version 哨兵 (round-16 survivor) ==="
if mutate 's/            for key in \("fsrs_library_version", "fsrs_params_hash"\)/            for key in ("fsrs_library_version",)/'; then
  expect_red test_survivor_params_hash_sentinel_in_interval "survivor_params_hash"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体K: out_of_order 退回"键存在即排除" (round-16 HIGH) ==="
if mutate 's/            if payload\["out_of_order"\] is True:/            if True:/'; then
  expect_red test_out_of_order_false_cannot_hide_tail_event "out_of_order_false"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 变体L: scheduler_config 退回 Python == 比较 (round-16 HIGH) ==="
if mutate 's/            if _canon\(config\) != _canon\(manifest\["scheduler_config"\]\):/            if config != manifest["scheduler_config"]:/'; then
  expect_red "test_scheduler_config_compared_by_canonical_json" "canonical_json"
fi
cp "$BAK" "$VALIDATOR"

echo
echo "=== 还原后全量 ==="
FINAL="$(cd "$WT/backend" && "$PY" -m pytest "$TESTS" -q 2>&1)"
FINAL_RC=$?
if [ "$FINAL_RC" -ne 0 ]; then
  fail "还原后 exit code $FINAL_RC — 脚本未正确恢复文件, 或存在真实失败"
  grep "^FAILED" <<<"$FINAL" | head -3 | sed 's/^/     /'
elif ! cmp -s "$VALIDATOR" "$BAK"; then
  fail "还原后校验器与备份不逐字节相同 (cmp) — 恢复不完整"
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
