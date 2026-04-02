# M001: 核心管道端到端打通

**Gathered:** 2026-04-02
**Status:** Ready for planning

## Project Description

Canvas Learning System 是一个 AI 辅助学习桌面应用（Tauri 2 + React + FastAPI + Neo4j + LanceDB），brownfield 项目约 430K 行代码。后端算法（BKT/FSRS/AutoSCORE/5信号融合）全部已实现，但端到端管道未跑通。本 milestone 聚焦让核心学习体验链路真正工作。

## Why This Milestone

代码存在但管道断裂。用户无法：
1. 和节点 AI 对话时让 Agent 调用后端工具（MCP 不触发）
2. 搜索到自己的笔记（RAG 端点不工作）
3. 让系统记住自己的学习历史（Graphiti 利用率仅 25%，双写残留）
4. 完成一次检验白板考察（全链路未验证）

这些是"系统越来越懂你"的基石——没有这些，上层所有功能都是空中楼阁。

## User-Visible Outcome

### When this milestone is complete, the user can:

- 点击白板节点 → 打开 AI 对话 → Agent 能调用 MCP 工具（search_memories、generate_question、score_answer 等）
- 对话中 Agent 能检索并引用用户的笔记片段（RAG 返回真实结果）
- 对话中犯的错误、标注的 Tips、Edge 理由被写入 Graphiti 且可被精准检索
- 从 Dashboard 选择白板 → 生成检验白板 → AI 出题 → 用户答题 → 隐形评分 → 精通度更新
- 以上所有在 Mac M5 Max 上流畅运行

### Entry point / environment

- Entry point: `npm run tauri dev`（前端）+ `docker compose up -d`（后端）
- Environment: macOS 本地开发（M5 Max 128GB）
- Live dependencies: Docker（Neo4j 7691 + FastAPI 8001）+ 原生 Ollama（11434，Metal GPU）+ Claude API（via Agent SDK sidecar）+ Gemini API（后端 Graphiti embedding）

## Completion Class

- Contract complete means: MCP 工具调用成功率 100%、RAG 返回真实笔记片段、Graphiti search 返回用户记忆、检验白板出题→评分→精通度更新全链路通过
- Integration complete means: 前端 sidecar → MCP → 后端 → Neo4j/Graphiti/LanceDB 全链路数据流通
- Operational complete means: `docker compose up -d` + `npm run tauri dev` 一键启动，Mac 上稳定运行

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- 用户在 Mac 上打开应用，创建白板，点击节点对话，Agent 成功调用 search_memories 返回之前写入的 Tips
- 用户触发检验白板考察，AI 基于 FSRS+BKT+KG 选择薄弱节点出题，AutoSCORE 评分后精通度变化可观察
- RAG 检索用户指定文件夹中的中文笔记，返回精确片段
- 上述流程无需手动干预中间环节（端到端自动化）

## Risks and Unknowns

- Sidecar MCP 不触发的根因未知（可能是连接配置、后端 MCP 端点注册、或 SDK 版本兼容性）— 需要诊断
- RAG 端点不工作的根因未知（可能是 Ollama embedding 模型未加载、LanceDB 索引为空、或 agentic_rag 配置断裂）— 需要诊断
- Graphiti 高级搜索（search_）从未被调用过 — 接入可能有 API 兼容性问题
- Gemini API 额度（免费 10RPM/250RPD vs 付费 Key vs CLI Proxy vs 本地模型）— 三个方案都可行但需要选定

## Existing Codebase / Prior Art

- `frontend/sidecar/sidecar.js` (491行) — Agent SDK sidecar，MCP_TOOLS 白名单已配置
- `frontend/src/stores/chat-store.ts` (1125行) — 对话状态管理，learning context 注入已有
- `backend/app/mcp/server.py` — 15 个 MCP 工具注册（query_mastery/generate_question/score_answer/search_memories 等）
- `backend/app/services/memory_service.py` (1768行) — 3 层搜索 + episode 写入 + 批量处理
- `backend/app/services/episode_worker.py` (~440行) — GraphitiEpisodeWorker 真实 SDK 集成
- `src/agentic_rag/` (19K行) — 完整 Agentic RAG 管道（state_graph + agent_graph + reranking + compression）
- `backend/app/services/question_generator.py` (911行) — 5 层 Prompt + ACP + 三角选择
- `backend/app/services/autoscore.py` (469行) — AutoSCORE 4 维 SOLO 评分 + 3x 采样
- `backend/app/services/mastery_engine.py` (458行) — BKT + FSRS + 5 信号融合
- `backend/app/graphiti/entity_types.py` (180行) — 学习实体 Pydantic 模型

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001 — Sidecar MCP 工具触发修复（M001 核心阻塞项）
- R008~R013, R060~R065, R072, R089, R091 — Graphiti 记忆系统全量接入
- R014~R018, R020, R022 — 检索系统修复和激活
- R023~R031, R070, R086, R087 — 检验白板考察全链路 + 精通度
- R041~R043, R074, R080~R084 — 代码质量 + 平台 + 安全基础

## Scope

### In Scope

- Sidecar MCP 工具调用修复（诊断+修复）
- Graphiti 全量 API 接入（自定义类型、高级搜索、社区检测、批量摄入、时间线检索）
- G-FAKE 清理 + LearningMemoryClient JSON 双写消除
- RAG 端点激活（数据流入 + 中文搜索验证 + Reranker 中文适配）
- 检验白板考察全链路端到端验证
- 前端 1730 TS 错误修复 + 垃圾文件清理 + 已废弃代码清理
- Mac M5 Max 平台验证
- 数据零丢失 + LLM 断连降级 + Neo4j 异常降级 + 错误不静默
- 双层 Key 分离

### Out of Scope / Non-Goals

- Windows 平台验证（M002+）
- Dashboard 完整版（M002）
- 深色主题全局应用（M002）
- Edge 对话双重策略（M002）
- 对话拉出节点（M002）
- /命令技能系统完整版（M002）
- 学习档案面板完整版（M002）
- 安装引导向导（M002）
- Beta-Bayesian 融合（M003+）
- 多学科隔离（M003+）

## Technical Constraints

- Mac M5 Max + 128GB 为主要平台
- Ollama 原生运行（Metal GPU），不走 Docker
- Neo4j port 7691（Docker 映射），区别于开发记忆 7689
- Rust 1.94.1 已安装（aarch64-apple-darwin）
- Node.js v25.8.2（较新版本）
- Agent SDK 0.2.79
- Gemini API 用于 Graphiti embedding（付费 Key / CLI Proxy / 本地模型三选一）

## Integration Points

- Claude API — via Agent SDK sidecar（用户 Claude 订阅额度）
- Gemini API — 后端 Graphiti embedding + Reranker（后端配置的 Key）
- Neo4j 7691 — Docker 容器，知识图谱 + 学习记忆
- LanceDB — 本地文件 data/lancedb/，向量检索
- Ollama 11434 — 原生 macOS Metal GPU，bge-m3 embedding + Qwen3.5 35B 推理

## Open Questions

- Sidecar MCP 不触发的具体根因（需要启动项目诊断）
- RAG 端点不工作的具体根因（需要启动后端诊断）
- Gemini API 额度方案最终选定（付费 Key vs CLI Proxy vs 本地模型）
- Neo4j 7691 中的实际数据内容（学习数据 vs 开发记忆数据）
