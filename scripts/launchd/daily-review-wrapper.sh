#!/usr/bin/env bash
# 每日复习推送 launchd 入口 wrapper (DAILY-REVIEW-PUSH-2026-07-29, 终审 A6)。
# 安装位置: ~/Library/Application Support/CanvasReview/bin/ — launchd 只指向
# 这个稳定路径, worktree 移动/清理不再让任务永久失效 (memory-health 6 天
# 停摆教训的结构性修复)。本文件是 git 追踪的源码副本, 改动后需重新 cp 安装。
set -uo pipefail

export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="${HOME:-/Users/Heishing}"
export LANG="zh_CN.UTF-8"

BOOTLOG="$HOME/Library/Logs/canvas-daily-review.boot.log"
# 第一行探针: 连 ~/Library 都写不了 = launchd 环境彻底异常
echo "[$(date '+%F %T')] wrapper start" >> "$BOOTLOG"

REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
VAULT="$REPO/canvas-vault"

fail() { echo "[$(date '+%F %T')] PREFLIGHT-FAIL: $1" >> "$BOOTLOG"; exit 78; }

# TCC preflight: Desktop 路径受 TCC 管辖。⚠ 必须真实读取 — [ -r ] 走 access()
# 在 TCC 域内会假通过 (2026-07-29 实测: 测试全过但 exec 仍 Operation not
# permitted), 只有 ls/head 这类真 I/O 才探得出来
ls "$VAULT/节点" >/dev/null 2>&1 \
    || fail "vault_not_readable_tcc — 系统设置→隐私与安全性→完全磁盘访问→给 /bin/bash 开启"
mkdir -p "$REPO/backups" 2>/dev/null || fail "backups_not_writable_tcc"
head -c 1 "$WT/scripts/daily-review-push.sh" >/dev/null 2>&1 \
    || fail "repo_script_unreadable_tcc_or_missing — TCC 未授权或 worktree 被清理"
# 双副本一致性 (Code-Review M4): runner import 的是主仓 vault 里的
# decay_beta.py, worktree 改了忘 cp 会造成静默行为漂移
cmp -s "$WT/canvas-vault/.claude/scripts/decay_beta.py" \
       "$REPO/canvas-vault/.claude/scripts/decay_beta.py" \
    || fail "decay_beta_version_skew — worktree 与主仓 vault 的 decay_beta.py 不一致, 需 cp 部署"

exec "$WT/scripts/daily-review-push.sh" "$@"
