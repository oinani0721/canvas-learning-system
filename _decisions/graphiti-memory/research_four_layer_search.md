---
name: 四层搜索协作架构调研
description: Claude Code Grep + Obsidian CLI + RAG管道 + Graphiti 四层搜索互补关系分析（2026-03-15，待用户确认）
type: project
---

Session：PRD Review | 背景：用户问 Claude Code 的搜索能力如何与 Session A 讨论的索引管道配合

## 调研结论：三种搜索是强互补、零冲突

### 四层搜索定位
- **RAG 管道**（Session A 成果）：语义搜索，理解含义，跨语言匹配 → 概念理解类查询 ~35%
- **Obsidian CLI**：结构化搜索，tag/property/path → 位置回忆/结构化查询 ~35%
- **Graphiti**：时序+关系搜索，学习轨迹/错误历史 → 个性化查询 ~15%
- **Claude Code Grep**：精确关键词搜索，降级/补充 → Obsidian CLI 不可用时的备选 ~15%

### Session A 成果全部保留
- A1-A5 的 RAG 管道通过 MCP 工具暴露给 Agent
- LangGraph question_router 扩展：新增 Obsidian CLI 为第 4 个检索节点
- Claude Code Grep 是降级层，不是替代层

### 新增内容
- Obsidian CLI search 注册为 LangGraph 检索节点
- Agent 意图分析决定路由到哪层搜索
- 复合查询并行多层 → RRF 融合

**Why:** 用户担心 Claude Code 的搜索能力与已有 RAG 管道冲突
**How to apply:** PRD 需增加 Obsidian CLI 搜索通道 + 四层搜索路由架构
**决策状态：待用户确认**
