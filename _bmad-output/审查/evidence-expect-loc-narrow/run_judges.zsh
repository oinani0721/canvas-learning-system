#!/bin/zsh
# CARD-EXPECT-LOC-NARROW 的真跑批（串行，⛔ 不可并行：三套共用被变异文件
# `canvas-vault/.claude/skills/quiz-answer/SKILL.md`，并行会互踩）。
# 每次真跑前后对**所有**被变异文件 + 零写者 `fsrs_bridge.py` 落 `shasum -a 256`。
# 承重：`fsrs_bridge.py` 跑前跑后逐字同（裁定 R-B14-9 (2)(3)，不同 = 卡阻断）。
set -u
R=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools
PY=$R/backend/.venv/bin/python
EV=$R/_bmad-output/审查/evidence-expect-loc-narrow

# g33 的 4 个被变异文件（AST 实测 `MUTATIONS` 第 2 字段）+ 零写者（第 4 个就是它）
G33_FILES=(
  $R/canvas-vault/.claude/skills/quiz-answer/SKILL.md
  $R/backend/app/services/learning_event_log.py
  $R/canvas-vault/.claude/skills/start-exam-board/SKILL.md
  $R/canvas-vault/.claude/scripts/fsrs_bridge.py
)
# g32cb / g32ccr1 的 2 个被变异文件 + 零写者（零写者不在它们的变异表里，一并记以便对照）
G32_FILES=(
  $R/canvas-vault/.claude/skills/quiz-answer/SKILL.md
  $R/backend/scripts/validate_learning_events.py
  $R/canvas-vault/.claude/scripts/fsrs_bridge.py
)

run_one() {
  local name=$1; shift
  local -a files; files=("${(@P)1}"); shift
  local ts=$(date +%Y%m%dT%H%M%S)
  local out=$EV/$name-$ts.txt
  { echo "=== 跑前 shasum -a 256 ==="; shasum -a 256 "${files[@]}" } > $out
  print -r -- "=== 命令: $* （cwd=backend）===" >> $out
  ( cd $R/backend && "$@" ) 2>&1 | tee -a $out > /dev/null
  local rc=$pipestatus[1]
  { echo "=== 跑后 shasum -a 256 ==="; shasum -a 256 "${files[@]}" } >> $out
  echo "rc=$rc" >> $out
  echo "[$name] rc=$rc → $out"
}

# ① g33 probe 干净重跑（首次 probe 在收尾打印处崩于已修复的 NameError，17 条观察值已完整打印）
run_one probe-g33-skipM5-clean G33_FILES $PY scripts/g33_mutation_gates.py --probe --skip M5-cas-revision-only
# ② g33 裁决：17 条（排零写者条目 M5），rc 恒 4（部分跑）
run_one only-g33-skipM5        G33_FILES $PY scripts/g33_mutation_gates.py --skip M5-cas-revision-only
# ③ g32cb 抽样形态 ①：实测无 --only ⇒ 跑全量 9 条，rc=0 才算过
run_one only-g32cb-full        G32_FILES $PY scripts/g32cb_mutation_gates.py
# ④ g32ccr1 抽样：--only 是精确 mid 集合，rc 恒 4
run_one only-g32ccr1-E1        G32_FILES $PY scripts/g32ccr1_negative_controls.py --only=E1
# ⑤ --skip 精确性反例（零成本、无变异）：`--skip M1` 若按**前缀**会选中 M1+M10~M17 共 9 条；
#    精确语义下 `M1` 不是任何 mid ⇒ 当场 rc=4 拒跑
run_one skipctl-g33-prefixtrap G33_FILES $PY scripts/g33_mutation_gates.py --skip M1
# ⑥ --skip 未知取值反例（零成本、无变异）
run_one skipctl-g33-unknown    G33_FILES $PY scripts/g33_mutation_gates.py --skip NOPE
# ⑦ 双 --skip 反例：选中 16/18（卡文 §一(g) 乙 点名的判据）
run_one skipctl-g33-two        G33_FILES $PY scripts/g33_mutation_gates.py --skip M5-cas-revision-only --skip M1-per-node-lock
echo "ALL DONE"
