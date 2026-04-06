# CLAUDE.md — Canvas Learning System

## 项目

Tauri 2 + React + TypeScript + FastAPI + Neo4j + LanceDB 桌面学习应用。
前端: `frontend/src/`。后端: `backend/app/`。Sidecar: `frontend/sidecar/`。

## 硬规则（Hook exit 2 确定性执行，违反 = 阻断）

1. **DD-03 禁 mock** — 禁止假 API/模拟数据/TODO 空函数。PreToolUse hook 检测 mock 模式并 exit 2 阻断
2. **DD-12 范围约束** — frontend agent 只改 frontend/，backend agent 只改 backend/。PreToolUse hook exit 2 阻断
3. **DD-13 名实一致** — 函数名必须匹配实际行为。PreToolUse hook 检测名称-导入不匹配并 exit 2 阻断

> 其余 DD 规则详见 `.claude/rules/development-discipline.md`（自动加载）

## 工作流（Boris 模式）

1. **Plan Mode 先行** — 多文件/多技术任务必须先进 Plan Mode（Shift+Tab×2）读代码+提问+产出计划
2. **设计先于代码** — 创建功能前，先问清楚需求，提出 2-3 种方案，用户确认后再写代码
3. **增量提问** — 不确定就问用户。技术决策用用户能听懂的语言解释
4. **验收步骤** — 代码修改后提供最小验收步骤（启动→操作→预期看到什么）

## Graphiti 协议

- **MCP**: `graphiti-canvas`（group_id: `canvas-dev`）
- **搜索**: 每轮 `search_memory_facts(exclude_invalidated: true)`。需要精确结果时用 `center_node_uuid`
- **记录**: 决策记 `[Decision]`，审查记 `[Code-Review]`，不确定→记录
- **搜索模式**: 默认 `rrf`。审计用 `mmr`(去重)。精确查询用 `cross_encoder`

## MCP 工具

- **Sequential Thinking**: 复杂推理/多步骤/解题 → 必须调用
- **Context7**: 查库/框架/API 文档 → 先查文档再写代码
- **LSP**: 编辑代码后查 diagnostics

## 测试

- 后端: `pytest`（80+ 测试文件已就绪）
- 前端: `vitest` + `@testing-library/react`
- Hook 会在代码编辑后自动运行相关测试

## 已知问题

详见 `docs/known-gotchas.md`（20 条，12 待修）。重点关注:
- G-FAKE: 42+ 假命名函数（名称含 graphiti 但实际调 Neo4j）
- G-PIPE: 6 条断裂管道（已实现但无调用方）

## 风格参考文件

修改代码前先读对应的参考文件：
- 后端 service: `backend/app/services/rag_service.py`
- 后端 router: `backend/app/api/v1/endpoints/canvas.py`
- 前端 state: `frontend/src/stores/chat-store.ts`
- 前端组件: `frontend/src/components/ChatPanel.tsx`

## Bug 修复规则

- 复杂 bug（多文件）必须先分析根因，用户确认方案后再修
- 禁止一次修复混合多个不相关变更
- 修复后必须跑测试：`.venv/bin/pytest tests/ -x -q`
- 批注追踪清单: `docs/project-status/annotation-tracker.md`

## OpenSpec 工作流（Hybrid — CLI 强制结构 + Claude 填内容）

从 2026-04-06 起，所有**新**的 OpenSpec change 必须走 CLI 流程：

1. **创建**：`npx openspec new change <kebab-name>` —— 禁止手动 `mkdir` 或复制现有目录
2. **获取模板**：`npx openspec instructions <artifact-id> --change <name> --json` —— 每个 artifact（proposal/design/specs/tasks）单独跑
3. **填内容**：Claude 按 template + config.yaml 的 context + rules 填文件
4. **校验**：`npx openspec validate <name> --strict` —— 失败即重写
5. **状态**：`npx openspec status --change <name>` —— `Progress: 4/4 artifacts complete` 才算 apply-ready
6. **归档**：`npx openspec archive <name>` —— 禁止 `git mv`，归档命令会自动合并 delta 到主 spec

### Proposal 格式硬约束（CLI schema 要求）

- `## Why`（必需，不能用 `## What & Why` 之类的变体）
- `## What Changes`（必需）
- `## Capabilities`（可选但推荐）
- `## Impact`（可选）

### Specs 格式硬约束

- 每个 capability 一个文件：`specs/<capability>/spec.md`
- Delta 头部：`## ADDED Requirements` / `## MODIFIED Requirements` / `## REMOVED Requirements`
- 每个 requirement 必须至少 1 个 scenario
- Scenario 头部**必须**是 4 个 hashtag（`#### Scenario:`）—— 3 个会静默失败
- 语法：`### Requirement: <name>` + SHALL/MUST 描述 + `#### Scenario: <name>` + WHEN/THEN

### 历史债（legacy changes）

3 个 CLI 安装前手写的 change（`fr-kg-05-recommendation-mvp`, `trackpad-pan-support`, 以及 validate 失败的部分 `fr-kg-04-sync-pipeline-fix`）缺 `specs/` 目录，无法通过 `openspec archive`。这些 change 需要在真正归档前回填 specs，否则 `openspec/specs/` 下的主 spec 永远不累积。

### 为什么是 Hybrid 而不是 Only CLI

CLI 负责**结构 + 校验 + 归档**，Claude 负责**内容写作**。Boris 工作流（Plan → Design → Confirm → Execute）与 CLI 零冲突。

## 项目文档

- 架构: `docs/architecture.md`
- MVP 刚需: `_decisions/mvp-plan.md`（14 项 + 用户批注）
- 决策索引: `_decisions/decision-log.md`
- 前端组件: `docs/component-inventory-frontend.md`
- 后端 API: `docs/api-contracts-backend.md`
- **Gap Analysis**: `docs/project-status/gap-analysis.md`（99 FR + 用户批注）
- **批注追踪**: `docs/project-status/annotation-tracker.md`（108 条分类追踪）
- **进度报告**: `docs/project-status/s40-progress-report.md`
- **OpenSpec**: `openspec/config.yaml`
