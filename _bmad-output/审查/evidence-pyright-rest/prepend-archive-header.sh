#!/bin/zsh
# 协议 §2.1 存档首部：六行 blockquote + `---`，缺三字段任一该轮不计入轮次配额。
# 用法: prepend-archive-header.sh <round> <绑定SHA>
set -u
T=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u2-pyright-rest
R=$1; SHA=$2
MD="$T/_bmad-output/审查/codex-review-CARD-PYRIGHT-DEBT-rest-r$R.md"
ERR="$T/_bmad-output/审查/codex-review-CARD-PYRIGHT-DEBT-rest-r$R.stderr"
test -s "$MD" || { echo "ABORT: $MD 为空或不存在"; exit 1; }
grep -q '^> 批次:' "$MD" && { echo "ABORT: 首部已存在, 不重复加"; exit 1; }
# 会话头自证：抄 stderr 里含 model / reasoning effort 的三行（stderr 本身不入库）
L1=$(grep -m1 '^OpenAI Codex' "$ERR")
L2=$(grep -m1 '^model:' "$ERR")
L3=$(grep -m1 '^reasoning effort:' "$ERR")
test -n "$L1" && test -n "$L2" && test -n "$L3" || { echo "ABORT: stderr 里取不到会话头三行（首部缺字段=该轮不计配额）"; exit 1; }
CODEXV=$(codex --version 2>&1 | tail -1)
TMP=$(mktemp)
{
  echo "> 批次: BATCH-2026-09-07-第十三批 · 车道 U2 · 卡 CARD-PYRIGHT-DEBT-rest round-$R"
  echo "> 模型: \`gpt-6-astra\` · reasoning_effort: \`ultra\` · codex: \`$CODEXV\`"
  echo "> 命令: \`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort=\"ultra\" \"\$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-DEBT-rest-r$R.md)\"\`"
  echo "> 审查绑定: \`$SHA\`（= 阶段 1 末 HEAD；按 D-15 阶段 1 这一轮**不绑合并态**，阶段 2 末轮必绑最终 HEAD）"
  echo "> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:"
  echo "> \`$L1\` / \`$L2\` / \`$L3\`"
  echo
  echo "---"
  echo
  cat "$MD"
} > "$TMP"
cp "$TMP" "$MD"
echo "首部已加。前 8 行:"
head -8 "$MD"
