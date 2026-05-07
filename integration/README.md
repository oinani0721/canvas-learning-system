# Integration: Canvas → DeepTutor MVP

> **目标**：10 天验证 Canvas 5 大核心嵌入 DeepTutor 14 块 BlockType 的集成效果。
> **不是 production**。失败可弃。

## 目录结构

```
integration/
├── README.md                        ← 本文件
├── deeptutor-patches/               ← cp 到 DeepTutor fork 的代码
│   ├── backend/
│   │   ├── canvas_client.py         ← HTTP 客户端 to Canvas :8011
│   │   ├── wikilink_proxy_router.py ← Day 2 wikilink 代理
│   │   └── exam_proxy_router.py     ← Day 4 ACP 代理
│   ├── frontend/
│   │   ├── wikilink-parser.ts       ← Day 1 [[xxx]] 正则
│   │   ├── remark-wikilink-plugin.ts← Day 1 remark plugin
│   │   └── BLOCK_TYPE_PATCH.md      ← Day 5 Enum 扩展指南
│   └── docker/
│       └── docker-compose.canvas.yml← Day 3 双服务编排
└── scripts/
    ├── start-integration.sh         ← 一键启动（Canvas + DeepTutor）
    ├── health-check.sh              ← 双服务健康检查
    └── apply-staging-patches.sh     ← cp patches 到 fork
```

## 一键启动流程

### 0. 前置（用户必须自己做）

```bash
# 1. 在 GitHub 浏览器 fork
open https://github.com/HKUDS/DeepTutor

# 2. Clone 到 ~/Desktop/canvas/deeptutor-fork/
cd ~/Desktop/canvas
git clone https://github.com/<你的用户名>/DeepTutor.git deeptutor-fork
cd deeptutor-fork
git checkout -b mvp-canvas-integration
git tag mvp-baseline
git remote add upstream https://github.com/HKUDS/DeepTutor.git
```

### 1. 启动 Canvas 后端（这个 worktree 内）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp

# Canvas only（DeepTutor fork 没就绪时）
./integration/scripts/start-integration.sh --canvas-only

# 或双服务（fork 已就绪）
./integration/scripts/start-integration.sh
```

### 2. 健康检查

```bash
./integration/scripts/health-check.sh
```

期望输出：
```
[OK]    Canvas       http://localhost:8011/api/v1/health  (HTTP 200)
[OK]    DeepTutor    http://localhost:8001/api/v1/health  (HTTP 200)
[OK]    Neo4j        http://localhost:7478                (HTTP 200)
[OK]    access-control-allow-origin: http://localhost:3782
===== 全部通过 =====
```

### 3. 应用 patches 到 fork

```bash
# 先 dry-run 看效果
./integration/scripts/apply-staging-patches.sh --dry-run

# 确认后真正应用
./integration/scripts/apply-staging-patches.sh

# 在 fork 内提交
cd ~/Desktop/canvas/deeptutor-fork
git status
git diff
git add -A && git commit -m "feat: apply Canvas integration patches (Day 1)"
git tag mvp-day-1
```

## 端口约定

| 服务 | 端口 | 容器 |
|---|---|---|
| Canvas backend | **8011** | canvas-mvp-backend-1 |
| Canvas Neo4j Bolt | 7691 | canvas-mvp-neo4j-1 |
| Canvas Neo4j HTTP | 7478 | canvas-mvp-neo4j-1 |
| DeepTutor backend | 8001 | （fork 自决） |
| DeepTutor frontend | 3782 | （fork 自决） |

## Day 0 → Day 1 准备就绪 5 项

```
[ ] 1. 新 worktree 已创建（git worktree list 看到 feature-deeptutor-canvas-mvp）
[ ] 2. Canvas backend/.env 已修：FASTAPI_PORT=8011 + CORS 含 :3782 :8001
[ ] 3. Canvas :8011/api/v1/health 返回 HTTP 200
[ ] 4. DeepTutor fork 已 clone（~/Desktop/canvas/deeptutor-fork/.git 存在）
[ ] 5. DeepTutor :8001/api/v1/health 返回 HTTP 200（baseline 零代码改动）
```

5 项全勾 → 立刻执行 Day 1 wikilink 6 步（详见 round-22 报告 §四）。

## Day 1 wikilink 6 步速览

| 步 | 内容 | 工具 |
|---|---|---|
| 1 | cp staging frontend → fork web/lib/wikilink/ | apply-staging-patches.sh |
| 2 | 改 fork RichMarkdownRenderer.tsx 注入 plugin | 手动 Edit |
| 3 | 验证 `[[xxx]]` 渲染 | 浏览器 + DevTools |
| 4 | cp staging backend → fork backend/app/clients/ + routers/ | apply-staging-patches.sh |
| 5 | 注册 wikilink_proxy router | 手动 Edit fork main.py |
| 6 | 端到端 HTTP 链路 | curl `:8001/api/v1/wikilink/build` |

完整命令见 `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md` §四。

## 风险红线（违反 = MVP 失败）

| ⛔ | 规则 | 后果 |
|---|---|---|
| 🚫 | 不 `git pull upstream`（DeepTutor 30 天 24 release）| 主分支漂移会冲掉 patch |
| 🚫 | 不跑 DeepTutor 完整测试 | 14 块 Enum patch 必然挂部分单测 |
| 🚫 | 不改 Canvas backend 端口 8011 | 双服务约定，改了集成层会断 |
| 🚫 | 不在本 worktree 跑 Canvas 业务开发 | 集成专用，避免污染 |
| 🚫 | vault md 单一源 | DeepTutor 只 read-only mount，禁副本 |

## 退出策略

Day 6 / Day 10 决策点选"弃集成"：

```bash
# 1. 删 DeepTutor fork
rm -rf ~/Desktop/canvas/deeptutor-fork

# 2. 删 worktree
cd /Users/Heishing/Desktop/canvas/canvas-learning-system
git worktree remove .claude/worktrees/feature-deeptutor-canvas-mvp
git branch -D worktree-feature-deeptutor-canvas-mvp

# 3. Canvas 主线（feature-obsidian-hybrid-dev）零影响
```

## 双仓库

- **本 worktree**（Canvas）：push 到 `origin canvas-learning-system` + `backup`
- **DeepTutor fork**：push 到用户 GitHub fork，**不** push upstream HKUDS

## 决策报告

完整 10 天计划 + 5 个验证场景 + 10 个 hack + 5 个风险见：
`_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
