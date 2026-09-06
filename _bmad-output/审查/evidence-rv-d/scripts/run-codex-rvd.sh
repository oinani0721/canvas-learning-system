#!/bin/bash
# CARD-RV-D 的 Codex 复核：1 轮 2 prompt（协议 §2）
# 用法：bash run-codex-rvd.sh p1   /   bash run-codex-rvd.sh p2
set -uo pipefail

P="${1:?用法: $0 p1|p2}"
TREE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene
PROMPT="$TREE/_bmad-output/审查/prompts/codex-prompt-CARD-RV-D-$P.md"
OUT="$TREE/_bmad-output/审查/codex-review-CARD-RV-D-$P.md"
ERR="$TREE/_bmad-output/审查/codex-review-CARD-RV-D-$P.stderr"
CODEX=/opt/homebrew/bin/codex

cd "$TREE" || exit 90
test -s "$PROMPT" || { echo "⛔ prompt 缺失: $PROMPT"; exit 91; }
# 前置：harness 必须已退出，否则 SKILL.md / validator 可能是变异体
# ⚠️ 判据必须「解释器 + 脚本路径」同时出现：宽判据 `pgrep -f '<脚本路径>'` 会命中
# **别的进程参数里提到该路径的文本**（实测 2026-09-06：另一车道的 codex 把 prompt
# 塞进 argv，里面正好写了这个脚本名 ⇒ 假阳性拦停）。
if ps -A -o command= | grep -qE 'python[^ ]*[[:space:]]+[^ ]*scripts/g32(cb_mutation_gates|ccr1_negative_controls)\.py'; then
  echo "⛔ 变异 harness 仍在运行 —— 此刻工作树文件可能是变异体，拒绝送审"
  exit 92
fi
# 交叉验证（比进程判据更硬）：harness 运行期间这两个文件是变异体，sha 必然 ≠ 基线
SB=$(ls -t "$TREE/_bmad-output/审查/evidence-rv-d"/sha-before-*.txt 2>/dev/null | head -1)
if [ -n "$SB" ]; then
  if ! diff -q <(cd "$TREE" && shasum -a 256 canvas-vault/.claude/skills/quiz-answer/SKILL.md backend/scripts/validate_learning_events.py) "$SB" >/dev/null; then
    echo "⛔ SKILL.md / validator 的 sha 不等于基线 —— 可能是变异体，拒绝送审"
    exit 93
  fi
  echo "前置 OK：两文件 sha = 基线（harness 已结束且完整还原）"
fi
echo "prompt $(wc -c < "$PROMPT")B / codex $("$CODEX" --version 2>&1 | head -1)"

"$CODEX" exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat "$PROMPT")" > "$OUT" 2> "$ERR" </dev/null
RC=$?
echo "codex($P) rc=$RC  正文 $(wc -c < "$OUT")B  stderr $(wc -c < "$ERR")B"
if [ ! -s "$OUT" ]; then
  echo "⛔ 正文 0 字节 —— 按四因查 stderr 尾部（配额 / 内容拦 / tls / CLI 版本）:"
  tail -20 "$ERR"
else
  echo "--- 正文首 12 行 ---"; head -12 "$OUT"
fi
echo "--- 会话头（存档首部自证用） ---"
grep -m1 '^workdir:' "$ERR"; grep -m1 '^model:' "$ERR"; grep -m1 '^reasoning effort:' "$ERR"
