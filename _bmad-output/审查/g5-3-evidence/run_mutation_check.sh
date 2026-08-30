#!/bin/bash
# G5-3 — 回归门变异反证
#
# 背景（如实说明）：对抗审查抓到的 11 个根因是「先修后补门」，所以那 14 条回归门的
# 「先红」没有天然存证。本脚本补上：把每条修复**逐个撤销**（在 /private/tmp 的引擎副本上，
# 绝不动仓库文件），让对应的门跑在被污染的引擎上，断言它**变红**。
# 全绿 = 那道门是空转的，必须当场暴露。
#
# ⛔ 串行执行（历史教训 reference_mutation_script_serial_only）：变异体各自独立成文件，
#    互不覆盖；测试副本用 SCRIPT 常量指向对应变异体。
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
ENGINE="$REPO/canvas-vault/.claude/skills/board-split/scripts/split_preview.py"
JUDGE="$REPO/backend/tests/skills/test_split_stable_id.py"
WORK="${G53_MUT_WORK:?必须传 G53_MUT_WORK（/private/tmp 下的工作目录）}"
PY="$REPO/backend/.venv/bin/python"

mkdir -p "$WORK"
exec > >(tee "$HERE/mutation-check.txt") 2>&1
echo "== G5-3 回归门变异反证 =="
echo "engine: $(shasum -a 256 "$ENGINE" | cut -d' ' -f1)"
echo "judge : $(shasum -a 256 "$JUDGE" | cut -d' ' -f1)"
echo

"$PY" "$HERE/mutate_engine.py" "$ENGINE" "$JUDGE" "$WORK"
rc=$?
echo
echo "变异反证退出码: $rc （0 = 每个变异体都让对应的门变红）"
exit $rc
