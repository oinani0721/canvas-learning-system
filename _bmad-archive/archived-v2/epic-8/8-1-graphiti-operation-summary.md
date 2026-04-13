---
doc_type: story
story_id: "8.1"
aliases: ["8.1"]
epic_id: "EPIC-8"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 2
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 8.1: Skill 末尾 Graphiti 操作摘要行

## Story

As a 系统,
I want 在 Skill 结束时附加 Graphiti 操作摘要行,
so that 学习者可以确认每次操作后 Graphiti 是否成功记录。

## Acceptance Criteria

1. **Given** 任意 Skill（对话、考察、概念提取等）执行完毕
   **When** Skill 返回结果
   **Then** 末尾附加摘要行，格式：`[Graphiti] wrote N episodes, read M facts (Xms)`
   **And** N、M、X 均为实际运行数据（不可为占位符）

2. **Given** Graphiti 写入在 Skill 执行期间失败
   **When** Skill 返回结果
   **Then** 末尾显示：`[Graphiti] ⚠ write failed (will retry)`
   **And** 失败提示不影响 Skill 的主体结果输出

3. **Given** Skill 执行期间未触发任何 Graphiti 读写（如纯本地操作）
   **When** Skill 返回结果
   **Then** 不追加摘要行（避免无意义的 `[Graphiti] wrote 0 episodes, read 0 facts` 噪声）

## Tasks / Subtasks

- [ ] Task 1: 设计 Graphiti 操作上下文收集器 (AC: #1, #2, #3)
  - [ ] 1.1 在 `backend/app/core/graphiti_context.py` 创建 `GraphitiOpContext` dataclass，字段：`writes: int`、`reads: int`、`elapsed_ms: int`、`last_error: str | None`
  - [ ] 1.2 实现 `GraphitiOpContext.accumulate(write=0, read=0, elapsed_ms=0)` 方法，线程安全地累加计数
  - [ ] 1.3 实现 `GraphitiOpContext.to_summary_line() -> str | None`：写入数为 0 且读取数为 0 时返回 None；有错误时返回 warning 格式；否则返回正常格式
  - [ ] 1.4 使用 `contextvars.ContextVar` 在异步调用链中传递 `GraphitiOpContext`，避免全局状态

- [ ] Task 2: 在 Graphiti 调用点注入计数 (AC: #1, #2)
  - [ ] 2.1 修改 `backend/app/services/graphiti_service.py` 中的写入方法（`add_episode`、`add_memory` 等），在成功时调用 `ctx.accumulate(write=1, elapsed_ms=...)`
  - [ ] 2.2 修改读取方法（`search_memory_facts`、`get_episodes` 等），在成功时调用 `ctx.accumulate(read=1, elapsed_ms=...)`
  - [ ] 2.3 捕获写入失败异常，设置 `ctx.last_error`，不向上抛出（允许 Skill 主流程继续）
  - [ ] 2.4 验证：异步并发调用时计数不丢失（使用 `asyncio.Lock` 或原子操作）

- [ ] Task 3: 在 Skill 出口注入摘要行 (AC: #1, #2, #3)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/` 各 Skill 路由的响应序列化阶段，读取当前 `GraphitiOpContext`
  - [ ] 3.2 若 `to_summary_line()` 返回非 None，追加到响应的 `summary_footer` 字段（新增字段，不破坏已有结构）
  - [ ] 3.3 前端（Claudian MCP handler）读取 `summary_footer`，在显示 Skill 结果后追加该行
  - [ ] 3.4 确认 Claudian 端摘要行显示为 monospace 小字（与主体内容视觉区分）

- [ ] Task 4: 编写测试 (AC: #1, #2, #3)
  - [ ] 4.1 单元测试：`GraphitiOpContext.to_summary_line()` 三种场景（正常/失败/零操作）
  - [ ] 4.2 集成测试：Mock Graphiti 写入失败，断言响应含 `⚠ write failed` 摘要
  - [ ] 4.3 集成测试：正常写入 2 次读取 1 次，断言摘要行格式正确（`wrote 2 episodes, read 1 facts`）
  - [ ] 4.4 测试零操作场景：断言 `summary_footer` 字段为 null

## Dev Notes

- **上下文传递**：使用 `contextvars.ContextVar` 而非全局变量，确保并发请求的计数互相隔离。参考 Python 3.12 文档 `contextvars` 章节
- **NFR-DEG-6 对齐**：写入失败后摘要行显示 warning 并触发自动重试（重试逻辑在 `graphiti_service.py` 内已有，此处只收集结果）
- **不改变 Skill 主流程**：摘要行是附加信息，任何异常都不可阻断主结果返回
- **延迟统计**：记录 Graphiti 操作的实际耗时（ms），不含 LLM 时间，便于与 NFR-PERF-7 (`< 3s`) 和 NFR-PERF-8 (`< 10s`) 对比
- **前端字段约定**：`summary_footer: str | null` 追加到现有 Skill 响应 schema，前端需更新 TypeScript 类型定义

### Project Structure Notes

- 新建文件：`backend/app/core/graphiti_context.py`
- 修改文件：`backend/app/services/graphiti_service.py`（注入计数）
- 修改文件：`backend/app/api/v1/endpoints/` 各 Skill 路由（读取并输出 `summary_footer`）
- 前端修改：Claudian MCP handler 中读取 `summary_footer` 并渲染
- 测试文件：`backend/tests/unit/test_graphiti_context.py`、`backend/tests/integration/test_skill_summary_footer.py`

### References

- [Source: backend/app/services/graphiti_service.py] — Graphiti 读写方法入口
- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.1] — AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/epics.md#NFR-OBS-1] — 可观测性 NFR
- [FR44] Skill 末尾 Graphiti 摘要行
- [NFR-OBS-1] Skill 末尾 Graphiti 摘要行

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证正常摘要行** (AC: #1)
   - 打开 Obsidian，启动一次 AI 对话 Skill（例如 `/chat`）
   - 对话结束后，在对话结果的最后一行，应看到类似：`[Graphiti] wrote 1 episodes, read 2 facts (312ms)`
   - 如果没有看到这行文字，记录 Story 8.1 和实际看到的内容

2. **验证失败提示** (AC: #2)
   - （需要开发者临时关闭 Neo4j 来制造 Graphiti 失败）
   - 关闭 Neo4j 后再启动一次 Skill
   - 结果末尾应看到：`[Graphiti] ⚠ write failed (will retry)`
   - 且 Skill 的主要结果（AI 回答）仍然正常显示

3. **验证零操作不显示** (AC: #3)
   - 执行一个不涉及 Graphiti 的本地操作
   - 结果末尾不应出现任何 `[Graphiti]` 字样

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-8.1.1 | pytest | `.venv/bin/pytest tests/unit/test_graphiti_context.py -x -q` | 0 failed |
| CP-8.1.2 | pytest | `.venv/bin/pytest tests/integration/test_skill_summary_footer.py -x -q` | 0 failed |

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

- EPIC: [[EPIC-8]]
- PRD: [[PRD14]]
