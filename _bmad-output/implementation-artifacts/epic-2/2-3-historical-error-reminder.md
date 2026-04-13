---
story_id: "2.3"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 8
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-02"
---

# Story 2.3: 历史误解主动提醒

Status: ready-for-dev

## Story

As a 学习者,
I want AI 在对话中基于我的历史误解主动提醒,
So that 我不会重复犯同样的错误。

## Acceptance Criteria

1. **Given** 学习者讨论的概念有历史误解记录（存储在 Graphiti 中）
   **When** 系统调用 `search_memories` MCP 工具检索该节点的历史错误
   **Then** 返回与当前讨论概念相关的错误记录（按时间倒序，最多 5 条）
   **And** 每条记录包含 error_type / description / corrected_at / tags

2. **Given** 历史误解记录已获取
   **When** 系统将记录注入 LLM system prompt
   **Then** AI 回答中自然融入提醒（如"你之前曾把 X 和 Y 搞混，注意区分..."）
   **And** 提醒以正面措辞呈现（"你上次标记过..." 而非 "你犯了错误..."）
   **And** 提醒不生硬插入，而是在回答中自然过渡

3. **Given** 系统调用 `search_memories`
   **When** 检索完成
   **Then** 记忆搜索响应时间 < 3s（NFR-PERF）

4. **Given** Graphiti / Neo4j 服务不可用
   **When** `search_memories` 调用失败
   **Then** 对话正常继续，跳过历史误解提醒（NFR-DEG 静默降级）
   **And** 后端日志记录降级事件（structlog warning 级别）
   **And** 学习者不感知降级发生

5. **Given** 该概念没有历史误解记录
   **When** `search_memories` 返回空结果
   **Then** AI 正常回答，不包含误解提醒
   **And** 不显示"无历史误解"之类的冗余提示

## Tasks / Subtasks

- [ ] Task 1: `search_memories` 错误记录检索集成 (AC: #1)
  - [ ] 1.1: 在 Story 2.1 的 skill workflow Step 4 中调用 `search_memories` MCP 工具，传入 `node_scope=slug` 和 `query` 参数
  - [ ] 1.2: 在 `backend/app/services/memory_service.py` 中确保 `search_memories` 能按 `node_id` 过滤历史错误记录
  - [ ] 1.3: 返回结构化错误列表，每项含 `error_type` / `description` / `corrected_at` / `tags` / `source_session`
  - [ ] 1.4: 限制返回最多 5 条记录，按 `created_at` 倒序排列

- [ ] Task 2: 提醒注入策略 (AC: #2)
  - [ ] 2.1: 在 `backend/app/services/chat_context_assembler.py`（Story 2.1 创建）中新增 `inject_error_reminders(errors: list) -> str` 方法
  - [ ] 2.2: 将错误记录格式化为 LLM 可理解的上下文片段，使用正面措辞模板：`"学习者之前标记过：{description}。如果讨论涉及此话题，请自然地提醒区分。"`
  - [ ] 2.3: 将格式化的错误上下文追加到 system prompt 的 `{memories}` 部分
  - [ ] 2.4: prompt 中明确指示 LLM 不要生硬插入提醒，而是在回答中自然过渡

- [ ] Task 3: 性能优化与超时保护 (AC: #3)
  - [ ] 3.1: 在 `search_memories` 调用处设置 3s 超时（使用 `asyncio.wait_for`）
  - [ ] 3.2: 超时时按降级路径处理（等同服务不可用）
  - [ ] 3.3: 添加 structlog 延迟日志：`memory_search_latency_ms`

- [ ] Task 4: Graphiti 降级处理 (AC: #4)
  - [ ] 4.1: 在 `search_memories` 调用处捕获 `ConnectionError` / `TimeoutError` / `neo4j.exceptions.ServiceUnavailable`
  - [ ] 4.2: 降级时返回空错误列表 + 降级标记，skill workflow 正常继续
  - [ ] 4.3: 使用 `logger.warning("graphiti_degraded", node_id=slug, error=str(e))` 记录降级事件
  - [ ] 4.4: 降级状态不影响 pipeline_token 传递

- [ ] Task 5: 测试 (AC: #1~#5)
  - [ ] 5.1: 单元测试 `inject_error_reminders`：有错误记录、空记录、正面措辞验证
  - [ ] 5.2: 单元测试 `search_memories` 超时降级：3s 超时后返回空结果
  - [ ] 5.3: 集成测试：Graphiti 中预设错误记录 → 启动对话 → 验证 AI 回答包含提醒
  - [ ] 5.4: 集成测试：停止 Neo4j → 启动对话 → 验证对话正常、无提醒、日志有 warning

## Dev Notes

- **Graphiti 数据格式**: 错误记录以 episode 形式存储，group_id 为 `canvas-dev`（或按学科分隔的 group_id），name 前缀为 `[Error]`
- **已有代码**: `backend/app/services/memory_service.py` 已有 `search_memories` 方法（Story 22.4），需确认其支持按 node_id 过滤 error 类型记录
- **正面措辞**: PRD §4.1 Step 5 和 CLAUDE.md 均强调"正面措辞规范"，提醒用"标记过/之前遇到过"而非"错误/失败"
- **Anchor PRD 引用**: §1.8 间隔复习 (line 2870-2914) 描述了 Claudian 主动检测 + 复用 Graphiti 的完整流程

### Project Structure Notes

```
backend/app/services/
  chat_context_assembler.py       # Story 2.1 创建，本 Story 扩展 inject_error_reminders()
  memory_service.py               # 已有，确认 search_memories 按 node_id 过滤
backend/tests/unit/
  test_error_reminder_injection.py  # 新增
backend/tests/integration/
  test_chat_degradation.py          # 扩展降级测试
```

### References

- PRD §1.8 间隔复习流程: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 2870-2914)
- memory_service.py: `backend/app/services/memory_service.py`
- NFR 降级策略: BMAD PRD (line 558-567)

## UAT Script

> 1. 确保 Neo4j 运行中，Graphiti 中已有 `admissibility` 节点的错误记录（"consistent vs admissible 搞混"）
> 2. 打开 `wiki/concepts/admissibility.md`，启动 AI 对话
> 3. 提问："admissibility 是什么？"
> 4. 验证 AI 回答中包含类似"你之前标记过 consistent 和 admissible 容易搞混..."的提醒
> 5. 验证提醒措辞正面自然，不是生硬插入
> 6. 停止 Neo4j，重新启动对话，验证对话正常但无误解提醒

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 错误提醒注入 | unit | `pytest tests/unit/test_error_reminder_injection.py -x` | 全部通过 |
| 正面措辞 | unit | `pytest tests/unit/test_error_reminder_injection.py::test_positive_phrasing -x` | 无负面词汇 |
| 搜索延迟 | perf | `pytest tests/perf/test_memory_search_latency.py --timeout=5` | < 3s |
| Graphiti 降级 | integration | `pytest tests/integration/test_chat_degradation.py::test_graphiti_unavailable -x` | 对话正常 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
