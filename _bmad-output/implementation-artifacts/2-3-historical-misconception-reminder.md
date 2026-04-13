---
doc_type: story
story_id: "2.3"
aliases: ["2.3"]
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
# Story 2.3: 历史误解主动提醒

## Story

As a 系统,
I want 在对话中基于学习者的个人历史误解主动提醒,
so that 学习者不会重复犯相同的错误。

## Acceptance Criteria

1. **Given** 学习者在对话中讨论某个概念
   **When** 该概念存在历史误解记录（Graphiti 中）
   **Then** AI 在回答中主动提醒："你之前在 X 概念上曾有误解：Y"
   **And** Graphiti search 延迟 < 3s（NFR-PERF-7）
   **And** 只在 API 可用时提醒，Graphiti 不可用时静默跳过（NFR-DEG-3）

## Tasks / Subtasks

- [ ] Task 1: 实现 Graphiti 历史误解查询服务 (AC: #1)
  - [ ] 1.1 在 `backend/app/services/` 新建 `misconception_service.py`，定义 `MisconceptionService` 类
  - [ ] 1.2 实现 `search_misconceptions(concept: str, group_id: str) -> List[MisconceptionRecord]`：调用 Graphiti `search_memory_facts` 检索含 `misconception` 或 `misunderstanding` 标签的历史记录
  - [ ] 1.3 `MisconceptionRecord` dataclass：`concept: str`、`description: str`、`recorded_at: datetime`、`source_episode_id: str`
  - [ ] 1.4 实现 Graphiti 连接健康检查 `is_available() -> bool`：ping Graphiti API，超时 1s 视为不可用
  - [ ] 1.5 实现降级策略：`is_available()` 返回 False 时，`search_misconceptions()` 返回空列表并记录警告日志（不抛异常）

- [ ] Task 2: 将误解记录注入对话 prompt (AC: #1)
  - [ ] 2.1 修改 `DialogContextService.build_context()`（Story 2.1 实现），在 context 组装阶段调用 `MisconceptionService.search_misconceptions()`
  - [ ] 2.2 将误解记录以结构化方式追加到系统 prompt 末尾：`## 学习者历史误解\n- 概念：X，曾有误解：Y`
  - [ ] 2.3 误解记录的 token 预算：在 3K token 总限制内单独为误解区域预留最多 300 tokens，超出则截断最旧的记录
  - [ ] 2.4 LLM prompt 指令中明确要求：如存在相关误解记录，回答时主动提醒一次（自然语言，不直接暴露内部字段名）

- [ ] Task 3: 误解记录写入 Graphiti (AC: #1)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/dialog.py` 中，评分完成后（Story 3.5，或者由 LLM 判定答案错误时），将误解内容写入 Graphiti
  - [ ] 3.2 写入 episode body 格式：`[Misconception] 概念: X | 误解内容: Y | 记录时间: ISO8601`
  - [ ] 3.3 写入操作异步非阻塞（`asyncio.create_task()`），不阻塞对话响应
  - [ ] 3.4 写入失败时记录错误日志，自动重试 3 次（指数退避），最终失败静默跳过

- [ ] Task 4: 编写测试 (AC: #1)
  - [ ] 4.1 单元测试 `backend/tests/unit/test_misconception_service.py`：
    - `search_misconceptions()` 返回正确的误解记录列表
    - Graphiti 不可用时（mock 超时）返回空列表，不抛异常
    - 降级时 structlog 记录警告，级别为 `warning`
  - [ ] 4.2 集成测试 `backend/tests/integration/test_misconception_injection.py`：
    - Graphiti 中存在误解记录时，`build_context()` 的 system prompt 包含误解提醒段落
    - 误解段落 token 数 ≤ 300
  - [ ] 4.3 延迟测试 `backend/tests/integration/test_misconception_latency.py`：
    - `search_misconceptions()` with real Graphiti < 3000ms

## Dev Notes

- **Graphiti group_id 约定**：从配置（`settings.GRAPHITI_GROUP_ID`）读取，不能硬编码。按 canvas 白板名隔离（参考 `decision_s27_gda_batch.md`：group_id 按白板名）
- **search_memory_facts 调用方式**：Graphiti MCP 在后端通过 HTTP/gRPC 调用，参考项目已有的 Graphiti 调用代码（`backend/app/services/` 下含 graphiti 字样的文件，注意 G-FAKE 问题：函数名含 graphiti 但实际调 Neo4j 的要排除）
- **NFR-DEG-3 降级**：Graphiti 不可用时静默跳过，这是系统非核心功能，不可因此阻塞对话。`is_available()` 的超时设为 1s，`search_misconceptions()` 的总超时设为 3s（NFR-PERF-7）
- **误解的识别逻辑**：本 story 的误解写入时机是 Story 3.5 评分完成后。在 story 2.3 实现中，仅需实现读取和注入；写入触发点和 Story 3.5 共享，避免重复实现
- **prompt 中的提醒措辞**：`"你之前在 X 概念上曾有误解：Y"`——这是 LLM 生成的，通过 system prompt 指令引导，不是代码硬编码字符串

### Project Structure Notes

- 新建文件：`backend/app/services/misconception_service.py`
- 修改文件：`backend/app/services/dialog_context_service.py`（注入误解记录，Story 2.1 实现）
- 修改文件：`backend/app/api/v1/endpoints/dialog.py`（误解写入触发点）
- 测试文件：
  - `backend/tests/unit/test_misconception_service.py`
  - `backend/tests/integration/test_misconception_injection.py`
  - `backend/tests/integration/test_misconception_latency.py`
- 样式参考：`backend/app/services/rag_service.py`（service 结构）、`backend/app/api/v1/endpoints/canvas.py`（router 结构）

### References

- [Source: backend/app/services/dialog_context_service.py] — Story 2.1 实现，本 story 修改的核心文件
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.3] — AC 原文和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR2] — FR2 原文：历史误解主动提醒
- [Source: memory/decision_s27_gda_batch.md] — group_id 按白板名约定
- [Source: docs/known-gotchas.md#G-FAKE] — 42+ 假命名函数警告，避免引用错误的 Graphiti 服务

## UAT Script

> 非技术用户验收脚本：只描述用户操作和预期看到的内容，不含代码术语。

1. **验证误解提醒出现在回复中** (AC: #1)
   - 前提：系统中已有该学习者的历史误解记录（可在首轮测试中先创造一条错误答案，触发记录写入）
   - 打开 AI 对话，提问与之前犯过错误的概念相关的问题
   - AI 的回复中应该出现类似"你之前在这个概念上曾有一个误解：……"的提醒文字
   - 如果没有看到提醒，请记录 Story 2.3 和问题内容

2. **验证 Graphiti 不可用时不崩溃** (AC: #1)
   - 请技术人员临时关闭 Graphiti 服务
   - 在应用中继续进行 AI 对话，发送任意问题
   - 对话应该正常工作，只是不会出现历史误解提醒
   - 应用不应该报错或崩溃
   - 记录是否正常收到了 AI 回复（无误解提醒但应有正常回复）

3. **验证提醒响应不太慢** (AC: #1)
   - 发送问题后，整体回复（含误解提醒）应在 5 秒内完成
   - 误解查询不应导致明显的延迟感
   - 如果感觉比没有误解提醒时慢了 3 秒以上，请记录 Story 2.3

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-2.3.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_misconception_service.py -x -q` | 0 failed |
| CP-2.3.2 | pytest | `.venv/bin/pytest backend/tests/integration/test_misconception_injection.py -x -q` | 0 failed |
| CP-2.3.3 | pytest | `.venv/bin/pytest backend/tests/integration/test_misconception_latency.py -x -q` | 0 failed |
| CP-2.3.4 | ruff | `ruff check backend/app/services/misconception_service.py` | exit 0 |

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
