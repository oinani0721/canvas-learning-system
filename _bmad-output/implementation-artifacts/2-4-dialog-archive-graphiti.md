---
doc_type: story
story_id: "2.4"
epic_id: "EPIC-2"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["2.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 2.4: 对话归档到 Graphiti

## Story

As a 系统,
I want 在对话结束时自动将会话归档到 Graphiti 长期记忆,
so that 未来对话可以引用历史交互内容。

## Acceptance Criteria

1. **Given** 学习者结束对话（关闭对话面板或手动结束）
   **When** 系统处理对话归档
   **Then** 异步非阻塞地将对话摘要写入 Graphiti（NFR-REL-5）
   **And** 写入原子性（NFR-INT-2），失败自动重试 3 次（NFR-DEG-6）
   **And** Graphiti 写入队列延迟 < 10s per episode（NFR-PERF-8）
   **And** 归档不阻塞 UI（学习者可立即开始其他操作）

## Tasks / Subtasks

- [ ] Task 1: 实现对话归档服务 (AC: #1)
  - [ ] 1.1 在 `backend/app/services/` 新建 `dialog_archive_service.py`，定义 `DialogArchiveService` 类
  - [ ] 1.2 实现 `archive_dialog(session_id: str, messages: List[DialogMessage], note_path: str, group_id: str) -> None`：生成对话摘要并写入 Graphiti
  - [ ] 1.3 对话摘要生成：将 messages 列表格式化为 episode body，格式：`[Dialog] note: {note_path} | turns: {turn_count} | summary: {messages 前 1000 chars}`
  - [ ] 1.4 调用 Graphiti `add_memory`，`source_description` 设为 `"Canvas dialog session {session_id}"`，`source` 设为 `"text"`
  - [ ] 1.5 实现原子性保证：写入前检查 session 未被重复归档（通过 session_id 查询 Graphiti，已存在则跳过不重复写）

- [ ] Task 2: 异步写入队列与重试机制 (AC: #1)
  - [ ] 2.1 在 `backend/app/workers/` 新建 `archive_worker.py`，实现 `asyncio.Queue` 接收归档任务
  - [ ] 2.2 worker 循环消费队列：调用 `DialogArchiveService.archive_dialog()`，记录开始时间
  - [ ] 2.3 失败重试：捕获异常后用指数退避（1s→2s→4s）重试最多 3 次（NFR-DEG-6）
  - [ ] 2.4 3 次重试全部失败后：记录 structlog error 日志（含 session_id、错误类型、最终 exception），不抛出，不崩溃 worker
  - [ ] 2.5 写入延迟监控：记录 `archive_queue_wait_ms`（入队到开始处理）和 `archive_write_ms`（写入耗时），确保 p99 < 10000ms（NFR-PERF-8）

- [ ] Task 3: 对话结束触发归档 (AC: #1)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/dialog.py` 新增 `POST /api/v1/dialog/{session_id}/end` endpoint
  - [ ] 3.2 endpoint 接收 `DialogEndRequest(session_id: str, messages: List[DialogMessage])`，立即入队，返回 `{"status": "queued"}`（不等待写入完成）
  - [ ] 3.3 FastAPI lifespan 中启动 `archive_worker` 后台任务（`asyncio.create_task()`）
  - [ ] 3.4 在前端 `ChatPanel.tsx` 的对话面板关闭事件（`onClose`）中，调用 `POST /api/v1/dialog/{session_id}/end`，传入当前对话历史

- [ ] Task 4: 前端关闭时触发归档 (AC: #1)
  - [ ] 4.1 修改 `dialog-store.ts`（Story 2.1 实现），新增 `endDialog(sessionId: string)` action
  - [ ] 4.2 `endDialog` 调用 `POST /api/v1/dialog/{session_id}/end`，传入当前 `messages` 列表
  - [ ] 4.3 `ChatPanel.tsx` 关闭按钮 / 面板 unmount 时触发 `endDialog()`
  - [ ] 4.4 `endDialog` 调用后，UI 立即可用（不 loading，不等待归档完成），学习者可立即开始其他操作

- [ ] Task 5: 编写测试 (AC: #1)
  - [ ] 5.1 单元测试 `backend/tests/unit/test_dialog_archive_service.py`：
    - `archive_dialog()` 生成正确格式的 episode body
    - 重复 session_id 不重复归档（幂等）
    - Graphiti 写入失败时不抛异常
  - [ ] 5.2 单元测试 `backend/tests/unit/test_archive_worker.py`：
    - 任务入队后 worker 消费并调用 `archive_dialog()`
    - 写入失败时重试 3 次（mock Graphiti 抛异常，验证调用次数为 3）
    - 3 次重试失败后 worker 继续运行（不崩溃），下一个任务正常处理
  - [ ] 5.3 集成测试 `backend/tests/integration/test_dialog_archive_api.py`：
    - `POST /api/v1/dialog/{session_id}/end` 返回 `{"status": "queued"}` 且响应 < 200ms
    - 队列处理后 Graphiti 中可以查到该 session 的 episode
  - [ ] 5.4 前端测试 `frontend/src/stores/__tests__/dialog-store.test.ts`：
    - `endDialog()` action 调用了正确的 API endpoint
    - 调用后 UI state 不阻塞

## Dev Notes

- **归档不等待**：`POST /api/v1/dialog/{session_id}/end` 必须立即返回，不等待 Graphiti 写入完成。使用 asyncio.Queue 解耦是关键——endpoint 只入队，worker 异步消费
- **session_id 生成**：在 `POST /api/v1/dialog/start`（Story 2.1）调用时由后端生成 UUID4，返回给前端，前端后续持有这个 ID。dialog-store 中存储 `sessionId: string`
- **幂等保证**：Graphiti 不原生支持幂等写入；通过 `search_memory_facts(query=session_id)` 检查是否已存在，存在则跳过。这个检查要在 worker 内部做，不能在 endpoint 做（会阻塞 API 响应）
- **episode 摘要长度**：messages 总长可能很长；取前 1000 chars 作为摘要。完整对话历史不存 Graphiti（Graphiti 是长期记忆索引，不是完整日志）
- **NFR-INT-2 原子性**：Graphiti 的 `add_memory` 是单次写入操作，本身不支持事务；"原子性"在此语境指：要么写入成功，要么完全不写（失败时不写入半条记录）。指数退避重试满足此要求

### Project Structure Notes

- 新建文件：`backend/app/services/dialog_archive_service.py`
- 新建文件：`backend/app/workers/archive_worker.py`
- 修改文件：`backend/app/api/v1/endpoints/dialog.py`（新增 `/end` endpoint + worker 启动）
- 修改文件：`frontend/src/stores/dialog-store.ts`（新增 `endDialog` action）
- 修改文件：`frontend/src/components/ChatPanel.tsx`（关闭时触发 endDialog）
- 测试文件：
  - `backend/tests/unit/test_dialog_archive_service.py`
  - `backend/tests/unit/test_archive_worker.py`
  - `backend/tests/integration/test_dialog_archive_api.py`
  - `frontend/src/stores/__tests__/dialog-store.test.ts`
- 样式参考：`backend/app/services/rag_service.py`（service）、`backend/app/api/v1/endpoints/canvas.py`（router）、`frontend/src/stores/chat-store.ts`（Zustand store）

### References

- [Source: backend/app/services/dialog_context_service.py] — Story 2.1 对话服务，本 story 的上游
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.4] — AC 原文和 FR/NFR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR5] — FR5 原文：对话归档到 Graphiti 长期记忆
- [Source: memory/decision_s27_gda_batch.md] — group_id 按白板名约定，归档时需传入正确 group_id
- [Source: docs/known-gotchas.md#G-FAKE] — 避免调用假命名的 graphiti 服务函数

## UAT Script

> 非技术用户验收脚本：只描述用户操作和预期看到的内容，不含代码术语。

1. **验证关闭对话面板后可立即操作** (AC: #1)
   - 进行一段 AI 对话（发送 2-3 条消息）
   - 点击对话面板右上角的关闭按钮（或点击 X）
   - 面板应立即关闭，不出现"正在保存…"之类的加载提示
   - 关闭后应该可以立即打开其他笔记或进行其他操作
   - 如果关闭时出现加载等待，请记录 Story 2.4 和等待时长

2. **验证历史对话被记住（间接验证归档成功）** (AC: #1)
   - 进行一段对话，讨论某个概念（例如"讨论了微积分的链式法则"）
   - 关闭对话面板，等待约 15 秒（让后台归档完成）
   - 重新打开对话面板，提问："你还记得我们之前讨论的链式法则吗？"
   - AI 应该能引用之前的对话内容（因为已归档到长期记忆）
   - 如果 AI 完全不记得，请记录 Story 2.4

3. **验证归档失败时应用不崩溃** (AC: #1)
   - 请技术人员临时关闭 Graphiti 服务
   - 进行对话后关闭面板
   - 应用应该正常运行，不崩溃、不弹错误弹窗
   - 如果应用崩溃或弹出错误提示，请记录 Story 2.4 和错误内容

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-2.4.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_dialog_archive_service.py -x -q` | 0 failed |
| CP-2.4.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_archive_worker.py -x -q` | 0 failed |
| CP-2.4.3 | pytest | `.venv/bin/pytest backend/tests/integration/test_dialog_archive_api.py -x -q` | 0 failed |
| CP-2.4.4 | vitest | `cd frontend && npx vitest run src/stores/__tests__/dialog-store.test.ts` | 0 failed |
| CP-2.4.5 | ruff | `ruff check backend/app/services/dialog_archive_service.py backend/app/workers/archive_worker.py` | exit 0 |

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

- EPIC: [[EPIC-2]]
- PRD: [[PRD14]]
- Depends on: [[2.1]]
