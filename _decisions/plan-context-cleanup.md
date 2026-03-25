# Plan: 上下文污染清理 + 项目理解重建

> **Date**: 2026-03-24 | **Status**: DRAFT — 等待用户批注
> **问题**: 每个新 session 读到 Obsidian 时代过时上下文 → 做出过时建议 → 用户纠正 → 浪费时间
> **目标**: 清理全部过时引用 + BMAD document-project 从实际代码生成新项目理解

---

## Step 1: 归档 Legacy 目录（~15 min）

### 1A: 移动 canvas-progress-tracker/ → _archive/
- **路径**: `canvas-progress-tracker/` (22,611 文件，含 node_modules)
- **操作**: `git mv canvas-progress-tracker/ _archive/canvas-progress-tracker/`
- **风险**: 无——完全 legacy，无任何文件被当前 Tauri+React 代码 import

### 1B: 移动 obsidian-canvas-learning/ → _archive/
- **路径**: `obsidian-canvas-learning/` (991 文件，含 34 Svelte 组件)
- **操作**: `git mv obsidian-canvas-learning/ _archive/obsidian-canvas-learning/`
- **风险**: 无——旧版 Svelte 前端 + v1 参考，完全 legacy

### 1C: .gitignore 排除 _archive/ 的 node_modules
- 添加 `_archive/**/node_modules/` 到 .gitignore（如有）

<!-- 用户批注区 ———————————————————————————
Q: 是 git mv 保留历史，还是直接删除？保留归档的好处是以后还能参考旧实现。
User:git mv 保留历史
————————————————————————————————————————— -->

---

## Step 2: 精简 CLAUDE.md + Rules（~30 min）

### 2A: 全局 ~/.claude/CLAUDE.md（29行→~20行）

| 行 | 现状 | 改为 |
|----|------|------|
| 8 | `不脱离用户初衷、实际代码、Obsidian 插件环境` | `不脱离用户初衷、实际代码、Tauri+React 环境` |
| 12 | `DD-06 Obsidian 适配 — CSS 隔离、Plugin API 限制、主题兼容、Electron 约束` | `DD-06 前端规范 — Tauri+React+Vite，组件在 frontend/src/` |

### 2B: 删除重复 rules 文件（canvas-learning-system/.claude/rules/ 的 3 个副本）

**删除**以下 3 个与 canvas/.claude/rules/ 100% 重复的文件：
- `canvas-learning-system/.claude/rules/dd06-obsidian-adaptation.md` (38行)
- `canvas-learning-system/.claude/rules/development-discipline.md` (101行)
- `canvas-learning-system/.claude/rules/mcp-tools.md` (28行)

**原因**: canvas-learning-system 是 canvas 的子目录，Claude Code 自动加载父目录的 rules。子目录的副本是纯粹浪费。

### 2C: 重命名+清理 canvas/.claude/rules/dd06-obsidian-adaptation.md

- 重命名为 `dd06-frontend-standards.md`
- 删除全部 Legacy Obsidian 段落（34-38行）
- 删除"禁止使用 Obsidian Plugin API"（产品已完全脱离，不需要反复提醒）
- 保留 Tauri+React 规范部分

### 2D: 更新 canvas/.claude/rules/development-discipline.md 行12

- `旧 Obsidian 插件为 legacy。前端用 React 规范，不用 Obsidian Plugin API`
- → `前端用 React 规范（frontend/src/）`

### 2E: 删除 obsidian-canvas-learning/CLAUDE.md

- 如果 Step 1B 已归档整个目录，此文件自动移走
- 如果分开操作：直接 `git rm`

### 2F: canvas-learning-system/CLAUDE.md 行14

- `旧 Obsidian 插件为 legacy` → 删除此引用（legacy 已归档不需要提）

<!-- 用户批注区 ———————————————————————————
Q1: canvas/.claude/rules/ 里的 brainstorming-decisions.md 和 deep-explore-code-review.md
    这两个文件（94+87=181行）只存在于父目录，不重复。要保留还是也精简？
U:请你进行保留，然后obsidian 上有一个内容是十分重要的就是实现我们的Session A 可以在agent 对话回复的过程中返回我们的精确的笔记片段，然后这时候就有相关链接点击跳转回obsidian，但是有一个实现的大前提就是你要看这个方案是否成熟
Q2: 精简后的 CLAUDE.md 总量目标是 <100 行（当前 ~87 行正文，950 行含 rules）。
    删除 3 个副本 + 清理 Obsidian 引用后预计降到 ~700 行。还需要进一步压缩吗？不需要
————————————————————————————————————————— -->

---

## Step 3: BMAD document-project（1-2 小时）

运行 `/bmad-bmm-document-project`，让它**直接读实际代码**（不读 Graphiti 旧决策）：
- 扫描 frontend/src/ (54 文件, 7982 行 React+TS)
- 扫描 backend/app/ (179 文件, 83846 行 FastAPI)
- 扫描 docker-compose.yml, package.json, Cargo.toml
- 生成 `project-context.md` + `project-knowledge/` 分模块文档

**这是核心步骤**——生成的 project-context.md 反映代码库真实现状，替代 Graphiti 里那些过时的 fact。

<!-- 用户批注区 ———————————————————————————
Q: document-project 生成的文件放在哪？根目录？_bmad-output/? U ：放在bmad out put；然后我还有一个想法就是我们的Graphiti 检索过滤能不能按照时间来过滤检索，因为我记得一个点就是我们的Graphiti 是时序图谱，不应该老是看过时的内容
————————————————————————————————————————— -->

---

## Step 4: 基于 project-context.md 写 mvp-plan.md（30 min）

用 Boris Tane plan.md 模式：
1. 读 project-context.md（Step 3 产出）
2. 对照 MVP 刚需 14 项清单
3. 写 `_decisions/mvp-plan.md`：14 项功能 × 当前代码真实状态 = 具体任务
4. 你在 plan 上批注
5. 批准后开始写代码

---

## 执行顺序和时间估算

| Step | 内容 | 时间 | 前置 |
|------|------|------|------|
| 1 | 归档 legacy 目录 | 15 min | 无 |
| 2 | 精简 CLAUDE.md + rules | 30 min | 无（可与 Step 1 并行） |
| 3 | /bmad-bmm-document-project | 1-2 h | Step 1+2 完成（确保不扫描 legacy 代码） |
| 4 | 写 mvp-plan.md | 30 min | Step 3 完成 |
| **总计** | | **2-3 h** | |

---

## 不在本 Plan 范围内

- ❌ Graphiti 旧 fact 清理（量太大，后续单独处理）
- ❌ 6Phase Graphiti 迁移（被 Gemini 额度阻塞）
- ❌ 假命名修复（依赖迁移计划，Step 4 之后再排期）
- ❌ 测试基线（Step 4 mvp-plan 里再安排）
