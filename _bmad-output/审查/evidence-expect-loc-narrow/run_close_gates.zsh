#!/bin/zsh
# CARD-EXPECT-LOC-NARROW 收工门（⛔ 必须在 run_judges.zsh 全部结束之后跑 ——
# 变异窗口里跑 `--list` / `tests/unit` 会读到变异态，得出与事实不符的结论）。
set -u
R=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools
PY=$R/backend/.venv/bin/python
PYTEST=$R/backend/.venv/bin/pytest
EV=$R/_bmad-output/审查/evidence-expect-loc-narrow
BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt
TS=$(date +%Y%m%dT%H%M%S)

echo "══ (f) 改后覆盖自检 ══"
for pair in "g32cb:scripts/g32cb_mutation_gates.py --list" "g32ccr1:scripts/g32ccr1_negative_controls.py --list" "g33:scripts/g33_mutation_gates.py --selfcheck-loc"; do
  h=${pair%%:*}; cmd=${pair#*:}
  out=$EV/list-after-$h-$TS.txt
  ( cd $R/backend && $PY ${=cmd} ) 2>&1 | tee $out > /dev/null
  echo "rc=$pipestatus[1]" >> $out
  echo "[list-after-$h] $(tail -2 $out | tr '\n' ' ')"
done

echo "══ (k) 目录级 tests/unit（R-B14-3：cd backend 在前、--ignore 用相对路径）══"
RUN=$EV/unit-close-$TS.txt
( cd $R/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider ) 2>&1 | tee $RUN > /dev/null
echo "rc=$pipestatus[1]" | tee -a $RUN
grep -E '^(FAILED|ERROR) tests/' $RUN | sed 's/ - .*//' | sort -u > $EV/close.nodeids
grep -v '^#' $BASE | sort -u > $EV/base.nodeids
echo "--- diff base.nodeids close.nodeids (只允许 < 行) ---"
diff $EV/base.nodeids $EV/close.nodeids | tee $EV/unit-diff-$TS.txt
echo "diff-rc=$pipestatus[1]"
echo "base 条数=$(wc -l < $EV/base.nodeids)  close 条数=$(wc -l < $EV/close.nodeids)"
echo "ALL DONE"
