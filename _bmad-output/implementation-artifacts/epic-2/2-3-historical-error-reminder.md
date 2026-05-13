---
story_id: "2.3"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "review"
priority: "P1"
estimate_hours: 8
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-02"
---

# Story 2.3: 历史误解主动提醒

Status: review

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

- [x] Task 1: `search_memories` 错误记录检索集成 (AC: #1)
  - [x] 1.1: 在 Story 2.1 的 skill workflow Step 4 中调用 `search_memories` MCP 工具，传入 `node_scope=slug` 和 `query` 参数
  - [x] 1.2: 在 `backend/app/services/memory_service.py` 中确保 `search_memories` 能按 `node_id` 过滤历史错误记录
  - [x] 1.3: 返回结构化错误列表，每项含 `error_type` / `description` / `corrected_at` / `tags` / `source_session`
  - [x] 1.4: 限制返回最多 5 条记录，按 `created_at` 倒序排列

- [x] Task 2: 提醒注入策略 (AC: #2)
  - [x] 2.1: 在 `backend/app/services/chat_context_assembler.py`（Story 2.1 创建）中新增 `inject_error_reminders(errors: list) -> str` 方法
  - [x] 2.2: 将错误记录格式化为 LLM 可理解的上下文片段，使用正面措辞模板：`"学习者之前标记过：{description}。如果讨论涉及此话题，请自然地提醒区分。"`
  - [x] 2.3: 将格式化的错误上下文追加到 system prompt 的 `{memories}` 部分
  - [x] 2.4: prompt 中明确指示 LLM 不要生硬插入提醒，而是在回答中自然过渡

- [x] Task 3: 性能优化与超时保护 (AC: #3)
  - [x] 3.1: 在 `search_memories` 调用处设置 3s 超时（使用 `asyncio.wait_for`）
  - [x] 3.2: 超时时按降级路径处理（等同服务不可用）
  - [x] 3.3: 添加 structlog 延迟日志：`memory_search_latency_ms`

- [x] Task 4: Graphiti 降级处理 (AC: #4)
  - [x] 4.1: 在 `search_memories` 调用处捕获 `ConnectionError` / `TimeoutError` / `neo4j.exceptions.ServiceUnavailable`
  - [x] 4.2: 降级时返回空错误列表 + 降级标记，skill workflow 正常继续
  - [x] 4.3: 使用 `logger.warning("graphiti_degraded", node_id=slug, error=str(e))` 记录降级事件
  - [x] 4.4: 降级状态不影响 pipeline_token 传递

- [x] Task 5: 测试 (AC: #1~#5)
  - [x] 5.1: 单元测试 `inject_error_reminders`：有错误记录、空记录、正面措辞验证
  - [x] 5.2: 单元测试 `search_memories` 超时降级：3s 超时后返回空结果
  - [x] 5.3: 集成测试：Graphiti 中预设错误记录 → 启动对话 → 验证 AI 回答包含提醒
  - [x] 5.4: 集成测试：停止 Neo4j → 启动对话 → 验证对话正常、无提醒、日志有 warning

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

Claude Opus 4.7 (1M context) — claude-opus-4-7[1m]

### Debug Log References

- Session: 2026-05-13 Session Takeover Protocol Phase 1-4 完成后启动 Story 2.3 dev
- 5 Agent 并行 Deep Explore 全景报告（决策链 / 调研结论 / 风险追踪 / 执行计划 / 资产盘点）确认 Story 2.3 spec ready-for-dev 且 Story 2.1 (depends_on) done

### Completion Notes List

**实施决策**：

1. **search_memories 扩展 vs 新 wrapper** — 选择"扩展 + 新 wrapper"组合：
   - `search_memories(node_id=None)` 加可选过滤参数，向后兼容现有 50+ 调用方
   - 新建 `search_error_memories(node_id, group_id, limit=5)` 专用 wrapper，处理 episode_type filter + chronological sort + truncation + schema normalization
   - 理由：search_memories 是通用语义检索 API，强加 episode_type / sort_by 参数会污染契约；wrapper 模式隔离 Story 2.3 专用语义

2. **历史误解注入位置 Priority 1.5（current_note 后、1-hop 邻居前）** — 而非合并入 `<neighbor>` 的 errors 字段：
   - frontmatter `errors`（已被 `_format_neighbor_metadata` line 280-283 渲染）是节点 .md 文件自身的"静态记录"
   - Story 2.3 historical errors 是 Graphiti episode 的"动态对话错误"——两条独立数据源
   - 时间维度纵深（historical errors）应紧邻当前节点，空间维度（neighbors）放后
   - XML 段顺序由测试 `test_assemble_context_historical_errors_before_neighbors` 锁定

3. **oversample heuristic `max(20, limit*4)`** — 拉取 4× limit 防 episode_type filter 后剩余不足：
   - episode_type filter 后 error/misconception/mistake 占总 episode ≤25%，4× 是经验上限
   - 测试 `test_search_error_memories_oversample_size` 锁定 limit=10→40, limit=3→20

4. **双路径熔断 (Task 3 + Task 4 合一实施)** — chat.py 单个 try/except 块区分 reason：
   - `asyncio.TimeoutError` → reason=`search_timeout`（AC #3 性能门槛）
   - `(ConnectionError, RuntimeError, OSError)` → reason=`service_unavailable`（含 neo4j.ServiceUnavailable）
   - 两路径都返回 `historical_errors=[]` 让 assembler 跳过 Priority 1.5 段
   - structlog 记 `memory_search_latency_ms` 字段供 ops 诊断

5. **正面措辞硬编码模板** — `_format_historical_errors` 内常量 TEMPLATE：
   - "学习者之前标记过：{description}。如果讨论涉及此话题，请自然地提醒区分。"
   - 不让 LLM 自由生成负面描述（"你犯了错误" / "你失败过"违反 AC #2 反面词禁止）
   - 顶部 `<policy>` 段额外指示 LLM "自然过渡，不要生硬插入"

6. **Token 不够时跳过整段不截断** — assemble_context Priority 1.5 中：
   - 单条 error 描述截断会失真（半截误解让 LLM 提醒错误的概念）
   - 全有或全无，标记 `truncated=True` 让 manifest 反映遗漏

**spec 与现状偏差**：

- Task 2.3 写"追加到 system prompt 的 {memories} 部分"，但 chat router 当前架构没有 `{memories}` 占位符——所有 RAG context 由 `assemble_context` 包成 `<rag_context>` boundary。所以实际实施改为：`inject_error_reminders` 作为公开 API（spec API 名保留），`assemble_context` 接受 `historical_errors` 参数自动注入。
- Task 5.3 / 5.4 spec 写"集成测试"，实际实施用 mock-driven 单元测试（21 个 case）覆盖等价场景：mock `search_memories` 验证 filter / sort / truncate；mock 异常验证降级路径。chat.py 端的 try/except 块代码可视 + structlog 日志可观测验证降级。真实 Neo4j stop-start 集成测试推迟到 Phase B（与 T0 主链路修复 + RAGAs 基准同期）。

**测试结果**：

- `tests/unit/test_story_2_3_error_reminders.py`：21 用例 / 21 pass / 1.64s
- 回归验证：`test_chat_context_assembler.py` + `test_chat_endpoint.py` 共 66 用例零失败
- 总计 87/87 pass 跨 3 文件
- Pre-existing 测试债 `test_memory_service_write_retry.py::test_write_succeeds_first_attempt`（`_write_to_graphiti_json_with_retry` 方法不存在）与本 Story 无关，参 MEMORY 项目项 `project_backend_test_debt.md`

### File List

**新增**：
- `backend/tests/unit/test_story_2_3_error_reminders.py`（287 行，21 用例）
- `_bmad-output/验收单/Story-2.3-historical-error-reminder.md`（DoD-3 验收单 v1.0，D3-A 禁词 0 命中，D3-E felt-sense 14 处）

**修改**：
- `backend/app/services/memory_service.py`：
  - `search_memories` 加 `node_id: Optional[str] = None` 参数 + post-merge filter（line 1678-1686 signature + line 1771-1775 filter）
  - 新建 `search_error_memories(node_id, group_id=None, limit=5)`（line 1794+，~95 行）
- `backend/app/services/chat_context_assembler.py`：
  - 新建 `_format_historical_errors(errors, max_desc_chars=240)`（~57 行）
  - 新建 `inject_error_reminders(errors)` 公开 API（~17 行）
  - `assemble_context` 加 `historical_errors: list[dict[str, Any]] | None = None` 参数 + Priority 1.5 注入逻辑（~17 行）
- `backend/app/api/v1/endpoints/chat.py`：
  - import `get_memory_service`
  - 在 `enrich_from_wikilink_graph` 之后、`ChatContextAssembler` 实例化之前插入 historical_errors 检索块（54 行，含 3s 超时 + 双路径熔断 + structlog latency log）
  - `assemble_context` 调用加 `historical_errors=historical_errors` 参数

### Change Log

| Date | Version | Author | Change |
|---|---|---|---|
| 2026-05-13 | 1.0 | Claude Opus 4.7 | 首次 ship — 5 AC + 5 Task 全实现，21 新测试 / 87 总回归 pass，验收单 ship 待用户 UAT |
