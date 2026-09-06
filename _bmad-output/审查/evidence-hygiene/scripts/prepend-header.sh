#!/bin/bash
# 按协议 §2.1 给 Codex 存档加首部 blockquote（六行）+ ---，正文一字不改。
# 牙齿：缺 模型 / reasoning_effort / codex 任一字段，该轮不计入轮次配额。
set -uo pipefail

TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene
CARD=CARD-TEST-hygiene-vaultinit
OUT="$TREE/_bmad-output/审查/codex-review-$CARD.md"
ERR="$TREE/_bmad-output/审查/codex-review-$CARD.stderr"
SHA=$(git -C "$TREE" rev-parse HEAD)

test -s "$OUT" || { echo "⛔ 正文为空，不加首部（先查 stderr 四因）"; exit 1; }
grep -q '^> 批次:' "$OUT" && { echo "已有首部，跳过"; exit 0; }

# 从 stderr 抄会话头三行（含 model 行）作自证
L_WORK=$(grep -m1 '^workdir:' "$ERR")
L_MODEL=$(grep -m1 '^model:' "$ERR")
L_EFFORT=$(grep -m1 '^reasoning effort:' "$ERR")
for v in "$L_MODEL" "$L_EFFORT"; do
  [ -n "$v" ] || { echo "⛔ 会话头缺字段，首部无法自证"; exit 2; }
done
CODEX_VER=$(grep -m1 '^OpenAI Codex' "$ERR" | sed 's/^OpenAI //')

TMP=$(mktemp)
{
  echo "> 批次: BATCH-2026-09-05-第十二批 · 车道 Y6 · 卡 $CARD round-1"
  echo "> 模型: \`gpt-6-astra\` · reasoning_effort: \`ultra\` · codex: \`${CODEX_VER}\`"
  echo "> 命令: \`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort=\"ultra\" \"\$(cat _bmad-output/审查/prompts/codex-prompt-$CARD.md)\"\`"
  echo "> 审查绑定: \`$SHA\`（本卡唯一代码 commit；其后仅 _bmad-output 变更）"
  echo "> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:"
  echo "> \`${L_WORK}\` / \`${L_MODEL}\` / \`${L_EFFORT}\`"
  echo ""
  echo "---"
  echo ""
  cat "$OUT"
} > "$TMP"
mv "$TMP" "$OUT"
echo "✅ 首部已加，正文未改。前 8 行："
head -8 "$OUT"
