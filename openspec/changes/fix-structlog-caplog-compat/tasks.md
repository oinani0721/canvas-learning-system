# Fix structlog ↔ caplog 兼容性 — 任务清单

## Task 1: 提取 structlog + stdlib 配置到 core/logging.py
- **文件**:
  - `backend/app/core/logging.py`（修改，新增函数）
  - `backend/app/middleware/logging_middleware.py`（删除模块级 `structlog.configure(...)`）
- **改动**:
  - 在 `core/logging.py` 新增 `configure_logging(level=logging.INFO)` 函数，内部原子化处理两步：
    1. `_configure_structlog()`: 用 `structlog.stdlib.LoggerFactory` + `structlog.stdlib.BoundLogger`，processors 末尾用 `ProcessorFormatter.wrap_for_formatter`
    2. `_configure_stdlib_handler(level)`: root logger 挂 `StreamHandler` + `structlog.stdlib.ProcessorFormatter`（foreign_pre_chain 含 merge_contextvars, add_log_level, TimeStamper；processors 含 remove_processors_meta + JSONRenderer）
  - 幂等保护：`if getattr(configure_logging, "_configured", False): return`
  - 从 `logging_middleware.py` 删除模块级 `structlog.configure(...)`，只保留 `LoggingMiddleware` class
- **验证**:
  - `python -c "from app.core.logging import configure_logging; configure_logging(); configure_logging()"`（幂等检查）
  - `grep -n "structlog.configure" backend/app/ -r` 应只有 1 处在 core/logging.py
- **依赖**: 无
- **状态**: [ ] 未开始

## Task 2: main.py 启动阶段调用 configure_logging
- **文件**: `backend/app/main.py`
- **改动**:
  - 在 `lifespan` 或 `app = FastAPI(...)` 之前 import 并调用 `configure_logging()`
  - 位置要早于任何 `from app.services import ...`，以确保 service import 时 logger 已就绪
- **验证**:
  - 启动 FastAPI：`.venv/bin/python -m app.main`
  - `curl http://localhost:8001/health` 应看到 JSON 格式的 access log
  - log 行应包含 `"request_id"`, `"level"`, `"timestamp"` 字段
- **依赖**: Task 1
- **状态**: [ ] 未开始

## Task 3: conftest.py 添加测试环境 fixture
- **文件**: `backend/tests/conftest.py`
- **改动**:
  - 添加 `_configure_logging_for_tests` session-scoped autouse fixture：调用 `configure_logging(level=logging.DEBUG)` + 设置 `logging.getLogger().propagate = True`
  - 添加 `_reset_structlog_contextvars` function-scoped autouse fixture：测试前后各调一次 `structlog.contextvars.clear_contextvars()`
- **验证**:
  - 运行最小 caplog 测试：
    ```bash
    cd backend && .venv/bin/python -m pytest \
      tests/unit/grouping/test_analyze_canvas.py::TestSilhouetteScore::test_low_silhouette_score_warning \
      -xvs --no-cov --override-ini="addopts="
    ```
    预期：PASS（修复前 FAIL）
  - 确认 `request_id` 不跨测试泄露：手动写一个临时测试 A 调 `bind_contextvars(request_id="test-A")`，测试 B 读 `get_contextvars()` 应为空
- **依赖**: Task 1, Task 2
- **状态**: [ ] 未开始

## Task 4: 重新迁移 intelligent_grouping_service.py 到 structlog
- **文件**: `backend/app/services/intelligent_grouping_service.py`
- **改动**:
  - `import logging` → 保留（有些地方可能仍需 stdlib 常量）
  - 重新添加 `import structlog`
  - `logger = logging.getLogger(__name__)` → `logger = structlog.get_logger(__name__)`
  - 注意：Stage 0 为了解锁 silhouette 测试做过 revert，现在修复了 bridge 所以可以迁回
- **验证**:
  - 重跑 silhouette 测试：
    ```bash
    cd backend && .venv/bin/python -m pytest \
      tests/unit/grouping/test_analyze_canvas.py \
      -xvs --no-cov --override-ini="addopts="
    ```
    预期：7/7 PASS（确认 bridge 对 structlog logger 也有效，不只是 stdlib logger）
- **依赖**: Task 3（必须先跑通 stdlib logger 场景）
- **状态**: [ ] 未开始

## Task 5: 全量 caplog 类回归验收
- **文件**: 无改动，只跑测试
- **改动**: N/A
- **验证**:
  ```bash
  cd backend && .venv/bin/python -m pytest tests/unit/ \
    -m "not integration" \
    --ignore=tests/unit/test_story_30_11_batch_parallel.py \
    --ignore=tests/unit/test_story_30_13_batch_idempotency.py \
    -q --no-header \
    -p no:cacheprovider --override-ini="addopts=" \
    --no-cov 2>&1 | tail -10
  ```
  - 预期结果：`2381 passed, 0 failed`（pass 数从 2212 升到 ~2381，不含被 ignore 的 87 个 errors）
  - 若出现新 failure（非 caplog 相关）：按 triage 规则处理：
    1. 真 bug → 单独提新 change 修复
    2. 断言过严 → 在本 change 内调整
    3. out-of-scope → 加 `@pytest.mark.skip(reason="...")` 并记录
- **依赖**: Task 1-4 全部完成
- **状态**: [ ] 未开始

## Task 6: 生产日志格式回归（人工验证）
- **文件**: 无改动
- **改动**: N/A
- **验证**:
  1. 启动 backend：`.venv/bin/python -m app.main`
  2. 发请求（带自定义 X-Request-ID）:
     ```bash
     curl -H "X-Request-ID: test-trace-001" http://localhost:8001/health
     ```
  3. 检查 terminal 输出：
     - [ ] log 行是合法 JSON（`echo "<line>" | jq .` 成功）
     - [ ] 含 `"request_id": "test-trace-001"`
     - [ ] 含 `"level"`, `"timestamp"`, `"event"` 或 `"message"` 字段
     - [ ] 含 `"logger"` 字段（源头定位）
  4. 检查同一请求的所有 log 行 `request_id` 一致（贯穿 middleware → service → Neo4j 客户端）
- **依赖**: Task 2
- **状态**: [ ] 未开始

## Task 7: pre-push hook 真实跑测试验证
- **文件**: 无改动，只触发 hook
- **改动**: N/A
- **验证**:
  1. 在本 change 的 feature 分支做一个 no-op 修改（例如 touch 一个 .py 文件的 trailing whitespace）
  2. `git add <file> && git commit -m "test: verify pre-push runs tests"`
  3. 观察 post-commit hook 输出的 `backend-smoke` 耗时
  4. 预期：**≥ 30 秒**（之前只有 0.03s，说明 cwd/PATH 问题实际没有跑测试）
  5. 如果仍是 0.03s：说明 pre-push hook 的 cwd/PATH 问题独立于本 change，需要单开 task 修复 hook 脚本
- **依赖**: Task 5 通过
- **状态**: [ ] 未开始

## Task 8: 更新 proposal.md 的"发现来源"与 commit
- **文件**: `openspec/changes/fix-structlog-caplog-compat/proposal.md`
- **改动**:
  - 在"发现来源"补充本 change 完成后的最终测试数据（修复后的 `pass/fail/error` 具体数字）
  - 更新 tasks.md 所有状态为 `[x]`
- **验证**: `git diff openspec/changes/fix-structlog-caplog-compat/` 仅影响本 change 目录
- **依赖**: Task 5, Task 7 均通过
- **状态**: [ ] 未开始

## Task 9: archive change
- **文件**: 移动 `openspec/changes/fix-structlog-caplog-compat/` → `openspec/changes/archive/<date>-fix-structlog-caplog-compat/`
- **改动**: 按项目 OpenSpec archive 规范（如果有 `openspec` CLI 就 `openspec archive`，否则 `git mv`）
- **验证**: `ls openspec/changes/archive/` 含新条目
- **依赖**: Task 8 完成
- **状态**: [ ] 未开始

---

## 执行顺序建议

```
Task 1 (core/logging.py)
    ↓
Task 2 (main.py 调用)
    ↓
Task 3 (conftest.py fixture) ← 此时跑 silhouette 测试 PASS
    ↓
Task 4 (intelligent_grouping_service 迁回 structlog) ← 再跑 silhouette 测试 PASS
    ↓
Task 5 (全量 caplog 回归)  ← 关键验收点
    ↓
Task 6 (生产日志人工验证)
    ↓
Task 7 (pre-push hook 验证)
    ↓
Task 8 (回填 proposal.md 数据 + commit)
    ↓
Task 9 (archive)
```

**阻塞点**：Task 5 如果出现新 failure，必须完成 triage 才能进 Task 6。

**预计时长**：Task 1-4 约 1-1.5 小时；Task 5 跑测试 ~2 分钟 + triage 按结果而定；Task 6-7 约 20 分钟；Task 8-9 约 10 分钟。乐观情况 2 小时内结束，悲观情况（triage 发现真 bug 要修）半天。

## 回滚清单

如果任何 task 完成后发现生产日志坏了或者新 failure 无法快速修：
1. `git revert <commit-hash>` —— 所有改动在本 change 相关的 commit 里，互不依赖
2. 验证 `.venv/bin/python -m app.main` 能启动且日志是旧格式
3. 这次 change 进 archive 时标记为 "reverted, root cause 未完全解决"

## 跨 change 遗留问题（明确不在本 change 处理）

- **87 个 story_30_11/30_13 ERROR**：独立诊断，可能需要新 change `fix-batch-story-test-fixtures`
- **pre-push hook cwd 问题**：Task 7 如果揭示这是根因，需要新 change `fix-lefthook-cwd-propagation`
- **`@pytest.mark.broken` marker**：如果 Task 5 的 triage 发现需要标记 skip 的测试超过 3 个，考虑单开 change 建立 triage 机制
