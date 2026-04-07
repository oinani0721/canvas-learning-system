---
name: A5 Graphiti 记忆提取机制确认 — 事件驱动 + 官方 SDK + Gemini 2.5 Flash
description: user2 在 FR-KG-04 的 A5 deep explore：Canvas 记忆提取既不是 Hook 也无本地兜底，是 FastAPI background_task → episode_worker.enqueue() → graphiti-core add_episode() 的事件驱动流（2026-04-07 三方对账）
type: project
---

## [Decision] A5 — Graphiti 记忆提取机制三方对账

Session: 2026-04-07 | 来源: user2 在 `docs/project-status/fr-exploration/A5.md` 的 deep explore 任务

### user2 原始问题（FR-KG-04.md:401）

> "这里的 Graphiti 的记忆提取方式是想在 claude code 中的一样用 hook 来判定检索...还是你自己调用了不成熟的工具完成的...还是说你这里的 llm 提取，实际上是一个使用本地模型进行兜底提取的一个方式？"

### 三方对账结论（代码 / 文档 / Git 全部交叉验证）

| A5 子问题 | 答案 | 一句话依据 |
|---|---|---|
| 是 Hook 吗？ | ❌ NO | `backend/app/services/episode_worker.py` 全文无 pre/post tool hook 调用，唯一 hook 命中是无关的 `WebhookNotificationChannel`（通知系统） |
| 是官方 SDK 吗？ | ✅ YES | `requirements.txt:25` 声明 `graphiti-core>=0.28.2`，`episode_worker.py:32` 直接 `from graphiti_core import Graphiti` |
| 是本地模型兜底吗？ | ❌ NO | `episode_worker.py:222` 默认 `llm_model="gemini-2.5-flash"`（云端），失败路径只丢死信队列，无任何 fallback 切换到本地模型的代码 |

### 触发链路（事件驱动）

```
Agent 回答完成 (e.g. POST /api/v1/agents/decompose/basic)
      ↓
FastAPI BackgroundTasks.add_task(_record_learning_event)   ← agents.py:831-838
      ↓
memory_service.record_learning_event()                      ← agents.py:369-401
      ↓
memory_service._enqueue_episode()                           ← memory_service.py:310-344
      ↓
episode_worker.enqueue(EpisodeTask)                         ← episode_worker.py:336-362
      ↓
asyncio queue → episode_worker._run() loop                  ← episode_worker.py:376-406
      ↓
episode_worker._process_episode(task)                       ← episode_worker.py:408-425
      ↓
self._graphiti.add_episode(**kwargs)                        ← graphiti-core 官方 SDK
      ↓
Neo4j 持久化（带 entity_types/edge_types Pydantic schema）
```

### 类型化提取

`backend/app/graphiti/entity_types.py` 定义 4 个 Pydantic 实体 + 1 个边类型，并通过 `CANVAS_ENTITY_TYPES` / `CANVAS_EDGE_TYPES` 注册表传给 `add_episode()`：

| 实体 | 行号 | 用途 |
|---|---|---|
| `LearningConcept` | 198-213 | 学习概念（名/描述/学科/难度/前置条件） |
| `Misconception` | 134-158 | Agent 检测的学生错误（4 类分类 + 补救） |
| `LearningTip` | 106-127 | 用户标注的学习提示 |
| `MasteryRecord` | 215-228 | 掌握度追踪（等级/最后复习/错误计数） |
| `PrerequisiteRelation`（边） | 230-241 | 前置关系强度 |

注册表：`entity_types.py:247-256`。

### Gemini 2.5 Flash 配置

`episode_worker.py:246-265` 的客户端初始化：

- `LLMConfig(api_key=GOOGLE_API_KEY, model="gemini-2.5-flash")`
- `GeminiClient(config=llm_config)` —— LLM 提取
- `GeminiEmbedder(embedding_model="gemini-embedding-001")` —— 向量化
- `GeminiRerankerClient(config=llm_config)` —— 重排序
- `Graphiti(uri=NEO4J_URI, ..., llm_client, embedder, cross_encoder, max_coroutines=3)`

应用启动初始化：`backend/app/main.py:264-276`。

### 测试覆盖

| 测试 | 验证点 |
|---|---|
| `test_s02_entity_types.py::test_forwards_entity_and_edge_types` | entity_types/edge_types 实际传给 add_episode |
| `test_s02_entity_types.py::TestCanvasTypeDicts` | 4 个实体 + 1 个边类型注册完整 |
| `test_story_38_2_episode_recovery.py` | Neo4j 持久化 + 启动时 episode 恢复 |
| `test_failure_observability.py` | 死信队列 + 失败可观测性 |

### 文档对账

A5 三个结论在 4 份文档中表述一致（**无矛盾**）：

1. `docs/project-status/fr-exploration/A5.md` —— 任务原文
2. `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04-user2-annotations.md:117-138` —— 调研结论
3. `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04.md:418-449` —— `[[A5]]` 锚点 + 流程图
4. `docs/project-status/fr-exploration/FR-KG-04/deep-research-user-annotations.md:93-102` —— 注入/调出时机

### 已知风险（实施侧，不影响结论）

- **Gemini API 速率限制**：Gemini 2.5 Flash 云端 API 高峰可能限速（参考 `project_s28_phase2_plan.md:50`）
- **失败路径**：API 不可用时，episode 进 `data/dead_letter_episodes.jsonl` 死信队列，**不重试**也**不切本地模型**
- **没有本地 fallback** 是设计选择，不是缺失 —— 用户明确要求云端模型保证质量

### ⚠️ 修正：Sidecar Fallback Path（2026-04-07 ChatGPT 对抗审计补充）

**起因**：user2 此前提到"我看到了 hook 调用"。我之前的 A5 三方对账只看了**后端事件驱动主路径**（`agents.py → memory_service → episode_worker → add_episode`），结论是 ❌ 不是 Hook。三个并行 Explore agent 后续验证 ChatGPT 对抗审计时，发现还有**第二条由前端 sidecar 触发的回退路径**，这条路径的入口确实是 hook。我之前的对账**没有矛盾，但片面**——主路径不是 hook，sidecar 这条 fallback 路径是。修正如下：

**Path B（sidecar PostToolUse hook → 后端 Distiller → Graphiti）**：

1. **触发器**：Agent SDK 内部的 `PostToolUse` hook（不是 Claude Code 的 OS-level hook）
   - 实现：`frontend/sidecar/sidecar.js:163-194` 在 `queryOpts.options.hooks.PostToolUse[0].hooks[0]` 注册 async 回调
   - 命中条件：`BEA_EXTRACTION_TOOLS = {'score_answer', 'record_error'}`（sidecar.js:77-80）
   - 当 Agent 调用这两个 MCP 工具中的任一时，回调 fire-and-forget POST 到 backend

2. **第二个触发器**：sidecar 的 SDK result loop（不是 hook，是 stream 监听）
   - 实现：`frontend/sidecar/sidecar.js:328-360` 在 `msg.type === 'result' && msg.subtype === 'success' && !learningRecorded` 时触发
   - 兜底意图：当一整轮对话**没有任何 memory tool** 被调用时，把整段对话发给后端做 Ollama-based fallback 提取

3. **后端入口**：`POST /api/v1/memory/extract-conversation`
   - Handler：`backend/app/api/v1/endpoints/memory.py:435+`
   - 调用 `ConversationDistiller(messages, node_id)` → `result.tips` + `result.errors` → `memory_service.record_knowledge_entity()` → 同样进 episode_worker → `add_episode()`

4. **和主路径的关系**：
   - **主路径（事件驱动）**：Agent 在后端通过 background_task 直接 enqueue → 这条无 hook
   - **回退路径 A（sidecar PostToolUse hook）**：Agent 在 sidecar 内调 MCP 工具 → hook 命中 → 前端 fetch → 后端 Distiller → enqueue
   - **回退路径 B（sidecar Stop fallback）**：整轮对话没用 memory 工具 → 前端 fetch → 后端 Distiller → enqueue
   - 三条路径**最终都汇聚到同一个** `episode_worker._process_episode()` → `graphiti.add_episode()`，所以原结论"是 graphiti-core 官方 SDK"和"是 Gemini 2.5 Flash 云端"**仍然成立**

5. **修正后的"是 Hook 吗？"答案**：
   - **后端主路径**：❌ NO（事件驱动 background_task）
   - **sidecar PostToolUse 路径**：✅ YES（Agent SDK 内部的 PostToolUse hook）
   - **sidecar Stop fallback 路径**：❌ NO（result message 监听，不是 hook）

### 修正后的代码锚点（完整）

| 路径 | 触发器 | 文件:行 |
|---|---|---|
| 后端主路径入口 | FastAPI BackgroundTasks | `backend/app/api/v1/endpoints/agents.py:831-838` |
| sidecar PostToolUse hook | Agent SDK hooks API | `frontend/sidecar/sidecar.js:163-194` |
| sidecar Stop fallback | SDK result loop | `frontend/sidecar/sidecar.js:328-360` |
| sidecar 触发的 backend 入口 | extract-conversation handler | `backend/app/api/v1/endpoints/memory.py:435+` |
| 三路径汇聚点 | episode_worker enqueue | `backend/app/services/episode_worker.py:336-362` |

### 修正影响：审计闭环

ChatGPT 对抗审计还在 sidecar fallback 这条路径上发现了 5 类安全/正确性 bug，已在 audit-2026-04-07 修复批次中处理（详见 `_decisions/decision-log.md` 对应条目）：

- **P0-1**：sidecar `canUseTool` 默认 deny + 高风险工具走 `permission_request` 闭环（`sidecar.js:140-189`）
- **P0-2**：`/extract-conversation` 加 `X-Canvas-Observer-Token` opt-in 鉴权 + canvas_path 参数化解析 group_id（`memory.py:402-490`）
- **P1-1**：`DeadLetterStore` 默认不落盘完整 episode_body，仅 sha256 + redact secrets
- **P1-2**：sync_outbox `retryCount` 字段 + dexie schema v7 + full jitter exponential backoff

**Why:** A5 是 user2 对"项目是否在用 Claude Code 同款 hook 偷懒、或用本地模型糊弄"的核心 challenge。三方对账证明项目主路径用的是最规范的 graphiti-core 官方路径；ChatGPT 对抗审计补充发现 sidecar fallback 路径才是 user2 看到的"hook 调用"，但这条路径**最终汇聚到同一 SDK**，所以"是官方 SDK + Gemini 云端"的核心结论依然成立。
**How to apply:** 后续 Graphiti 提取机制的设计/改动，都应基于"3 条路径并存（主+2 fallback），最终汇聚到 episode_worker → graphiti.add_episode"这个事实出发。任何讨论"是不是 hook"必须区分主路径（不是）和 sidecar fallback（是 PostToolUse hook + Stop fallback 监听）。禁止重新走"本地模型兜底"路线（除非用户显式要求）。

**决策状态: [Decision-Review] CONFIRMED — 三方对账（代码侧 Agent + 文档侧 Agent + Git 历史 Agent）2026-04-07 通过 + ChatGPT 对抗审计 2026-04-07 补充修正 sidecar fallback path，记录为本项目 Graphiti 提取机制的事实基线。**
