---
name: S25 上下文污染清理 + BMAD document-project
description: S25完成Legacy归档+Obsidian引用清除+exhaustive scan生成8文档。用户方向调整：上下文污染是根本问题。
type: project
---

S25 Session (2026-03-24) — 上下文污染清理 + BMAD document-project exhaustive scan

**Why:** 用户指出"真正问题不是代码，是上下文污染"——Graphiti里几百条Obsidian时代fact，CLAUDE.md引用已废弃的Plugin API，每个新session被过时信息误导。

**How to apply:** 后续session应以 docs/index.md 为项目理解入口，不依赖Graphiti旧fact。

## 已完成
1. Legacy归档: canvas-progress-tracker/ + obsidian-canvas-learning/ → _archive/ (310 files, commit 146218b)
2. Obsidian引用清除: 全局CLAUDE.md DD-02/DD-06→Tauri+React, 3个重复rules删除(167行去重), dd06重命名
3. BMAD document-project exhaustive scan: 325文件/165617行, 生成8文档 (commit 2fcdd41)
   - docs/index.md (主入口)
   - docs/architecture.md, api-contracts-backend.md, data-models-backend.md
   - docs/component-inventory-frontend.md, integration-architecture.md
   - docs/development-guide.md, source-tree-analysis.md

## 关键发现
- Frontend: 48文件/8829行, 30组件, 12 services, Agent SDK sidecar
- Backend: 179文件/83846行, ~155端点, 15 MCP tools, 38 services
- Src-Legacy: 98文件/72942行, ~47500行死代码(api/全mock, command_handlers/Obsidian CLI, canvas_utils.py 34641行monolith)
- 活跃legacy仅: agentic_rag(19220行) + memory/temporal(1335行) + rollback(2613行)

## 下一步
- Step 4: 基于 docs/index.md + MVP 14项清单写 _decisions/mvp-plan.md (Boris Tane模式)

## 用户新想法（待调研）
1. Obsidian深度链接: Agent对话返回精确笔记片段+点击跳转回Obsidian（需验证方案成熟度）
2. Graphiti按时间过滤: 时序图谱应支持按时间过滤检索，避免看过时内容

## 工作模式（本session起生效）
- Boris Tane plan.md: Claude写方案文件→用户在文件批注→批准后编码
- 调研限时25分钟/问题
- bug fix/接线/重命名不触发DD-01/DD-04
- 改动<50行不需要独立审查
