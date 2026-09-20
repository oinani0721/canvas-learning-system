#!/bin/zsh
# ZCode r6 runner — CARD-HARNESS-TREE-PARSE-R2 (protocol §2.4.2 supplementary review channel)
# Read-only by construction: zcode --mode build blocks Bash/Write inside the reviewer.
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-harness-tree-r2
mkdir -p "$EV"
LOG=$EV/zcode-r6-run-$(date +%Y%m%dT%H%M%S).txt
P=_bmad-output/审查/prompts/zcode-review-prompt-CARD-HARNESS-TREE-PARSE-R2-r6.md
OUT=_bmad-output/审查/zcode-review-CARD-HARNESS-TREE-PARSE-R2-r6.md
ERR=_bmad-output/审查/zcode-review-CARD-HARNESS-TREE-PARSE-R2-r6.stderr
{
  echo "=== ZCode r6 runner (CARD-HARNESS-TREE-PARSE-R2, protocol §2.4.2) ==="
  echo "cwd=$(pwd)"
  echo "zcode_bin=$(command -v zcode)"
  echo "start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "--- command (verbatim) ---"
  echo 'zcode --prompt "$(cat _bmad-output/审查/prompts/zcode-review-prompt-CARD-HARNESS-TREE-PARSE-R2-r6.md)" --cwd "$(pwd)" --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-HARNESS-TREE-PARSE-R2-r6.md 2> _bmad-output/审查/zcode-review-CARD-HARNESS-TREE-PARSE-R2-r6.stderr'
  echo "--- run ---"
  zcode --prompt "$(cat $P)" --cwd "$(pwd)" --mode build --no-color --json > "$OUT" 2> "$ERR"
  rc=$?
  echo "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "rc=$rc"
  echo "stdout_bytes=$(wc -c < "$OUT" | tr -d ' ')"
  echo "stderr_bytes=$(wc -c < "$ERR" | tr -d ' ')"
  echo "$rc" > "$EV/zcode-r6-rc.txt"
} 2>&1 | tee "$LOG"
echo "DONE $LOG"
