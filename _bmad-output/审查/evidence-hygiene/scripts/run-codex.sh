#!/bin/bash
# Codex 复核 round-1（协议 §2 固定形式）
# 模型固定 gpt-6-astra + ultra（用户 2026-09-05 裁定）
# 坑规避：</dev/null 防 stdin 挂起；绝对路径；留 stderr 抢救正文（不入库）
set -uo pipefail

TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene
CARD=CARD-TEST-hygiene-vaultinit
PROMPT="$TREE/_bmad-output/审查/prompts/codex-prompt-$CARD.md"
OUT="$TREE/_bmad-output/审查/codex-review-$CARD.md"
ERR="$TREE/_bmad-output/审查/codex-review-$CARD.stderr"
CODEX=/opt/homebrew/bin/codex

cd "$TREE" || exit 90
test -s "$PROMPT" || { echo "⛔ prompt 为空或不存在"; exit 91; }
echo "prompt $(wc -c < "$PROMPT") 字节 / codex $("$CODEX" --version 2>&1 | head -1)"

"$CODEX" exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat "$PROMPT")" > "$OUT" 2> "$ERR" </dev/null
RC=$?

echo "codex rc=$RC"
echo "正文 $(wc -c < "$OUT") 字节 / stderr $(wc -c < "$ERR") 字节"
if [ ! -s "$OUT" ]; then
  echo "⛔ 正文 0 字节 —— 按 codex 四因查 stderr 尾部（配额 / 内容拦 / tls / CLI 版本）:"
  tail -20 "$ERR"
else
  echo "--- 正文首 15 行 ---"; head -15 "$OUT"
fi
echo "--- stderr 前 3 行（存档首部自证用，stderr 本身不入库） ---"
head -3 "$ERR"
