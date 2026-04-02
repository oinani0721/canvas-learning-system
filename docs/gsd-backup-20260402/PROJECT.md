# Canvas Learning System

## What This Is

AI 辅助学习桌面应用（Tauri 2 + React + FastAPI + Neo4j + LanceDB），将可视化知识画布与 AI 对话式学习深度融合。用户在白板上构建知识节点和关系，每个节点拥有独立的 AI 对话窗口，系统通过 Graphiti 时序知识图谱追踪学习轨迹，精准识别薄弱环节并递归考察检验。

核心差异化：没有任何现有产品同时整合可视化知识图谱 + AI 节点对话 + 精通度追踪 + 间隔重复 + 递归考察检验 + 元认知校准。竞品最多覆盖 4/9 组件。

## Core Value

**"系统越来越懂你"** — Agent 精准记住用户的 Tips、Edge 理由、犯过的错误，并在考察和对话中精准利用这些记忆。这是核心价值锚点——如果只能保留一个能力，这个必须工作。

## Current State

Brownfield 项目，~430K 行代码，MVP 14 项约 50% 完成。代码大部分已写但端到端管道未跑通。

**已完成：**
- Phase 3 Pipeline Repair（6 Epic 全部完成）
- 后端 59 个 Service + 15 MCP 工具 + 155 API 端点框架到位
- 前端 30 个 React 组件 + 4 Zustand Store + Dexie 持久化
- Sidecar 流式对话可用
- BKT/FSRS/5 信号融合/AutoSCORE 4 维评分算法全部已实现
- Agentic RAG 19K 行管道（src/agentic_rag/）框架完整
- Graphiti EpisodeWorker 真实 SDK 集成（Phase 2-3 完成）

**未跑通：**
- Sidecar MCP 工具调用不触发
- RAG 端点级不工作（数据流未激活）
- 检验白板考察全链路未端到端验证
- Graphiti 利用率仅 25%（高级搜索/自定义类型/社区检测/时序过滤全未用）
- 前端 1730 TS 错误 + 浅色主题未切换
- 大量垃圾文件（Windows temp + backend 乱码）

## Architecture / Key Patterns

**三层架构：**
- 前端：Tauri 2 + React 19 + ReactFlow 12 + Zustand 5 + Dexie (IndexedDB) + TailwindCSS v4
- 对话引擎：Node.js Sidecar (@anthropic-ai/claude-agent-sdk 0.2.79) via NDJSON stdin/stdout
- 后端：Docker 容器 (FastAPI + Neo4j 5.26 port 7691 + LanceDB + Ollama bge-m3/Qwen3 via Metal GPU)

**关键模式：**
- Outbox 同步：前端 Dexie sync_outbox → SyncEngine 批量同步后端
- MCP 工具链：pipeline_token HMAC-SHA256 强制步骤顺序（generate_question→score_answer→update_fsrs）
- 3 层记忆搜索：Graphiti 语义 → Neo4j fulltext → 内存子串
- 5 信号融合：BKT(0.30) + FSRS_R(0.25) + ExamScore(0.25) + CalibrationBias(0.10) + SelfConfidence(0.10)
- EventBus 3 层优先级：Tier1 同步 / Tier2 异步重试 / Tier3 fire-and-forget

**平台：** Mac 为主（M5 Max + 128GB），Windows 支持延后。Ollama 在 Mac 上跑原生（Metal GPU），不走 Docker。

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract (93 requirements), requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: 核心管道端到端打通 — Sidecar MCP 修复 + Graphiti 全量接入 + RAG 检索激活 + 检验白板考察链路
- [ ] M002: 功能完善与体验打磨 — Dashboard + 学习档案 + Edge 对话 + 深色主题 + 技能系统 + 对话继承
- [ ] M003: 高级功能与优化 — Beta-Bayesian 融合 + 多学科隔离 + 自动备份 + LKT 评估
