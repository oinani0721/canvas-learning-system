#!/bin/bash
# G5-2 — live 真实板取证 v3 (自记录: set -x 完整命令回放 + 逐步退出码 + 引擎字节绑定)
# 产物: live-full-before/after.tsv · live-run-log.txt(本脚本 set -x 转录) · engine-and-products.sha256
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
LIVE="/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault"
OUT="$REPO/canvas-vault/outputs"
ENGINE="$REPO/canvas-vault/.claude/skills/board-split/scripts/split_preview.py"

exec > >(tee "$HERE/live-run-log.txt") 2>&1
set -x
export PYTHONDONTWRITEBYTECODE=1
date -u +%Y-%m-%dT%H:%M:%SZ
shasum -a 256 "$ENGINE"
python3 "$HERE/collect_live_baseline.py" "$LIVE" > "$HERE/live-full-before.tsv"; echo "collect-before rc=$?"
python3 "$ENGINE" --vault "$LIVE" --board "CS188 lecture 2" --out-dir "$OUT"; echo "run1 rc=$?"
python3 "$ENGINE" --vault "$LIVE" --board "特征值与特征向量" --out-dir "$OUT"; echo "run2 rc=$?"
python3 "$HERE/collect_live_baseline.py" "$LIVE" > "$HERE/live-full-after.tsv"; echo "collect-after rc=$?"
diff "$HERE/live-full-before.tsv" "$HERE/live-full-after.tsv"; echo "baseline-diff rc=$? (0=零净差异)"
shasum -a 256 "$ENGINE" \
  "$OUT/split-preview-CS188 lecture 2.json" "$OUT/split-preview-CS188 lecture 2.md" \
  "$OUT/split-preview-特征值与特征向量.json" "$OUT/split-preview-特征值与特征向量.md" \
  | tee "$HERE/engine-and-products.sha256"
date -u +%Y-%m-%dT%H:%M:%SZ
