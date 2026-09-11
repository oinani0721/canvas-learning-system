#!/usr/bin/env bash
# (k)(l)(o) 收尾对账：跑后 sha / 标记残留 / 目录级 diff / 地盘 / 卫生。
# ⛔ 全部判据都要能被第三方复跑，所以数字一律现算，不引用我在对话里说过的数。
set -u
TREE="$(cd "$(dirname "$0")/../../.." && pwd)"
E="$TREE/_bmad-output/审查/evidence-mutkill-r2"
BASE="/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/unit-red-baseline-da690bf8.txt"
U8A="3f073a1a"
M="MUT""ANT"
cd "$TREE" || exit 9

echo "═══ (k) 跑后 sha（对 sha-targets-pre-20260908T073501.txt 逐字节）═══"
shasum -a 256 $(cat "$E/target_files.txt")
echo "--- diff（空 = 逐字节还原）---"
diff <(grep -v '^===' "$E/sha-targets-pre-20260908T073501.txt" | grep -v '^(') \
     <(shasum -a 256 $(cat "$E/target_files.txt")) && echo "✓ 无差异"

echo
echo "═══ (k) 标记残留（文件清单必须仍是那 5 项）═══"
git -c core.quotepath=false grep -l "$M" -- . ':(exclude)_bmad-output' | sort
echo "--- 逐项计数 ---"
for f in $(git -c core.quotepath=false grep -l "$M" -- . ':(exclude)_bmad-output' | sort); do
  printf '%s %s\n' "$f" "$(grep -c "$M" "$f")"
done
echo "--- 与开工基线对比（差额只允许出现在本卡地盘的 backend/scripts/*.py 上，且须能逐行解释）---"
diff <(grep -A99 -- '--- counts ---' "$E/marker-baseline-pre-20260908T073501.txt" | tail -n +2) \
     <(for f in $(git -c core.quotepath=false grep -l "$M" -- . ':(exclude)_bmad-output' | sort); do
         printf '%s %s\n' "$f" "$(grep -c "$M" "$f")"; done) && echo "✓ 完全一致"

echo
echo "═══ (k) git status 里不得出现 canvas-vault/** ═══"
git status --porcelain --no-renames | grep 'canvas-vault' && echo "⛔ 有 canvas-vault 改动" || echo "✓ 无"

echo
echo "═══ (o) 地盘：<U8-A 末 commit>..HEAD 只许 5 个 backend/scripts/*.py ═══"
git diff --stat --no-color "$U8A" -- . ':(exclude)_bmad-output'
echo "--- 工作树未提交的改动（同一口径）---"
git status --porcelain --no-renames -- . ':(exclude)_bmad-output'

echo
echo "═══ 卫生：仓库里不得有 *.stderr* ═══"
echo "已跟踪: $(git ls-tree -r HEAD --name-only | grep -c stderr)"
echo "工作树未跟踪: $(git status --porcelain --no-renames | grep -c stderr)"

echo
echo "═══ (l) tests/unit 对主干基线 diff（只许 '<' 行）═══"
echo "基线: $BASE"
UA=$(ls -t "$E"/unit-after-*.txt 2>/dev/null | head -1)
echo "本卡 after 存档: $UA"
if [ -n "$UA" ]; then
  grep -E '^(FAILED|ERROR) tests/' "$UA" | sed 's/ - .*//' | sort -u > /tmp/mkr2-after.txt
  grep -v '^#' "$BASE" | sort -u > /tmp/mkr2-base.txt
  echo "--- diff 基线 → 本卡 ---"
  diff /tmp/mkr2-base.txt /tmp/mkr2-after.txt
  echo "diff-rc=$?"
  echo "--- 只看 '>' 行（新增红，必须为空）---"
  diff /tmp/mkr2-base.txt /tmp/mkr2-after.txt | grep '^>' && echo "⛔ 有新增红" || echo "✓ 无新增红"
  echo "--- 汇总行 ---"; tail -3 "$UA"
else
  echo "⛔ 找不到 unit-after 存档"
fi

echo
echo "═══ (l) tests/regression 开工 / 收工 对比 ═══"
RB=$(ls -t "$E"/regression-before-*.txt 2>/dev/null | head -1)
RA=$(ls -t "$E"/regression-after-*.txt 2>/dev/null | head -1)
echo "before=$RB"; echo "after=$RA"
if [ -n "$RB" ] && [ -n "$RA" ]; then
  grep -E '^(FAILED|ERROR) tests/' "$RB" | sed 's/ - .*//' | sort -u > /tmp/mkr2-rb.txt
  grep -E '^(FAILED|ERROR) tests/' "$RA" | sed 's/ - .*//' | sort -u > /tmp/mkr2-ra.txt
  diff /tmp/mkr2-rb.txt /tmp/mkr2-ra.txt && echo "✓ 无差异"
  echo "--- 汇总行 ---"; tail -3 "$RB"; echo "---"; tail -3 "$RA"
fi

echo
echo "═══ 四套全跑的汇总行原文（六档并列，供逐字核字段名）═══"
for f in "$E"/run-g32b-*.txt "$E"/run-g32cb-*.txt "$E"/run-g32ccr1-*.txt "$E"/run-g33-*.txt; do
  [ -f "$f" ] || continue
  echo "───── $(basename "$f")"
  grep -E 'KILLED|SURVIVED|HARNESS-ERROR|ANCHOR-ERROR|SYNTAX-INVALID|六档之和|^rc=' "$f" | tail -12
done
