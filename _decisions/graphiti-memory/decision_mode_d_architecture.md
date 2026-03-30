---
name: Mode D 架构方向确认 + 4 项子决策
description: 用户确认 MCP Server 暴露方案，确定 Tool-UI Bridge 对话框、LiteLLM+Ollama 模型配置、6 层防御架构（2026-03-15，待验证）
type: project
---

Session：PRD Review | 背景：用户确认 Mode D 方向后深入调研 4 个实施细节

## [Decision] Mode D MCP Server 暴露 — 用户已确认
- FastAPI 后端不变，新增 MCP Server 接口
- Claude Code/OpenCode 通过 MCP 协议接入后端算法
- Agent 是"对话路由器"，后端是"算法执行器"

## [Decision] Tool-UI Bridge 对话框架构
- 自建 Svelte 对话 UI + Claude Agent SDK TypeScript 驱动
- 不用 Claude Code 的终端界面（无法支持 Tips/Tag/拖拽等富交互）
- Agent 调用自定义工具 → 工具同时更新数据库 + Svelte Store → UI 响应式更新
- 社区验证：Claudian 插件已用此架构

## [Decision] 模型配置：LiteLLM SDK + Ollama bge-m3
- LiteLLM SDK（非 Proxy）作为后端统一 LLM 调用层
- Ollama 容器运行 bge-m3 嵌入模型（独立进程，CPU 可运行）
- 双层 API Key 分离：外层 Agent 用用户 Key，内层后端用后端 Key
- Dashboard：系统状态 + 模型配置（简单/高级）+ 使用统计

## [Decision] 6 层 Agent 行为防御
- Layer 0: 后端算法权威（不可绕过）
- Layer 1: 密码学令牌管道（不可绕过）
- Layer 2: CLAUDE.md/AGENTS.md（建议性 ~80%）
- Layer 3: Claude Code Hooks（确定性，仅 Claude Code）
- Layer 4: 后端审计守护（不可绕过，异步）
- Layer 5: 结构化输出（引导性 ~90%）

## [Decision] 上下文压缩不影响学习记忆
- 学习记忆存在后端（SQLite/Graphiti/LanceDB），不依赖 Agent session
- Claude Code 压缩的只是临时工作记忆
- Agent 每次通过 MCP 工具从后端检索上下文

**Why:** 用户需要强力 Agent 兜底但不能破坏 13 算法管道，且对话框需要富交互
**How to apply:** 需更新 PRD 增加 MCP Server 层、Tool-UI Bridge 架构、Ollama 服务、6 层防御
**决策状态：[Decision-Review] PENDING — 待独立验证 session 制定验收标准**
