---
story_id: "5.8"
epic_id: "5"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["5.5"]
blocks: ["8.6"]
trace:
  - "FR-MEM-05"
  - "FR-MEM-06"
---

# Story 5.8: 异步写入 + Hot/Warm/Cold 归档

Status: ready-for-dev

## Story
As a 系统,
I want 异步非阻塞地将学习事件写入知识图谱，并按 Hot-Warm-Cold 时间分层归档对话消息,
So that 写入不影响用户交互体验（< 10s/episode），且历史数据按时效性分层存储节省资源。

## Acceptance Criteria

1. **Given** 学习事件产生（评分/错误/对话归档）**When** 系统写入 Graphiti 知识图谱 **Then** 使用 `asyncio.create_task` 异步非阻塞执行 **And** 不阻塞当前的用户对话或考察流程 **And** 写入完成前 MCP 工具立即返回 `{"status": "accepted", "write_mode": "async"}`

2. **Given** 异步写入执行中 **When** 写入时间 **Then** 单个 episode 写入 < 10s（NFR-PERF）**And** 超过 10s 时自动取消并记录超时审计日志

3. **Given** 异步写入失败 **When** 系统检测到失败 **Then** 自动重试最多 3 次（指数退避：1s, 2s, 4s）**And** 3 次全部失败后记录到 `FAILED_WRITES_FILE` 审计日志 **And** 通过 WebSocket 发送通知给用户"学习记录写入失败，数据已本地缓存"

4. **Given** 对话消息存储在 SQLite 中 **When** 消息年龄 0-30 天 **Then** 归档层级为 Hot：完整消息存储 **And** 搜索时返回全文内容 **And** 上下文注入使用完整消息

5. **Given** 对话消息存储在 SQLite 中 **When** 消息年龄 30-180 天 **Then** 触发 Hot → Warm 归档：LLM 提取摘要 + 关键错误 + Tips **And** 原文标记 `archived: true`（保留但不默认返回）**And** 搜索时返回摘要 **And** Graphiti 三通道写入（Agent 自报告 + 对话蒸馏 + 考察提取）

6. **Given** 对话消息存储在 SQLite 中 **When** 消息年龄 > 180 天 **Then** 触发 Warm → Cold 归档：仅保留 Graphiti 提取物 **And** SQLite 原文可选删除（配置控制）**And** 搜索时仅返回 Graphiti 提取的关键事实

7. **Given** Hot/Warm/Cold 归档流程 **When** 双触发条件满足（时间触发 OR 容量触发 50K tokens）**Then** 执行归档操作 **And** 容量触发优先于时间触发（50K tokens 即使不到 30 天也提前归档）

8. **Given** `record_learning_memory` 或 `archive_conversation` MCP 工具被调用 **When** 执行异步写入 **Then** 使用 `EpisodeWorker`（episode_worker.py）的后台任务队列 **And** 通过 `EpisodeTask` 封装写入任务 **And** 写入完成后发布 EventBus 事件通知下游

## Tasks / Subtasks

- [ ] Task 1: 实现异步非阻塞写入框架 (AC: #1, #2)
  - [ ] 验证 `record_learning_memory` MCP 工具已使用 fire-and-forget 模式（memory_service.py Story 36.9）
  - [ ] 验证 `EpisodeWorker`（episode_worker.py）后台任务队列
  - [ ] 添加 10s 超时保护：`asyncio.wait_for(write_task, timeout=10.0)`
  - [ ] 超时时取消任务并记录审计日志
  - [ ] 单元测试：异步写入不阻塞调用方、超时取消正确

- [ ] Task 2: 实现 3 次重试 + 失败审计 + 通知 (AC: #3)
  - [ ] 实现 `async_write_with_retry(task, max_retries=3)` 函数
  - [ ] 指数退避：1s, 2s, 4s
  - [ ] 全部失败后写入 `FAILED_WRITES_FILE`（`backend/app/core/failed_writes_constants.py`）
  - [ ] 通过 WebSocket 发送失败通知给前端
  - [ ] 单元测试：模拟 3 次失败 → 审计日志 + 通知

- [ ] Task 3: 实现 Hot → Warm 归档 (AC: #4, #5, #7)
  - [ ] 创建 `ConversationArchiver` 类（或扩展现有 conversation_archive.py）
  - [ ] Hot（0-30d）：完整消息，全文搜索
  - [ ] Warm（30-180d）：LLM 提取摘要 + 错误 + Tips
  - [ ] 双触发条件：时间（30 天）OR 容量（50K tokens）
  - [ ] Graphiti 三通道写入：Agent 自报告 / 对话蒸馏 / 考察提取
  - [ ] 原文标记 `archived: true` 保留
  - [ ] 单元测试：归档触发条件、摘要提取、Graphiti 写入

- [ ] Task 4: 实现 Warm → Cold 归档 (AC: #6)
  - [ ] Cold（> 180d）：仅保留 Graphiti 提取物
  - [ ] SQLite 原文删除配置：`ARCHIVE_DELETE_COLD_ORIGINALS` 环境变量（默认 false）
  - [ ] 搜索时仅返回 Graphiti 关键事实
  - [ ] 单元测试：Cold 归档后搜索返回正确数据源

- [ ] Task 5: MCP 工具集成 + 端到端测试 (AC: #8)
  - [ ] 验证 `record_learning_memory` 在 `backend/app/mcp/server.py` 已注册（line 364-379）
  - [ ] 验证 `archive_conversation` 在 `backend/app/mcp/server.py` 已注册（line 395-405）
  - [ ] 集成测试：record_learning_memory → EpisodeWorker → Graphiti 写入
  - [ ] 集成测试：archive_conversation → Hot/Warm/Cold 归档流
  - [ ] 性能测试：单 episode 写入 < 10s

## Dev Notes

### Architecture
- 异步写入是 FR-MEM-05 的核心要求，现有 Story 36.9 已实现 fire-and-forget 双写模式
- Hot-Warm-Cold 是 FR-MEM-06 + 架构文档 §8 的数据生命周期策略
- 归档流：对话进行中 → SQLite Hot → 双触发（30d OR 50K tokens）→ LLM 提取 → Warm → 6 个月后 → Cold
- `EpisodeWorker`（episode_worker.py）是现有的后台任务队列，基于 asyncio Queue
- Graphiti 三通道写入在架构文档中定义：Agent 自报告 + 对话蒸馏 + 考察提取
- 容量触发（50K tokens）是防止长对话占用过多 Hot 存储的保护机制

### File Paths
- 记忆服务：`backend/app/services/memory_service.py` (MemoryService)
- Episode Worker：`backend/app/services/episode_worker.py` (EpisodeWorker, EpisodeTask)
- 对话归档：`backend/app/services/conversation_archive.py`（待创建/扩展）
- 对话蒸馏：`backend/app/services/conversation_distiller.py`
- MCP 工具：`backend/app/mcp/tools/memory_tools.py` (record_learning_memory, line 338+)
- MCP 工具：`backend/app/mcp/tools/conversation_tools.py` (archive_conversation, line 87+)
- 失败写入：`backend/app/core/failed_writes_constants.py` (FAILED_WRITES_FILE)
- MCP server：`backend/app/mcp/server.py` (line 364-405)

### Testing
- 单元测试：异步非阻塞、超时取消、重试逻辑、归档触发条件
- 集成测试：完整归档流（Hot → Warm → Cold）
- 性能测试：单 episode < 10s
- 边界测试：50K token 容量触发、Graphiti 不可用时的降级

### References
- **From PRD**: FR-MEM-05 异步非阻塞写入
- **From PRD**: FR-MEM-06 Hot-Warm-Cold 三层归档
- Architecture doc: 对话归档流 Hot→Warm→Cold (line 882-891)
- Architecture doc: 对话持久化 SQLite + Hot-Warm-Cold (line 164)
- `backend/app/services/episode_worker.py`: EpisodeWorker 后台任务队列
- `backend/app/services/conversation_distiller.py`: 对话蒸馏管道

## UAT Script

> 1. 进行一段学习对话（至少 10 轮）
> 2. 结束对话，触发 archive_conversation
> 3. 确认对话没有卡顿（异步写入不阻塞）
> 4. 检查 SQLite 中对话消息状态为 Hot
> 5. 修改系统时间或 mock 时间到 31 天后
> 6. 触发归档检查，确认 Hot → Warm 转换
> 7. 搜索该对话，确认返回摘要而非全文
> 8. 故意停止 Graphiti，再次触发写入
> 9. 确认看到失败通知 + 3 次重试日志

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 异步非阻塞 | unit | `pytest tests/unit/test_async_write.py -x` | 0 failures |
| 10s 超时 | unit | `pytest tests/unit/test_write_timeout.py -x` | 0 failures |
| 3 次重试 | unit | `pytest tests/unit/test_write_retry.py -x` | 0 failures |
| Hot→Warm 归档 | unit | `pytest tests/unit/test_hot_warm_archive.py -x` | 0 failures |
| Warm→Cold 归档 | unit | `pytest tests/unit/test_warm_cold_archive.py -x` | 0 failures |
| 端到端归档 | integration | `pytest tests/integration/test_archive_lifecycle.py -x` | 0 failures |
| 写入性能 | performance | `pytest tests/performance/test_episode_write.py -x` | < 10s/episode |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
