---
name: deploy-vault
description: Deploy a new Obsidian vault for a course. Use when the user says "/deploy-vault <课程名>" to create, initialize, and switch to a new vault.
license: MIT
metadata:
  author: canvas-learning-system
  version: "2.0"
  story: "Story 1.8 + 1.9 → DEPLOY-VAULT-2026-08-02 翻新 (方案 1 用户拍板)"
---

Deploy a new, fully-working Canvas Learning System vault in one command.

**Input**: Course name (e.g., `/deploy-vault 操作系统`), optionally a subject
different from the vault name.

**实现**: 全部逻辑在 `scripts/install-vault.sh`（活 vault 即模板 — 从当前
ACTIVE_VAULT 复制系统件：8 个 skills、decay_beta/fsrs_bridge、hooks、
mcp.json、5 个 Obsidian 插件、快捷键、鉴权 key、Dashboard/CLAUDE.md，
并建现行骨架 原白板/检验白板/节点/outputs/raw + 按 vault 生成
.canvas-config.yaml）。本 skill 只是薄壳。

**Steps**

1. **Ask (only if unclear)**: vault 名是否即学科名？用户没说就用 vault 名当
   subject。是否立即激活（让后端/推送切到新 vault）？用户没提激活意图就
   **不加 --activate**（可先建多个 vault 再选择激活）。

2. **Run the installer**:

   ```bash
   /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/scripts/install-vault.sh "<vault-name>" --subject "<学科>" [--activate]
   ```

   脚本自带 10 项自检（--activate 时 +1 项）并打印 ✅/❌ 报告 + 后续步骤。
   任何 ❌ 都会非零退出，且自检失败时激活会被自动跳过（.env 不动）。

3. **If --activate was used and the script exited 0**: apply it —

   ```bash
   docker compose up -d backend
   ```

   然后 `curl -s http://127.0.0.1:8011/api/v1/vault/current` 确认
   `vault_name` 已是新 vault。

4. **Report to the user** (原样转述脚本的自检报告), plus:
   - 在 Obsidian 里「打开另一个 vault」→ 选新目录（插件与快捷键已随 vault 就位，无需再配置）
   - 首验路径：Cmd+P 建原白板 → 写内容 → `/start-exam-board` 出题
   - 未激活时提醒：检索/推送仍指向旧 vault，激活方法见脚本输出第 2 条

**Error Handling**

- 目标目录已存在 → 脚本会拒绝（防误伤学习数据）。想切换到已有 vault：
  手改 `.env` `ACTIVE_VAULT=<name>` + `docker compose up -d backend`。
- 自检出现 ❌ → 把失败项原样报给用户，不要宣称部署成功。
