#!/usr/bin/env bash
# (j)(l) 四套全跑 + 目录级 —— ⛔ **串行单实例**：同一时刻只允许一个 harness 在跑。
# 并发原地变异会互踩，且各 harness 自带的「还原后字节相同」自检在并发下是自证。
#
# 每一步 tee 到 evidence-mutkill-r2/，末行写 `rc=`（取被测命令的 rc，不是 tee 的）。
# ⛔ 后缀用 `.txt` 不用 `.log`：仓根 .gitignore 有全局 `*.log`，存档会被静默忽略。
set -u
TREE="$(cd "$(dirname "$0")/../../.." && pwd)"
E="$TREE/_bmad-output/审查/evidence-mutkill-r2"
BASE="/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/unit-red-baseline-da690bf8.txt"
export PYTHONDONTWRITEBYTECODE=1
cd "$TREE/backend" || exit 9

ts() { date +%Y%m%dT%H%M%S; }
# ⚠️ python 一律 `-u`：存档经 tee 是**块缓冲**，不加的话跑到一半时存档文件是空的，
# 「进度」完全不可观测（第一次跑就因此把「块缓冲」误读成「卡住」）。

step() {  # step <名字> <命令...>
  local name="$1"; shift
  local f="$E/$name-$(ts).txt"
  echo "───────── $name  →  $f"
  "$@" 2>&1 | tee "$f"
  local rc=${PIPESTATUS[0]}
  echo "rc=$rc" | tee -a "$f"
  echo "$f" >> "$E/_run_index.txt"
  return 0   # 一步失败不中断后续步骤：其余套的数字仍然有信息量
}

: > "$E/_run_index.txt"

# ── 目录级（本卡改动后首跑）────────────────────────────────────────────────
step unit-before .venv/bin/pytest tests/unit -q -p no:cacheprovider
step regression-before .venv/bin/pytest tests/regression -q -p no:cacheprovider

# ── 四套全跑（串行）────────────────────────────────────────────────────────
step run-g32b    .venv/bin/python -u scripts/g32b_mutation_gates.py
step run-g32cb   .venv/bin/python -u scripts/g32cb_mutation_gates.py
step run-g32ccr1 .venv/bin/python -u scripts/g32ccr1_negative_controls.py
step run-g33     .venv/bin/python -u scripts/g33_mutation_gates.py --json "$E/g33-$(ts).json"

# ── 目录级（收工）──────────────────────────────────────────────────────────
step unit-after .venv/bin/pytest tests/unit -q -p no:cacheprovider
step regression-after .venv/bin/pytest tests/regression -q -p no:cacheprovider

# ── U8-A 的两道门仍在 ─────────────────────────────────────────────────────
step ast-gate .venv/bin/python -u scripts/lifespan_isolation_negative_control.py --ast-only
step guard-probes .venv/bin/python -u scripts/lifespan_isolation_guard_probes.py

echo "═══ 全部步骤完成，存档清单 ═══"
cat "$E/_run_index.txt"
echo "基线（tests/unit 对照用，主干那份）: $BASE"
