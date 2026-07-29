#!/usr/bin/env bash
# 每日复习推送 — 编排壳 (DAILY-REVIEW-PUSH-2026-07-29)。
# 只做两件事: mkdir 互斥锁 (终审 A7: 手工/kickstart/定时可能重叠) +
# 固定解释器调 runner。业务逻辑全在 daily_review_run.py (--now 可测)。
set -uo pipefail

REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
LOCK="$REPO/backups/.daily-review.lock"

mkdir -p "$REPO/backups"
if ! mkdir "$LOCK" 2>/dev/null; then
    # 陈旧锁恢复 (Code-Review M5): 断电/SIGKILL 会留下锁目录, 不处理则
    # 之后每天 "skip: already running" 且 exit 0 永久静默。mtime 超 6h
    # 视为死锁夺回 (单次运行实测秒级, 6h 余量极大)。
    if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +360 2>/dev/null)" ]; then
        echo "stale lock (>6h), reclaiming" >&2
        rmdir "$LOCK" 2>/dev/null || true
    fi
    if ! mkdir "$LOCK" 2>/dev/null; then
        echo "skip: already running" >&2
        exit 0
    fi
fi
# 不用 exec — exec 会替换进程使 trap 失效, 锁永不释放
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT INT TERM

PY="$WT/backend/.venv/bin/python"
[ -x "$PY" ] || PY="/usr/bin/python3"   # venv 缺失兜底 (runner 仅 stdlib)

"$PY" "$WT/scripts/daily_review_run.py" "$@"
