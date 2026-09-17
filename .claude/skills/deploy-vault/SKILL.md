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

**实现**: 入口是 `<harness>/scripts/deploy-vault.sh`，六步
（preflight / install / postprocess / verify / activate / evidence；内部第 2 步
才调 `install-vault.sh`）。模板源 = **harness 树的 `canvas-vault/`**（git 追踪
系统件）+ 脚本生成件 —— 不是「活 vault 即模板」。每 vault 应当不同的东西
（后端鉴权 key、插件绑定值、MCP 批准）一律按实例**生成**，绝不从旧库复制。
本 skill 只是薄壳。

**harness 树怎么定**：Claude Code 在仓内时 `git rev-parse --show-toplevel`；
在 vault 内时读该 vault `.canvas-config.yaml` 的 `harness_tree` 字段
（schema 2.1 起写入）。

**Steps**

1. **Ask (only if unclear)**: vault 名是否即学科名？用户没说就用 vault 名当
   subject。是否立即激活（起这个 vault 的后端实例）？用户没提激活意图就
   **不加 --activate**（可先建多个 vault 再选择激活）。
   ⚠️ vault 名必须是 `sanitize_vault_id` 与 `vault_key` 的**共同不动点**
   （小写 ASCII 字母数字下划线，无 `-`、无空格），否则 preflight 直接 rc 71
   拒绝 —— 两套命名口径分裂会让后端与推送链指向不同的 key。

2. **先 dry-run**（不加 `--apply` 就是 dry-run，零写）:

   ```bash
   <harness>/scripts/deploy-vault.sh --vault <目标 vault 绝对路径> \
       --harness <harness 树> --port <n> --hosts claude
   ```

   打印六行 `[N/6] <step>: OK|SKIP|FAIL <一句>`。rc：0 成功 / 64 用法错 /
   7N 第 N 步失败。看清楚每步要做什么，再加 `--apply` 真做。
   `--port` 缺省 8011；`--hosts` 本版支持 `claude` 与 `opencode`（逗号分隔，可并存），
   其余（`codex` / `dsh` …）仍 rc 64 等实测表。带 `opencode` 时 `--apply` 会在 vault 里
   多生成两件**静态**绑定件：`.agents/skills/<name>`（指向同名 `.claude/skills` 条目的
   条目级软链）与 `AGENTS.md`（技能清单 + 项目级 MCP 接线指引）。不跑 OpenCode 模型，
   也不碰 `~/.config` 下的用户级配置。

3. **Apply**: 同一条命令加 `--apply`（要激活再加 `--activate`）。
   脚本会按实例重生鉴权 key（0600）并同步到 `.env.<vault>` 与插件 `data.json`
   三处，再跑只读校验器（rc 必须 0）。

4. **If --activate was used**: 步 5 先 `docker compose config` 结构化断言容器名
   与端口映射，再起这个 vault 的绑定实例 —

   ```bash
   docker compose -f <harness>/docker-compose.yml \
       --env-file <harness>/.env.<vault> -p cls-<vault> up -d backend
   ```

   这一步**由 deploy-vault.sh 步 5 执行，需用户当次授权**（顶替容器 = 影响现网）。
   之后 `curl -s http://127.0.0.1:<port>/api/v1/vault/current` 确认
   `vault_name` 已是新 vault。

5. **Report to the user** (原样转述六行状态), plus:
   - 在 Obsidian 里「打开另一个 vault」→ 选新目录（插件与快捷键已随 vault 就位，无需再配置）
   - 首验路径：Cmd+P 建原白板 → 写内容 → `/start-exam-board` 出题
   - 未激活时提醒：检索/推送仍指向旧 vault，激活方法见上一步

**Error Handling**

- 目标目录已存在 → 步 2 会拒绝（防误伤学习数据），rc 72。想重新绑定一个已有
  vault（adopt）本版不支持。
- 任何一步 FAIL → rc 是 `7N`，`N` 就是失败的步号；把那一行原样报给用户，
  不要宣称部署成功。
- rc 71 且消息含「禁写面」→ 传进来的路径落在受保护目录（live vault、
  `$HOME/Library`、各家 CLI 配置目录、`.git` 内、`*.env` 文件），换路径。
