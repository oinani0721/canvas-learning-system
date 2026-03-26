# Phase 2：Graphiti 真实接入 — 实施计划

> **给 Agent 执行者：** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐 Task 实施本计划。步骤使用 `- [ ]` 语法追踪。

**目标：** 用真正的 `graphiti-core` `add_episode()` 替换假的 Graphiti 集成（Neo4j Cypher 直写 + JSON 文件双写 + 实体桥接），通过 asyncio.Queue 后台 Worker 处理，由 Gemini LLM/Embedder 驱动。

**架构：** 基于 asyncio.Queue 的 `GraphitiEpisodeWorker` 作为 FastAPI lifespan 后台任务运行。API 处理器通过 `put_nowait`（非阻塞）将 `EpisodeTask` 对象入队。单个 Worker 循环按顺序 await `graphiti.add_episode()`（graphiti-core 为了时序一致性要求必须顺序执行）。失败的 episode 会指数退避重试，耗尽后写入死信 JSONL。`search_memories()` 从内存子字符串匹配升级为三层分级搜索：Graphiti 语义搜索 → Neo4j 全文索引 → 内存缓存。

**技术栈：** `graphiti-core>=0.28.2`、`asyncio.Queue`（Python 3.13+ `shutdown()`）、`GeminiClient` + `GeminiEmbedder`（来自 graphiti-core）、Neo4j 5.26（端口 7691）、FastAPI lifespan

**关键参考文档：**
- 设计文档：`docs/superpowers/specs/2026-03-25-path-a-pipeline-design.md`（Phase 2 章节）
- 迁移计划：`_decisions/migration-plan-graphiti-real-integration.md`
- Worker 手册：`_decisions/research-asyncio-queue-graphiti-worker.md`（877 行，经过验证的代码）
- 审查清单：`docs/superpowers/specs/2026-03-25-review-checklist.md`

---

## 文件结构

### 新建文件

| 文件 | 职责 |
|------|------|
| `backend/app/services/episode_worker.py` | GraphitiEpisodeWorker：asyncio.Queue、Worker 循环、重试、死信、监控指标、Graphiti 客户端初始化 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `backend/.env` | 添加 `GOOGLE_API_KEY` 用于 graphiti-core Gemini 集成 |
| `backend/.env.example` | 添加 `GOOGLE_API_KEY` 占位符 + 文档 |
| `docker-compose.yml` | 添加 `GOOGLE_API_KEY` 环境变量传递给后端服务 |
| `backend/app/config.py` | 添加 `GOOGLE_API_KEY`、`GRAPHITI_QUEUE_MAXSIZE`；废弃 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` |
| `backend/app/main.py` | 在 lifespan 中添加 Worker 启动/停止；移除 JSON 回退同步块 |
| `backend/app/services/memory_service.py` | 添加 `_enqueue_episode()`；替换 3 处 `record_learning_event()` fire-and-forget 调用；向 `record_knowledge_entity()` 添加 enqueue；删除 `_write_to_graphiti_json*`、`_bridge_to_claude_graphiti`；清理 import |
| `backend/app/api/v1/endpoints/monitoring.py` | 添加 `GET /monitoring/episode-worker` 端点 |
| `backend/app/services/verification_service.py` | 移除死代码方法（C5/C6）及其调用方 |

### 删除文件

| 文件 | 原因 |
|------|------|
| `backend/app/services/graphiti_bridge_service.py` | 被 episode_worker.py 真正的 Graphiti 集成替代 |

---

## 依赖关系图

```
[T1: 环境配置] ────────┐
[T2: 死代码删除] ───────┼──→ [T3: episode_worker.py] ──→ [T4: lifespan + config] ──┬──→ [T6: _enqueue 适配器]
                        │                                 [T5: 监控端点] ─────────────┘     │
                        │                                                                    ▼
                        │                                                       [T7: 替换调用（临界交换）]
                        │                                                                    │
                        │                                                                    ▼
                        │                                                       [T8: 删除旧代码]
                        │                                                                    │
                        │                                                                    ▼
                        │                                                       [T9: 交换后验证]
                        │                                                           │              │
                        │                                                           ▼              ▼
                        │                                                [T10: 假命名清理]  [T11: 分层搜索]
                        │                                                           │              │
                        │                                                           └──────┬───────┘
                        │                                                                  ▼
                        └─────────────────────────────────────────────────→ [T12: 最终验证]
```

**可并行执行：**
- T1 + T2（互不依赖，无文件重叠）
- T4 + T5（T3 完成后，不同文件）
- T10 + T11（T9 完成后，不同关注点）

---

## Task 1：环境配置

**文件：**
- 修改：`backend/.env`（在第 41 行后添加 GOOGLE_API_KEY）
- 修改：`backend/.env.example`（在第 93 行后添加 GOOGLE_API_KEY 章节）
- 修改：`docker-compose.yml`（在后端服务 environment 中添加，约第 105-113 行）

- [ ] **步骤 1：在 backend/.env 中添加 GOOGLE_API_KEY**

在 `AI_TIMEOUT=120` 行（第 41 行）之后添加：

```env
# Graphiti 知识图谱 — 真实接入（Phase 2）
# graphiti-core 使用 Google Gemini 作为 LLM + Embedder
GOOGLE_API_KEY=AIzaSyCJnS1vK0fhpuGPBv30_5yOBv1k40fVewo
```

注意：复用 `AI_API_KEY` 中已有的同一个 Gemini 密钥。

- [ ] **步骤 2：在 backend/.env.example 中添加 GOOGLE_API_KEY**

在 AI 章节之后（第 93 行之后）添加：

```env
# Graphiti 知识图谱（Phase 2）
# graphiti-core 使用 Google Gemini 进行实体提取（LLM）和向量嵌入。
# 真实 Graphiti 集成所必需（替代 JSON 双写）。
# 获取密钥：https://aistudio.google.com/apikey
GOOGLE_API_KEY=your-google-api-key-here
```

- [ ] **步骤 3：在 docker-compose.yml 后端服务中添加 GOOGLE_API_KEY 传递**

在 `backend` 服务的 `environment` 部分（第 113 行 `CORS_ORIGINS` 之后）添加：

```yaml
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

- [ ] **步骤 4：验证 requirements.txt 中的 graphiti-core 版本**

运行：`grep graphiti backend/requirements.txt`

预期：`graphiti-core>=0.28.2`（已存在于第 70 行）

- [ ] **步骤 5：提交**

```bash
git add backend/.env.example docker-compose.yml
git commit -m "feat(phase2): add GOOGLE_API_KEY for graphiti-core Gemini integration"
```

注意：不要 `git add backend/.env`（包含真实 API 密钥）。

---

## Task 2：删除死代码（C5/C6）

**文件：**
- 修改：`backend/app/services/verification_service.py`
- 修改：`backend/tests/unit/test_verification_dedup.py`
- 修改：`backend/tests/unit/test_verification_service_injection.py`

**背景：** GDA 审计发现 2 个方法调用了 `GraphitiEdgeClient` 上不存在的方法：
- `_get_question_history_from_graphiti()`（第 2340 行）调用 `.search_verification_questions()` — 不存在
- `_store_question_to_graphiti()`（第 2677 行）调用 `.add_verification_question()` — 不存在

两个方法都已有优雅降级（返回空/无操作），调用方不会崩溃。

- [ ] **步骤 1：替换第 2196 行的调用**

将调用替换为空列表赋值（该方法失败时本来就返回空）：

```python
# 修改前（第 2196 行）：
history_questions = await self._get_question_history_from_graphiti(
    concept=concept,
    canvas_name=canvas_name,
    group_id=group_id
)

# 修改后：
# Phase 2：题目历史将通过 Graphiti episode 搜索重新实现
history_questions = list()  # 优雅降级，直到 Graphiti 搜索接入
```

- [ ] **步骤 2：移除第 2264 行和第 2478 行的 fire-and-forget 调用**

两处都包裹在 `asyncio.create_task()` 中。删除两个位置的完整 `asyncio.create_task(self._store_question_to_graphiti(...))` 代码块。

- [ ] **步骤 3：删除死方法定义**

删除 `_get_question_history_from_graphiti()`（第 2340-2387 行）和 `_store_question_to_graphiti()`（第 2677-2719 行）。

- [ ] **步骤 4：更新测试**

在 `test_verification_dedup.py` 和 `test_verification_service_injection.py` 中，删除或跳过所有引用已删除方法的测试。

- [ ] **步骤 5：验证**

```bash
cd backend && python -m ruff check app/services/verification_service.py
cd backend && python -m pytest tests/unit/test_verification_dedup.py tests/unit/test_verification_service_injection.py -v --timeout=30 2>&1 | head -50
```

- [ ] **步骤 6：提交**

```bash
git add backend/app/services/verification_service.py backend/tests/unit/test_verification_dedup.py backend/tests/unit/test_verification_service_injection.py
git commit -m "fix(phase2): remove dead code calling non-existent GraphitiEdgeClient methods (C5/C6)"
```

---

## Task 3：构建 GraphitiEpisodeWorker

**文件：**
- 新建：`backend/app/services/episode_worker.py`

**背景：** 核心新文件。架构：asyncio.Queue(maxsize=100) → 单个 Worker 任务 → 顺序执行 `graphiti.add_episode()`。模式来自 graphiti 官方 MCP 服务器（`queue_service.py`）。完整调研见 `_decisions/research-asyncio-queue-graphiti-worker.md`。

- [ ] **步骤 1：验证 graphiti-core API 导入**

```bash
cd backend && python -c "from graphiti_core import Graphiti; print('Graphiti OK')"
cd backend && python -c "from graphiti_core.llm_client import LLMConfig; print('LLMConfig OK')"
```

如果 `GeminiClient` 无法导入，检查：`python -c "import graphiti_core; print(dir(graphiti_core))"`

在继续之前记录正确的导入路径。

- [ ] **步骤 2：创建 episode_worker.py**

创建 `backend/app/services/episode_worker.py`，包含完整实现。

**重要：** graphiti-core 的初始化导入可能需要根据步骤 1 的结果调整。下面的代码使用已文档化的 Graphiti 构造函数和基于环境变量的 Gemini 配置。如果步骤 1 显示不同的 API，需要更新。

完整代码在 `_decisions/research-asyncio-queue-graphiti-worker.md` 第 8 节（第 414-782 行）。复制该骨架并做以下适配：

1. `initialize_graphiti()` 方法：使用 `settings.NEO4J_URI`、`settings.NEO4J_USER`、`settings.NEO4J_PASSWORD`、`settings.GOOGLE_API_KEY`
2. 设置 `os.environ["GOOGLE_API_KEY"]` 以便 graphiti-core 内部 Gemini 客户端能获取
3. 初始化时调用 `await self._graphiti.build_indices_and_constraints()`
4. `is_ready` 属性：返回 `self._started and self._graphiti is not None`
5. 使用 Python 3.13+ `Queue.shutdown()` 实现优雅终止
6. `DeadLetterStore` 写入 `data/dead_letter_episodes.jsonl`
7. 通过 `get_episode_worker()` 和 `cleanup_episode_worker()` 实现单例模式

需要包含的类：
- `EpisodeTask` 数据类：`name`、`episode_body`、`group_id`、`source_description`、`reference_time`、重试字段
- `WorkerMetrics` 数据类：计数器 + 延迟追踪 + `to_dict()`
- `DeadLetterStore`：JSONL 追加写入 + 计数
- `GraphitiEpisodeWorker`：`initialize_graphiti()`、`start()`、`stop()`、`enqueue()`、`_run()`、`_process_episode()`、`_handle_failure()`

- [ ] **步骤 3：验证文件可编译**

```bash
cd backend && python -c "from app.services.episode_worker import GraphitiEpisodeWorker, EpisodeTask; print('Import OK')"
cd backend && python -m ruff check app/services/episode_worker.py
```

- [ ] **步骤 4：提交**

```bash
git add backend/app/services/episode_worker.py
git commit -m "feat(phase2): add GraphitiEpisodeWorker with asyncio.Queue + retry + dead-letter"
```

---

## Task 4：将 Worker 接入 FastAPI Lifespan + 配置

**文件：**
- 修改：`backend/app/config.py`（在约第 430 行添加新字段）
- 修改：`backend/app/main.py`（添加 Worker 启动/停止）

- [ ] **步骤 1：在 config.py 中添加配置字段**

找到 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 字段（约第 426 行）。在其后添加：

```python
    # Graphiti Episode Worker（Phase 2）
    GOOGLE_API_KEY: str = Field(
        default="",
        description="graphiti-core Gemini LLM/Embedder 的 Google API 密钥"
    )

    GRAPHITI_QUEUE_MAXSIZE: int = Field(
        default=100,
        description="graphiti Worker 队列满后丢弃的最大 episode 数"
    )
```

- [ ] **步骤 2：在 main.py lifespan 中添加 Worker 启动（yield 之前，约第 278 行之后）**

在 Signal Registry 块之后、`yield` 之前添加：

```python
    # Phase 2：GraphitiEpisodeWorker — 真实 Graphiti 集成
    from app.services.episode_worker import get_episode_worker, cleanup_episode_worker

    episode_worker = get_episode_worker()
    try:
        graphiti_ready = await episode_worker.initialize_graphiti(
            neo4j_uri=settings.NEO4J_URI,
            neo4j_user=settings.NEO4J_USER,
            neo4j_password=settings.NEO4J_PASSWORD,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        if graphiti_ready:
            await episode_worker.start()
            app.state.episode_worker = episode_worker
            logger.info("[Phase 2] GraphitiEpisodeWorker 已启动")
        else:
            app.state.episode_worker = episode_worker
            logger.warning("[Phase 2] GraphitiEpisodeWorker 降级模式（无 graphiti 客户端）")
    except Exception as e:
        app.state.episode_worker = None
        logger.warning(f"[Phase 2] GraphitiEpisodeWorker 初始化失败（非致命）：{e}")
```

- [ ] **步骤 3：添加 Worker 关闭（yield 之后，cleanup_memory_service 之前）**

```python
    # Phase 2：优雅停止 episode worker
    try:
        await cleanup_episode_worker()
        logger.info("[Phase 2] GraphitiEpisodeWorker 已停止")
    except Exception as e:
        logger.warning(f"[Phase 2] Episode worker 清理失败：{e}")
```

- [ ] **步骤 4：验证**

```bash
cd backend && python -m ruff check app/main.py app/config.py
cd backend && python -c "from app.config import settings; print(f'GOOGLE_API_KEY 已配置: {bool(settings.GOOGLE_API_KEY)}')"
```

- [ ] **步骤 5：提交**

```bash
git add backend/app/config.py backend/app/main.py
git commit -m "feat(phase2): wire GraphitiEpisodeWorker to FastAPI lifespan"
```

---

## Task 5：Worker 监控端点

**文件：**
- 修改：`backend/app/api/v1/endpoints/monitoring.py`

- [ ] **步骤 1：在文件末尾添加监控端点**

```python
@router.get("/monitoring/episode-worker")
async def episode_worker_health(request: Request):
    """Phase 2：GraphitiEpisodeWorker 健康状态和指标。"""
    worker = getattr(request.app.state, "episode_worker", None)
    if worker is None:
        return {"status": "unavailable", "message": "Episode worker 未初始化"}

    metrics = worker.metrics.to_dict()
    metrics["status"] = "running" if worker.is_ready else "degraded"
    return metrics
```

确保 `Request` 已从 `fastapi` 导入（文件中应该已有）。

- [ ] **步骤 2：验证**

```bash
cd backend && python -m ruff check app/api/v1/endpoints/monitoring.py
```

- [ ] **步骤 3：提交**

```bash
git add backend/app/api/v1/endpoints/monitoring.py
git commit -m "feat(phase2): add GET /monitoring/episode-worker health endpoint"
```

---

## Task 6：在 MemoryService 中添加 _enqueue_episode 适配器

**文件：**
- 修改：`backend/app/services/memory_service.py`

- [ ] **步骤 1：添加 EpisodeTask 导入**

在 `memory_service.py` 顶部（第 68 行之后）添加：

```python
from app.services.episode_worker import EpisodeTask, get_episode_worker
```

- [ ] **步骤 2：在 record_learning_event() 之前（第 506 行之前）添加 _enqueue_episode 方法**

```python
    def _enqueue_episode(
        self,
        name: str,
        episode_body: str,
        group_id: str,
        source_description: str = "canvas_learning_system",
    ) -> bool:
        """
        将学习 episode 入队等待 Graphiti 处理。

        Phase 2：替代 fire-and-forget JSON 双写和桥接调用。
        非阻塞。Worker 通过 graphiti add_episode 顺序处理。

        返回 True 表示已入队，False 表示队列满或 Worker 不可用。
        """
        worker = get_episode_worker()
        if not worker.is_ready:
            logger.debug("Episode worker 未就绪，跳过入队")
            return False

        task = EpisodeTask(
            name=name,
            episode_body=episode_body,
            group_id=group_id,
            source_description=source_description,
        )
        return worker.enqueue(task)
```

- [ ] **步骤 3：验证**

```bash
cd backend && python -m ruff check app/services/memory_service.py
```

- [ ] **步骤 4：提交**

```bash
git add backend/app/services/memory_service.py
git commit -m "feat(phase2): add _enqueue_episode adapter to MemoryService"
```

---

## Task 7：替换 Fire-and-Forget 调用（临界交换）

**文件：**
- 修改：`backend/app/services/memory_service.py`

**背景：** 将 3 处 `asyncio.create_task()` fire-and-forget 调用替换为 `_enqueue_episode()`，并向 `record_knowledge_entity()` 添加 enqueue。

- [ ] **步骤 1：替换 record_learning_event() 中第 604-629 行**

找到以下代码块：

```python
            if getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True):
                asyncio.create_task(
                    self._write_to_graphiti_json_with_retry(...)
                )
            asyncio.create_task(
                self._bridge_to_claude_graphiti(...)
            )
```

将整个代码块替换为：

```python
            # Phase 2：入队到 GraphitiEpisodeWorker 进行真正的 add_episode
            score_text = f"（得分：{score}/100）" if score is not None else ""
            self._enqueue_episode(
                name=f"learning:{concept[:80]}",
                episode_body=(
                    f"学生通过 {agent_type} agent 在画布 "
                    f"'{canvas_path}' 上学习了 '{concept}'{score_text}。节点：{node_id}。"
                ),
                group_id=group_id,
                source_description=f"canvas_learning:{inferred_subject}",
            )
```

- [ ] **步骤 2：向 record_knowledge_entity() 添加 enqueue**

在 `record_knowledge_entity()` 中，Neo4j 写入 try/except 块之后（约第 1376 行之后），logger.info 调用之前，添加：

```python
        # Phase 2：入队到 GraphitiEpisodeWorker
        self._enqueue_episode(
            name=f"{event_type}:{meta.get('title', content[:40])}",
            episode_body=content,
            group_id=resolved_group_id,
            source_description=f"canvas_learning:{event_type}",
        )
```

- [ ] **步骤 3：验证**

```bash
cd backend && python -m ruff check app/services/memory_service.py
```

- [ ] **步骤 4：提交**

```bash
git add backend/app/services/memory_service.py
git commit -m "feat(phase2): swap fire-and-forget JSON/bridge with GraphitiEpisodeWorker enqueue"
```
User："C:\Users\Heishing\Pictures\Screenshots\屏幕截图 2026-03-26 102759.png" 完全没有看到触发 record_learning_event / record_knowledge_entity；我们的hook 哪些是不是还是设置失败的？
User2：  问题 1：Gemini 速率限制（主因）

  Rate limit exceeded. Please try again later.

  管道实际上是通的！ 2 个 episode 成功入队（来自 conversation_distillation），但 Gemini 免费额度 10 RPM 太低 — graphiti-core 的 add_episode() 内部会多次调用
  Gemini（实体提取+向量嵌入+关系推理），瞬间触发速率限制。3 次重试后进入死信。

  这正是设计文档预见的风险（决策 GDR-CRITICAL：免费 10RPM=1episode/min，250RPD=18-35/day 不够）。
（那么请你deep explore 一下如何解决速率限制的问题，还是因为其他配置的问题，因为我的gemini 在当前的claude code 的 Graphiti 上是可以正常使用的）
  User3┌─────────────────┬──────────────────────┬─────────────────────┬─────────────────────┐
  │     配置项      │ Claude Code Graphiti │    我们的 Worker    │     需要修改？      │
  ├─────────────────┼──────────────────────┼─────────────────────┼─────────────────────┤
  │ LLM Model       │ gemini-2.5-flash     │ gemini-2.0-flash    │ ✅ 改为 2.5-flash   │
  ├─────────────────┼──────────────────────┼─────────────────────┼─────────────────────┤
  │ Embedder        │ gemini-embedding-001 │ GeminiEmbedder 默认 │ ✅ 对齐             │
  ├─────────────────┼──────────────────────┼─────────────────────┼─────────────────────┤
  │ SEMAPHORE_LIMIT │ 3                    │ 未设置              │ ✅ 这是速率限制根因 │
  ├─────────────────┼──────────────────────┼─────────────────────┼─────────────────────┤
  │ API Key         │ AIzaSyD5t...VBA      │ AIzaSyCJn...ewo     │ ⚠️ 不同 key         │
  ├─────────────────┼──────────────────────┼─────────────────────┼─────────────────────┤
  │ max_coroutines  │ 通过 SEMAPHORE 控制  │ None（无限制）      │ ✅ 设为 3           │
  └─────────────────┴──────────────────────┴─────────────────────┴─────────────────────┘

  根因： SEMAPHORE_LIMIT=3 + max_coroutines 未设置。graphiti-core 的 add_episode() 内部并发多个 Gemini 调用，没有并发限制就瞬间触发速率限制。
（你还要deep explore 一下限制是否会影响质量？请你查找社区成熟的方案）
---

## Task 8：删除旧桥接/JSON 代码

**文件：**
- 修改：`backend/app/services/memory_service.py`（删除方法 + 导入）
- 删除：`backend/app/services/graphiti_bridge_service.py`
- 修改：`backend/app/main.py`（移除 JSON 回退同步块）

- [ ] **步骤 1：删除 memory_service.py 中的方法**

完全移除以下 3 个方法：
1. `_write_to_graphiti_json()` — 第 305-384 行
2. `_write_to_graphiti_json_with_retry()` — 第 386-504 行
3. `_bridge_to_claude_graphiti()` — 第 637-674 行

- [ ] **步骤 2：清理 memory_service.py 中的导入**

移除以下导入块：

```python
# 移除（第 54-58 行）：
from app.clients.graphiti_client import (
    LearningMemory,
    LearningMemoryClient,
    get_learning_memory_client,
)

# 移除（第 68 行）：
from app.services.graphiti_bridge_service import get_graphiti_bridge

# 移除（第 69-73 行）：
from app.core.failure_counters import (
    DUAL_WRITE_DEAD_LETTER_PATH,
    increment_dual_write_failures,
    write_dead_letter,
)
```

同时移除以下常量（约第 80-89 行）：
- `GRAPHITI_JSON_WRITE_TIMEOUT`
- `GRAPHITI_RETRY_BACKOFF_BASE`
- `GRAPHITI_RETRY_MAX_DELAY`

- [ ] **步骤 3：删除 graphiti_bridge_service.py**

```bash
rm backend/app/services/graphiti_bridge_service.py
```

- [ ] **步骤 4：移除 main.py 中的 JSON 回退同步**

移除 lifespan 启动部分中的 Story 38.8 代码块（第 167-193 行）和双写日志块（第 156-165 行）。

- [ ] **步骤 5：验证无断裂引用**

```bash
cd backend && python -m ruff check app/services/memory_service.py app/main.py
cd backend && grep -rn "graphiti_bridge_service\|get_graphiti_bridge\|_write_to_graphiti_json\|_bridge_to_claude_graphiti\|get_learning_memory_client" app/ --include="*.py" | grep -v __pycache__ | grep -v test
```

预期：`app/` 中零匹配（测试文件除外）。

- [ ] **步骤 6：提交**

```bash
git add -u backend/app/services/ backend/app/main.py
git commit -m "refactor(phase2): delete fake bridge/JSON dual-write code, replaced by GraphitiEpisodeWorker"
```

---

## Task 9：交换后验证

**文件：** 无（仅验证）

- [ ] **步骤 1：lint 整个后端**

```bash
cd backend && python -m ruff check app/
```

预期：0 错误。

- [ ] **步骤 2：验证所有导入可解析**

```bash
cd backend && python -c "
from app.services.memory_service import MemoryService, get_memory_service
from app.services.episode_worker import GraphitiEpisodeWorker, get_episode_worker, EpisodeTask
from app.main import app
print('所有导入 OK')
"
```

- [ ] **步骤 3：验证管道连通性（DD-11）**

```bash
# episode_worker.py 被其他模块引用
cd backend && grep -rn "get_episode_worker\|EpisodeTask\|cleanup_episode_worker" app/ --include="*.py" | grep -v __pycache__ | grep -v episode_worker.py

# _enqueue_episode 被调用（不只是定义）
cd backend && grep -rn "_enqueue_episode" app/services/memory_service.py | grep -v "def _enqueue"
```

预期：`get_episode_worker` 出现在 memory_service.py + main.py。`_enqueue_episode` 在 `record_learning_event` 和 `record_knowledge_entity` 中被调用。

- [ ] **步骤 4：API 冒烟测试（如果后端运行中）**

```bash
curl -s http://localhost:8001/api/v1/health | python -m json.tool
curl -s http://localhost:8001/api/v1/metrics/episode-worker | python -m json.tool
```

---

## Task 10：假命名清理

**文件：**
- 修改：`backend/app/` 中多个文件

**背景：** GDA 审计发现 26+ 个函数名中包含 "graphiti" 但实际执行 Neo4j Cypher 或 JSON 操作。重命名误导性的函数。

- [ ] **步骤 1：审计所有 "graphiti" 函数引用**

```bash
cd backend && grep -rn "def.*graphiti" app/ --include="*.py" -l | grep -v __pycache__ | grep -v episode_worker.py | sort
```

将每个函数分类为：准确（真正使用 graphiti-core）或误导（使用 Neo4j/JSON/内存）。

- [ ] **步骤 2：重命名 review_service.py 中的误导性函数**

- `_query_weak_concepts_from_graphiti()` → `_query_weak_concepts_from_memory()`
- `_query_review_history_from_graphiti()` → `_query_review_history_from_memory()`
- `_query_review_sessions_from_graphiti()` → `_query_review_sessions_from_memory()`

对每个：重命名方法定义并更新同文件内所有调用方。

- [ ] **步骤 3：重命名其他文件中的误导性函数**

检查 `context_enrichment_service.py`、`agent_service.py` 和步骤 1 中发现的其他文件。应用相同的重命名模式。

- [ ] **步骤 4：更新文档注释**

```bash
cd backend && grep -rn "Graphiti JSON\|graphiti_json\|graphiti json" app/ --include="*.py" | grep -v __pycache__
```

更新误导性注释以反映实际行为。

- [ ] **步骤 5：废弃 ENABLE_GRAPHITI_JSON_DUAL_WRITE**

在 config.py 中将默认值改为 False 并添加废弃说明。
在 .env 中注释掉该行。

- [ ] **步骤 6：验证**

```bash
cd backend && python -m ruff check app/
```

- [ ] **步骤 7：提交**

```bash
git add -u backend/
git commit -m "refactor(phase2): rename misleading 'graphiti' functions to match actual behavior"
```

---

## Task 11：分层搜索实现

**文件：**
- 修改：`backend/app/services/memory_service.py`（重写 `search_memories()`）

**背景：** 将内存子字符串匹配替换为三层分级搜索。方法签名不变（25+ 调用方不受影响）。

- [ ] **步骤 1：添加 _search_graphiti 私有方法**

在 `search_memories()` 之前添加：

```python
    async def _search_graphiti(
        self, query: str, group_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """第 1 层：通过 graphiti-core 语义 + 时序搜索。"""
        worker = get_episode_worker()
        if not worker.is_ready or worker._graphiti is None:
            return list()  # Worker 尚未初始化

        try:
            results = await asyncio.wait_for(
                worker._graphiti.search(
                    query=query,
                    group_ids=[group_id] if group_id else None,
                    num_results=limit,
                ),
                timeout=2.0,
            )
            # ... 将结果转换为 episode 字典格式
        except Exception as e:
            logger.warning(f"Graphiti 搜索失败或超时：{e}")
            return list()
```

- [ ] **步骤 2：添加 _search_neo4j_fulltext 私有方法**

```python
    async def _search_neo4j_fulltext(
        self, query: str, group_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """第 2 层：通过 Neo4j 全文索引进行关键词匹配。"""
        # 使用 CALL db.index.fulltext.queryNodes('episode_content_index', $search_term)
        # 注意用 run_query 而非 execute_query，参数名用 search_term 避免冲突
```

- [ ] **步骤 3：重写 search_memories()**

```python
    async def search_memories(self, query, group_id=None, max_results=50, limit=None):
        """三层分级搜索学习记忆。签名不变，25+ 调用方不受影响。"""
        # 第 1 层：Graphiti 语义搜索
        # 第 2 层：Neo4j 全文索引
        # 第 3 层：内存缓存（始终可用的兜底）
        # 结果合并去重，按 episode_id 去重
```

- [ ] **步骤 4：验证**

```bash
cd backend && python -m ruff check app/services/memory_service.py
```

- [ ] **步骤 5：提交**

```bash
git add backend/app/services/memory_service.py
git commit -m "feat(phase2): upgrade search_memories to 3-tier layered search (Graphiti+Neo4j+memory)"
```

---

## Task 12：最终集成验证

**文件：** 无（验证 + 清理）

- [ ] **步骤 1：全量 lint 检查**

```bash
cd backend && python -m ruff check app/
```

- [ ] **步骤 2：验证 graphiti_bridge_service.py 已删除**

```bash
ls backend/app/services/graphiti_bridge_service.py 2>&1
```

预期："No such file or directory"

- [ ] **步骤 3：管道连通性（DD-11）**

```bash
# 每个新函数都有调用方
cd backend && grep -rn "get_episode_worker\|EpisodeTask\|cleanup_episode_worker" app/ --include="*.py" | grep -v __pycache__ | grep -v episode_worker.py | grep -v test
cd backend && grep -rn "_enqueue_episode" app/services/memory_service.py | grep -v "def _enqueue"
cd backend && grep -rn "_search_graphiti\|_search_neo4j_fulltext" app/services/memory_service.py | grep -v "def _search"
```

- [ ] **步骤 4：集成测试（如果后端运行中）**

```bash
# 健康检查
curl -s http://localhost:8001/api/v1/health | python -m json.tool

# Worker 状态
curl -s http://localhost:8001/api/v1/metrics/episode-worker | python -m json.tool

# 写入事件 → 入队
curl -s -X POST http://localhost:8001/api/v1/memory/episodes \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","canvas_path":"CS188/test.canvas","node_id":"n1","concept":"BFS","agent_type":"feynman","score":90}' | python -m json.tool

# 搜索 → 分层搜索
curl -s "http://localhost:8001/api/v1/memory/search?query=BFS&group_id=cs188" | python -m json.tool

# 处理后的 Worker 指标
sleep 5 && curl -s http://localhost:8001/api/v1/metrics/episode-worker | python -m json.tool
```

- [ ] **步骤 5：审查清单交叉验证**

来自 `docs/superpowers/specs/2026-03-25-review-checklist.md`：

| 检查项 | 状态 |
|--------|------|
| MCP 6 工具迁移 | `record_learning_memory` → `record_knowledge_entity` → 通过 T7 入队。`search_memories` → 通过 T11 分层搜索。其他不变。 |
| Phase 2→3 依赖 | 已标注：3.5（格式）需要 Worker，3.6（补救）需要 PostToolUse。均已就绪。 |
| GDA-3 group_id 范围 | `_enqueue_episode` 使用 `build_group_id()` 结果。Worker 传递给 `add_episode()`。 |
| 死代码 ruff 清理 | T9 步骤 1 已验证。 |
| 假命名已清理 | T10 已验证。 |
| 管道连通性 | T12 步骤 3 已验证。 |

User：  ┌───────────────────────────────────────────────────────────┬────────────────┬─────────────────────────┐
  │                         完成标准                          │    验证方式    │          状态           │
  ├───────────────────────────────────────────────────────────┼────────────────┼─────────────────────────┤
  │ graphiti-core >= 0.28.2 导入成功                          │ Agent 自动     │ ✅ 已验证               │
  ├───────────────────────────────────────────────────────────┼────────────────┼─────────────────────────┤
  │ POST /memory/episodes → Worker enqueue → add_episode 成功 │ curl API 测试  │ ✅ episodes_processed=1 │
  ├───────────────────────────────────────────────────────────┼────────────────┼─────────────────────────┤
  │ search_memories 返回之前写入的 episode                    │ debug 端点实测 │ ✅ 三层共 7 条结果      │
  ├───────────────────────────────────────────────────────────┼────────────────┼─────────────────────────┤
  │ 假命名 grep → 名实一致                                    │ Agent 自动     │ ✅ 已清理               │
  ├───────────────────────────────────────────────────────────┼────────────────┼─────────────────────────┤
  │ Worker 监控端点返回 queue_depth=0                         │ curl 测试      │ ✅                      │
  ├───────────────────────────────────────────────────────────┼────────────────┼─────────────────────────┤
  │ 无 mock/死代码                                            │ Agent 自动     │ ✅                      │
  └───────────────────────────────────────────────────────────┴────────────────┴─────────────────────────┘

  唯一需要你上手测试但尚未通过的：

  ┌───────────────────────┬───────────────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────┐
  │         测试          │                                       操作                                        │                      当前状态                      │
  ├───────────────────────┼───────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────┤
  │ MCP 6                 │ 在产品中触发 record_learning_memory / search_memories / record_error /            │ ⚠️ 未测——前端对话不自动触发 enqueue（Phase 2.6     │
  │ 工具迁移后功能正常    │ archive_conversation / search_notes / generate_question                           │ PostToolUse Hook 缺失）                            │
  └───────────────────────┴───────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────┘
（这里你说Phase2 的测试都通过了，我保持怀疑态度）
---

## Phase 2 完成标准（来自设计文档）

- [ ] graphiti-core >= 0.28.2 安装并导入成功
- [ ] POST /memory/episodes → Worker 入队 → graphiti add_episode 成功
- [ ] search_memories("BFS") 返回之前写入的 episode
- [ ] 假命名：grep "graphiti" → 所有引用名实一致
- [ ] Worker 监控端点返回 queue_depth=0（处理完成后）
- [ ] 6 个 MCP 工具迁移后功能正常
- [ ] 修改的文件中无 mock 或死代码

---

## 风险缓解

| 风险 | 缓解措施 |
|------|---------|
| Gemini 速率限制（10 RPM） | Worker 指数退避 + 死信存储 |
| graphiti-core 初始化失败 | 降级模式：Worker 启动但 episode 进入死信 |
| Neo4j 全文索引不存在 | `_search_neo4j_fulltext` 捕获异常优雅降级 |
| 突发流量队列满 | `put_nowait` 丢弃 + 记录警告 + 指标追踪 |
| 需要回滚 | 每个 Task 有独立 commit；可按 Task `git revert` |
