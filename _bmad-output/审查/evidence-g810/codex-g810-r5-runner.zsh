#!/bin/zsh
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
LOG=$EV/codex-g810-r5-run-$(date +%Y%m%dT%H%M%S).txt
{
  echo "=== Codex glm-5.3 r5 runner (CARD-G8-10) ==="
  echo "cwd=$(pwd)"
  echo "codex_version=$(codex --version 2>&1)"
  echo "start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  source "$HOME/.codex/zai.env"
  codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r5.md)" > _bmad-output/审查/codex-review-CARD-G8-10-r5.md 2> _bmad-output/审查/codex-review-CARD-G8-10-r5.stderr </dev/null
  rc=$?
  echo "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "rc=$rc"
  echo "stdout_bytes=$(wc -c < _bmad-output/审查/codex-review-CARD-G8-10-r5.md)"
  echo "$rc" > "$EV/codex-g810-r5-rc.txt"
} 2>&1 | tee "$LOG"
echo "DONE $LOG"
