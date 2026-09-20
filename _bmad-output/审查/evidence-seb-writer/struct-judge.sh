#!/bin/bash
# CARD-SEB-WRITER-SUBSTRING-TMP 结构成对判据（同一脚本跑 open/close 两侧，口径逐字同）
# 用法: bash struct-judge.sh <worktree-root> <probe-tmpfile>
#  - 第 2 个参数是验伪锚用的临时正例文件路径（调用方负责建/留，脚本不删文件）
set -u
cd "$1" || exit 2
PROBE="$2"
SEB=canvas-vault/.claude/skills/start-exam-board/SKILL.md
CAS=backend/tests/regression/test_g3_3_cas.py
SCH=backend/tests/regression/test_learning_events_schema_contract.py
echo "=== struct-judge @ $(git rev-parse --short=8 HEAD) $(date -Iseconds) ==="
echo "--- (f)4 裸字面量 / 命名空间字面量（三文件成对）---"
for f in "$SEB" "$CAS" "$SCH"; do
  printf '%s bare=%s ns=%s\n' "$f" \
    "$(grep -cF '/tmp/exam-created-event.json' "$f")" \
    "$(grep -cF '/tmp/cls-exam/exam-created-event.json' "$f")"
done
echo "--- (f)1 2 3 7 写规结构 ---"
printf 'in_ln=%s\n'   "$(grep -cF 'in ln for ln in _lines' "$SEB")"
printf 'replace=%s\n' "$(grep -cF 'decode("utf-8", "replace")' "$SEB")"
printf 'eq=%s\n'      "$(grep -cF '_rec.get("event_id") == evid' "$SEB")"
printf 'card=%s\n'    "$(grep -c 'CARD-SEB-WRITER-SUBSTRING-TMP' "$SEB")"
echo "--- 计数两端 + digest ---"
printf 'tmp_all=%s tmp_ns=%s\n' \
  "$(grep -o '/tmp/' "$SEB" | wc -l | tr -d ' ')" \
  "$(grep -o '/tmp/cls-exam/' "$SEB" | wc -l | tr -d ' ')"
shasum -a 256 "$SEB"
echo "--- 验伪锚: 六个 grep 模式各喂一条已知为真的独立正例（证明模式本身能命中，非文件真为零）---"
printf 'anchorfile=%s\n' "$PROBE"
printf 'anchor in_ln=%s replace=%s eq=%s card=%s bare=%s ns=%s (六项均须=1)\n' \
  "$(grep -cF 'in ln for ln in _lines' "$PROBE")" \
  "$(grep -cF 'decode("utf-8", "replace")' "$PROBE")" \
  "$(grep -cF '_rec.get("event_id") == evid' "$PROBE")" \
  "$(grep -c 'CARD-SEB-WRITER-SUBSTRING-TMP' "$PROBE")" \
  "$(grep -cF '/tmp/exam-created-event.json' "$PROBE")" \
  "$(grep -cF '/tmp/cls-exam/exam-created-event.json' "$PROBE")"
