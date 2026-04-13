# Story 7.2: LLM 调用日志与 Token 追踪

Status: review

## Story

As a 用户,
I want 查看 AI 的使用统计——调用次数、Token 消耗、响应延迟，
So that 我能了解系统的使用情况和成本，发现异常调用，优化使用策略。

## Acceptance Criteria

1. **Given** 系统运行中 **When** 每次 LLM 调用完成（通过 LiteLLM SDK） **Then** 自动记录结构化日志，包含：请求 ID、任务类型、模型名称、输入 token 数、输出 token 数、总 token 数、延迟（ms）、估算成本（USD）、成功/失败状态、时间戳
2. **Given** LLM 调用日志 **When** 查看日志覆盖率 **Then** 100% 的 LLM 调用被记录（NFR-OBS-01），无遗漏
3. **Given** 多种 LLM 调用场景 **When** 日志记录时 **Then** Token 消耗按任务类型分类统计：对话（conversation）、评分（scoring）、提取（extraction）、索引（indexing）、质量检查（qa_check）（NFR-OBS-04）
4. **Given** LLM 调用失败 **When** 异常发生（超时/API 错误/模型不可用） **Then** 错误自动分类记录（LLM 错误/网络错误/配置错误），支持聚合统计（NFR-OBS-03）
5. **Given** 用户打开 Dashboard **When** CostTracker 组件加载 **Then** 展示使用统计摘要：今日/本周/本月的调用次数、总 Token 消耗、估算成本、按任务类型的 Token 分布饼图
6. **Given** 结构化日志记录中 **When** 日志包含 LLM 调用输入/输出内容 **Then** API Key 不出现在日志中（NFR-SEC-02），敏感用户输入可选脱敏
7. **Given** 后端 API **When** 前端请求使用统计 **Then** 提供 `GET /api/v1/system/llm-stats` 端点返回聚合统计数据（按时间范围和任务类型可筛选）

## Tasks / Subtasks

- [ ] **Task 1: LiteLLM 回调集成——结构化日志采集** (AC: #1, #2, #6)
  - [ ] 1.1 创建 `backend/app/middleware/logging_middleware.py` — LiteLLM `success_callback` 和 `failure_callback` 实现
  - [ ] 1.2 定义 `LLMCallLog` Pydantic 模型：request_id(UUID)、task_type(enum)、model_name、input_tokens、output_tokens、total_tokens、latency_ms、estimated_cost_usd、status(success/failure)、error_type(可选)、error_message(可选)、timestamp
  - [ ] 1.3 在 `core/litellm_config.py` 中注册 LiteLLM callback handler（`litellm.success_callback` / `litellm.failure_callback`）
  - [ ] 1.4 实现 API Key 过滤：日志序列化时自动移除 `api_key`、`authorization` 等敏感字段
  - [ ] 1.5 实现 task_type 自动推断：通过 LiteLLM 调用时传入的 `metadata.task_type` 字段确定任务类型

- [ ] **Task 2: Token 消耗按任务统计与持久化** (AC: #3, #4)
  - [ ] 2.1 创建 `backend/app/middleware/cost_tracker.py` — Token 消耗聚合服务
  - [ ] 2.2 定义 `TaskType` 枚举：CONVERSATION / SCORING / EXTRACTION / INDEXING / QA_CHECK
  - [ ] 2.3 实现 SQLite 存储表 `llm_call_logs`：id、request_id、task_type、model_name、input_tokens、output_tokens、total_tokens、latency_ms、estimated_cost_usd、status、error_type、error_message、created_at
  - [ ] 2.4 实现聚合查询方法：`get_stats_by_period(start, end, task_type?)` 返回按任务类型的 Token 分布、调用次数、平均延迟、总成本
  - [ ] 2.5 实现错误分类逻辑：解析 LiteLLM 异常类型映射到 `LLM_ERROR` / `NETWORK_ERROR` / `CONFIG_ERROR`
  - [ ] 2.6 实现日志轮转策略：保留最近 90 天的详细日志，90 天前的压缩为每日汇总

- [ ] **Task 3: 后端 API 端点——使用统计查询** (AC: #7)
  - [ ] 3.1 创建 `GET /api/v1/system/llm-stats` 端点，支持查询参数：period（today/week/month/custom）、start_date、end_date、task_type
  - [ ] 3.2 返回格式：`{ "data": { "summary": {...}, "by_task": [...], "by_day": [...], "errors": {...} }, "meta": {...} }`
  - [ ] 3.3 summary 包含：total_calls、total_tokens、total_input_tokens、total_output_tokens、total_cost_usd、avg_latency_ms
  - [ ] 3.4 by_task 包含：每种 TaskType 的 calls/tokens/cost 聚合
  - [ ] 3.5 errors 包含：按 error_type 的计数聚合

- [ ] **Task 4: 前端 CostTracker 组件——Dashboard 展示** (AC: #5)
  - [ ] 4.1 创建 `obsidian-canvas-learning/src/components/dashboard/CostTracker.svelte` — Token 成本展示组件
  - [ ] 4.2 实现时间范围选择器（今日/本周/本月）
  - [ ] 4.3 实现摘要卡片：调用次数、总 Token、估算成本（三个数值卡片）
  - [ ] 4.4 实现任务类型分布展示：按任务类型的 Token 消耗占比（简洁列表或进度条）
  - [ ] 4.5 实现每日趋势展示：最近 7/30 天的 Token 消耗趋势（简单柱状图或折线）
  - [ ] 4.6 CSS 隔离：使用 `cl-dash-cost-*` 类名前缀 + Svelte scoped CSS + Obsidian CSS 变量

- [ ] **Task 5: EventBus 集成与管道健康指标** (AC: #2, #4)
  - [ ] 5.1 定义 `LLM_CALL_LOGGED` 事件到 `canvas_events.py`（Tier3 fire-and-forget）
  - [ ] 5.2 logging_middleware 每次记录日志后发布事件到 EventBus
  - [ ] 5.3 cost_tracker 订阅事件进行聚合更新
  - [ ] 5.4 实现管道健康探针：LLM 调用成功率（最近 100 次）、平均延迟，通过 health_monitor 暴露

- [ ] **Task 6: 单元测试与集成测试** (AC: #1-#7)
  - [ ] 6.1 单元测试：`test_logging_middleware.py` — 回调正确解析 LiteLLM 响应、API Key 过滤、task_type 推断
  - [ ] 6.2 单元测试：`test_cost_tracker.py` — 聚合计算正确性、日志轮转、错误分类
  - [ ] 6.3 集成测试：`test_llm_stats_api.py` — API 端点返回格式、时间范围过滤、task_type 过滤
  - [ ] 6.4 集成测试：LiteLLM 实际调用 → 日志记录 → 聚合统计端到端验证

## Dev Notes

### LiteLLM 回调集成方案

**核心机制：LiteLLM Custom Callback**

LiteLLM SDK 提供原生的 callback 机制，可在每次 LLM 调用成功/失败后自动触发回调函数。这是实现 100% 日志覆盖率的关键——所有通过 LiteLLM 的调用都会被自动拦截记录，无需在每个调用点手动添加日志。

**回调注册方式：**

```python
# backend/app/core/litellm_config.py
import litellm
from app.middleware.logging_middleware import llm_call_logger

# 注册回调
litellm.success_callback = [llm_call_logger.on_success]
litellm.failure_callback = [llm_call_logger.on_failure]
```

**回调数据提取：**

LiteLLM 回调提供 `kwargs` 和 `completion_response` 参数，包含：
- `model`: 实际使用的模型名称
- `response_cost`: LiteLLM 内置的成本计算（基于其定价数据库）
- `usage.prompt_tokens` / `usage.completion_tokens`: Token 计数
- `response_time`: 响应时间（秒）
- `litellm_params.metadata`: 调用时传入的自定义元数据（用于 task_type）

**任务类型传递方式：**

所有 LiteLLM 调用时通过 `metadata` 参数传入 task_type：

```python
response = await litellm.acompletion(
    model="gpt-4",
    messages=[...],
    metadata={"task_type": "scoring", "request_id": str(uuid4())}
)
```

各模块的 task_type 映射：
- `context_assembler.py` / `chat.py` → `"conversation"`
- `autoscore.py` → `"scoring"`
- `conversation_archive.py` / `error_classifier.py` → `"extraction"`
- `indexing/pipeline.py` → `"indexing"`
- `faithfulness_check.py` → `"qa_check"`

### 结构化日志格式

**单条 LLM 调用日志 Schema：**

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "scoring",
  "model_name": "gpt-4o-mini",
  "input_tokens": 1250,
  "output_tokens": 340,
  "total_tokens": 1590,
  "latency_ms": 2340,
  "estimated_cost_usd": 0.00285,
  "status": "success",
  "error_type": null,
  "error_message": null,
  "created_at": "2026-03-16T14:30:00.000Z"
}
```

**成本估算：** 使用 LiteLLM 内置的 `response_cost` 计算（LiteLLM 维护 100+ 模型的定价数据库）。如果 LiteLLM 无法计算（如自定义模型），记录 `estimated_cost_usd = null`，不阻塞日志记录。

### SQLite 存储设计

**表结构：**

```sql
CREATE TABLE IF NOT EXISTS llm_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    task_type TEXT NOT NULL,  -- CONVERSATION/SCORING/EXTRACTION/INDEXING/QA_CHECK
    model_name TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd REAL,
    status TEXT NOT NULL DEFAULT 'success',  -- success/failure
    error_type TEXT,  -- LLM_ERROR/NETWORK_ERROR/CONFIG_ERROR
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX idx_llm_logs_task_type ON llm_call_logs(task_type);
CREATE INDEX idx_llm_logs_created_at ON llm_call_logs(created_at);
CREATE INDEX idx_llm_logs_status ON llm_call_logs(status);
```

**日志轮转：** 定期任务（FastAPI lifespan 或 background task）每天执行一次，将 90 天前的详细日志压缩为每日汇总行后删除原始行。汇总表 `llm_call_logs_daily` 存储每日每 task_type 的聚合值。

### 错误分类规则

| LiteLLM 异常类型 | 映射分类 | 说明 |
|-----------------|---------|------|
| `AuthenticationError` | CONFIG_ERROR | API Key 无效或过期 |
| `RateLimitError` | LLM_ERROR | 速率限制 |
| `APIError` / `ServiceUnavailableError` | LLM_ERROR | LLM 服务端错误 |
| `Timeout` | NETWORK_ERROR | 请求超时 |
| `APIConnectionError` | NETWORK_ERROR | 网络连接失败 |
| `NotFoundError` | CONFIG_ERROR | 模型不存在 |
| `BadRequestError` | LLM_ERROR | 请求格式错误（如 token 超限） |

### API 端点响应示例

**`GET /api/v1/system/llm-stats?period=week`**

```json
{
  "data": {
    "summary": {
      "total_calls": 342,
      "total_tokens": 485200,
      "total_input_tokens": 380100,
      "total_output_tokens": 105100,
      "total_cost_usd": 2.45,
      "avg_latency_ms": 1850,
      "success_rate": 0.97
    },
    "by_task": [
      { "task_type": "conversation", "calls": 180, "tokens": 280000, "cost_usd": 1.40 },
      { "task_type": "scoring", "calls": 85, "tokens": 120000, "cost_usd": 0.60 },
      { "task_type": "extraction", "calls": 45, "tokens": 55000, "cost_usd": 0.28 },
      { "task_type": "indexing", "calls": 20, "tokens": 18000, "cost_usd": 0.09 },
      { "task_type": "qa_check", "calls": 12, "tokens": 12200, "cost_usd": 0.08 }
    ],
    "by_day": [
      { "date": "2026-03-10", "calls": 48, "tokens": 68500, "cost_usd": 0.34 },
      { "date": "2026-03-11", "calls": 52, "tokens": 72100, "cost_usd": 0.36 }
    ],
    "errors": {
      "total": 10,
      "by_type": {
        "LLM_ERROR": 6,
        "NETWORK_ERROR": 3,
        "CONFIG_ERROR": 1
      }
    }
  },
  "meta": {
    "period": "week",
    "start_date": "2026-03-10",
    "end_date": "2026-03-16",
    "timestamp": "2026-03-16T14:30:00.000Z"
  }
}
```

### CostTracker 前端组件设计

**组件位置：** `obsidian-canvas-learning/src/components/dashboard/CostTracker.svelte`

**UI 布局（CSS: cl-dash-cost-*）：**

```
┌──────────────────────────────────────────┐
│  Token 使用统计          [今日|本周|本月]  │
├──────────┬──────────┬────────────────────┤
│ 调用次数  │  总Token  │   估算成本         │
│   342    │  485.2K  │   $2.45           │
├──────────┴──────────┴────────────────────┤
│  任务类型分布                              │
│  对话 ████████████████░░░░  57.7%         │
│  评分 █████████░░░░░░░░░░░  24.7%         │
│  提取 █████░░░░░░░░░░░░░░░  11.3%         │
│  索引 ██░░░░░░░░░░░░░░░░░░   3.7%         │
│  质检 █░░░░░░░░░░░░░░░░░░░   2.5%         │
├──────────────────────────────────────────┤
│  每日趋势（最近7天）                       │
│  ▁▃▅▇█▆▄                                │
└──────────────────────────────────────────┘
```

**数据获取：** 通过 `api-client.ts` 调用 `GET /api/v1/system/llm-stats`，使用 Svelte 5 `$state` 响应式绑定。

**无外部图表依赖：** 使用纯 CSS（进度条 + 简易 SVG 柱状图）实现可视化，避免引入 chart.js 等重量级库。Obsidian 插件环境下保持轻量。

### 架构约束与注意事项

- **LiteLLM 统一调用**：所有 LLM 调用必须通过 `litellm.acompletion()` / `litellm.aembedding()`，确保回调 100% 覆盖。直接使用 openai SDK 等会绕过日志采集
- **API Key 安全**：日志序列化时 MUST 过滤 `api_key`、`api_base`、`authorization` 字段（NFR-SEC-02），使用白名单而非黑名单策略
- **性能影响**：日志写入使用异步 SQLite（aiosqlite），不阻塞 LLM 调用返回。批量写入优化（攒 10 条或 5 秒一批）
- **EventBus 集成**：`LLM_CALL_LOGGED` 事件为 Tier3（fire-and-forget WebSocket），不影响主调用流程
- **双层 Key 分离**：外层 Agent 对话使用用户 Key（通过 Claude Code CLI），内层评分/提取使用后端配置的 Key。日志中记录 `key_source: "user" | "backend"` 但不记录 Key 值
- **与 Story 7.1 的关系**：7.1 的 faithfulness_check 和 prompt_injection_guard 的检查结果也通过本 Story 的日志体系记录。7.2 为整个后端提供统一的 LLM 可观测性基础设施

### Project Structure Notes

**新增文件（按架构目录规范）：**

| 文件 | 目录 | 说明 |
|------|------|------|
| `logging_middleware.py` | `backend/app/middleware/` | LiteLLM 回调 + 结构化日志采集 |
| `cost_tracker.py` | `backend/app/middleware/` | Token 消耗聚合服务 + SQLite 持久化 |
| `CostTracker.svelte` | `obsidian-canvas-learning/src/components/dashboard/` | Dashboard Token 成本展示组件 |
| `test_logging_middleware.py` | `backend/tests/unit/` | 日志中间件单元测试 |
| `test_cost_tracker.py` | `backend/tests/unit/` | 成本追踪单元测试 |
| `test_llm_stats_api.py` | `backend/tests/integration/` | LLM 统计 API 集成测试 |

**修改文件：**

| 文件 | 修改内容 |
|------|---------|
| `backend/app/core/litellm_config.py` | 注册 LiteLLM success/failure callback handler |
| `backend/app/api/v1/system.py` | 添加 `GET /api/v1/system/llm-stats` 端点 |
| `backend/app/models/canvas_events.py` | 追加 `LLM_CALL_LOGGED` 事件枚举（加法编辑） |
| `backend/app/db/sqlite_client.py` | 添加 `llm_call_logs` 表初始化（加法编辑） |
| `obsidian-canvas-learning/src/services/api-client.ts` | 添加 `getLLMStats(period)` 方法（加法编辑） |
| `obsidian-canvas-learning/src/components/dashboard/DashboardView.svelte` | 嵌入 CostTracker 组件（加法编辑） |

**不触及的文件：**

- `agentic_rag/` 管道节点 — 不修改检索管道逻辑
- `mcp/` MCP 工具定义 — 不暴露新 MCP 工具
- IndexedDB schema — Token 统计存后端 SQLite，不存前端
- `prompt_injection_guard.py` — 属于 Story 7.1 范围

### 不做的事项（防蔓延）

- 不实现实时 WebSocket 推送 Token 统计更新（Dashboard 打开时拉取即可）
- 不实现 LLM 调用输入/输出内容的完整存储（仅存 token 数和元数据，节省存储空间）
- 不实现可视化图表库集成（纯 CSS 进度条 + 简易 SVG）
- 不实现用户自定义成本预算告警（可作为后续增强）
- 不实现 Claude Code CLI spawn 方式的 Token 追踪（外层 Agent 对话使用用户订阅额度，不经过后端 LiteLLM）
- 不实现管道健康 Dashboard 完整 UI（仅暴露 API 端点和健康探针，完整 UI 留后续）

### References

- [Source: _bmad-output/planning-artifacts/prd.md#能力域9 — FR-QA-03, FR-QA-04]
- [Source: _bmad-output/planning-artifacts/prd.md#可观测性 — NFR-OBS-01, NFR-OBS-03, NFR-OBS-04]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure — middleware/logging_middleware.py, middleware/cost_tracker.py]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure — dashboard/CostTracker.svelte]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns #3 — LLM调用管理: 成本追踪+多模型路由(LiteLLM)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns #7 — 错误处理与可观测性: 100%LLM日志+结构化日志]
- [Source: _bmad-output/planning-artifacts/architecture.md#FR Mapping #9 — 质量保证: dashboard/CostTracker + middleware/* + 结构化日志]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Stack — LiteLLM SDK (100+ 模型，双层 Key)]
- [Source: _bmad-output/planning-artifacts/architecture.md#External Integrations — Claude API / LLM Provider: LiteLLM SDK (HTTP)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure — 监控: 100% LLM 调用日志 + Token 成本追踪]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.2 — AC 原始定义]
- [Source: _bmad-output/planning-artifacts/architecture.md#Security — API Key 仅本地不明文不入日志]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Context7 LiteLLM docs: confirmed CustomLogger + litellm.callbacks is the correct async callback pattern
- Previous code used litellm.success_callback (sync-only list) which would not fire async callbacks

### Completion Notes List

1. **Critical fix: LiteLLM callback registration** - Refactored `LLMCallLogger` to inherit from `litellm.integrations.custom_logger.CustomLogger` (was plain class). Async callbacks (`async_log_success_event` / `async_log_failure_event`) are now correctly invoked by LiteLLM SDK. Registration changed from `litellm.success_callback` (sync) to `litellm.callbacks` (supports CustomLogger instances). Reference: https://docs.litellm.ai/docs/observability/custom_callback
2. **Graceful fallback** - If litellm is not installed, `_LiteLLMCustomLogger` falls back to `object`, and the logger still works via the manual `log_call()` API.
3. **Extracted `_compute_latency_ms`** - Deduplicated latency calculation from on_success/on_failure into a shared static method.
4. **All 5 tasks verified complete**: (1) LiteLLM callback registration, (2) LLMCallLogger completeness, (3) CostTracker SQLite persistence, (4) LLM Stats API endpoint, (5) Unit + integration tests.
5. **Test coverage expanded**: Added tests for async_log_success_event/async_log_failure_event delegation, all 7 LiteLLM error classification mappings + fallback heuristics, API key whitelist serialization, error message truncation, task_type extraction paths, E2E callback-to-SQLite pipeline, API key absence in persisted rows.

### File List

| File | Action | Description |
|------|--------|-------------|
| `backend/app/middleware/llm_call_logger.py` | Modified | Inherit from CustomLogger, add async_log_success/failure_event, extract _compute_latency_ms |
| `backend/app/core/litellm_config.py` | Modified | Use litellm.callbacks instead of litellm.success_callback/failure_callback |
| `backend/app/middleware/cost_tracker.py` | Verified | Complete: tables, indices, batch insert, aggregation, rotation, health probe |
| `backend/app/api/v1/system.py` | Verified | Complete: GET /api/v1/system/llm-stats with period/task_type filtering |
| `backend/app/main.py` | Verified | Complete: startup init + shutdown cleanup for CostTracker and LLMCallLogger |
| `backend/tests/unit/test_llm_call_logger.py` | Modified | Added 12 new tests: async delegation, error classification, API key filtering, latency, task_type |
| `backend/tests/unit/test_cost_tracker.py` | Verified | Complete: table creation, insert/query, rotation, health probe |
| `backend/tests/integration/test_llm_stats_api.py` | Modified | Added TestCallbackToSQLiteE2E: 4 E2E tests for callback->SQLite pipeline and API key absence |
