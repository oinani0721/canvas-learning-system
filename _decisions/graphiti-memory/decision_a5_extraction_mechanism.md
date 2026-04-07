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

**Why:** A5 是 user2 对"项目是否在用 Claude Code 同款 hook 偷懒、或用本地模型糊弄"的核心 challenge。三方对账证明项目用的是最规范的 graphiti-core 官方路径，结论可信度高。
**How to apply:** 任何后续涉及 Graphiti 提取机制的设计/改动，都应基于"事件驱动 + 官方 SDK + Gemini 云端"这个事实出发，禁止重新走 hook 或本地兜底路线（除非用户显式要求）。

**决策状态: [Decision-Review] CONFIRMED — 三方对账（代码侧 Agent + 文档侧 Agent + Git 历史 Agent）2026-04-07 通过，记录为本项目 Graphiti 提取机制的事实基线。**
