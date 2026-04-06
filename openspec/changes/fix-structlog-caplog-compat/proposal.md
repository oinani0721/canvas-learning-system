# Fix structlog ↔ caplog 兼容性 — 解锁 256 个 backend 单元测试

## What & Why

### 问题

本 session（2026-04-06）在为 FR-KG-04 修复预跑 pre-push hook 时发现 `backend/tests/unit/` 有大规模失败：

```
169 failed, 2212 passed, 87 errors  (in 63.06s)
─────────────────────────────────────────────────
总计 256 个问题测试（~10% 失败率）
```

诊断（见 `docs/project-status/fr-exploration/FR-KG-04/` Stage 0 报告）确认根因：

**根因 — structlog `PrintLoggerFactory` 绕过 stdlib logging**

在同 session 之前的 structlog 迁移（commit `793cd53`）中，47 个 `backend/app/services/*.py` 文件从 `logger = logging.getLogger(__name__)` 改成 `logger = structlog.get_logger(__name__)`。但 `backend/app/middleware/logging_middleware.py:31-45` 的全局 structlog 配置使用了 `PrintLoggerFactory`：

```python
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),  # ← 病根
    cache_logger_on_first_use=True,
)
```

`PrintLoggerFactory` 直接 `print()` 到 stdout，完全不走 stdlib `logging` 模块。pytest 的 `caplog` fixture 通过 hook stdlib logging 的 `LogRecord` 工作 —— 所以任何 migrated service 的 `caplog.records` 永远是空的，导致：

```python
# 这类断言全部失败
assert any("Low clustering quality" in r.message for r in caplog.records)
# caplog.records == []  ← 因为 structlog 的输出没进 stdlib
```

### 失败分类

| 类别 | 数量 | 是否本 change 范围 |
|------|------|-------------------|
| **caplog 类失败**（structlog/PrintLoggerFactory 根因）| ~169 | ✅ 本 change 范围 |
| **fixture/import ERROR**（story_30_11, story_30_13 batch 测试）| 87 | ❌ 独立 change（根因未诊断）|

### 为什么不在上一个 session 做

上一 session（FR-KG-04 修复 + 代码同步到 origin）目标是"让本地代码和 origin 仓库同步，让 ChatGPT Deep Research 能看到完整代码"。
为了解锁 push 流程，用户授权一次性 `--no-forget` 绕过 pre-push，并把测试失败作为独立任务拆出来 — 即本 change。

当时采用的最小解锁方案：**revert** `intelligent_grouping_service.py` 一个文件的 structlog 迁移（commit `793cd53` 之后的 unstaged 改动），让 silhouette 测试重新通过。这是一次性应急，不是根因修复，且其他 46 个已 commit 的 structlog 迁移文件仍在 fail 状态。

### 目标

1. **根因修复**：让 `caplog` fixture 能捕获 `structlog.get_logger` 的输出
2. **恢复 47 个服务的 structlog 迁移**（含 `intelligent_grouping_service.py` 重新迁回）
3. **解锁 pre-push hook 完整保护**：pre-push 的 `pytest tests/unit/` 能真正跑完而不只是 0.03s 秒过
4. **不破坏现有生产日志输出**：request_id 注入、JSON 格式、时间戳等行为保持

### 范围

**做**：
- 修改 `logging_middleware.py` 的 structlog 配置：
  - `PrintLoggerFactory()` → `structlog.stdlib.LoggerFactory()`
  - `wrapper_class=structlog.BoundLogger` → `structlog.stdlib.BoundLogger`
  - processors 最后一项 `JSONRenderer()` → `ProcessorFormatter.wrap_for_formatter`
- 初始化 stdlib root logger：`StreamHandler` + `structlog.stdlib.ProcessorFormatter`（final processor 仍是 `JSONRenderer`）
- 在 `backend/app/main.py` 或 `backend/app/core/logging.py` 集中做 stdlib handler 挂载（单次调用，幂等）
- 重新迁移 `intelligent_grouping_service.py`：`logging.getLogger` → `structlog.get_logger`（Stage 0 为应急 revert 过）
- 在 `backend/tests/conftest.py` 添加一个 fixture 或 session-scoped 初始化，确保测试环境下 structlog ↔ stdlib 桥接生效
- 验证 `backend/tests/unit/grouping/test_analyze_canvas.py::test_low_silhouette_score_warning` + 其他 caplog 测试恢复 pass

**不做（延后到独立 change）**：
- 87 个 fixture/import ERROR（story_30_11/30_13 batch 测试）—— 根因未诊断，可能和 `episode_worker`、`DeadLetterStore` 的 DI 链相关
- pre-push hook 的 backend-smoke cwd/PATH 问题（0.03s 秒过，怀疑 `cd backend` 在 post-commit 子进程中失效）
- 性能 benchmark：新 factory 对请求延迟的影响
- 从 `JSONRenderer` 切到 `ConsoleRenderer` 做 dev 环境着色输出
- `structlog` 版本升级
- 清理 print 语句 / 迁移 `logging.warning` 的散落调用

### 影响文件

| 文件 | 改动 |
|------|------|
| `backend/app/middleware/logging_middleware.py` | factory + wrapper_class + processors 最后一步改写 |
| `backend/app/core/logging.py` | 初始化 stdlib handler（用 `ProcessorFormatter` + `JSONRenderer`） |
| `backend/app/main.py` | 启动时调用 logging 初始化函数（如果 core/logging.py 的初始化不是自动的） |
| `backend/app/services/intelligent_grouping_service.py` | 从 stdlib 重新迁回 `structlog.get_logger` |
| `backend/tests/conftest.py` | 添加 session-scoped fixture 保证测试环境 bridge 生效 |

### 验证方式

1. **根因验证**：
   ```bash
   cd backend && .venv/bin/python -m pytest \
     tests/unit/grouping/test_analyze_canvas.py::TestSilhouetteScore::test_low_silhouette_score_warning \
     -xvs --no-cov --override-ini="addopts="
   ```
   修复前 FAIL，修复后 PASS。

2. **全量 caplog 类回归**：
   ```bash
   cd backend && .venv/bin/python -m pytest tests/unit/ \
     -m "not integration" -q --no-header \
     -p no:cacheprovider --override-ini="addopts="
   ```
   预期结果：**≤ 87 errors（仅剩 out-of-scope 的 fixture/import ERROR）, 0 caplog-related failures, pass 数从 2212 提升到 ~2381**。

3. **生产日志格式回归**：
   ```bash
   cd backend && .venv/bin/python -m app.main  # 启动 FastAPI
   # 另一个终端
   curl http://localhost:8001/health
   ```
   预期：log 输出仍是 JSON 格式，含 `request_id`、`level`、`timestamp` 字段。

4. **request_id 链路完整性**：调用任意带 `X-Request-ID` header 的 API，日志中应能看到同一个 request_id 贯穿 middleware → service → Neo4j 调用。

5. **pre-push hook 真正跑测试**：解锁后下一次 `git push origin` 的 pre-push 应该看到 backend-smoke 跑 ~60s 而不是 0.03s。

### 回滚方式

- 所有改动集中在 `logging_middleware.py` + `core/logging.py` + `main.py` + `intelligent_grouping_service.py` + `conftest.py`，共 5 个文件
- 可按文件单独 revert
- `conftest.py` 的 fixture 添加是 additive，不影响现有测试
- 如果新 factory 触发生产日志格式变化，可以通过单独 revert `logging_middleware.py` 快速回到旧状态（代价是 caplog 测试又会失败）

### 风险

- **R1**: `structlog.stdlib.LoggerFactory()` 和 `BoundLogger` 的 API 与原 `BoundLogger` 有细微差异，`bind()`、`contextvars.merge_contextvars` 的行为可能需要调整
- **R2**: stdlib handler 和 structlog processor 的职责划分需要明确 —— 错位会导致 JSON 被双重序列化或时间戳打两次
- **R3**: `cache_logger_on_first_use=True` 和测试环境的 per-test structlog reset 可能冲突 —— 可能需要在 conftest.py 里加 `structlog.reset_defaults()` 清理
- **R4**: 47 个服务中若有 service 使用了 structlog 特有的 `kv` 语法（例如 `logger.info("msg", key=value)`），迁移到 stdlib bridge 后需确认关键字参数仍能被 JSONRenderer 正确渲染
- **R5**: 修复完成后可能暴露更多原先被 caplog 空记录掩盖的断言逻辑错误

### 发现来源
- FR-KG-04 代码同步 session（2026-04-06）Stage 0 诊断 agent 报告
- `backend/app/middleware/logging_middleware.py:31-45` 源码审查
- `structlog` 官方文档（`structlog.stdlib.LoggerFactory` + `ProcessorFormatter.wrap_for_formatter` 的 bridging 模式）
- `backend/tests/unit/grouping/test_analyze_canvas.py::TestSilhouetteScore::test_low_silhouette_score_warning` 作为最小复现测试

## 探索记录

详见 commit 历史：
- `793cd53` — structlog 迁移（本 change 修复的根因所在）
- Stage 0 诊断 agent 的 root cause 分析（见 FR-KG-04 同步 session transcript）
- 未修复时的失败清单：`pytest tests/unit/ -m "not integration"` 输出 `169 failed + 87 errors`
