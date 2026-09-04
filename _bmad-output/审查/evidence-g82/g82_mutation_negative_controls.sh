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
def _conv(s):
    return s.replace("\\n", "\n")  # (r11: \\Q 占位分支已删——当前锚无 \\Q)
old, new = (_conv(s) for s in repl.split("|||"))
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
echo "== CARD-G8-2 变异负验证 round-11 (串行; 判据 = 指定门的 FAILED 行) =="

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
# M7 text-token 过滤拆除 → code_inline/html_inline 里的伪链全部重新豁免孤儿
# (token 流法; round-7 前 M7 锚定区间法, 已随重构重锚)
mutate_and_test "M7-text过滤拆除" \
  '            if child.type != "text" or "[[" not in child.content:\n                continue  # code_inline/html_inline/softbreak 等: 不扫|||            if False:\n                continue  # MUTANT' \
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
# M11 自身贡献排除拆除 (round-3 后为物理路径形态) → A 被自己的出链豁免
mutate_and_test "M11-自身贡献不排除" \
  '        sources = inbound.get(_norm_key(node.stem), set()) - {own_phys}|||        sources = inbound.get(_norm_key(node.stem), set())' \
  "test_orphan_subdir_node_crosslink"

# M12a symlink 文件层守卫拆除 → vault 外内容豁免真孤儿
mutate_and_test "M12a-symlink层拆除" \
  '    if path.is_symlink():\n        return "symlink"|||    if False:\n        return "symlink"' \
  "test_orphan_symlink_never_read"

# M12b 越界解析层守卫拆除 → 目录 symlink 后代豁免真孤儿
mutate_and_test "M12b-越界层拆除" \
  '    if not cvr._resolves_inside_vault(vault, rel):\n        return "resolves-outside-vault"|||    if False:\n        pass' \
  "test_orphan_symlink_never_read"

# (M16/M21/M22 已删除: Markdown 库语义不可变异, 行为由集成测试锁定;
#  可变异面收敛到 M7 text 过滤 / M20 AUTO 段跳过等本卡自有决策点。)

# M14 裸 null 字面识别拆除 → source_board: null 豁免真孤儿 (round-1 MEDIUM-1b)
mutate_and_test "M14-裸null识别拆除" \
  '    if v in ("null", "Null", "NULL", "~"):\n        return None  # 裸 null 字面 (先于剥引号 —— 引号包裹的是字符串, 不是 null)|||    if False:\n        return None' \
  "test_orphan_uppercase_md_link_and_null_source_board"

# ── round-3 整改新增的防线 ──
# M15 入链来源退回相对路径 → 目录别名 (原白板->节点/) 的自贡献绕过自身排除
mutate_and_test "M15-来源相对路径" \
  '                inbound.setdefault(target, set()).add(src_phys)|||                inbound.setdefault(target, set()).add(src.relative_to(vault).as_posix())  # MUTANT' \
  "test_orphan_directory_alias_self_link_uses_realpath"

# M17 freshness 越界前置检查拆除 → 读 vault 外投影
mutate_and_test "M17-投影越界不拦" \
  '    if proj.is_symlink() or not cvr._resolves_inside_vault(vault, "/".join(_PROJECTION_REL)):\n        return "corrupt", "投影路径是 symlink 或解析后越出 vault, 拒读", None|||    if False:\n        pass' \
  "test_projection_symlink_outside_is_corrupt"

# M18 枚举层盲区并入拆除 → chmod 000 子树重新静默消失
# (round-3 后盲区并入只有源目录循环这一处; 曾在 nodes 侧另有冗余并入,
#  拆单路测试仍绿 —— 结构冗余已消除, 本变异现对唯一路径承重)
mutate_and_test "M18-枚举盲区丢弃" \
  '        for rel, why in src_blind.items():\n            blind[f"{src_dir}/{rel}"] = why|||        pass  # MUTANT' \
  "test_orphan_unreadable_subtree_is_blind"

# ── round-4 整改新增的防线 ──
# M19 raw_derived 状态判定去掉 G8/G10/G11 盲区 → 扫描面问题假绿 ok
mutate_and_test "M19-盲区不计状态" \
  '        status=WARN if (findings or recap_blind or blind) else OK,|||        status=WARN if (findings or recap_blind) else OK,  # MUTANT' \
  "test_raw_derived_g8_blind_forces_warn"

# M20 AUTO BEGIN 分支拆除 (round-9 深度计数形态) → AUTO 段不识别, [[A]] 泄漏
mutate_and_test "M20-BEGIN分支拆除" \
  '        if _AUTO_BEGIN_RE.match(stripped):
            depth += 1|||        if False:
            depth += 1  # MUTANT' \
  "test_orphan_ignores_nonsemantic_wikilinks"

# ── round-8 整改新增的防线 ──
# M23 嵌套 BEGIN 深度 +1 拆除 (round-9, round-11 字节重锚) → 内层 BEGIN 不加深,
#     第一个 END 提前关闸
# (r12 LOW3 / CARD-G8-2b: 此处原有同一句注释的 5 份重复残留, 已去重留最新一份。)
mutate_and_test "M23-嵌套深度拆除" \
  '            if _AUTO_BEGIN_RE.match(stripped):\n                # r9 H2: 嵌套 BEGIN —— 深度 +1 (真实生成器单层; 嵌套 = 结构异常, 显式记录)\n                depth += 1|||            if False:\n                depth += 1  # MUTANT' \
  "test_nested_auto_begin_depth"

# M24 fence 行保留谓词拆除 (round-9 fullmatch 形态) → AUTO 内 fence opener 被盲化,
#  跨段 fence 状态丢失, [[A]] 泄漏 (r8 H1 回归)
mutate_and_test "M24-fence行不保留" \
  '            if re.fullmatch(r"(`{3,}|~{3,})[^`]*", stripped):|||            if False and re.fullmatch(r"(`{3,}|~{3,})[^`]*", stripped):  # MUTANT' \
  "test_auto_fence_cross_keeps_fence_state"

# M25 content 反斜杠剥离 (round-9 承重点) → escaped content 的 [[ 显形, 伪链采纳
#  (raw_targets 守卫为冗余层: content 本身保留反斜杠才是 escaped 拒绝的承重路径)
#  锚内的 \\ 在 bash 单引号中字面传递, python replace("\\n") 不动它, 正确落到源码
# (M25 已删除: escaped 拒绝由 markdown-it-py 的转义处理直接承重——两个候选变异
#  (拆 raw_targets 守卫 / 剥 content 反斜杠) 实测均不改变行为, 即该库语义不可变异;
#  行为由集成测试 test_escaped_brackets_are_not_wikilink 锁定, 与 M16/M21/M22 同类。)


echo "== 汇总 =="
if [ -n "$FAILED" ]; then
  echo "SURVIVED:$FAILED"
  exit 1
fi
echo "ALL-KILLED"
