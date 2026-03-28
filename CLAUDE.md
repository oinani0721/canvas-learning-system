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

## 项目文档

- 架构: `docs/architecture.md`
- MVP 刚需: `_decisions/mvp-plan.md`（14 项 + 用户批注）
- 决策索引: `_decisions/decision-log.md`
- 前端组件: `docs/component-inventory-frontend.md`
- 后端 API: `docs/api-contracts-backend.md`
