# Canvas Learning System - 整体架构文档

> 生成时间: 2026-03-24 | 扫描模式: exhaustive

## 1. 项目概览

Canvas Learning System 是一个 AI 辅助学习的桌面应用，核心功能包括：

- **知识画布**：用户在画布上组织知识节点和边（类似 Obsidian Canvas），系统自动追踪每个概念的掌握度
- **AI 对话教学**：基于 Feynman 方法的 AI Tutor，通过对话、提问、纠错帮助用户深度理解概念
- **间隔重复复习**：FSRS + BKT 融合算法驱动的智能复习调度
- **自动考试**：根据画布内容自动生成考题，AutoSCORE 评分，4 类错误分类 + 差异化补救策略
- **学习记忆图谱**：Graphiti 时序知识图谱记录学习历程、misconception、tips

## 2. 多部件结构

系统由三个主要部分组成：

```
┌────────────────────────────────────────────────────────┐
│  Frontend: Tauri + React Desktop App                   │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐            │
│  │ ReactFlow│ │ ChatPanel │ │ ExamCanvas │  ...30 组件 │
│  │ 画布引擎 │ │ AI 对话   │ │ 考试画布   │            │
│  └─────┬────┘ └─────┬─────┘ └─────┬──────┘            │
│        │            │             │                    │
│  ┌─────┴────────────┴─────────────┴──────┐             │
│  │  4 Zustand Stores + Dexie (IndexedDB) │             │
│  └──────────────────┬────────────────────┘             │
│                     │                                  │
│  ┌──────────────────┴───────────────────┐              │
│  │  Sidecar (Node.js Agent SDK, 468行)  │              │
│  └──────────────────┬───────────────────┘              │
└─────────────────────┼──────────────────────────────────┘
                      │ REST API + MCP JSON-RPC
┌─────────────────────┼──────────────────────────────────┐
│  Backend: FastAPI Python (179 文件, 83,846 行)          │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐            │
│  │ REST API │ │ MCP Server│ │ WebSocket  │            │
│  │ ~155端点 │ │ 15 Tools  │ │ 2 端点     │            │
│  └─────┬────┘ └─────┬─────┘ └─────┬──────┘            │
│        └────────────┬──────────────┘                   │
│  ┌──────────────────┴───────────────────┐              │
│  │  38 Service Classes (业务逻辑层)     │              │
│  └──────────────────┬───────────────────┘              │
│        ┌────────────┼───────────────┐                  │
│  ┌─────┴────┐ ┌─────┴─────┐ ┌──────┴─────┐           │
│  │  Neo4j   │ │  LanceDB  │ │  Ollama    │           │
│  │  知识图谱│ │  向量检索 │ │  本地 LLM  │           │
│  └──────────┘ └───────────┘ └────────────┘            │
└────────────────────────────────────────────────────────┘
                      │ PYTHONPATH 引用
┌─────────────────────┼──────────────────────────────────┐
│  Src-Legacy: 部分活跃的 Python 模块                    │
│  ┌───────────────┐ ┌──────────┐ ┌──────────┐          │
│  │ agentic_rag/  │ │ memory/  │ │ rollback/│          │
│  │ RAG 管道      │ │ FSRS     │ │ 回滚引擎 │          │
│  │ 19,220行      │ │ 1,335行  │ │ 2,613行  │          │
│  └───────────────┘ └──────────┘ └──────────┘          │
└────────────────────────────────────────────────────────┘
```

## 3. 架构模式

### Frontend 架构

- **Component-based SPA**：React 组件驱动的单页应用
- **Zustand 状态管理**：4 个 store (canvas, chat, exam, mastery) 管理全局状态
- **Dexie (IndexedDB) 持久化**：节点/边/消息离线存储在 IndexedDB
- **Outbox 同步模式**：数据变更写入 Dexie sync_outbox 表，SyncEngine 批量同步到后端
- **Agent SDK Sidecar**：Node.js 进程通过 Claude Agent SDK 连接后端 MCP，实现 AI 对话

### Backend 架构

- **Service-oriented FastAPI**：38 个 service 类封装业务逻辑，通过依赖注入组合
- **Agentic RAG Pipeline**：6 路并行检索 -> fusion -> rerank -> quality check -> compress -> faithfulness
- **多数据库**：Neo4j (知识图谱) + LanceDB (向量检索) + SQLite (会话历史)
- **Event-driven**：EventBus 事件总线连接 FSRS、Graphiti、RAG 子系统

### 通信架构

| 路径 | 协议 | 说明 |
|------|------|------|
| Frontend -> Backend | REST API | `http://localhost:8001/api/v1/*` (Dexie Outbox -> sync/batch) |
| Sidecar -> Backend | MCP JSON-RPC | `/mcp` 端点，15 个工具 |
| Backend -> Neo4j | Bolt | `bolt://localhost:7691`，AsyncGraphDatabase，连接池 50 |
| Backend -> LanceDB | 本地文件 | `data/lancedb/`，bge-m3 embeddings (1024d) |
| Backend -> Ollama | HTTP | `http://localhost:11434`，Qwen3 8B + bge-m3 |
| Backend -> Cloud AI | HTTP | LiteLLM 网关 -> Gemini / OpenAI / Anthropic |
| Frontend <-> Backend | WebSocket | 2 端点：mastery 实时推送 + intelligent-parallel 进度 |

## 4. 技术栈总结

详细技术栈清单见 [technology-stack.md](technology-stack.md)。核心技术：

- **前端**：Tauri 2 + React 19 + TypeScript 5 + ReactFlow + Zustand + Dexie + TailwindCSS v4 (Catppuccin Mocha)
- **后端**：FastAPI + Pydantic v2 + LangGraph + FSRS + fastapi-mcp
- **数据库**：Neo4j 5.26 + LanceDB + SQLite (aiosqlite)
- **AI**：LiteLLM (多 provider 网关) + Ollama (Qwen3 8B / bge-m3) + Gemini / Claude / OpenAI
- **基础设施**：Docker Compose + Lefthook + Ruff + Pyright

## 5. 关键集成点

### Neo4j 知识图谱

- **连接**：`bolt://localhost:7691` (Docker 映射 7687->7691 避免冲突)
- **客户端**：`backend/app/clients/neo4j_client.py` (AsyncGraphDatabase)
- **节点类型**：Canvas, Node, Concept, User, Episode, LearningNode
- **关系类型**：CONTAINS_NODE, CONNECTS_TO, ASSOCIATED_WITH, LEARNED, SCORED, HAS_CONCEPT 等
- **Graphiti 实体**：LearningTip, Misconception (通过 HAS_TIP / HAS_MISCONCEPTION 关系)

### LanceDB 向量检索

- **存储**：本地文件 `data/lancedb/`
- **集合**：`canvas_nodes` (配置项 `LANCEDB_INDEX_TABLE_NAME`)
- **Embedding**：bge-m3 (1024 维, 中英双语) 通过 Ollama 本地推理
- **用途**：Canvas 节点语义检索、Vault 笔记检索

### Ollama 本地 LLM

- **连接**：`http://localhost:11434`
- **模型**：Qwen3 8B (推理, RTX 4060 GPU) + bge-m3 (embedding)
- **Docker 配置**：GPU passthrough, OLLAMA_NUM_PARALLEL=1, OLLAMA_MAX_QUEUE=8

### MCP (Model Context Protocol)

- **端点**：`/mcp` (FastAPI-MCP ASGI 集成)
- **工具数**：15 个 (mastery 3 + exam 4 + memory 3 + conversation 2 + error 1 + hint/skip 2)
- **pipeline_token 机制**：generate_question -> score_answer -> update_fsrs/update_bkt 的链式验证

## 6. Agentic RAG 管道

核心检索管道（位于 `src/agentic_rag/pipeline/`）：

```
用户查询
    │
    ├─[1] LanceDB Semantic Search (bge-m3 向量)
    ├─[2] Neo4j Graph Search (知识图谱邻居)
    ├─[3] Graphiti Temporal Search (时序记忆)
    ├─[4] Multimodal Search (图片/PDF)
    ├─[5] Textbook Search (教科书关联)
    └─[6] Cross-Canvas Search (跨画布关联)
          │
          ▼
    Reciprocal Rank Fusion (RRF)
          │
          ▼
    Reranker (bge-reranker / Gemini)
          │
          ▼
    Quality Check + Compression
          │
          ▼
    Faithfulness Score
          │
          ▼
    最终结果
```

## 7. 状态管理

### 前端 4 个 Zustand Stores

| Store | 文件 | 主要状态 |
|-------|------|----------|
| canvas-store | 9,593 行 | 画布列表、当前画布、视图路由、节点/边 CRUD |
| chat-store | 47,247 行 | 对话消息、Agent 引擎状态、Observer、技能选择 |
| exam-store | 7,043 行 | 考试会话、题目队列、评分结果 |
| mastery-store | 5,726 行 | 节点掌握度、复习调度、批量查询 |

### 持久化

- **Dexie (IndexedDB)**：boards, nodes, edges, messages, sync_outbox 5 张表
- **Outbox Pattern**：所有 CUD 操作先写 Dexie，再由 SyncEngine 异步同步到后端

## 8. 安全

| 层 | 机制 | 说明 |
|----|------|------|
| Layer 0 | Backend Algorithm Authority | 后端算法权威 — Agent 通过 MCP 调用后端工具 |
| Layer 1 | PromptInjectionGuard | Prompt 注入检测 |
| Layer 2 | EncodingValidation | 编码验证 (防 Unicode 攻击) |
| Layer 3 | CORS | 跨域资源共享控制 |
| Layer 4 | pipeline_token | MCP 工具链 token 验证 (强制步骤顺序) |
| Layer 5 | Rate Limiting | 请求频率限制 (MAX_CONCURRENT_REQUESTS) |
