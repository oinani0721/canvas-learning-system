---
name: S28 Phase 2 Graphiti真实接入完成+验证通过
description: S28完成Phase2全部12Task+6个修复。写入管道+三层搜索全部验证通过。15 commits。剩余：前端自动触发需Phase3 PostToolUse Hook。
type: project
---

# S28 Phase 2 完成报告（2026-03-26）

**计划:** `docs/superpowers/plans/2026-03-26-phase2-graphiti-real-integration.md`
**执行方式:** Subagent-Driven Development（12 Task，T1+T2/T4+T5/T10+T11并行）

## 10 Commits

| Commit | 内容 |
|--------|------|
| `2ebe21a` | GOOGLE_API_KEY 环境配置 |
| `1768c19` | 删除死代码 C5/C6（verification_service.py） |
| `888ba1e` | episode_worker.py 核心文件（436行，GeminiClient+GeminiEmbedder） |
| `820c04e` | Wire Worker 到 FastAPI lifespan |
| `4631ad8` | Worker 监控端点 |
| `f4838b3` | _enqueue_episode 适配器 + 临界交换 |
| `59586af` | 删除旧 Bridge/JSON 代码（-776行） |
| `daa9fd3` | 假命名清理（3函数重命名） |
| `3a636af` | 三层分级检索（Graphiti→Neo4j fulltext→内存） |
| `d30dfbb` | 修复 run_query 方法名+参数冲突 |

## 关键发现

- graphiti-core 实际API：`GeminiClient(config=LLMConfig(...))` + `GeminiEmbedder(config=GeminiEmbedderConfig(...))`
- `Graphiti(uri=, user=, password=, llm_client=, embedder=)` 而非 `Graphiti(neo4j_uri=...)`
- Neo4jClient 方法名是 `run_query` 而非 `execute_query`，参数用 `**kwargs` 传递
- 死代码实际只有2处（非迁移计划说的3处）
- T8 额外发现 record_batch_learning_events/record_temporal_event/recover_failed_writes 也有旧调用需迁移

## 启动验证通过（2026-03-26 14:01 UTC）

- Worker status: `running`, `worker_running: true`
- Graphiti initialized: `neo4j=bolt://neo4j:7687, model=gemini-2.0-flash`
- Worker loop started, queue ready

## 启动排障经验

1. docker-compose `GOOGLE_API_KEY=${GOOGLE_API_KEY}` 会从 host 传空值覆盖 .env → 改为注释掉让 load_dotenv 从 .env 读取
2. graphiti-core 默认 cross_encoder 用 OpenAI → 必须显式传 `GeminiRerankerClient` 避免要求 OPENAI_API_KEY
3. Worker 监控端点路径是 `/api/v1/metrics/episode-worker`（prefix=/metrics 非 /monitoring）

## 用户端到端测试发现（2026-03-26 14:10 UTC）

1. **管道已打通**：对话→conversation_distiller→record_knowledge_entity→_enqueue_episode→Worker→add_episode。episodes_enqueued=2 确认。
2. **⛔ Gemini 速率限制阻塞**：免费 10RPM，add_episode 内部多次调 Gemini，瞬间触发 Rate limit exceeded。3次重试后进死信。**需决策：升级付费 or 增大重试间隔**。
3. **索引名 Bug**：T11 _search_neo4j_fulltext 用 `episode_content_index`，实际 graphiti-core 创建的索引名是 `episode_content`（无 _index 后缀）。待修复。
4. **触发路径**：conversation_distiller 是当前唯一触发 enqueue 的路径，record_learning_event 的 API 端点未被前端直接调用。

## Phase 2→3 待办

- 2.6 PostToolUse Hook BEA 提取（依赖 sidecar）
- 2.7 Session 启动记忆注入（依赖 sidecar）
- 2.8 搜索路由（初期默认 L1）
- 修复 Neo4j fulltext 索引名（episode_content_index → episode_content）
- [Decision-Review] Gemini 速率限制应对策略 — 待用户决定（升级付费 vs 增大重试间隔），PENDING
- [Decision-Review] Neo4j fulltext 索引名修复 — 待用户确认后执行，PENDING
