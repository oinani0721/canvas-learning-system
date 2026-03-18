# Story 1.10: LLM 调用结构化日志基础设施

Status: ready-for-dev

## Story

As a 开发者,
I want 所有 LLM 调用自动记录结构化日志（输入/输出/延迟/token 数/成本），
So that 后续所有 Epic 的 LLM 调用都有完整的可观测性基础。

## Acceptance Criteria

1. **Given** 系统中任何模块调用 LLM（LiteLLM SDK 统一层）
   **When** 调用完成（成功或失败）
   **Then** 自动记录结构化日志：请求 prompt、模型名称、响应内容、延迟 ms、input/output token 数、估算成本
2. **And** 日志存储在本地 SQLite 数据库中（非文件日志）
3. **And** 日志覆盖率 100%（NFR-OBS-01）
4. **And** 日志不包含敏感信息（API Key 脱敏）

## Tasks / Subtasks

- [ ] Task 1: 激活 LiteLLM 回调注册 (AC: #1, #3)
  - [ ] 1.1 在 `backend/app/core/litellm_config.py` 中注册 `LLMCallLogger` 的 `on_success` 和 `on_failure` 回调到 LiteLLM
  - [ ] 1.2 确认所有 LiteLLM 调用路径（chat/embedding/rerank）都经过回调
  - [ ] 1.3 在 `backend/app/main.py` 启动时初始化 LiteLLM 回调配置
- [ ] Task 2: 验证现有 LLMCallLogger 完整性 (AC: #1, #4)
  - [ ] 2.1 审查 `backend/app/middleware/llm_call_logger.py` 的字段完整性（已有：request_id, task_type, model_name, tokens, latency, cost, status, error）
  - [ ] 2.2 确认 API Key 脱敏逻辑有效（白名单方式过滤字段）
  - [ ] 2.3 确认 prompt 内容记录但不含 API Key
- [ ] Task 3: 验证 CostTracker SQLite 持久化 (AC: #2)
  - [ ] 3.1 审查 `backend/app/middleware/cost_tracker.py` 的 `llm_call_logs` 和 `llm_call_logs_daily` 表 Schema
  - [ ] 3.2 确认 batch write（10条/5秒）和 90 天日志轮转工作正常
  - [ ] 3.3 确认 SQLite 数据库路径 `backend/data/llm_call_logs.db` 自动创建
- [ ] Task 4: 创建 LLM Stats API 端点 (AC: #1)
  - [ ] 4.1 在 `backend/app/api/v1/` 创建或更新 system 端点：`GET /api/v1/system/llm-stats`
  - [ ] 4.2 支持查询参数：period（today/week/month/all）、task_type（可选过滤）
  - [ ] 4.3 返回格式：summary + by_task + by_day + errors
- [ ] Task 5: 集成测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 测试 LiteLLM 回调实际触发并写入 SQLite
  - [ ] 5.2 测试 API Key 不出现在日志中
  - [ ] 5.3 测试 stats API 端点返回正确聚合数据

## Dev Notes

### 现有代码资产（⚠️ 已实现 ~90%，需激活+集成）

本 Story 的核心代码已存在于以下文件中（来自旧 Epic 7 / Story 7.2 的实现），**主要工作是激活回调注册和创建 API 端点**：

| 文件 | 状态 | 说明 |
|------|------|------|
| `backend/app/middleware/llm_call_logger.py` | ✅ 已实现 | LLMCallLog Pydantic模型 + LiteLLM success/failure 回调 + batch write + API Key 过滤 |
| `backend/app/middleware/cost_tracker.py` | ✅ 已实现 | SQLite 持久化 + 聚合查询 + 90天轮转 + 健康探针 |
| `backend/app/middleware/logging_middleware.py` | ✅ 已实现 | structlog HTTP 请求日志（非 LLM 特定） |
| `backend/app/core/litellm_config.py` | ❌ TODO | LiteLLM 回调注册——**本 Story 核心工作** |
| `backend/app/api/v1/system.py` | ❌ TODO | `GET /api/v1/system/llm-stats` 端点——**本 Story 核心工作** |

### 关键技术细节

**LiteLLM 回调注册方式：**
```python
import litellm
from app.middleware.llm_call_logger import LLMCallLogger

logger = LLMCallLogger()
litellm.success_callback = [logger.on_success]
litellm.failure_callback = [logger.on_failure]
```

**TaskType 枚举（5 种任务分类）：**
- `CONVERSATION` — chat.py, context_assembler.py
- `SCORING` — autoscore.py
- `EXTRACTION` — conversation_archive.py, error_classifier.py
- `INDEXING` — indexing/pipeline.py
- `QA_CHECK` — faithfulness_check.py

**ErrorCategory 枚举（3 种错误分类）：**
- `LLM_ERROR` — Rate limits, API 错误
- `NETWORK_ERROR` — 超时, 连接失败
- `CONFIG_ERROR` — 认证失败, 模型不存在

**SQLite Schema（已定义在 cost_tracker.py）：**
- `llm_call_logs` — 详细调用记录，索引 task_type/created_at/status
- `llm_call_logs_daily` — 每日聚合摘要（90天压缩）

### Architecture Compliance

- **LLM 调用层**：所有 LLM 调用必须通过 LiteLLM SDK 统一层（architecture.md Cross-Cutting #3）
- **存储**：SQLite/aiosqlite 本地存储（NFR-SEC-01 数据不上传）
- **安全**：API Key 不明文显示、不写日志（NFR-SEC-02）
- **性能**：async 非阻塞写入，不影响 LLM 调用延迟
- **覆盖率**：100% LLM 调用日志（NFR-OBS-01）

### Library/Framework Requirements

| 库 | 版本 | 用途 |
|----|------|------|
| `litellm` | >= 1.40.0 | 统一 LLM SDK + 回调系统 |
| `aiosqlite` | >= 0.19.0 | 异步 SQLite |
| `structlog` | >= 23.0.0 | 结构化日志 |
| `pydantic` | >= 2.5.0 | LLMCallLog Schema 验证 |

### Project Structure Notes

- 后端目录：`backend/app/`
- 中间件目录：`backend/app/middleware/`（已有 llm_call_logger.py, cost_tracker.py）
- API 端点目录：`backend/app/api/v1/`
- 数据库路径：`backend/data/llm_call_logs.db`（自动创建）
- 编辑 Python 文件后执行：`ruff check {file}` + `ruff format --check {file}`

### References

- [Source: epics.md#Story 1.10]
- [Source: architecture.md#Cross-Cutting Concerns #3 LLM调用管理]
- [Source: architecture.md#Cross-Cutting Concerns #7 错误处理与可观测性]
- [Source: prd.md#FR-QA-03 LLM调用结构化日志]
- [Source: prd.md#NFR-OBS-01 LLM调用日志100%覆盖]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
