# Fix structlog ↔ caplog 兼容性 — 设计方案

## 背景

当前 `logging_middleware.py` 用 `PrintLoggerFactory` 配置 structlog，绕过 stdlib logging，导致 `caplog` 无效。修复目标是改用 `structlog.stdlib.LoggerFactory` + `ProcessorFormatter` 的 bridging 模式，让 structlog 事件最终通过 stdlib `LogRecord` 流出，既保留 JSON 结构化输出和 `contextvars` 支持，也恢复 pytest `caplog` 的可见性。

## 架构决策

### D1: 采用 structlog stdlib bridging 模式（替代 PrintLoggerFactory）

**问题**：`PrintLoggerFactory` 直接 `print()` 到 stdout，`caplog` 看不到。

**方案**：改用 structlog 官方推荐的 stdlib bridging 模式。structlog 事件经过 processors 处理后转换成 stdlib `LogRecord`，由 stdlib `Handler` + `Formatter` 输出最终 JSON。

```python
# logging_middleware.py（修改后）
import logging
import structlog

shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

structlog.configure(
    processors=shared_processors + [
        # 桥接到 stdlib Formatter — 不再用 JSONRenderer 作为 structlog 终点
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),   # ← 关键改动
    wrapper_class=structlog.stdlib.BoundLogger,         # ← 关键改动
    cache_logger_on_first_use=True,
)
```

**理由**：这是 structlog 官方文档 "Rendering Using structlog-based Formatters Within logging" 章节的标准模式，被 Django、FastAPI 社区广泛使用。`ProcessorFormatter.wrap_for_formatter` 是结构化事件 → stdlib 的 adapter，让 `logger.info("...")` 既能被 `caplog.records` 捕获（因为它现在走了 stdlib 的 `LogRecord`），又能保留最终 JSON 输出。

**替代方案（已否决）**：
- **A**: 写自定义 handler 把 `print()` 重定向 — 脆弱，会破坏其他 stdout 输出
- **B**: Monkey-patch `caplog` 让它 hook structlog — 侵入测试框架，未来 pytest 升级风险
- **C**: 在 conftest 里给每个测试 swap factory — 意味着 dev/test 行为不一致，难以排查
- **D**: 放弃 structlog 回到 stdlib logging — 丢失 47 个服务已做的 observability 工作

### D2: stdlib root handler 单次初始化（marker-based ownership）

**问题**：D1 要求 stdlib root logger 配一个 handler 用 `ProcessorFormatter` 渲染最终 JSON。这个初始化不能重复，否则会有多行重复日志。

**关键陷阱（2026-04-07 实证发现）**：当前 `core/logging.py:62-64` 的 `setup_logging()` 在挂新 handler 之前**显式清空所有 root handlers**：

```python
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
```

如果 `configure_logging()` 在 pytest session 中被调用（即使是被 conftest fixture 调用），这段"全量清空"会**把 pytest `LogCaptureHandler` 一并踢掉**——caplog.records 永远为空，bridging 形同虚设。pytest 文档也明确警告这种"clear-all-then-add"模式。

朴素的 `if root_logger.hasHandlers(): return` 也不可靠：pytest 的 `_LiveLoggingStreamHandler` 在 session start 就会 attach，导致 `configure_logging()` 直接 return early，**我们的 JSON handler 永远没机会装上**。

**方案**：marker-based handler ownership。我们装的 handler 都打上 `_canvas_setup_logging_owned = True` 属性。重入时**只清自己装的**，其他（包括 pytest 的）一律保留。

```python
# core/logging.py（新增函数 — replaces buggy setup_logging）
import io
import logging
import sys
import structlog

OWNED_MARKER = "_canvas_setup_logging_owned"

def configure_logging(level: int = logging.INFO) -> None:
    """
    Idempotent + caplog-safe logging setup.

    1. Configure structlog with stdlib factory + ProcessorFormatter bridging
    2. Mount a JSON-rendering StreamHandler on root logger
    3. On re-entry, remove only handlers WE previously installed (marker-based),
       leaving pytest LogCaptureHandler / LiveLoggingStreamHandler intact.
    """
    if getattr(configure_logging, "_configured", False):
        return

    # 1. Configure structlog (idempotent at structlog level via cache_logger_on_first_use)
    _configure_structlog()

    # 2. Mount stdlib JSON handler on root, preserving non-owned handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Marker-based incremental cleanup: only remove handlers we installed previously
    for handler in root_logger.handlers[:]:
        if getattr(handler, OWNED_MARKER, False):
            root_logger.removeHandler(handler)

    # UTF-8 wrapping (preserve Story 12.I.1 / 12.J.1 Windows compat)
    utf8_stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )

    json_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    json_handler = logging.StreamHandler(utf8_stdout)
    json_handler.setLevel(level)
    json_handler.setFormatter(json_formatter)
    setattr(json_handler, OWNED_MARKER, True)  # mark as owned
    root_logger.addHandler(json_handler)

    # Reduce noise from third-party libraries (preserved from setup_logging)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    configure_logging._configured = True
```

`app/main.py` 启动阶段调用（**replaces** the existing `setup_logging(log_level=settings.LOG_LEVEL)` call at main.py:66）：
```python
from app.core.logging import configure_logging
configure_logging(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
```

**理由**：
- 集中配置，避免分散
- Marker-based 重入安全：pytest LogCaptureHandler 永不被踢
- 保留 UTF-8 wrapping 兼容 Windows（Story 12.I.1 / 12.J.1）
- 删除买一送一：旧 `setup_logging()` 和 `ContextVarsFilter` 一起作废（contextvars 注入由 `foreign_pre_chain` 的 `merge_contextvars` 接管）

### D3: `structlog.configure` 的调用位置

**问题**：当前 `structlog.configure(...)` 写在 `logging_middleware.py` 模块级，**副作用导向的 import-time 初始化**。测试环境如果在 structlog.configure 跑之前就 import service 并调 `logger.info`，会拿到未配置的 logger。

**方案**：把 `structlog.configure(...)` 从 `logging_middleware.py` 移到 `core/logging.py`，并在 `configure_stdlib_logging()` 同一函数里一起调。`logging_middleware.py` 只保留 `LoggingMiddleware` class（HTTP request log 逻辑），不再做全局配置。

```python
# core/logging.py（完整结构）
def configure_logging(level: int = logging.INFO) -> None:
    """
    Idempotent logging setup:
    1. configure structlog processors + stdlib factory
    2. mount stdlib root handler with ProcessorFormatter
    """
    if getattr(configure_logging, "_configured", False):
        return
    _configure_structlog()
    _configure_stdlib_handler(level)
    configure_logging._configured = True
```

**理由**：让 "structlog setup" 和 "stdlib handler setup" 原子化，避免顺序问题；`logging_middleware.py` 回归单一职责（middleware 本身）。

**替代方案（已否决）**：
- 保留在 `logging_middleware.py`：符合最小改动原则，但和 D2 的"幂等初始化"冲突（middleware 是每次 FastAPI 实例化时挂载，可能在 pytest 里被多次 import）。

### D4: `intelligent_grouping_service.py` 的重新迁移策略

**问题**：Stage 0 为了解锁 silhouette 测试，把这个文件的 logger 从 `structlog.get_logger` revert 回 `logging.getLogger`（见 commit `793cd53` 的 unstaged 改动，最终被合并进 Stage 5 的 refactor commit）。修复完 D1-D3 后，这个文件需要重新迁回 structlog 以保持一致性。

**方案**：作为 Task 5 最后一步执行。顺序很重要：
1. 先完成 D1-D3 的 bridging 修复
2. 运行 silhouette 测试验证 `caplog` 能看到 stdlib logger
3. 再把 `intelligent_grouping_service.py` 的 logger 改回 `structlog.get_logger`
4. 再跑一次 silhouette 测试验证 `caplog` 能看到 structlog logger（经 bridging）

这样测试从 stdlib → structlog 迁移过程中每一步都可验证。

**理由**：测试驱动的迁移顺序，任何一步失败都能精确定位是 D1-D3 的 bridging bug 还是 structlog API 差异。

### D5: `conftest.py` 测试环境 fixture

**问题**：pytest 每次收集测试时会触发 `app.main` import，间接触发 `configure_logging()`。但测试之间的 structlog `contextvars` 不一定干净（比如上一个测试设了 `request_id`，下一个测试还残留）。

**方案**：在 `backend/tests/conftest.py` 加两个 fixture：

```python
# conftest.py 新增
import logging
import pytest
import structlog

@pytest.fixture(autouse=True, scope="session")
def _configure_logging_for_tests():
    """Ensure logging is bridged for caplog before any test runs."""
    from app.core.logging import configure_logging
    configure_logging(level=logging.DEBUG)  # DEBUG so caplog catches everything
    # Force root logger to propagate — pytest's LogCaptureHandler needs this
    logging.getLogger().propagate = True

@pytest.fixture(autouse=True)
def _reset_structlog_contextvars():
    """Clear structlog contextvars between tests to prevent cross-contamination."""
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()
```

**理由**：
- 第一个 fixture 是 session-scoped + autouse，保证 `caplog` 在任何测试跑之前已经 bridge 好
- 第二个 fixture 是 function-scoped + autouse，防止 request_id 泄露（见 R3）
- `propagate = True` 是关键 —— pytest `LogCaptureHandler` 通过 propagation 捕获日志

### D6: 诊断 87 个 ERROR 的分离策略

**问题**：全量 pytest 有 87 个 ERROR，来自 `test_story_30_11_batch_parallel.py` 和 `test_story_30_13_batch_idempotency.py`。这些不是 caplog 问题（是 fixture/import 错误），但它们和本 change 的成功判定交织 —— 如果不排除，"本 change 成功"的判定会被污染。

**方案**：
1. 不修复这 87 个 ERROR（out of scope，明确写在 proposal.md）
2. 验证命令明确用 `--ignore=tests/unit/test_story_30_11_batch_parallel.py --ignore=tests/unit/test_story_30_13_batch_idempotency.py` 或通过 pytest marker `-m "not broken"` 排除
3. 在 Task 6 的验收命令里写清楚：修复后应该是 `2381 passed, 0 failed, 87 errors`（errors 数量不变，但 failures 归零）

**理由**：明确 scope 边界，让后续的"诊断 87 个 ERROR"作为独立 change（例如 `fix-batch-story-test-fixtures`）。

## 数据流对比

### 修复前（当前）

```
service 调用 logger.info("msg")
    ↓
structlog.BoundLogger.info
    ↓
processors 链（add_log_level, TimeStamper, JSONRenderer）
    ↓
PrintLoggerFactory → print("json-line") 到 stdout
    ↓
❌ 绕过 stdlib logging
    ↓
caplog.records == []
```

### 修复后（bridging）

```
service 调用 logger.info("msg")
    ↓
structlog.stdlib.BoundLogger.info
    ↓
shared_processors (add_log_level, TimeStamper, ...)
    ↓
ProcessorFormatter.wrap_for_formatter  ← 转成 stdlib 事件
    ↓
stdlib logging.Logger (root) 派发
    ├─→ ✅ pytest LogCaptureHandler → caplog.records
    └─→ StreamHandler → ProcessorFormatter.format
            ↓
            JSONRenderer → 最终 JSON 行输出到 stdout
```

## 兼容性矩阵

| 调用 | 修复前 | 修复后 |
|------|--------|--------|
| `structlog.get_logger().info("msg")` | ✅ JSON 输出 / ❌ 不进 caplog | ✅ JSON 输出 + ✅ 进 caplog |
| `logging.getLogger().info("msg")` (e.g. 3rd-party lib) | ✅ 进 stdlib 但无 JSON | ✅ JSON 输出 + ✅ 进 caplog |
| `logger.info("msg", user_id="u1")` (structlog kv) | ✅ 输出含 user_id | ✅ 输出含 user_id（经 ProcessorFormatter）|
| `structlog.contextvars.bind_contextvars(request_id=...)` | ✅ 注入 | ✅ 注入（shared_processors 保留 merge_contextvars）|
| pytest `caplog.records` | ❌ 空 | ✅ 有记录 |
| pytest `caplog.text` | ❌ 空 | ✅ 包含 rendered 消息 |

## 已知风险与缓解

- **R1 (BoundLogger API)**: `structlog.BoundLogger` → `structlog.stdlib.BoundLogger` 的主要差异是后者更严格遵循 stdlib 的方法签名。实测时需关注 `logger.exception(...)` 和 `logger.debug(...)` 的 kwargs 传递。缓解：Task 3 跑全量 unit test 后，个别 case 用 grep 定位并修正。
- **R2 (双序列化)**: 如果同时在 `structlog.configure` 的 processors 末尾和 `ProcessorFormatter` 的 processors 末尾都放 `JSONRenderer`，会出现 JSON 被渲染两次。缓解：D1 的 processors 链末尾已改成 `ProcessorFormatter.wrap_for_formatter`（不是 JSONRenderer），`JSONRenderer` 只保留在 `ProcessorFormatter.processors` 里。
- **R3 (contextvars 泄露)**: D5 的 `_reset_structlog_contextvars` fixture 已处理。
- **R4 (3rd-party kwargs)**: 如果某个 service 用了 `logger.info("msg", extra={"foo": "bar"})`（stdlib 风格）而不是 `logger.info("msg", foo="bar")`（structlog 风格），混用会导致 `extra` 字段丢失。缓解：Task 3 的 grep 审查会扫出这些混用。
- **R5 (测试暴露新 bug)**: 恢复 caplog 可见性后，之前因为"断言在空列表上返回 False 但代码路径本身是 buggy 的"可能暴露新 bug。缓解：Task 6 的回归验收时，对任何新出现的 failure 做三选一 triage — 真 bug 修 / 断言过严调松 / out-of-scope 标记。

## 不做的决策

- 不升级 structlog 版本（当前 25.4.0 足够）
- 不改输出格式（JSON + request_id 保持）
- 不引入 `python-json-logger` 或其他第三方 JSON formatter
- 不分 dev/prod 两套配置（一套 JSON 够用，dev 可以通过 `jq` 美化输出）
- 不做性能 benchmark（bridging 增加 ~1 层函数调用，可忽略）
