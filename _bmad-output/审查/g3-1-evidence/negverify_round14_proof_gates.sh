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
# ⚠️ 判据的诚实边界 (round-18 Codex MEDIUM, 如实登记而非假装闭合):
#   预期测试**体内**的运行时异常 (如误写 1/0) 也会被 pytest 记作 FAILED、RC=1,
#   本脚本无法与「门真的变红」区分。缓解 = 基线段先确认这些测试未改动时全绿;
#   若某变体的红源自异常而非断言失败, 需人工看输出判别。
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
# round-18 Codex LOW: EXIT trap 的 cp 原本不查返回码 —— 异常退出时恢复失败会静默
cleanup() {
  cp "$BAK" "$VALIDATOR" || echo "  ❌ EXIT trap 恢复失败! 请手动从 git 还原 $VALIDATOR"
  rm -f "$BAK"
}
trap cleanup EXIT

fail() { echo "  ❌ $*"; FAILURES=$((FAILURES + 1)); }
# round-17 Codex MEDIUM: 中间恢复的 cp 原本不查返回码 —— 恢复失败会让后续变体
# 全部跑在污染文件上, 结论不可信
restore() { cp "$BAK" "$VALIDATOR" || { echo "  ❌ 恢复失败, 中止 (用 git checkout 还原)"; return 1; }; }
pass() { echo "  ✅ $*"; }

# mutate <perl表达式> — 断言恰好命中 1 处
mutate() {
  local expr="$1" hits
  local before after
  before="$(shasum -a 256 "$VALIDATOR" | cut -d' ' -f1)"
  # round-16 Codex MEDIUM: 只比前后 SHA 不能排除"命中两处"。先用 /g 变体数命中数。
  hits="$(perl -0ne "\$n = () = (\$_ =~ s${expr#s}g); print \$n" "$VALIDATOR" 2>/dev/null)" || hits=""
  # round-17 Codex MEDIUM: 原实现把计数失败降级为 "?" 并放行 —— 计数不出来
  # 就等于不知道变体语义是否唯一, 必须失败而不是放行
  if [ -z "$hits" ]; then
    fail "无法统计 mutation 命中次数 — 变体语义不可证, 拒绝据此下结论"
    return 1
  fi
  if [ "$hits" != "1" ]; then
    fail "mutation 命中 $hits 处 (要求恰 1 处) — 变体语义不唯一"
    return 1
  fi
  if ! perl -0pi -e "$expr" "$VALIDATOR"; then
    fail "perl mutation 返回非零 — 可能已部分改写, 本变体结论无效"
    return 1
  fi
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
  # round-20 Codex MEDIUM: 原实现对整份输出做全局 grep, 汇总行与 short summary
  # 会被重复累加 (实际 171 项算成 334)。只取**最后一行汇总**再累加。
  COLLECTED="$(grep -E "(passed|failed|deselected|no tests ran)" <<<"$OUT" | tail -1 \
    | grep -oE "[0-9]+ (passed|failed|deselected)" | awk '{s+=$1} END {print s+0}')"
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
  local first="${expected%%|*}" name
  # round-17 Codex MEDIUM: "⊆ 预期集合"只要求至少一条预期项变红 —— 多测试场景下
  # 其余预期项即便没红也会被判承重。改为**每一条预期项都必须变红**。
  # round-22 Codex MEDIUM: 预期项写**参数化基名**时, `^FAILED .*::name` 只要
  # 任一实例红就通过, 无法机械证明"该门覆盖的全部实例都红"。故对基名额外要求:
  # 该基名在**收集面**里有几个实例, 失败集合里就必须有几个。
  local IFS_SAVE="$IFS"; IFS='|'
  for name in $expected; do
    if ! grep -qE "^FAILED .*::${name}" <<<"$OUT"; then
      IFS="$IFS_SAVE"
      fail "预期 ${name} 变红, 实际未失败"
      grep "^FAILED" <<<"$OUT" | head -3 | sed 's/^/     /'
      return 1
    fi
    # 基名 (不带 [ ]) 才做实例数核对
    if [[ "$name" != *"["* ]]; then
      local want got
      want="$(cd "$WT/backend" && "$PY" -m pytest "$TESTS" --collect-only -q 2>/dev/null \
        | grep -cE "::${name}(\[|$)")"
      got="$(grep -cE "^FAILED .*::${name}(\[|$)" <<<"$OUT")"
      if [ "${want:-0}" -gt 0 ] && [ "${got:-0}" -ne "${want:-0}" ]; then
        IFS="$IFS_SAVE"
        fail "${name} 收集到 ${want} 个实例但只有 ${got} 个变红 — 无法证明该门覆盖的全部实例都失效"
        return 1
      fi
    fi
  done
  IFS="$IFS_SAVE"
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
restore || exit 1

echo
echo "=== 变体B: 拆掉跨层单调门 (round-12 反例的封堵) ==="
if mutate 's/if ancestor_end is not None and ancestor_end >= instants\[0\]:/if False:/'; then
  expect_red test_layered_split_cannot_bypass_monotonicity "two_layer or bypass"
fi
restore || exit 1

echo
echo "=== 变体C: 拆掉最外层尾部门 (round-11 尾部逃逸的封堵) ==="
if mutate 's/    if is_top_level:\n        tail = sorted/    if False:\n        tail = sorted/'; then
  expect_red "test_top_level_must_cover_ledger_tail|test_out_of_order_false_cannot_hide_tail_event" "tail"
fi
restore || exit 1

echo
echo "=== 变体D: state_hash 恒返回常量 (round-14 Codex: 同源循环下 14/14 仍全绿) ==="
if mutate 's/    return hashlib\.sha256\(blob\)\.hexdigest\(\), \[\]/    return "0" * 64, []/'; then
  expect_red test_canonical_state_hash_matches_independent_oracle "independent_oracle"
fi
restore || exit 1

echo
echo "=== 变体E: genesis 原文 FSRS 字段检查失效 (round-14 Codex HIGH) ==="
if mutate 's/        if offenders:/        if False:/'; then
  expect_red test_genesis_anchor_is_really_anchored "genesis_anchor"
fi
restore || exit 1

echo
echo "=== 变体F: genesis first_event_line 不校验 (round-15 Codex HIGH) ==="
if mutate 's/    if earliest is not None and first_line != earliest:/    if False:/'; then
  expect_red test_first_event_line_must_equal_earliest_node_event "first_event_line"
fi
restore || exit 1

echo
echo "=== 变体G: 算法身份不绑 manifest (round-15 Codex HIGH) ==="
if mutate 's/        elif manifest is not None and version != manifest\["library_version"\]:/        elif False:/'; then
  expect_red "test_algorithm_identity_binds_to_golden_manifest\[fsrs_library_version-garbage-[^]]*\]" "algorithm_identity"
fi
restore || exit 1

echo
echo "=== 变体H: earliest 退回最早**适用**行 (round-16 survivor) ==="
if mutate 's/    earliest = min\(scan\["node_event_lines"\]\) if \(scan and scan\["node_event_lines"\]\) else \(min\(lines\) if lines else None\)/    earliest = min(lines) if lines else None/'; then
  expect_red test_survivor_earliest_uses_all_node_events "survivor_earliest"
fi
restore || exit 1

echo
echo "=== 变体I: stability 上界删除 (round-16 survivor) ==="
if mutate 's/    if isinstance\(stability, float\) and not \(0 < stability <= STABILITY_MAX\):/    if isinstance(stability, float) and not (0 < stability):/'; then
  expect_red test_survivor_stability_upper_bound_is_enforced "survivor_stability"
fi
restore || exit 1

echo
echo "=== 变体J: 区间只查 library_version 哨兵 (round-16 survivor) ==="
if mutate 's/            for key in \("fsrs_library_version", "fsrs_params_hash"\)/            for key in ("fsrs_library_version",)/'; then
  expect_red test_survivor_params_hash_sentinel_in_interval "survivor_params_hash"
fi
restore || exit 1

echo
echo "=== 变体K: out_of_order 退回"键存在即排除" (round-16 HIGH) ==="
if mutate 's/            if payload\["out_of_order"\] is not True:\n                problems.append\(/            if payload["out_of_order"] is not True:\n                continue\n                problems.append(/'; then
  expect_red test_out_of_order_false_cannot_hide_tail_event "out_of_order_false"
fi
restore || exit 1

echo
echo "=== 变体L: scheduler_config 退回 Python == 比较 (round-16 HIGH) ==="
if mutate 's/            if _canon\(config\) != _canon\(manifest\["scheduler_config"\]\):/            if config != manifest["scheduler_config"]:/'; then
  expect_red "test_scheduler_config_compared_by_canonical_json\[config0-enable_fuzzing\]|test_scheduler_config_compared_by_canonical_json\[config1-learning_steps_minutes\]" "canonical_json"
fi
restore || exit 1

echo
echo "=== 变体M: manifest 残缺不再 fail-closed (round-17 HIGH) ==="
if mutate 's/        elif manifest is not None and not _manifest_config_usable\(manifest\):/        elif False:/'; then
  expect_red test_partially_corrupt_manifest_fails_closed "partially_corrupt_manifest"
fi
restore || exit 1

echo
echo "=== 变体N: out_of_order 语义门失效 (round-17 HIGH) ==="
if mutate 's/                if marked_at is not None and marked_at.tzinfo is not None and \(not prior or marked_at > max\(prior\)\):/                if False:/'; then
  expect_red test_out_of_order_true_cannot_disguise_a_real_successor "disguise_a_real_successor"
fi
restore || exit 1

echo
echo "=== 变体O: vault 无证据不再 fail-closed (round-17 HIGH) ==="
if mutate 's/            if not vault_ids and ledger_vault_id is None:/            if False:/'; then
  expect_red "test_vault_identity_without_evidence_fails_closed\\[none\\]" "without_evidence"
fi
restore || exit 1

echo
echo "=== 变体P: 递归不再共享账本事实 (round-17 survivor) ==="
if mutate 's/            scan=scan,\n            ledger_raw=ledger_raw,\n            ledger_vault_id=ledger_vault_id,/            scan=None,\n            ledger_raw=None,\n            ledger_vault_id=None,/'; then
  expect_red test_survivor_recursion_shares_ledger_facts "recursion_shares"
fi
restore || exit 1

echo
echo "=== 变体Q: vault 收集退回 out_of_order 的 continue 之后 (round-18 HIGH) ==="
echo "    round-20 Codex: 原变体是**删除**收集 (靠「无 vault 证据」的替代 fail-closed 变红),"
echo "    不能证明「次序」本身承重。现忠实地把收集移到 continue 之后。"
if mutate 's/        vault_id = payload.get\("vault_id"\)\n        if isinstance\(vault_id, str\) and vault_id:\n            scan\["vault_ids"\].add\(vault_id\)\n            scan\["vault_id_lines"\].add\(idx\)\n        scan\["review_ext_lines"\].append\(idx\)\n/        scan["review_ext_lines"].append(idx)\n/' \
   && mutate 's/        review_time = payload.get\("review_time"\)\n/        vault_id = payload.get("vault_id")\n        if isinstance(vault_id, str) and vault_id:\n            scan["vault_ids"].add(vault_id)\n            scan["vault_id_lines"].add(idx)\n        review_time = payload.get("review_time")\n/'; then
  # round-21 Codex MEDIUM: 原先只期待 proof 级那条, 但它变红是被「仅 N/M 条带
  # vault_id」这条**替代**门拒绝的, 归因不成立。新增的纯 scanner 事实门失败
  # **只可能**因为收集次序变了 —— 归因落在它身上。
  # ⚠️ round-22 Codex 称该 mutation 完整套件下 3 红 (含 vault 覆盖率门), 但本机
  # 实测**只有 2 红** —— 过滤器已选中覆盖率门而它未失败 (该门的 ooo 行本就
  # 不带 vault_id, 分母口径不受收集次序影响)。以实测为准, 分歧如实记录。
  expect_red "test_scanner_collects_vault_from_out_of_order_rows|test_genuine_out_of_order_cannot_hide_another_vault" "hide_another_vault or collects_vault or coverage_denominator"
fi
restore || exit 1

echo
echo "=== 变体R: 乱序比较改 >= (round-18 survivor: 误拒 review_time == W) ==="
if mutate 's/and \(not prior or marked_at > max\(prior\)\):/and (not prior or marked_at >= max(prior)):/'; then
  expect_red test_out_of_order_at_exactly_watermark_is_not_misrejected "exactly_watermark"
fi
restore || exit 1

echo
echo "=== 变体S: 范围声明三处同文门 (round-18 MEDIUM) ==="
if mutate 's/#   ① 不复算 FSRS 折叠/#   ① 不复算 FSRS 折叠 (漂移测试)/'; then
  expect_red test_scope_declaration_is_identical_in_three_places "identical_in_three_places"
fi
restore || exit 1

echo
echo "=== 变体T: 拆掉「部分行带 vault_id」分支 (round-19: 与变体O 是两个不同的门) ==="
if mutate 's/            elif vault_ids and len\(vault_ids\) == 1:/            elif False:/'; then
  expect_red "test_vault_identity_without_evidence_fails_closed\[partial\]" "without_evidence"
fi
restore || exit 1

echo
echo "=== 变体U: 缺 node_id 的记录退回静默跳过 (round-20 MEDIUM) ==="
if mutate 's/        if not isinstance\(raw_node, str\):\n            scan\["unroutable_lines"\].append\(idx\)\n            continue/        if not isinstance(raw_node, str):\n            continue/'; then
  # 同一道门被两条测试覆盖: 语义门 + 非字符串 node_id 的五个参数实例
  expect_red "test_v2_without_node_id_is_unroutable_not_silently_skipped|test_non_string_node_id_is_unroutable|test_float_node_id_is_unroutable" "unroutable"
fi
restore || exit 1

echo
echo "=== 变体V: 版本判断前移到 node 过滤之前 (round-20 误拒方向 survivor) ==="
if mutate 's/        if raw_node != node_id:\n            continue\n/        if record.get("event_version") != EVENT_VERSION:\n            scan["unknown_version_lines"].append(idx)\n            continue\n        if raw_node != node_id:\n            continue\n/'; then
  expect_red test_v2_of_another_node_does_not_false_reject "another_node"
fi
restore || exit 1

echo
echo "=== 变体W: 主体校验器不再执行路由信封 (round-21 MEDIUM) ==="
if mutate 's/                for key, ok in \(\n                    \("event_id", isinstance\(record.get\("event_id"\), str\) and bool\(record\["event_id"\]\)\),\n                    \("node_id", isinstance\(record.get\("node_id"\), str\)\),\n                \):/                for key, ok in ():/'; then
  expect_red "test_main_validator_enforces_routing_envelope\[.*node_id\]|test_main_validator_enforces_routing_envelope\[.*event_id\]" "enforces_routing_envelope"
fi
restore || exit 1

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
