#!/bin/bash
# CARD-G8-2 (BATCH-2026-09-01-第八批) — 变异负验证 (串行, 还原逐字节比对)
# 判据 (Codex round-1 HIGH-7 收紧): rc==1 **且** 输出里出现指定门的 FAILED 行。
#   rc∈{2,3,4} (usage/collection/internal error) = 指定门根本没跑 = 不算 KILLED;
#   rc=5 (收集为空) 也不算。每轮输出存 transcript 进 evidence, 不再只有自报。
# 教训锚 (MEMORY): 变异脚本必须串行; str.replace 不命中不报错 → 每处替换断言命中数;
#                  EXIT trap 还原; bash 是 PIPESTATUS; argv 里的 \n 是字面两字符;
#                  判据是"指定门红"不是"某处有失败"。
set -u
cd "$(dirname "$0")/../../.." || exit 9   # → LANE 根
LANE="$PWD"
SCRIPT="backend/scripts/vault_lint.py"
TRANS_DIR="_bmad-output/审查/evidence-g82/mutation-transcripts"
mkdir -p "$TRANS_DIR"
PYTHONDONTWRITEBYTECODE=1
export PYTHONDONTWRITEBYTECODE

mutate_and_test() {
  # $1=变异名 $2=python替换表达式(old|||new, \n 字面量) $3=pytest -k 表达式(指定门)
  local name="$1" repl="$2" gate="$3" rc out
  out="$TRANS_DIR/$name.txt"
  cp "$SCRIPT" "$SCRIPT.bak-g82"
  trap 'cp "$SCRIPT.bak-g82" "$SCRIPT" 2>/dev/null; rm -f "$SCRIPT.bak-g82"' EXIT INT TERM

  python3 - "$repl" <<'PYEOF'
import sys
repl = sys.argv[1]
old, new = (s.replace("\\n", "\n") for s in repl.split("|||"))
p = "backend/scripts/vault_lint.py"
src = open(p, encoding="utf-8").read()
n = src.count(old)
assert n == 1, f"替换锚必须恰命中 1 次, 实际 {n}: {old!r}"
open(p, "w", encoding="utf-8").write(src.replace(old, new))
PYEOF
  if [ $? -ne 0 ]; then
    echo "MUTANT $name: REPLACE-FAILED (锚不唯一/不命中) — 脚本缺陷, 不算通过"
    cp "$SCRIPT.bak-g82" "$SCRIPT"; rm -f "$SCRIPT.bak-g82"
    exit 9
  fi

  ( cd backend && .venv/bin/pytest tests/unit/test_vault_lint.py -q -p no:cacheprovider -k "$gate" ) > "$out" 2>&1
  rc=$?
  # 还原 + 逐字节比对 (先还原再判定, 防中途退出留毒)
  cp "$SCRIPT.bak-g82" "$SCRIPT"
  if ! cmp -s "$SCRIPT" "$SCRIPT.bak-g82"; then echo "MUTANT $name: RESTORE-MISMATCH"; exit 9; fi
  rm -f "$SCRIPT.bak-g82"

  # 判据: rc==1 且 **指定的那道门** 出现在 FAILED 行里 (HIGH-7: 光 rc!=0 不算)
  if [ "$rc" -eq 1 ] && grep -q "FAILED tests/unit/test_vault_lint.py::.*${gate%% and *}" "$out"; then
    echo "MUTANT $name: KILLED (rc=1, 指定门 [$gate] 的 FAILED 行在 transcript) ✓"
  elif [ "$rc" -eq 0 ]; then
    echo "MUTANT $name: SURVIVED (rc=0 — 指定门 [$gate] 没抓住) ❌"
    FAILED="$FAILED $name"
  else
    echo "MUTANT $name: NOT-KILLED-BY-GATE (rc=$rc, 指定门 [$gate] 无 FAILED 行 — 收集错/别的错, 不算杀) ❌"
    FAILED="$FAILED $name"
  fi
  tail -1 "$out"
}

FAILED=""
echo "== CARD-G8-2 变异负验证 round-2 (串行; 判据 = 指定门的 FAILED 行) =="

# M1 去掉 source_board 豁免 → 指定门: test_orphan_source_board_exemption
mutate_and_test "M1-去source_board豁免" \
  'if _fm_scalar(fm, "source_board"):\n            continue|||if False:\n            continue' \
  "test_orphan_source_board_exemption"

# M2 放宽 stale 为恒 fresh → 指定门: test_freshness_stale_and_corrupt_are_caught
mutate_and_test "M2-恒fresh" \
  'def _is_stale(generated_at: Any, today: date) -> bool:|||def _is_stale(generated_at: Any, today: date) -> bool:\n    return False  # MUTANT' \
  "test_freshness_stale_and_corrupt"

# M3 退出码恒 0 → 指定门: test_exit_code_mapping
mutate_and_test "M3-退出码恒0" \
  '    statuses = {c.status for c in report.checks}|||    return 0  # MUTANT\n    statuses = {c.status for c in report.checks}' \
  "test_exit_code_mapping"

# M4 JSON 与文本分叉 → 指定门: test_json_and_text_are_same_source
mutate_and_test "M4-JSON分叉" \
  '                "status": c.status,\n                "summary": c.summary,|||                "status": "ok",  # MUTANT\n                "summary": c.summary,' \
  "test_json_and_text_are_same_source"

# M5 oracle 类型门禁拆除 → 非字符串 generated_at 不再 corrupt →
#    指定门: 同源锁 SUMMARIZE 组 (活 oracle 比对出分叉)
mutate_and_test "M5-非str不corrupt" \
  '    if not isinstance(gen, str):\n        return "corrupt", f"generated_at 应为字符串, 实为 {type(gen).__name__}", None|||    if False:\n        pass' \
  "test_freshness_lock_with_live_oracle and SUMMARIZE"

# M6 skipped 伪造 → 未跑的检查被藏起来 → 指定门: test_only_skips_explicitly
mutate_and_test "M6-skipped伪造" \
  '        skipped=[n for n in CHECKS if n not in selected],|||        skipped=[],  # MUTANT' \
  "test_only_skips_explicitly"

# round-1 整改新增的 4 个门 (判别力回归)
# M7 剥离器整体拆除 → 围栏/行内/HTML/AUTO/跨行伪链全部重新豁免孤儿
mutate_and_test "M7-剥离器拆除" \
  '    for raw in _WIKILINK.findall(_strip_nonsemantic(body)):|||    for raw in _WIKILINK.findall(body):' \
  "test_orphan_ignores_nonsemantic_wikilinks"

# M8 symlink 恢复可读 → _read_text 最后一道防线拆除 (防御深度层;
# 专属判别 = 直达单测, 前置守卫正常时该分支轮不到, 整链测试抓不住它)
mutate_and_test "M8-symlink可读" \
  '    if path.is_symlink():\n        return None|||    if False:\n        return None' \
  "test_read_text_rejects_symlink_direct"

# M9 节点目录缺失不 fail → fail-open 回归
mutate_and_test "M9-缺目录不fail" \
  '            status=FAIL,\n            summary=f"`{NODE_DIR}/` 不存在|||            status=WARN,\n            summary=f"`{NODE_DIR}/` 不存在' \
  "test_orphan_missing_node_dir_fails"

# M10 argparse 用法错误退回 2 → 撞码回归
mutate_and_test "M10-argparse退2" \
  '        raise SystemExit(EXIT_CONFIG)|||        raise SystemExit(2)  # MUTANT' \
  "test_argparse_usage_errors_exit_3"

# ── round-2 整改新增的防线 ──
# M11 自身贡献排除拆除 → A 被自己的出链豁免 (round-2 MEDIUM-1a)
mutate_and_test "M11-自身贡献不排除" \
  '        sources = inbound.get(_norm_key(node.stem), set()) - {own}|||        sources = inbound.get(_norm_key(node.stem), set())' \
  "test_orphan_subdir_node_crosslink"

# M12a symlink 文件层守卫拆除 → vault 外内容豁免真孤儿
mutate_and_test "M12a-symlink层拆除" \
  '    if path.is_symlink():\n        return "symlink"|||    if False:\n        return "symlink"' \
  "test_orphan_symlink_never_read"

# M12b 越界解析层守卫拆除 → 目录 symlink 后代豁免真孤儿
mutate_and_test "M12b-越界层拆除" \
  '    if not cvr._resolves_inside_vault(vault, rel):\n        return "resolves-outside-vault"|||    if False:\n        pass' \
  "test_orphan_symlink_never_read"

# M13 文件级跨行 span 剥离拆除 → 跨行 code span 豁免真孤儿 (round-2 HIGH-4)
mutate_and_test "M13-跨行span不剥" \
  '    text = re.sub(r"`+[^`]*`+", " ", text, flags=re.S)\n    return text|||    return text  # MUTANT' \
  "test_orphan_ignores_nonsemantic_wikilinks"

# M14 裸 null 字面识别拆除 → source_board: null 豁免真孤儿 (round-1 MEDIUM-1b)
mutate_and_test "M14-裸null识别拆除" \
  '    if v in ("null", "Null", "NULL", "~"):\n        return None  # 裸 null 字面 (先于剥引号 —— 引号包裹的是字符串, 不是 null)|||    if False:\n        return None' \
  "test_orphan_uppercase_md_link_and_null_source_board"

echo "== 汇总 =="
if [ -n "$FAILED" ]; then
  echo "SURVIVED:$FAILED"
  exit 1
fi
echo "ALL-KILLED"
