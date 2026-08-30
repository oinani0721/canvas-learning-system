#!/bin/bash
# G5-3 — 四态 diff 真实内容实景演示
#
# 硬边界: live vault **只读**（只 cp 出去，不写回）；变异只作用于 scratchpad 里的副本；
#         diff 产物落本 worktree canvas-vault/outputs/（供用户在 Obsidian 打开）；
#         证据目录只留摘要文本，不留 vault 内容副本。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
LIVE="/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault"
OUT="$REPO/canvas-vault/outputs"
ENGINE="$REPO/canvas-vault/.claude/skills/board-split/scripts/split_preview.py"
COLLECT="$REPO/_bmad-output/审查/g5-2-evidence/collect_live_baseline.py"
SCRATCH="${G53_SCRATCH:?必须传 G53_SCRATCH（scratchpad 目录），禁止落仓库内}"
BOARD="CS188 lecture 2"

exec > >(tee "$HERE/four-state-demo-log.txt") 2>&1
set -x
export PYTHONDONTWRITEBYTECODE=1
python3 "$COLLECT" "$LIVE" > "$SCRATCH/live-before.tsv"; echo "collect-before rc=$?"

# ── 只读复制 live 的板与节点池到 scratchpad（变异只发生在副本上）────────────
rm -rf "$SCRATCH/vault"
mkdir -p "$SCRATCH/vault/原白板" "$SCRATCH/vault/节点"
cp "$LIVE/原白板/$BOARD.md" "$SCRATCH/vault/原白板/"
cp "$LIVE"/节点/*.md "$SCRATCH/vault/节点/" 2>/dev/null || true

python3 "$ENGINE" --vault "$SCRATCH/vault" --board "$BOARD" --out-dir "$SCRATCH/base"; echo "base rc=$?"
python3 "$HERE/mutate_board.py" "$SCRATCH/vault" "$SCRATCH/base/split-preview-$BOARD.json"
python3 "$ENGINE" --vault "$SCRATCH/vault" --board "$BOARD" --out-dir "$SCRATCH/after"; echo "after rc=$?"

python3 "$ENGINE" --diff "$SCRATCH/base/split-preview-$BOARD.json" "$SCRATCH/after/split-preview-$BOARD.json" \
  --out-dir "$OUT"; echo "diff rc=$?"
mv "$OUT/split-diff-$BOARD.json" "$OUT/split-diff-$BOARD-四态演示.json"
mv "$OUT/split-diff-$BOARD.md" "$OUT/split-diff-$BOARD-四态演示.md"
python3 "$HERE/dump_ids.py" diff "$OUT/split-diff-$BOARD-四态演示.json" | tee "$HERE/four-state-demo-summary.txt"

python3 "$COLLECT" "$LIVE" > "$SCRATCH/live-after.tsv"; echo "collect-after rc=$?"
diff "$SCRATCH/live-before.tsv" "$SCRATCH/live-after.tsv"; echo "live-baseline-diff rc=$? (0=live 零净差异)"
