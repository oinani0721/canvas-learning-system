---
doc_type: story
story_id: "5.8"
aliases: ["5.8"]
epic_id: "EPIC-5"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 4
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 5.8: 异步非阻塞知识图谱写入

## Story

As a 系统,
I want 异步非阻塞地将学习事件写入知识图谱,
so that 写入操作不影响学习者的交互体验。

## Acceptance Criteria

1. **Given** 学习事件发生（答题、评分、概念提取等）
   **When** 系统需要写入 Graphiti
   **Then** 写入操作通过异步队列执行，不阻塞 UI 和 API 请求（AR27）
   **And** Graphiti 读在 LLM 调用前、写在操作后（NFR-REL-5）
   **And** EventBus 级联自动触发 Graphiti 写入（NFR-REL-6）
   **And** 写入失败自动重试 3 次（NFR-DEG-6）
   **And** 写入原子性（NFR-INT-2）

2. **Given** Graphiti 写入进入队列
   **When** FastAPI 请求已返回响应
   **Then** 队列中的写入任务继续后台执行，不随请求生命周期结束而丢失
   **And** 服务重启前未完成的任务在重启后恢复执行（持久化队列）

3. **Given** Graphiti 写入失败（网络错误、Neo4j 不可用等）
   **When** 重试机制触发
   **Then** 按指数退避重试：第 1 次重试等待 2s，第 2 次 4s，第 3 次 8s
   **And** 3 次重试全部失败后，任务写入死信队列（DLQ）
   **And** DLQ 任务数量超过 100 时发出 structlog warning 告警

4. **Given** EventBus 事件触发
   **When** 以下事件发布：`quiz.graded`, `concept.extracted`, `error.recorded`, `vote.cast`
   **Then** EventBus 自动将对应的 Graphiti 写入任务加入队列
   **And** 事件到写入的映射关系在 `event_graphiti_handlers.py` 中集中配置

## Tasks / Subtasks

- [ ] Task 1: AsyncQueue 实现 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/services/async_write_queue.py` 实现基于 `asyncio.Queue` 的 `GraphitiWriteQueue` 类
  - [ ] 1.2 `GraphitiWriteQueue` 单例（FastAPI lifespan 管理），保证全局唯一队列
  - [ ] 1.3 实现 `enqueue(task: GraphitiWriteTask) -> None`（非阻塞，立即返回）
  - [ ] 1.4 实现后台 worker coroutine `_process_queue()`：循环从队列取任务并执行
  - [ ] 1.5 FastAPI lifespan 中启动 worker：`asyncio.create_task(_process_queue())`

- [ ] Task 2: 持久化队列（服务重启恢复）(AC: #2)
  - [ ] 2.1 使用 SQLite 作为轻量持久化层（不引入 Redis，避免新系统依赖）
  - [ ] 2.2 队列任务入队时同步写入 SQLite `graphiti_write_queue` 表（task_id, payload JSON, status, created_at, attempts）
  - [ ] 2.3 服务启动时读取 SQLite 中 `status=pending` 的任务重新入队（恢复未完成任务）
  - [ ] 2.4 任务完成后 SQLite 记录更新为 `status=completed`（保留 24h 后清理）

- [ ] Task 3: 重试机制 + 死信队列 (AC: #3)
  - [ ] 3.1 在 `GraphitiWriteTask` 模型中包含：`attempts: int = 0, max_attempts: int = 3, last_error: Optional[str]`
  - [ ] 3.2 写入失败时捕获异常，`task.attempts += 1`，按指数退避重新入队（`asyncio.sleep(2**attempts)`）
  - [ ] 3.3 `attempts >= max_attempts` 时写入死信队列：SQLite `graphiti_dlq` 表
  - [ ] 3.4 DLQ 任务数 > 100 时触发 structlog warning（`logger.warning("graphiti_dlq_overflow", dlq_size=N)`）

- [ ] Task 4: EventBus 集成 (AC: #4)
  - [ ] 4.1 在 `backend/app/events/event_bus.py` 确认或创建简单 EventBus（基于 `asyncio` pub/sub，不引入外部消息队列）
  - [ ] 4.2 在 `backend/app/events/event_graphiti_handlers.py` 定义事件→写入任务映射：
    - `quiz.graded` → `write_quiz_episode(result)`
    - `concept.extracted` → `write_concept_episode(concept)`
    - `error.recorded` → `write_error_episode(record)`（Story 5.4）
    - `vote.cast` → `write_score_vote(vote)`（Story 5.6）
  - [ ] 4.3 handlers 在 FastAPI lifespan 中注册订阅
  - [ ] 4.4 每个 handler 调用 `GraphitiWriteQueue.enqueue(task)` 而不是直接写 Graphiti

- [ ] Task 5: NFR-REL-5 读/写顺序保证 (AC: #1)
  - [ ] 5.1 在 `backend/app/services/graphiti_service.py` 添加文档注释标注：读操作（search_memory_facts）必须在 LLM 调用前执行
  - [ ] 5.2 在需要 Graphiti 读+LLM 的服务（如 scoring_service.py）中添加明确顺序：先 `await graphiti_service.read(...)` → 再 `await llm_service.invoke(...)`
  - [ ] 5.3 写操作统一通过 EventBus 异步触发，不在 LLM 调用链中同步写

- [ ] Task 6: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 `tests/unit/test_async_write_queue.py`：验证入队、worker 处理、不阻塞调用方
  - [ ] 6.2 `tests/unit/test_graphiti_retry.py`：验证指数退避重试和 DLQ 触发（mock Graphiti 失败）
  - [ ] 6.3 `tests/unit/test_event_graphiti_handlers.py`：验证 4 个 EventBus 事件正确触发写入任务
  - [ ] 6.4 `tests/integration/test_async_write_persistence.py`：验证服务模拟重启后 SQLite 任务恢复执行

## Dev Notes

- **SQLite 持久化**：轻量无依赖，项目已有 SQLite 使用先例。对比 Redis：不引入新系统依赖（符合项目约束）；不需要高并发写吞吐（学习事件 QPS < 10）
- **asyncio.Queue vs 线程安全 Queue**：FastAPI 是 asyncio 框架，asyncio.Queue 是正确选择；混用 threading 会破坏事件循环
- **指数退避依据**：AWS SQS 最佳实践（2021）：`delay = min(cap, base * 2^attempt)` 防止惊群效应
- **写入原子性 (NFR-INT-2)**：Graphiti 本身不保证原子性，通过 SQLite 任务状态机实现补偿逻辑（pending → processing → completed/failed）
- **EventBus 简单实现**：项目体量不需要 Kafka/RabbitMQ，`asyncio` 原生 pub/sub + SQLite 已满足需求。参考：FastAPI background tasks 模式
- **NFR-REL-6 EventBus 级联**：目的是解耦业务逻辑与 Graphiti 写入——业务层只 publish 事件，不直接调用 graphiti_service

### Project Structure Notes

- AsyncQueue：`backend/app/services/async_write_queue.py`（新建）
- EventBus：`backend/app/events/event_bus.py`（新建或确认已存在）
- 事件处理：`backend/app/events/event_graphiti_handlers.py`（新建）
- SQLite 持久化：`backend/app/db/write_queue_db.py`（新建，使用 `aiosqlite`）
- Pydantic 模型：`backend/app/schemas/write_task.py`（新建 GraphitiWriteTask）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.8] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR27] — 异步写入需求
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-REL-5] — Graphiti 读写顺序
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-REL-6] — EventBus 级联触发
- [Source: _bmad-output/planning-artifacts/prd.md#NFR-DEG-6] — 写入失败重试 3 次
- [Story: 5.4] — error.recorded 事件来源
- [Story: 5.6] — vote.cast 事件来源

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证学习操作即时响应（不卡顿）** (AC: #1)
   - 完成一道考察题并提交
   - 系统应该在 1 秒内显示评分结果，不出现加载转圈超过 2 秒
   - 如果提交后系统卡住超过 2 秒，记录 Story 5.8

2. **验证后台保存不影响继续学习** (AC: #1)
   - 快速连续完成 5 道题（不等待每次的"保存确认"）
   - 所有 5 道题的评分结果都应该能正常查看
   - 之后打开对应概念笔记，5 次考察都应该反映在 mastery_score 中
   - 如果有记录丢失，记录 Story 5.8 和丢失的题号

3. **验证知识图谱写入失败时系统继续工作** (AC: #3)
   - 临时关闭 Neo4j（停止 Docker neo4j 服务）
   - 完成几次考察，系统应继续正常工作（评分结果显示，frontmatter 更新）
   - 重新启动 Neo4j 后，查看之前的考察记录是否最终同步到知识图谱
   - 如果关闭 Neo4j 后系统崩溃或无法继续，记录 Story 5.8

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-5.8.1 | pytest | `.venv/bin/pytest tests/unit/test_async_write_queue.py -x -q` | 0 failed |
| CP-5.8.2 | pytest | `.venv/bin/pytest tests/unit/test_graphiti_retry.py -x -q` | 0 failed |
| CP-5.8.3 | pytest | `.venv/bin/pytest tests/unit/test_event_graphiti_handlers.py -x -q` | 0 failed |
| CP-5.8.4 | pytest | `.venv/bin/pytest tests/integration/test_async_write_persistence.py -x -q` | 0 failed |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-5]]
- PRD: [[PRD14]]
