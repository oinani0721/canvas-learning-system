---
doc_type: story
story_id: "8.4"
epic_id: "EPIC-8"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 8.4: Token 成本追踪

## Story

As a 系统,
I want 追踪 LLM API 的 token 消耗并按任务类型统计,
so that 学习者和开发者可以了解成本分布并优化高消耗操作。

## Acceptance Criteria

1. **Given** 任何 LLM API 调用发生（Claude API 或本地 Ollama，经由 LiteLLM 统一层）
   **When** 调用返回
   **Then** 记录以下字段：`prompt_tokens`、`completion_tokens`、`model`、`task_type`（枚举值：`chat` / `score` / `quiz` / `graphify`）、时间戳、延迟（ms）

2. **Given** token 统计数据已积累
   **When** 学习者在 Dashboard 查看成本报告
   **Then** 可按天/周/月聚合查看：每个 `task_type` 的总 token 消耗、调用次数、平均延迟

3. **Given** Claude API 不可用，系统已降级到本地 Ollama 模型（NFR-DEG-2）
   **When** Ollama 模型调用返回
   **Then** token 追踪仍然生效：`model` 字段记录 Ollama 模型名，`task_type` 不变

4. **Given** LiteLLM 统一层处理 API 调用（AR8）
   **When** 双层 Key 分离生效（用户 Key 和系统 Key 分开使用）
   **Then** 追踪记录中包含 `key_tier` 字段（`user` 或 `system`），区分两层消耗来源

## Tasks / Subtasks

- [ ] Task 1: 设计 token 追踪数据模型和存储 (AC: #1, #2)
  - [ ] 1.1 在 `backend/app/models/token_usage.py` 定义 `TokenUsageRecord` Pydantic 模型：`ts: datetime`、`model: str`、`task_type: Literal["chat", "score", "quiz", "graphify"]`、`prompt_tokens: int`、`completion_tokens: int`、`latency_ms: int`、`key_tier: Literal["user", "system"]`
  - [ ] 1.2 在 `backend/app/core/token_tracker.py` 实现 `TokenTracker` 类，使用 SQLite（`data/token_usage.db`，本地文件）存储追踪记录
  - [ ] 1.3 实现 `TokenTracker.record(usage: TokenUsageRecord)` 异步方法，插入 SQLite
  - [ ] 1.4 实现 `TokenTracker.aggregate(period: Literal["day", "week", "month"], task_type: str | None = None) -> list[AggregateRow]` 查询方法，返回按时间分组的统计
  - [ ] 1.5 SQLite schema：`CREATE TABLE IF NOT EXISTS token_usage (id INTEGER PRIMARY KEY, ts TEXT, model TEXT, task_type TEXT, prompt_tokens INTEGER, completion_tokens INTEGER, latency_ms INTEGER, key_tier TEXT)`

- [ ] Task 2: 在 LiteLLM 调用层注入追踪 (AC: #1, #3, #4)
  - [ ] 2.1 在 `backend/app/services/llm_service.py`（LiteLLM 封装层）的调用出口处，从 LiteLLM 响应的 `usage` 字段提取 `prompt_tokens` 和 `completion_tokens`
  - [ ] 2.2 从响应的 `model` 字段提取实际模型名（LiteLLM 会填充 Ollama 模型名或 Claude 模型名）
  - [ ] 2.3 调用方在调用 `llm_service.call()` 时传入 `task_type` 参数（必填，不可默认）
  - [ ] 2.4 从 LiteLLM 调用上下文判断 `key_tier`（调用时传入，`user` 或 `system`）
  - [ ] 2.5 调用 `token_tracker.record(...)` 异步写入，写入失败时仅 structlog warning，不影响主流程

- [ ] Task 3: 更新所有 LLM 调用点传入 task_type (AC: #1)
  - [ ] 3.1 搜索项目中所有调用 `llm_service.call()` 的地方，补充 `task_type` 参数
  - [ ] 3.2 对话相关调用（`/chat`、`/discuss`）：`task_type="chat"`
  - [ ] 3.3 评分调用（AutoSCORE 相关）：`task_type="score"`
  - [ ] 3.4 出题调用（检验白板）：`task_type="quiz"`
  - [ ] 3.5 Graphify 提取调用：`task_type="graphify"`
  - [ ] 3.6 确保所有调用点均已更新（无遗漏，不得有未传 task_type 的调用）

- [ ] Task 4: 暴露聚合查询 API 供 Dashboard 使用 (AC: #2)
  - [ ] 4.1 在 `backend/app/api/v1/endpoints/stats.py`（新建）实现 `GET /api/v1/stats/token-usage` 端点
  - [ ] 4.2 接受 query params：`period=day|week|month`、`task_type=chat|score|quiz|graphify|all`
  - [ ] 4.3 返回 `AggregateResponse`：`[{"date": "2026-04-12", "task_type": "chat", "total_tokens": 12345, "call_count": 23, "avg_latency_ms": 820}]`
  - [ ] 4.4 在 `backend/app/api/v1/router.py` 中注册 stats 路由

- [ ] Task 5: Dashboard 展示（Dataview 或前端组件） (AC: #2)
  - [ ] 5.1 评估 Dashboard 展示方式：Dataview 无法直接查 SQLite，因此选用 MCP 工具 `/token_stats` 返回格式化文本，在 Claudian 对话中展示
  - [ ] 5.2 注册 `token_stats` MCP 工具，接受 `period` 参数（默认 `week`），调用 `GET /api/v1/stats/token-usage` 并格式化输出表格
  - [ ] 5.3 格式化示例输出：
    ```
    Token Usage (Past Week)
    task_type  calls  total_tokens  avg_latency
    chat          18        45,230        840ms
    quiz           6        12,100        920ms
    score         12        18,400        310ms
    graphify       3         4,200      1,240ms
    ```

- [ ] Task 6: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 6.1 单元测试：`TokenTracker.record()` 插入一条记录后 `aggregate()` 正确返回
  - [ ] 6.2 单元测试：Ollama 降级场景下 `model` 字段记录 Ollama 模型名
  - [ ] 6.3 单元测试：`key_tier` 字段正确区分 `user` 和 `system`
  - [ ] 6.4 集成测试：`GET /api/v1/stats/token-usage?period=week` 返回 200 且 schema 合法
  - [ ] 6.5 集成测试：一次完整对话 Skill 后，SQLite 中存在对应的 `task_type="chat"` 记录

## Dev Notes

- **LiteLLM 统一层（AR8）**：项目已有 LiteLLM 封装，此 Story 在其出口处注入追踪，不重写调用层
- **SQLite 选择理由**：NFR-INT-4 要求全部数据本地存储。SQLite 是单文件本地数据库，无需新系统依赖，Python 标准库 `sqlite3` 或 `aiosqlite` 均可（检查 `pyproject.toml`，优先用已有依赖）
- **AR8 双层 Key 分离**：用户 Key 用于个人 API 配额，系统 Key 用于后台任务。`key_tier` 字段让用户可以看到哪些操作消耗了其个人配额
- **AR9 Token 成本追踪**：此 Story 是 AR9 的主要实现
- **AR10 离线降级**：Ollama 降级后仍追踪（AC #3），覆盖 AR10 中的降级场景
- **`task_type` 枚举扩展**：如未来出现新的 Skill 类型，在 `Literal` 中追加即可，SQLite 不需要 migration（TEXT 字段）
- **token 成本估算**：此 Story 不做成本金额估算（需要 pricing 表），只追踪 token 数量。金额换算可在未来 Story 中添加
- **structlog 不用标准 logging**：项目规范

### Project Structure Notes

- 新建文件：`backend/app/models/token_usage.py`（`TokenUsageRecord`、`AggregateRow`）
- 新建文件：`backend/app/core/token_tracker.py`（`TokenTracker`）
- 新建文件：`backend/app/api/v1/endpoints/stats.py`（`GET /api/v1/stats/token-usage`）
- 修改文件：`backend/app/services/llm_service.py`（注入追踪）
- 修改文件：所有调用 `llm_service.call()` 的地方（传入 `task_type`）
- 修改文件：`backend/app/api/v1/router.py`（注册 stats 路由）
- 修改文件：MCP 工具定义（注册 `token_stats` 工具）
- 数据文件：`data/token_usage.db`（SQLite，自动创建，gitignore）
- 测试文件：`backend/tests/unit/test_token_tracker.py`、`backend/tests/integration/test_token_stats_api.py`

### References

- [Source: backend/app/services/llm_service.py] — LiteLLM 封装层入口
- [Source: backend/app/core/config.py] — LiteLLM 和 API Key 配置
- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.4] — AC 和 FR 映射
- [AR8] LiteLLM 统一层 + 双层 Key 分离
- [AR9] Token 成本追踪 + 按任务统计
- [AR10] 离线降级 4 场景
- [NFR-DEG-2] Claude API 不可用 → 离线模式

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证 Token 追踪生效** (AC: #1)
   - 执行一次 AI 对话（`/chat`）
   - 在 Claudian 对话中输入：`/token_stats`
   - 应看到一个表格，显示对话类型（chat）下本周至少有 1 次调用记录
   - 如果表格为空或命令不存在，记录 Story 8.4

2. **验证按类型统计** (AC: #2)
   - 依次执行对话、考察、评分操作各至少一次
   - 再次执行 `/token_stats`
   - 表格中应出现 `chat`、`quiz`、`score` 三行，各有对应的调用次数
   - 如果某行缺失，记录 Story 8.4 和缺少的类型

3. **验证降级时仍追踪** (AC: #3)
   - （需开发者临时关闭 Claude API 以触发 Ollama 降级）
   - 降级后执行一次对话
   - `/token_stats` 中应仍然有新增记录，`model` 字段应显示 Ollama 模型名
   - 如果降级后无追踪记录，记录 Story 8.4

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-8.4.1 | pytest | `.venv/bin/pytest tests/unit/test_token_tracker.py -x -q` | 0 failed |
| CP-8.4.2 | pytest | `.venv/bin/pytest tests/integration/test_token_stats_api.py -x -q` | 0 failed |
| CP-8.4.3 | curl | `curl -sf "http://localhost:8001/api/v1/stats/token-usage?period=week" | python3 -c "import sys,json; data=json.load(sys.stdin); assert isinstance(data, list)"` | exit 0 |

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
