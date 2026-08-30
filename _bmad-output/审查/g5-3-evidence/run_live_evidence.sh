#!/bin/bash
# G5-3 — 稳定 ID / diff 契约 live 真实板取证
#   （自记录: set -x 完整命令回放 + 逐步退出码 + 引擎字节绑定）
#
# 硬边界: live vault 全程**只读**；唯一写入 = 本 worktree 的 canvas-vault/outputs/
#         与本证据目录。基线采集器复用 G5-2 的 collect_live_baseline.py（同一把尺）。
#
# 证明什么:
#   1. 两块真实板各跑两次 → preview JSON 逐字节相等 ⇒ stable_id 完全一致（确定性）
#   2. run1 vs run2 的 diff → 四态全 0、unchanged = 全部候选 ⇒ diff 契约在真实板上自洽
#   3. live vault 全字段基线 before/after diff 为空 ⇒ 只读红线未破
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
LIVE="/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault"
OUT="$REPO/canvas-vault/outputs"
ENGINE="$REPO/canvas-vault/.claude/skills/board-split/scripts/split_preview.py"
COLLECT="$REPO/_bmad-output/审查/g5-2-evidence/collect_live_baseline.py"
B1="CS188 lecture 2"
B2="特征值与特征向量"

exec > >(tee "$HERE/live-run-log.txt") 2>&1
set -x
export PYTHONDONTWRITEBYTECODE=1
date -u +%Y-%m-%dT%H:%M:%SZ
shasum -a 256 "$ENGINE"

python3 "$COLLECT" "$LIVE" > "$HERE/live-full-before.tsv"; echo "collect-before rc=$?"

# ── run1: 两板 preview → outputs/，随即快照到证据目录 ─────────────────────────
python3 "$ENGINE" --vault "$LIVE" --board "$B1" --out-dir "$OUT"; echo "run1-b1 rc=$?"
python3 "$ENGINE" --vault "$LIVE" --board "$B2" --out-dir "$OUT"; echo "run1-b2 rc=$?"
mkdir -p "$HERE/run1"
cp "$OUT/split-preview-$B1.json" "$HERE/run1/"
cp "$OUT/split-preview-$B2.json" "$HERE/run1/"

# ── run2: 同输入再跑一次（覆盖 outputs/），比对逐字节相等 ────────────────────
python3 "$ENGINE" --vault "$LIVE" --board "$B1" --out-dir "$OUT"; echo "run2-b1 rc=$?"
python3 "$ENGINE" --vault "$LIVE" --board "$B2" --out-dir "$OUT"; echo "run2-b2 rc=$?"
diff "$HERE/run1/split-preview-$B1.json" "$OUT/split-preview-$B1.json"; echo "b1-two-run-diff rc=$? (0=stable_id 完全一致)"
diff "$HERE/run1/split-preview-$B2.json" "$OUT/split-preview-$B2.json"; echo "b2-two-run-diff rc=$? (0=stable_id 完全一致)"

# ── stable_id 显式清单（人可核对，不只靠 diff 沉默）────────────────────────
python3 "$HERE/dump_ids.py" preview "$OUT/split-preview-$B1.json" "$OUT/split-preview-$B2.json" | tee "$HERE/live-stable-ids.txt"

# ── diff 契约: run1 vs run2 → 应全 unchanged ────────────────────────────────
python3 "$ENGINE" --diff "$HERE/run1/split-preview-$B1.json" "$OUT/split-preview-$B1.json" --out-dir "$OUT"; echo "diff-b1 rc=$?"
python3 "$ENGINE" --diff "$HERE/run1/split-preview-$B2.json" "$OUT/split-preview-$B2.json" --out-dir "$OUT"; echo "diff-b2 rc=$?"
python3 "$HERE/dump_ids.py" diff "$OUT/split-diff-$B1.json" "$OUT/split-diff-$B2.json" | tee "$HERE/live-diff-summary.txt"

python3 "$COLLECT" "$LIVE" > "$HERE/live-full-after.tsv"; echo "collect-after rc=$?"
diff "$HERE/live-full-before.tsv" "$HERE/live-full-after.tsv"; echo "baseline-diff rc=$? (0=零净差异)"

# ⛔ 「全部产物」必须真的是全部。两次被抓：先是手写文件名清单漏了四态演示的两个产物
# （round-3），改成 glob 后注释写「扫全目录」而实现是 `-maxdepth 1 -name 'split-*'`,
# 漏掉 outputs/exam_boards/.gitkeep（round-4）。现在是**递归全部普通文件**，名副其实。
{ shasum -a 256 "$ENGINE"; find "$OUT" -type f -print0 \
    | sort -z | xargs -0 shasum -a 256; } | tee "$HERE/engine-and-products.sha256"
date -u +%Y-%m-%dT%H:%M:%SZ
