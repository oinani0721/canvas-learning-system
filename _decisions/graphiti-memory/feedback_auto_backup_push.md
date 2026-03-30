---
name: Git commit 后自动 push 到 backup 远程仓库
description: 用户要求每次 commit 后自动 push 到 backup remote（lefthook post-commit hook）
type: feedback
---

用户要求每次代码更新都自动 push 到 GitHub backup 仓库。

**Why:** 用户希望所有改动实时备份，不需要手动 push。

**How to apply:** 已通过 lefthook.yml post-commit 的 `backup-push` 命令实现（`git push backup HEAD --quiet`）。commit 时自动触发，网络失败不阻塞。无需再手动 push backup。
