# 集成架构文档

> 生成时间: 2026-03-24 | 扫描模式: exhaustive

## 概览

Canvas Learning System 采用多部件架构，各部件通过 REST API、MCP JSON-RPC、WebSocket、Bolt 协议等方式通信。

```
┌───────────────┐     REST API      ┌──────────────────────┐
│   Frontend    │ ───────────────── │                      │
│  (Tauri+React)│     /api/v1/*     │                      │
│               │                   │                      │
│  ┌──────────┐ │  MCP JSON-RPC     │   Backend (FastAPI)  │
│  │ Sidecar  │ │ ───────────────── │                      │
│  │ Agent SDK│ │     /mcp          │                      │
│  └──────────┘ │                   │                      │
│               │    WebSocket      │                      │
│               │ ←──────────────── │                      │
│               │  /ws, /ws/ip/*    │                      │
└───────────────┘                   └──────────┬───────────┘
                                               │
                      ┌────────────────────────┼────────────────────────┐
                      │                        │                        │
                ┌─────┴─────┐           ┌──────┴──────┐          ┌─────┴─────┐
                │   Neo4j   │           │   LanceDB   │          │  Ollama   │
                │  知识图谱  │           │  向量检索   │          │ 本地 LLM  │
                │ bolt:7691 │           │  本地文件   │          │ :11434    │
                └───────────┘           └─────────────┘          └───────────┘
                                                                       │
                                                               ┌───────┴───────┐
                                                               │  Cloud AI     │
                                                               │  (LiteLLM)    │
                                                               │ Gemini/OpenAI │
                                                               │ /Anthropic    │
                                                               └───────────────┘
```

---

## 1. Frontend -> Backend: REST API

### 连接信息

| 项目 | 值 |
|------|-----|
| 协议 | HTTP/HTTPS |
| 地址 | `http://localhost:8001` |
| 前缀 | `/api/v1` |
| 端点数 | ~155 |
| 客户端 | `frontend/src/services/api-client.ts` |

### 数据同步机制: Dexie Outbox Pattern

```
用户操作 (增/删/改)
    │
    ├─[1] 写入 Dexie (IndexedDB) — 立即持久化
    └─[2] 写入 sync_outbox 表 — 记录待同步操作
              │
              ▼
    SyncEngine (定时/手动触发)
              │
              ▼
    POST /api/v1/sync/batch — 批量同步到后端
              │
              ▼
    Backend -> Neo4j + LanceDB — 写入知识图谱和向量库
```

**关键特性**：
- 离线优先：数据先写入本地 IndexedDB，无网络也能操作
- 批量同步：SyncEngine 聚合多次变更，一次性发送
- 幂等操作：sync_outbox 中的每条记录有唯一 ID，防止重复处理

### CORS 配置

允许的源（通过 `CORS_ORIGINS` 环境变量配置）：
- `http://localhost:3000` / `http://127.0.0.1:3000`
- `http://localhost:5173` / `http://127.0.0.1:5173`
- `http://tauri.localhost`
- `app://obsidian.md`

---

## 2. Sidecar -> Backend: MCP JSON-RPC

### 连接信息

| 项目 | 值 |
|------|-----|
| 协议 | MCP (JSON-RPC 2.0) |
| 端点 | `/mcp` |
| 库 | fastapi-mcp |
| 工具数 | 15 |
| Sidecar 文件 | `frontend/sidecar/sidecar.js` (468 行) |

### 通信流程

```
React ChatPanel
    │
    ├─ useChatStore.sendMessage()
    │
    ▼
Tauri Shell (spawn sidecar process)
    │
    ▼
sidecar.js (Claude Agent SDK)
    │
    ├─ 创建/维护 Agent 会话
    ├─ 流式传输 Agent 响应
    └─ 调用 MCP 工具
         │
         ▼
    Backend /mcp (FastAPI-MCP)
         │
         ├─ /mcp/tools/query_mastery
         ├─ /mcp/tools/generate_question
         ├─ /mcp/tools/score_answer
         ├─ /mcp/tools/search_memories
         └─ ... (共 15 个工具)
```

### pipeline_token 链式验证

MCP 工具通过 pipeline_token 强制执行步骤顺序：

```
generate_question ──returns token──> score_answer ──returns token──> update_fsrs/update_bkt
```

token 由 `backend/app/mcp/pipeline_token.py` 管理，确保：
- `score_answer` 只能在 `generate_question` 之后调用
- `update_fsrs` / `update_bkt` 只能在 `score_answer` 之后调用
- 防止 Agent 跳过评分步骤直接修改掌握度

---

## 3. Backend -> Neo4j

### 连接信息

| 项目 | 值 |
|------|-----|
| 协议 | Bolt |
| 地址 (Docker 内) | `bolt://neo4j:7687` |
| 地址 (宿主机) | `bolt://localhost:7691` |
| 版本 | Neo4j 5.26-community |
| 客户端 | `backend/app/clients/neo4j_client.py` |
| 驱动 | AsyncGraphDatabase (neo4j Python driver) |
| 连接池 | 50 connections |
| APOC 插件 | 已启用 |

### 数据写入路径

```
1. Canvas 操作:
   POST /api/v1/sync/batch -> SyncService -> Neo4jClient.upsert_canvas_node()

2. 掌握度更新:
   EventBus UI_MASTERY_PUSH -> MasteryEngine -> Neo4jClient.update_mastery()

3. 学习记忆:
   MCP record_learning_memory -> MemoryService -> Neo4jClient.create_episode()

4. 关联发现:
   POST /api/v1/associations/auto-discover -> CrossCanvasService -> Neo4jClient
```

### JSON 双写降级

当 Neo4j 不可用时，启用 JSON 文件降级写入：
- 控制变量：`ENABLE_GRAPHITI_JSON_DUAL_WRITE` (默认 true)
- 降级文件存储在 `data/` 目录
- 启动时通过 `FallbackSyncService` 自动恢复

---

## 4. Backend -> LanceDB

### 连接信息

| 项目 | 值 |
|------|-----|
| 存储 | 本地文件系统 |
| 路径 | `data/lancedb/` |
| Docker Volume | `canvas-lancedb` (named volume) |
| 主要集合 | `canvas_nodes` |
| Embedding | bge-m3 (1024 维, 通过 Ollama) |
| 客户端 | `backend/app/services/lancedb_index_service.py` |

### 索引流程

```
1. 手动索引:
   POST /api/v1/canvas-meta/index -> LanceDBIndexService.index_node()

2. 批量索引:
   POST /api/v1/canvas-meta/index/batch -> LanceDBIndexService.batch_index()

3. Vault 全量索引:
   POST /api/v1/canvas-meta/index/vault -> LanceDBIndexService.index_vault()

4. 启动恢复:
   app.main.lifespan -> LanceDBIndexService.recover_pending()
```

### Embedding 调用链

```
LanceDBIndexService.index_node()
    │
    ▼
OllamaEmbedder.embed(text)
    │
    ▼
HTTP POST http://localhost:11434/api/embeddings
    body: { model: "bge-m3", prompt: text }
    │
    ▼
返回 1024 维 float 向量
```

---

## 5. Backend -> Ollama

### 连接信息

| 项目 | 值 |
|------|-----|
| 协议 | HTTP |
| 地址 (Docker 内) | `http://ollama:11434` |
| 地址 (宿主机) | `http://localhost:11434` |
| GPU | RTX 4060 (NVIDIA passthrough) |
| 并行请求 | 1 (OLLAMA_NUM_PARALLEL=1, 8GB VRAM 限制) |
| 最大队列 | 8 (OLLAMA_MAX_QUEUE=8) |

### 已部署模型

| 模型 | 类型 | 用途 |
|------|------|------|
| bge-m3 | Embedding | 中英双语 1024d 向量，LanceDB 索引+检索 |
| qwen3:8b | LLM | 本地推理 (备用, RTX 4060 约 37s/请求) |

### 调用路径

```
1. Embedding:
   LanceDBIndexService / RAG Pipeline -> Ollama /api/embeddings (bge-m3)

2. LLM 推理 (备用):
   AgentService -> LiteLLM -> Ollama /api/chat (qwen3:8b)
```

---

## 6. Backend -> Cloud AI

### 连接信息

| 项目 | 值 |
|------|-----|
| 网关 | LiteLLM (统一 LLM 接口) |
| 主要 Provider | Google Gemini (gemini-2.0-flash-exp) |
| 备选 Provider | OpenAI (gpt-4o), Anthropic (Claude 3.5 Sonnet) |
| 客户端 | `backend/app/clients/gemini_client.py`, `claude_client.py` |
| Provider Factory | `backend/app/clients/provider_factory.py` |

### Provider 选择逻辑

```
环境变量 AI_PROVIDER
    │
    ├── "google"    -> GeminiClient (gemini-2.0-flash-exp)
    ├── "openai"    -> OpenAIProvider (gpt-4o)
    ├── "anthropic" -> AnthropicProvider (claude-3-5-sonnet)
    └── "custom"    -> OpenAI-compatible (自定义 base URL)
```

### 降级策略

```
Primary Provider (配置的 AI_PROVIDER)
    │ 失败
    ▼
Engine Fallback Service
    │
    ├── 尝试其他已配置的 API Key
    └── 最终降级到 Ollama 本地推理
```

---

## 7. 实时通信: WebSocket

### 端点 1: Mastery 实时推送

| 项目 | 值 |
|------|-----|
| 路径 | `WS /ws` |
| 方向 | Server -> Client |
| 心跳 | 30s ping |
| 文件 | `endpoints/mastery_ws.py` |

**消息格式**:
```json
{
  "type": "mastery_update",
  "node_id": "abc-123",
  "effective_proficiency": 0.75,
  "has_interaction": true,
  "has_exam_record": true,
  "fsrs_next_review": "2026-03-20T00:00:00Z"
}
```

**触发路径**: EventBus `UI_MASTERY_PUSH` -> MasteryConnectionManager -> 广播到所有连接

### 端点 2: Intelligent Parallel 进度

| 项目 | 值 |
|------|-----|
| 路径 | `WS /ws/intelligent-parallel/{session_id}` |
| 方向 | Server -> Client |
| 心跳 | 30s ping |
| 超时 | 10 分钟无活动自动断开 |
| 文件 | `endpoints/websocket.py` |

**特性**:
- 连接前验证 session_id 存在性
- 实时推送 Agent 处理进度
- Session 完成后自动关闭连接
