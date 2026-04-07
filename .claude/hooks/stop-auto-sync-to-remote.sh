#!/bin/bash
# Stop hook: auto-sync working tree changes to remote
#
# 触发时机: 每轮 Claude Code 对话结束 (Stop event)
# 设计参考: stop-deep-research-clipboard.js (永不阻断、异常吞咽、dedup)
#
# 流程:
#   1. mkdir 原子锁 (POSIX 可移植，替代 macOS 缺失的 flock)
#   2. 检查 git 仓库 + git 状态机 (merge/rebase/cherry-pick 时跳过)
#   3. git add -A，但 reset 排除 _backups/ + backend/mutants/ (双保险)
#   4. commit 带 Co-Authored-By (走 lefthook commit-msg 的 escape hatch)
#   5. lefthook post-commit 自动推 backup + origin
#   6. 额外推 wip/auto-sync 双 remote (force-with-lease)
#   7. rmdir 锁，exit 0
#
# 铁律:
#   - 永不阻断 Claude (任何 error 都 exit 0)
#   - 永不写入 _backups/ 或 backend/mutants/ (即使 .gitignore 漏了)
#   - 永不在 git 状态机非空时 commit (避免污染冲突标记)

set -u  # 未定义变量报错。不用 set -e，避免单点失败 exit 非零阻断 Claude

LOG_FILE="$HOME/.claude/auto-sync.log"
LOCK_DIR="$HOME/.claude/auto-sync.lock.d"  # mkdir 原子锁，目录形式

log() {
  printf '[%s] [pid=%d] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$$" "$*" >> "$LOG_FILE"
}

# ─── Stage 1: 必须在 git 仓库内 ─────────────────────────────
if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then
  log "skip: CLAUDE_PROJECT_DIR unset"
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || {
  log "skip: cannot cd to $CLAUDE_PROJECT_DIR"
  exit 0
}

git rev-parse --git-dir > /dev/null 2>&1 || {
  log "skip: not a git repo"
  exit 0
}

GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)

# ─── Stage 2: mkdir 原子锁 (防多 worktree session 并发) ─────
# mkdir 在 POSIX 上原子: 要么成功创建目录，要么 EEXIST
# 比 flock 更可移植 (macOS 没有 flock)
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "skip: lock held by another session"
  exit 0
fi
# trap 确保任何 exit 路径都释放锁
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

# ─── Stage 3: 检查 git 状态机 (merge/rebase/cherry-pick) ────
# 这些状态下绝对不能 git add -A + commit，否则会 commit 冲突标记
if [ -f "$GIT_DIR/MERGE_HEAD" ]; then
  log "skip: merge in progress (MERGE_HEAD exists)"
  exit 0
fi
if [ -d "$GIT_DIR/rebase-merge" ] || [ -d "$GIT_DIR/rebase-apply" ]; then
  log "skip: rebase in progress"
  exit 0
fi
if [ -f "$GIT_DIR/CHERRY_PICK_HEAD" ]; then
  log "skip: cherry-pick in progress"
  exit 0
fi
if [ -f "$GIT_DIR/REVERT_HEAD" ]; then
  log "skip: revert in progress"
  exit 0
fi
if [ -f "$GIT_DIR/BISECT_LOG" ]; then
  log "skip: bisect in progress"
  exit 0
fi

# ─── Stage 4: 检查是否有 unmerged paths (双保险) ────────────
# 即使没有 MERGE_HEAD，也可能有遗留的冲突标记
if git diff --check --cached 2>/dev/null | grep -q "conflict marker"; then
  log "skip: unmerged conflict markers detected"
  exit 0
fi

# ─── Stage 5: 检测是否有变化需要 sync ────────────────────────
if git diff --quiet 2>/dev/null && \
   git diff --cached --quiet 2>/dev/null && \
   [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
  log "skip: clean working tree"
  exit 0
fi

# ─── Stage 6: 收集变化信息 (用于 commit message) ────────────
COUNT=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
SAMPLE=$(git status --short 2>/dev/null | head -5 | awk '{print $NF}' | tr '\n' ' ' | sed 's/ $//')

# ─── Stage 7: git add -A，但排除危险目录 (双保险) ──────────
git add -A 2>/dev/null
# 即使 .gitignore 有，也再 reset 一遍兜底
git reset HEAD -- _backups/ backend/mutants/ 2>/dev/null || true

# ─── Stage 8: reset 后二次检查 ──────────────────────────────
if git diff --cached --quiet 2>/dev/null; then
  log "skip: nothing to commit after reset"
  exit 0
fi

# ─── Stage 9: commit (Co-Authored-By 是 spec-ref escape hatch) ──
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
COMMIT_MSG="wip(auto-sync): ${COUNT} files [${SAMPLE}]

Auto-synced by Claude Code Stop hook.
Session: ${SESSION_ID}

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"

if ! git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1; then
  log "FAIL: commit aborted (lefthook pre-commit/commit-msg likely blocked, see above)"
  exit 0  # 永不阻断 Claude
fi

COMMIT_HASH=$(git rev-parse HEAD 2>/dev/null)
log "commit OK: $COMMIT_HASH ($COUNT files)"

# 注意: lefthook post-commit 已经在上面 commit 时自动跑了:
#   - backup-push: git push backup HEAD --no-verify (永过)
#   - origin-push: git push origin HEAD (会跑 pre-push tests)
# 我们只需要额外推 wip/auto-sync 分支

# ─── Stage 10: 额外推 wip/auto-sync 双 remote ───────────────
# force-with-lease 比 force 安全: 如果 remote 有别人推的新 commit 会失败
git push origin "${COMMIT_HASH}:refs/heads/wip/auto-sync" --force-with-lease >> "$LOG_FILE" 2>&1 \
  && log "wip origin push OK" \
  || log "WARN: wip origin push failed (commit still exists on main)"

git push backup "${COMMIT_HASH}:refs/heads/wip/auto-sync" --force-with-lease >> "$LOG_FILE" 2>&1 \
  && log "wip backup push OK" \
  || log "WARN: wip backup push failed"

log "DONE: auto-synced $COUNT files (commit $COMMIT_HASH)"
exit 0
